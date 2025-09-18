from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import time
import uuid
from typing import Dict, List
import logging
from datetime import datetime

from models import (
    CrawlRequest, CrawlResult, CrawlTask, CrawlStatus, 
    HealthResponse
)
from crawler_service import WebCrawler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# In-memory storage for tasks (in production, use Redis or database)
crawl_tasks: Dict[str, CrawlTask] = {}
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
@limiter.limit("10/minute")
async def start_crawl(
    request: CrawlRequest,
    background_tasks: BackgroundTasks
):
    """Start a new crawl task"""
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
        crawl_tasks[task_id] = task
        
        # Start background crawl
        background_tasks.add_task(execute_crawl, task_id)
        
        logger.info(f"Started crawl task {task_id} for URL: {request.url}")
        return task
        
    except Exception as e:
        logger.error(f"Error starting crawl: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/crawl/{task_id}", response_model=CrawlTask)
async def get_crawl_status(task_id: str):
    """Get the status of a crawl task"""
    if task_id not in crawl_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return crawl_tasks[task_id]


@app.get("/crawl/{task_id}/result", response_model=CrawlResult)
async def get_crawl_result(task_id: str):
    """Get the result of a completed crawl task"""
    if task_id not in crawl_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = crawl_tasks[task_id]
    if task.status not in [CrawlStatus.COMPLETED, CrawlStatus.FAILED]:
        raise HTTPException(status_code=400, detail="Task not completed yet")
    
    if not task.result:
        raise HTTPException(status_code=500, detail="No result available")
    
    return task.result


@app.get("/crawl", response_model=List[CrawlTask])
async def list_crawl_tasks():
    """List all crawl tasks"""
    return list(crawl_tasks.values())


@app.delete("/crawl/{task_id}")
async def delete_crawl_task(task_id: str):
    """Delete a crawl task"""
    if task_id not in crawl_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    del crawl_tasks[task_id]
    return {"message": "Task deleted successfully"}


async def execute_crawl(task_id: str):
    """Execute a crawl task in the background"""
    try:
        task = crawl_tasks[task_id]
        task.status = CrawlStatus.IN_PROGRESS
        task.updated_at = time.time()
        
        logger.info(f"Executing crawl task {task_id}")
        
        # Execute crawl
        async with WebCrawler() as crawler:
            result = await crawler.crawl_website(task.request)
        
        # Update task with result
        task.result = result
        task.status = result.status
        task.updated_at = datetime.now()
        
        logger.info(f"Completed crawl task {task_id} with status: {result.status}")
        
    except Exception as e:
        logger.error(f"Error executing crawl task {task_id}: {str(e)}")
        if task_id in crawl_tasks:
            task = crawl_tasks[task_id]
            task.status = CrawlStatus.FAILED
            task.updated_at = datetime.now()
            if not task.result:
                task.result = CrawlResult(
                    task_id=task_id,
                    status=CrawlStatus.FAILED,
                    errors=[str(e)],
                    started_at=datetime.now(),
                    completed_at=datetime.now()
                )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
