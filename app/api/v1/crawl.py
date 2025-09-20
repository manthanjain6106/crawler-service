"""
Crawl API endpoints for the crawler microservice.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uuid
from datetime import datetime

from app.models.crawl_models import (
    CrawlRequest, CrawlResult, CrawlTask, CrawlStatus
)
from app.core.dependencies import (
    get_settings_dependency,
    get_logger_dependency,
    get_storage_service_dependency,
    get_crawler_service_dependency,
    get_background_job_service_dependency
)
from app.core.exceptions import (
    CrawlTaskNotFoundError,
    InvalidCrawlRequestError,
    create_http_exception
)
from app.core.logging import crawler_logger

# Create router
router = APIRouter(prefix="/crawl", tags=["crawl"])

# Rate limiting
limiter = Limiter(key_func=get_remote_address)


@router.post("/", response_model=CrawlTask, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def start_crawl(
    request: CrawlRequest,
    settings=Depends(get_settings_dependency),
    logger=Depends(get_logger_dependency),
    storage_service=Depends(get_storage_service_dependency),
    background_job_service=Depends(get_background_job_service_dependency),
    crawler_service=Depends(get_crawler_service_dependency)
):
    """Start a new crawl task using background job processing or synchronous processing."""
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
        await storage_service.save_task(task)
        
        # Check if background jobs are available
        if settings.enable_background_jobs and background_job_service is not None:
            # Use background job processing
            try:
                job = await background_job_service.enqueue_crawl_task(task_id, request)
                task.job_id = job.id
                task.status = CrawlStatus.QUEUED
                
                # Update task with job ID
                await storage_service.update_task(task_id, {"job_id": job.id, "status": task.status})
                
                # Log task creation
                crawler_logger.crawl_started(
                    task_id=task_id,
                    url=str(request.url),
                    max_depth=request.max_depth,
                    job_id=job.id
                )
                
                return task
                
            except Exception as e:
                logger.warning(f"Background job failed, falling back to synchronous processing: {e}")
                # Fall through to synchronous processing
        
        # Use synchronous processing (fallback or when background jobs disabled)
        task.status = CrawlStatus.RUNNING
        await storage_service.update_task(task_id, {"status": task.status})
        
        # Log task creation
        crawler_logger.crawl_started(
            task_id=task_id,
            url=str(request.url),
            max_depth=request.max_depth
        )
        
        # Execute crawl synchronously
        try:
            result = await crawler_service.crawl_website(request)
            task.status = CrawlStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.now()
            
            # Update task with result
            await storage_service.update_task(task_id, {
                "status": task.status,
                "result": result.dict() if result else None,
                "completed_at": task.completed_at
            })
            
            # Log completion
            crawler_logger.crawl_completed(
                task_id=task_id,
                url=str(request.url),
                pages_crawled=result.total_pages if result else 0,
                duration=result.duration if result else 0
            )
            
        except Exception as e:
            task.status = CrawlStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
            
            # Update task with error
            await storage_service.update_task(task_id, {
                "status": task.status,
                "error": task.error,
                "completed_at": task.completed_at
            })
            
            # Log failure
            crawler_logger.crawl_failed(
                task_id=task_id,
                url=str(request.url),
                error=str(e)
            )
        
        return task
        
    except Exception as e:
        logger.error(f"Error starting crawl: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}", response_model=CrawlTask)
async def get_crawl_status(
    task_id: str,
    storage_service=Depends(get_storage_service_dependency)
):
    """Get the status of a crawl task."""
    task = await storage_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task


@router.get("/{task_id}/result", response_model=CrawlResult)
async def get_crawl_result(
    task_id: str,
    storage_service=Depends(get_storage_service_dependency)
):
    """Get the result of a completed crawl task."""
    task = await storage_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status not in [CrawlStatus.COMPLETED, CrawlStatus.FAILED]:
        raise HTTPException(status_code=400, detail="Task not completed yet")
    
    result = await storage_service.get_crawl_result(task_id)
    if not result:
        raise HTTPException(status_code=500, detail="No result available")
    
    return result


@router.get("/", response_model=List[CrawlTask])
async def list_crawl_tasks(
    limit: int = 100,
    offset: int = 0,
    storage_service=Depends(get_storage_service_dependency)
):
    """List all crawl tasks with pagination."""
    return await storage_service.list_tasks(limit=limit, offset=offset)


@router.delete("/{task_id}")
async def delete_crawl_task(
    task_id: str,
    storage_service=Depends(get_storage_service_dependency)
):
    """Delete a crawl task."""
    success = await storage_service.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {"message": "Task deleted successfully"}


@router.get("/search/tasks")
async def search_tasks(
    status: Optional[str] = None,
    url: Optional[str] = None,
    created_after: Optional[str] = None,
    created_before: Optional[str] = None,
    limit: int = 100,
    storage_service=Depends(get_storage_service_dependency)
):
    """Search crawl tasks by criteria."""
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
        
        tasks = await storage_service.search_tasks(query, limit=limit)
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/pages")
async def search_pages(
    url: Optional[str] = None,
    title: Optional[str] = None,
    status_code: Optional[int] = None,
    task_id: Optional[str] = None,
    crawled_after: Optional[str] = None,
    crawled_before: Optional[str] = None,
    limit: int = 100,
    storage_service=Depends(get_storage_service_dependency)
):
    """Search crawled pages by criteria."""
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
        
        pages = await storage_service.search_pages(query, limit=limit)
        return pages
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
