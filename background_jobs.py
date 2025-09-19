"""
Background job processing using RQ (Redis Queue) for scalable crawling.
Handles long-running crawl tasks asynchronously.
"""
import os
import time
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from rq import Queue, Worker, Connection
from rq.job import Job
import redis
import logging

from models import CrawlRequest, CrawlResult, CrawlStatus, CrawlTask
from crawler_service import WebCrawler
from storage import StorageManager, create_storage_backend
from config import settings
from logging_config import crawler_logger

# Configure Redis connection
redis_conn = redis.Redis.from_url(settings.REDIS_URL)

# Create job queue
crawl_queue = Queue('crawl_tasks', connection=redis_conn)

# Initialize storage manager
storage_backend = create_storage_backend(
    storage_type=settings.STORAGE_TYPE,
    data_dir=settings.STORAGE_DATA_DIR,
    connection_string=settings.MONGODB_URL,
    database_name=settings.MONGODB_DATABASE,
    hosts=settings.ELASTICSEARCH_HOSTS,
    cloud_id=settings.ELASTICSEARCH_CLOUD_ID,
    api_key=settings.ELASTICSEARCH_API_KEY,
    username=settings.ELASTICSEARCH_USERNAME,
    password=settings.ELASTICSEARCH_PASSWORD,
    index_prefix=settings.ELASTICSEARCH_INDEX_PREFIX
)
storage_manager = StorageManager(storage_backend)


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
        
        # Update task status to in progress
        asyncio.run(storage_manager.update_task(task_id, {
            "status": CrawlStatus.IN_PROGRESS,
            "updated_at": datetime.now()
        }))
        
        # Reconstruct CrawlRequest from data
        request = CrawlRequest(**request_data)
        
        # Execute crawl
        result = asyncio.run(_execute_crawl_async(request))
        
        # Update task with result
        result.task_id = task_id
        result.status = CrawlStatus.COMPLETED
        result.completed_at = datetime.now()
        result.duration = time.time() - start_time
        
        # Save result
        asyncio.run(storage_manager.save_crawl_result(result))
        
        # Update task status
        asyncio.run(storage_manager.update_task(task_id, {
            "status": result.status,
            "updated_at": datetime.now()
        }))
        
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
        
        # Update task status to failed
        try:
            asyncio.run(storage_manager.update_task(task_id, {
                "status": CrawlStatus.FAILED,
                "updated_at": datetime.now()
            }))
            
            # Create error result
            error_result = CrawlResult(
                task_id=task_id,
                status=CrawlStatus.FAILED,
                errors=[str(e)],
                started_at=datetime.now(),
                completed_at=datetime.now(),
                duration=time.time() - start_time
            )
            asyncio.run(storage_manager.save_crawl_result(error_result))
            
        except Exception as storage_error:
            crawler_logger.logger.error(
                "Failed to update task status after error",
                task_id=task_id,
                error=str(storage_error),
                event_type="storage_error"
            )
        
        return {
            "success": False,
            "task_id": task_id,
            "error": str(e)
        }


async def _execute_crawl_async(request: CrawlRequest) -> CrawlResult:
    """Execute crawl asynchronously."""
    async with WebCrawler() as crawler:
        return await crawler.crawl_website(request)


def enqueue_crawl_task(task_id: str, request: CrawlRequest) -> Job:
    """
    Enqueue a crawl task for background processing.
    
    Args:
        task_id: Unique task identifier
        request: CrawlRequest object
        
    Returns:
        RQ Job object
    """
    # Convert request to dict for serialization
    request_data = request.dict()
    
    # Enqueue job with timeout
    job = crawl_queue.enqueue(
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


def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the status of a background job.
    
    Args:
        job_id: RQ job identifier
        
    Returns:
        Dict containing job status information
    """
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        
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
        crawler_logger.logger.error(
            "Failed to get job status",
            job_id=job_id,
            error=str(e),
            event_type="job_status_error"
        )
        return None


def get_queue_stats() -> Dict[str, Any]:
    """
    Get statistics about the job queue.
    
    Returns:
        Dict containing queue statistics
    """
    try:
        return {
            "queue_name": crawl_queue.name,
            "queued_jobs": len(crawl_queue),
            "failed_jobs": len(crawl_queue.failed_job_registry),
            "finished_jobs": len(crawl_queue.finished_job_registry),
            "started_jobs": len(crawl_queue.started_job_registry),
            "scheduled_jobs": len(crawl_queue.scheduled_job_registry),
            "workers": Worker.count(connection=redis_conn)
        }
    except Exception as e:
        crawler_logger.logger.error(
            "Failed to get queue stats",
            error=str(e),
            event_type="queue_stats_error"
        )
        return {}


def cancel_job(job_id: str) -> bool:
    """
    Cancel a queued or running job.
    
    Args:
        job_id: RQ job identifier
        
    Returns:
        True if job was cancelled, False otherwise
    """
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        
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
        crawler_logger.logger.error(
            "Failed to cancel job",
            job_id=job_id,
            error=str(e),
            event_type="job_cancel_error"
        )
        return False


def cleanup_old_jobs(max_age_hours: int = 24) -> int:
    """
    Clean up old completed and failed jobs.
    
    Args:
        max_age_hours: Maximum age of jobs to keep (in hours)
        
    Returns:
        Number of jobs cleaned up
    """
    try:
        cleaned_count = 0
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        # Clean up finished jobs
        for job_id in crawl_queue.finished_job_registry.get_job_ids():
            job = Job.fetch(job_id, connection=redis_conn)
            if job.ended_at and job.ended_at.timestamp() < cutoff_time:
                job.delete()
                cleaned_count += 1
        
        # Clean up failed jobs
        for job_id in crawl_queue.failed_job_registry.get_job_ids():
            job = Job.fetch(job_id, connection=redis_conn)
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
        crawler_logger.logger.error(
            "Failed to cleanup old jobs",
            error=str(e),
            event_type="job_cleanup_error"
        )
        return 0


def start_worker():
    """Start a worker process to process background jobs."""
    with Connection(redis_conn):
        worker = Worker([crawl_queue], connection=redis_conn)
        crawler_logger.logger.info(
            "Starting background job worker",
            event_type="worker_started"
        )
        worker.work()


if __name__ == "__main__":
    # Configure logging
    from logging_config import configure_logging
    configure_logging(settings.LOG_LEVEL, "production")
    
    # Start worker
    start_worker()
