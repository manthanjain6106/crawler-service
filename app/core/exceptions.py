"""
Custom exceptions for the crawler microservice.
Provides structured error handling and proper HTTP status codes.
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException, status


class CrawlerServiceException(Exception):
    """Base exception for crawler service errors."""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code or "CRAWLER_ERROR"
        self.details = details or {}
        super().__init__(self.message)


class CrawlTaskNotFoundError(CrawlerServiceException):
    """Raised when a crawl task is not found."""
    
    def __init__(self, task_id: str):
        super().__init__(
            message=f"Crawl task '{task_id}' not found",
            error_code="TASK_NOT_FOUND",
            details={"task_id": task_id}
        )


class CrawlTaskAlreadyExistsError(CrawlerServiceException):
    """Raised when trying to create a crawl task that already exists."""
    
    def __init__(self, task_id: str):
        super().__init__(
            message=f"Crawl task '{task_id}' already exists",
            error_code="TASK_ALREADY_EXISTS",
            details={"task_id": task_id}
        )


class CrawlTaskInProgressError(CrawlerServiceException):
    """Raised when trying to modify a crawl task that is in progress."""
    
    def __init__(self, task_id: str):
        super().__init__(
            message=f"Crawl task '{task_id}' is in progress and cannot be modified",
            error_code="TASK_IN_PROGRESS",
            details={"task_id": task_id}
        )


class InvalidCrawlRequestError(CrawlerServiceException):
    """Raised when a crawl request is invalid."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            error_code="INVALID_REQUEST",
            details=details or {}
        )


class RateLimitExceededError(CrawlerServiceException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, domain: str, limit: int, retry_after: Optional[int] = None):
        super().__init__(
            message=f"Rate limit exceeded for domain '{domain}': {limit} requests per minute",
            error_code="RATE_LIMIT_EXCEEDED",
            details={
                "domain": domain,
                "limit": limit,
                "retry_after": retry_after
            }
        )


class StorageError(CrawlerServiceException):
    """Raised when a storage operation fails."""
    
    def __init__(self, operation: str, message: str, details: Dict[str, Any] = None):
        super().__init__(
            message=f"Storage operation '{operation}' failed: {message}",
            error_code="STORAGE_ERROR",
            details={
                "operation": operation,
                **(details or {})
            }
        )


class BackgroundJobError(CrawlerServiceException):
    """Raised when a background job operation fails."""
    
    def __init__(self, job_id: str, message: str, details: Dict[str, Any] = None):
        super().__init__(
            message=f"Background job '{job_id}' failed: {message}",
            error_code="BACKGROUND_JOB_ERROR",
            details={
                "job_id": job_id,
                **(details or {})
            }
        )


class ConfigurationError(CrawlerServiceException):
    """Raised when there's a configuration error."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(
            message=f"Configuration error: {message}",
            error_code="CONFIGURATION_ERROR",
            details=details or {}
        )


def create_http_exception(exc: CrawlerServiceException) -> HTTPException:
    """Convert a CrawlerServiceException to an HTTPException."""
    
    # Map error codes to HTTP status codes
    status_code_mapping = {
        "TASK_NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "TASK_ALREADY_EXISTS": status.HTTP_409_CONFLICT,
        "TASK_IN_PROGRESS": status.HTTP_409_CONFLICT,
        "INVALID_REQUEST": status.HTTP_400_BAD_REQUEST,
        "RATE_LIMIT_EXCEEDED": status.HTTP_429_TOO_MANY_REQUESTS,
        "STORAGE_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "BACKGROUND_JOB_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "CONFIGURATION_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    
    http_status = status_code_mapping.get(exc.error_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return HTTPException(
        status_code=http_status,
        detail={
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details
        }
    )
