"""
Background job service for the crawler microservice.
Handles long-running crawl tasks asynchronously using Redis Queue.
"""

import asyncio
import time
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from rq import Queue, Worker, Connection
from rq.job import Job
import redis

from app.models.crawl_models import CrawlRequest, CrawlResult, CrawlStatus, CrawlTask
from app.core.config import get_settings
from app.core.logging import get_logger, crawler_logger
from app.core.exceptions import BackgroundJobError


class BackgroundJobService:
    """Service for managing background job processing."""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.redis_conn: Optional[redis.Redis] = None
        self.crawl_queue: Optional[Queue] = None
        self.initialized = False
    
    async def initialize(self) -> None:
        """Initialize the background job service."""
        if self.initialized:
            return
        
        try:
            # Configure Redis connection
            self.redis_conn = redis.Redis.from_url(self.settings.redis_url)
            
            # Test Redis connection
            self.redis_conn.ping()
            
            # Create job queue
            self.crawl_queue = Queue('crawl_tasks', connection=self.redis_conn)
            
            self.initialized = True
            self.logger.info("Background job service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize background job service: {e}")
            raise BackgroundJobError("initialization", str(e))
    
    async def enqueue_crawl_task(self, task_id: str, request: CrawlRequest) -> Job:
        """
        Enqueue a crawl task for background processing.
        
        Args:
            task_id: Unique task identifier
            request: CrawlRequest object
            
        Returns:
            RQ Job object
        """
        if not self.initialized:
            raise BackgroundJobError("enqueue", "Background job service not initialized")
        
        try:
            # Convert request to dict for serialization
            request_data = request.dict()
            
            # Enqueue job with timeout
            job = self.crawl_queue.enqueue(
                execute_crawl_job,
                task_id,
                request_data,
                job_timeout='1h',  # 1 hour timeout for long crawls
                result_ttl=86400,  # Keep results for 24 hours
                failure_ttl=3600   # Keep failed jobs for 1 hour
            )
            
            crawler_logger.logger.info(
                "Crawl task enqueued",
                task_id=task_id,
                job_id=job.id,
                url=request.url,
                event_type="task_enqueued"
            )
            
            return job
            
        except Exception as e:
            self.logger.error(f"Failed to enqueue crawl task {task_id}: {e}")
            raise BackgroundJobError("enqueue", str(e), {"task_id": task_id})
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a background job.
        
        Args:
            job_id: RQ job identifier
            
        Returns:
            Dict containing job status information
        """
        if not self.initialized:
            raise BackgroundJobError("get_status", "Background job service not initialized")
        
        try:
            job = Job.fetch(job_id, connection=self.redis_conn)
            
            return {
                "job_id": job_id,
                "status": job.get_status(),
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "ended_at": job.ended_at.isoformat() if job.ended_at else None,
                "result": job.result if job.is_finished else None,
                "exc_info": job.exc_info if job.is_failed else None
            }
        except Exception as e:
            self.logger.error(f"Failed to get job status {job_id}: {e}")
            raise BackgroundJobError("get_status", str(e), {"job_id": job_id})
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the job queue.
        
        Returns:
            Dict containing queue statistics
        """
        if not self.initialized:
            raise BackgroundJobError("get_stats", "Background job service not initialized")
        
        try:
            return {
                "queue_name": self.crawl_queue.name,
                "queued_jobs": len(self.crawl_queue),
                "failed_jobs": len(self.crawl_queue.failed_job_registry),
                "finished_jobs": len(self.crawl_queue.finished_job_registry),
                "started_jobs": len(self.crawl_queue.started_job_registry),
                "scheduled_jobs": len(self.crawl_queue.scheduled_job_registry),
                "workers": Worker.count(connection=self.redis_conn)
            }
        except Exception as e:
            self.logger.error(f"Failed to get queue stats: {e}")
            raise BackgroundJobError("get_stats", str(e))
    
    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a queued or running job.
        
        Args:
            job_id: RQ job identifier
            
        Returns:
            True if job was cancelled, False otherwise
        """
        if not self.initialized:
            raise BackgroundJobError("cancel", "Background job service not initialized")
        
        try:
            job = Job.fetch(job_id, connection=self.redis_conn)
            
            if job.get_status() in ['queued', 'started']:
                job.cancel()
                crawler_logger.logger.info(
                    "Job cancelled",
                    job_id=job_id,
                    event_type="job_cancelled"
                )
                return True
            else:
                crawler_logger.logger.warning(
                    "Cannot cancel job - not in cancellable state",
                    job_id=job_id,
                    status=job.get_status(),
                    event_type="job_cancel_failed"
                )
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to cancel job {job_id}: {e}")
            raise BackgroundJobError("cancel", str(e), {"job_id": job_id})
    
    async def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """
        Clean up old completed and failed jobs.
        
        Args:
            max_age_hours: Maximum age of jobs to keep (in hours)
            
        Returns:
            Number of jobs cleaned up
        """
        if not self.initialized:
            raise BackgroundJobError("cleanup", "Background job service not initialized")
        
        try:
            cleaned_count = 0
            cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
            
            # Clean up finished jobs
            for job_id in self.crawl_queue.finished_job_registry.get_job_ids():
                job = Job.fetch(job_id, connection=self.redis_conn)
                if job.ended_at and job.ended_at.timestamp() < cutoff_time:
                    job.delete()
                    cleaned_count += 1
            
            # Clean up failed jobs
            for job_id in self.crawl_queue.failed_job_registry.get_job_ids():
                job = Job.fetch(job_id, connection=self.redis_conn)
                if job.ended_at and job.ended_at.timestamp() < cutoff_time:
                    job.delete()
                    cleaned_count += 1
            
            if cleaned_count > 0:
                crawler_logger.logger.info(
                    "Cleaned up old jobs",
                    cleaned_count=cleaned_count,
                    max_age_hours=max_age_hours,
                    event_type="job_cleanup"
                )
            
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old jobs: {e}")
            raise BackgroundJobError("cleanup", str(e))
    
    async def start_worker(self) -> None:
        """Start a worker process to process background jobs."""
        if not self.initialized:
            raise BackgroundJobError("start_worker", "Background job service not initialized")
        
        with Connection(self.redis_conn):
            worker = Worker([self.crawl_queue], connection=self.redis_conn)
            crawler_logger.logger.info(
                "Starting background job worker",
                event_type="worker_started"
            )
            worker.work()
    
    async def shutdown(self) -> None:
        """Shutdown the background job service."""
        if self.redis_conn:
            self.redis_conn.close()
        self.initialized = False
        self.logger.info("Background job service shutdown complete")


# Global functions for backward compatibility and worker processes
def execute_crawl_job(task_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a crawl job in the background.
    This function runs in a separate worker process.
    
    Args:
        task_id: Unique task identifier
        request_data: Serialized CrawlRequest data
        
    Returns:
        Dict containing job results
    """
    start_time = time.time()
    
    try:
        # Log job start
        crawler_logger.background_job_started(
            job_id=task_id,
            job_type="crawl",
            url=request_data.get("url")
        )
        
        # Reconstruct CrawlRequest from data
        request = CrawlRequest(**request_data)
        
        # Execute crawl
        result = asyncio.run(_execute_crawl_async(request))
        
        # Update result with task ID
        result.task_id = task_id
        result.status = CrawlStatus.COMPLETED
        result.completed_at = datetime.now()
        result.duration = time.time() - start_time
        
        # Log completion
        crawler_logger.background_job_completed(
            job_id=task_id,
            job_type="crawl",
            duration=result.duration,
            pages_crawled=result.total_pages,
            url=request.url
        )
        
        return {
            "success": True,
            "task_id": task_id,
            "status": result.status.value,
            "pages_crawled": result.total_pages,
            "duration": result.duration
        }
        
    except Exception as e:
        # Log failure
        crawler_logger.background_job_failed(
            job_id=task_id,
            job_type="crawl",
            error=str(e),
            url=request_data.get("url")
        )
        
        return {
            "success": False,
            "task_id": task_id,
            "error": str(e)
        }


async def _execute_crawl_async(request: CrawlRequest) -> CrawlResult:
    """Execute crawl asynchronously."""
    # This would need to be imported from the crawler service
    # For now, we'll create a placeholder
    from app.services.crawler import CrawlerService
    from app.services.storage import StorageService
    from app.services.rate_limiter import RateLimitService
    
    # Create temporary services for background execution
    storage_service = StorageService()
    await storage_service.initialize()
    
    rate_limiter = RateLimitService()
    
    crawler = CrawlerService(storage_service, rate_limiter)
    
    async with crawler:
        return await crawler.crawl_website(request)
