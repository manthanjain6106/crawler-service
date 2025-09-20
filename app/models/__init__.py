"""
Data models for the crawler microservice.
"""

from .crawl_models import (
    CrawlStatus,
    ErrorType,
    CrawlError,
    CrawlRequest,
    CrawledPage,
    CrawlResult,
    CrawlTask,
    HealthResponse
)

__all__ = [
    "CrawlStatus",
    "ErrorType", 
    "CrawlError",
    "CrawlRequest",
    "CrawledPage",
    "CrawlResult",
    "CrawlTask",
    "HealthResponse"
]
