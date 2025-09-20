"""
Structured logging configuration for the crawler microservice.
Supports multiple log levels and formats for different environments.
"""

import os
import sys
import logging
import structlog
from typing import Any, Dict, Optional
from datetime import datetime
import json

from app.core.config import get_settings


def configure_logging() -> None:
    """Configure structured logging for the application."""
    settings = get_settings()
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Configure standard library logging
    logging.basicConfig(
        level=numeric_level,
        format="%(message)s",
        stream=sys.stdout,
    )
    
    # Configure structlog processors based on environment
    if settings.environment == "development":
        # Human-readable format for development
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ]
    else:
        # JSON format for production/testing
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            add_service_context,
            structlog.processors.JSONRenderer()
        ]
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def add_service_context(logger, method_name, event_dict):
    """Add service context to all log entries."""
    settings = get_settings()
    event_dict["service"] = settings.app_name
    event_dict["version"] = settings.app_version
    event_dict["environment"] = settings.environment
    return event_dict


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


class CrawlerLogger:
    """Specialized logger for crawler operations with structured logging."""
    
    def __init__(self, name: str = "crawler"):
        self.logger = get_logger(name)
    
    def crawl_started(self, task_id: str, url: str, max_depth: int, **kwargs):
        """Log when a crawl task starts."""
        self.logger.info(
            "Crawl task started",
            task_id=task_id,
            url=url,
            max_depth=max_depth,
            event_type="crawl_started",
            **kwargs
        )
    
    def crawl_completed(self, task_id: str, url: str, pages_crawled: int, 
                       duration: float, status: str, **kwargs):
        """Log when a crawl task completes."""
        self.logger.info(
            "Crawl task completed",
            task_id=task_id,
            url=url,
            pages_crawled=pages_crawled,
            duration=duration,
            status=status,
            event_type="crawl_completed",
            **kwargs
        )
    
    def crawl_failed(self, task_id: str, url: str, error: str, **kwargs):
        """Log when a crawl task fails."""
        self.logger.error(
            "Crawl task failed",
            task_id=task_id,
            url=url,
            error=error,
            event_type="crawl_failed",
            **kwargs
        )
    
    def page_crawled(self, task_id: str, url: str, status_code: int, 
                    response_time: float, depth: int, **kwargs):
        """Log when a page is successfully crawled."""
        self.logger.debug(
            "Page crawled",
            task_id=task_id,
            url=url,
            status_code=status_code,
            response_time=response_time,
            depth=depth,
            event_type="page_crawled",
            **kwargs
        )
    
    def page_error(self, task_id: str, url: str, error: str, 
                  status_code: int = None, retry_attempt: int = 0, **kwargs):
        """Log when a page crawl fails."""
        self.logger.warning(
            "Page crawl error",
            task_id=task_id,
            url=url,
            error=error,
            status_code=status_code,
            retry_attempt=retry_attempt,
            event_type="page_error",
            **kwargs
        )
    
    def rate_limit_hit(self, domain: str, limit: int, **kwargs):
        """Log when rate limiting is triggered."""
        self.logger.warning(
            "Rate limit hit",
            domain=domain,
            limit=limit,
            event_type="rate_limit_hit",
            **kwargs
        )
    
    def concurrency_adjusted(self, old_limit: int, new_limit: int, 
                           success_rate: float, **kwargs):
        """Log when concurrency is dynamically adjusted."""
        self.logger.info(
            "Concurrency adjusted",
            old_limit=old_limit,
            new_limit=new_limit,
            success_rate=success_rate,
            event_type="concurrency_adjusted",
            **kwargs
        )
    
    def retry_attempt(self, url: str, attempt: int, max_attempts: int, 
                     delay: float, error: str, **kwargs):
        """Log when a retry attempt is made."""
        self.logger.info(
            "Retry attempt",
            url=url,
            attempt=attempt,
            max_attempts=max_attempts,
            delay=delay,
            error=error,
            event_type="retry_attempt",
            **kwargs
        )
    
    def storage_operation(self, operation: str, task_id: str = None, 
                         success: bool = True, **kwargs):
        """Log storage operations."""
        level = "info" if success else "error"
        getattr(self.logger, level)(
            f"Storage {operation}",
            operation=operation,
            task_id=task_id,
            success=success,
            event_type="storage_operation",
            **kwargs
        )
    
    def api_request(self, method: str, endpoint: str, status_code: int, 
                   response_time: float, **kwargs):
        """Log API requests."""
        self.logger.info(
            "API request",
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            response_time=response_time,
            event_type="api_request",
            **kwargs
        )
    
    def background_job_started(self, job_id: str, job_type: str, **kwargs):
        """Log when a background job starts."""
        self.logger.info(
            "Background job started",
            job_id=job_id,
            job_type=job_type,
            event_type="background_job_started",
            **kwargs
        )
    
    def background_job_completed(self, job_id: str, job_type: str, 
                                duration: float, **kwargs):
        """Log when a background job completes."""
        self.logger.info(
            "Background job completed",
            job_id=job_id,
            job_type=job_type,
            duration=duration,
            event_type="background_job_completed",
            **kwargs
        )
    
    def background_job_failed(self, job_id: str, job_type: str, error: str, **kwargs):
        """Log when a background job fails."""
        self.logger.error(
            "Background job failed",
            job_id=job_id,
            job_type=job_type,
            error=error,
            event_type="background_job_failed",
            **kwargs
        )


# Initialize the crawler logger
crawler_logger = CrawlerLogger()
