from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import time
import uuid
from typing import Dict, List, Optional
import logging
from datetime import datetime

from models import (
    CrawlRequest, CrawlResult, CrawlTask, CrawlStatus, 
    HealthResponse
)
from crawler_service import WebCrawler
from config import settings
from storage import StorageManager, create_storage_backend
from background_jobs import enqueue_crawl_task, get_job_status, get_queue_stats, cancel_job
from logging_config import configure_logging, get_logger, crawler_logger

# Configure structured logging
configure_logging(settings.LOG_LEVEL, "production")
logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Web Crawler Microservice",
    description="A microservice for crawling websites and extracting data",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests with structured logging."""
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate response time
    response_time = time.time() - start_time
    
    # Log request
    crawler_logger.api_request(
        method=request.method,
        endpoint=str(request.url.path),
        status_code=response.status_code,
        response_time=response_time,
        client_ip=request.client.host if request.client else None
    )
    
    return response

# Initialize storage backend
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

app_start_time = time.time()


@app.get("/", response_model=dict)
async def root():
    """Root endpoint"""
    return {
        "message": "Web Crawler Microservice",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        uptime=time.time() - app_start_time
    )


@app.post("/crawl", response_model=CrawlTask)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def start_crawl(request: CrawlRequest):
    """Start a new crawl task using background job processing"""
    try:
        task_id = str(uuid.uuid4())
        
        # Create task
        task = CrawlTask(
            task_id=task_id,
            request=request,
            status=CrawlStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Store task
        await storage_manager.save_task(task)
        
        # Enqueue background job
        job = enqueue_crawl_task(task_id, request)
        task.job_id = job.id
        
        # Update task with job ID
        await storage_manager.update_task(task_id, {"job_id": job.id})
        
        # Log task creation
        crawler_logger.crawl_started(
            task_id=task_id,
            url=str(request.url),
            max_depth=request.max_depth,
            job_id=job.id
        )
        
        return task
        
    except Exception as e:
        logger.error(f"Error starting crawl: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/crawl/{task_id}", response_model=CrawlTask)
async def get_crawl_status(task_id: str):
    """Get the status of a crawl task"""
    task = await storage_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task


@app.get("/crawl/{task_id}/result", response_model=CrawlResult)
async def get_crawl_result(task_id: str):
    """Get the result of a completed crawl task"""
    task = await storage_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status not in [CrawlStatus.COMPLETED, CrawlStatus.FAILED]:
        raise HTTPException(status_code=400, detail="Task not completed yet")
    
    result = await storage_manager.get_crawl_result(task_id)
    if not result:
        raise HTTPException(status_code=500, detail="No result available")
    
    return result


@app.get("/crawl", response_model=List[CrawlTask])
async def list_crawl_tasks(limit: int = 100, offset: int = 0):
    """List all crawl tasks with pagination"""
    return await storage_manager.list_tasks(limit=limit, offset=offset)


@app.delete("/crawl/{task_id}")
async def delete_crawl_task(task_id: str):
    """Delete a crawl task"""
    success = await storage_manager.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {"message": "Task deleted successfully"}


@app.get("/rate-limits")
async def get_rate_limits():
    """Get current rate limiting configuration and statistics"""
    try:
        # Create a temporary crawler to get rate limiting stats
        async with WebCrawler() as crawler:
            rate_stats = crawler.get_rate_limiting_stats()
        
        return {
            "api_rate_limit": f"{settings.RATE_LIMIT_PER_MINUTE}/minute",
            "per_domain_rate_limiting": {
                "enabled": settings.ENABLE_PER_DOMAIN_RATE_LIMITING,
                "default_limit": settings.DEFAULT_DOMAIN_RATE_LIMIT,
                "window_size": settings.DOMAIN_RATE_LIMIT_WINDOW,
                "domain_specific_limits": settings.DOMAIN_SPECIFIC_LIMITS
            },
            "current_stats": rate_stats
        }
    except Exception as e:
        logger.error(f"Error getting rate limits: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search/tasks")
async def search_tasks(
    status: Optional[str] = None,
    url: Optional[str] = None,
    created_after: Optional[str] = None,
    created_before: Optional[str] = None,
    limit: int = 100
):
    """Search crawl tasks by criteria"""
    try:
        query = {}
        if status:
            query["status"] = status
        if url:
            query["url"] = url
        if created_after:
            query["created_after"] = created_after
        if created_before:
            query["created_before"] = created_before
        
        tasks = await storage_manager.search_tasks(query, limit=limit)
        return tasks
    except Exception as e:
        logger.error(f"Error searching tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search/pages")
async def search_pages(
    url: Optional[str] = None,
    title: Optional[str] = None,
    status_code: Optional[int] = None,
    task_id: Optional[str] = None,
    crawled_after: Optional[str] = None,
    crawled_before: Optional[str] = None,
    limit: int = 100
):
    """Search crawled pages by criteria"""
    try:
        query = {}
        if url:
            query["url"] = url
        if title:
            query["title"] = title
        if status_code:
            query["status_code"] = status_code
        if task_id:
            query["task_id"] = task_id
        if crawled_after:
            query["crawled_after"] = crawled_after
        if crawled_before:
            query["crawled_before"] = crawled_before
        
        pages = await storage_manager.search_pages(query, limit=limit)
        return pages
    except Exception as e:
        logger.error(f"Error searching pages: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/storage/stats")
async def get_storage_stats():
    """Get storage statistics"""
    try:
        stats = await storage_manager.get_storage_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting storage stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs/queue/stats")
async def get_job_queue_stats():
    """Get background job queue statistics"""
    try:
        stats = get_queue_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting job queue stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs/{job_id}/status")
async def get_job_status_endpoint(job_id: str):
    """Get the status of a background job"""
    try:
        status = get_job_status(job_id)
        if not status:
            raise HTTPException(status_code=404, detail="Job not found")
        return status
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/jobs/{job_id}/cancel")
async def cancel_job_endpoint(job_id: str):
    """Cancel a background job"""
    try:
        success = cancel_job(job_id)
        if success:
            return {"message": "Job cancelled successfully"}
        else:
            raise HTTPException(status_code=400, detail="Job could not be cancelled")
    except Exception as e:
        logger.error(f"Error cancelling job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
