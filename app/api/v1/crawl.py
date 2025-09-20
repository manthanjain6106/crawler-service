"""
Crawl API endpoints for the crawler microservice.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
import json

from app.models.crawl_models import CrawlRequest, CrawlResult
from app.core.dependencies import (
    get_logger_dependency,
    get_crawler_service_dependency
)
from app.core.logging import crawler_logger

# Create router
router = APIRouter(prefix="/crawl", tags=["crawl"])

# Rate limiting
limiter = Limiter(key_func=get_remote_address)


@router.post("/", status_code=status.HTTP_200_OK)
async def start_crawl(
    crawl_request: CrawlRequest,
    response: Response,
    logger=Depends(get_logger_dependency),
    crawler_service=Depends(get_crawler_service_dependency)
):
    """Crawl a website and return the result as JSON without storing data."""
    try:
        # Set JSON content type
        response.headers["Content-Type"] = "application/json"
        
        # Log crawl start
        crawler_logger.crawl_started(
            task_id="direct_crawl",
            url=str(crawl_request.url),
            max_depth=crawl_request.max_depth
        )
        
        # Execute crawl directly
        result = await crawler_service.crawl_website(crawl_request)
        
        # Log completion
        crawler_logger.crawl_completed(
            task_id="direct_crawl",
            url=str(crawl_request.url),
            pages_crawled=result.total_pages if result else 0,
            duration=result.duration if result else 0,
            status=result.status.value if result else "unknown"
        )
        
        # Return as JSON
        return result.dict()
        
    except Exception as e:
        logger.error(f"Error during crawl: {str(e)}")
        # Log failure
        crawler_logger.crawl_failed(
            task_id="direct_crawl",
            url=str(crawl_request.url),
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/json", status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def crawl_json(
    request: CrawlRequest,
    response: Response,
    logger=Depends(get_logger_dependency),
    crawler_service=Depends(get_crawler_service_dependency)
):
    """Crawl a website and return raw JSON string response."""
    try:
        # Set JSON content type
        response.headers["Content-Type"] = "application/json"
        
        # Log crawl start
        crawler_logger.crawl_started(
            task_id="direct_crawl",
            url=str(request.url),
            max_depth=request.max_depth
        )
        
        # Execute crawl directly
        result = await crawler_service.crawl_website(request)
        
        # Log completion
        crawler_logger.crawl_completed(
            task_id="direct_crawl",
            url=str(request.url),
            pages_crawled=result.total_pages if result else 0,
            duration=result.duration if result else 0,
            status=result.status.value if result else "unknown"
        )
        
        # Convert to JSON string and return
        json_data = result.dict()
        return Response(
            content=json.dumps(json_data, indent=2, ensure_ascii=False),
            media_type="application/json"
        )
        
    except Exception as e:
        logger.error(f"Error during crawl: {str(e)}")
        # Log failure
        crawler_logger.crawl_failed(
            task_id="direct_crawl",
            url=str(request.url),
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simple", status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def crawl_simple_json(
    request: CrawlRequest,
    response: Response,
    logger=Depends(get_logger_dependency),
    crawler_service=Depends(get_crawler_service_dependency)
):
    """Crawl a website and return simplified JSON response."""
    try:
        # Set JSON content type
        response.headers["Content-Type"] = "application/json"
        
        # Execute crawl directly
        result = await crawler_service.crawl_website(request)
        
        # Create simplified JSON response
        if result and result.pages:
            page = result.pages[0]  # Only first page since we crawl landing page only
            simple_response = {
                "url": page.url,
                "title": page.title,
                "text": page.text_content,
                "images": page.images,
                "links": page.links,
                "status_code": page.status_code,
                "response_time": page.response_time,
                "crawled_at": page.crawled_at.isoformat() if page.crawled_at else None
            }
        else:
            simple_response = {
                "error": "No data crawled",
                "url": str(request.url)
            }
        
        return simple_response
        
    except Exception as e:
        logger.error(f"Error during crawl: {str(e)}")
        return {
            "error": str(e),
            "url": str(request.url)
        }


# Note: Storage-dependent endpoints removed since we don't store data anymore
# The service now returns crawl results directly without persistence
