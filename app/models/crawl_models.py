"""
Data models for crawl operations.
"""

from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class CrawlStatus(str, Enum):
    """Status of a crawl task."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ErrorType(str, Enum):
    """Type of error that occurred during crawling."""
    TRANSIENT = "transient"  # 502, 503, timeout, connection errors
    PERMANENT = "permanent"  # 404, 403, 401, 400
    UNKNOWN = "unknown"      # Other errors


class CrawlError(BaseModel):
    """Structured error information for crawl operations."""
    error_type: ErrorType
    status_code: Optional[int] = None
    message: str
    url: str
    timestamp: datetime
    retry_attempts: int = 0
    max_retries: int = 3
    is_retryable: bool = True


class CrawlRequest(BaseModel):
    """Request model for starting a crawl operation."""
    url: HttpUrl
    max_depth: int = Field(default=0, ge=0, description="Maximum crawl depth (0 = landing page only)")
    follow_links: bool = Field(default=False, description="Whether to follow internal links")
    extract_text: bool = Field(default=True, description="Whether to extract text content")
    extract_images: bool = Field(default=False, description="Whether to extract image URLs")
    extract_links: bool = Field(default=True, description="Whether to extract links")
    extract_headings: bool = Field(default=True, description="Whether to extract headings (h1, h2, h3)")
    extract_image_alt_text: bool = Field(default=False, description="Whether to extract image alt text")
    extract_canonical_url: bool = Field(default=True, description="Whether to extract canonical URL")
    custom_headers: Optional[Dict[str, str]] = Field(default=None, description="Custom HTTP headers")
    timeout: int = Field(default=30, ge=1, le=300, description="Request timeout in seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "url": "https://example.com",
                "max_depth": 0,
                "follow_links": False,
                "extract_text": True,
                "extract_images": False,
                "extract_links": True,
                "extract_headings": True,
                "extract_image_alt_text": False,
                "extract_canonical_url": True,
                "timeout": 30
            }
        }


class CrawledPage(BaseModel):
    """Model representing a single crawled page."""
    url: str
    title: Optional[str] = None
    text_content: Optional[str] = None
    images: List[str] = Field(default_factory=list)
    links: List[str] = Field(default_factory=list)
    meta_description: Optional[str] = None
    headings: Dict[str, List[str]] = Field(default_factory=dict, description="Headings organized by level (h1, h2, h3)")
    image_alt_text: List[str] = Field(default_factory=list, description="Alt text from images")
    canonical_url: Optional[str] = None
    status_code: int
    response_time: float
    crawled_at: datetime
    depth: int = 0
    error: Optional[CrawlError] = None
    retry_attempts: int = 0


class CrawlResult(BaseModel):
    """Result model for a completed crawl operation."""
    task_id: str
    status: CrawlStatus
    total_pages: int = 0
    pages: List[CrawledPage] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list, description="Legacy error messages for backward compatibility")
    structured_errors: List[CrawlError] = Field(default_factory=list, description="Structured error information")
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None
    retry_stats: Dict[str, int] = Field(default_factory=dict, description="Retry statistics")


class CrawlTask(BaseModel):
    """Model representing a crawl task."""
    task_id: str
    request: CrawlRequest
    status: CrawlStatus
    result: Optional[CrawlResult] = None
    job_id: Optional[str] = Field(default=None, description="Background job ID")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        schema_extra = {
            "example": {
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "request": {
                    "url": "https://example.com",
                    "max_depth": 0,
                    "follow_links": False
                },
                "status": "pending",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z"
            }
        }


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime
    version: str = "1.0.0"
    uptime: float
    services: Dict[str, str] = Field(default_factory=dict, description="Status of individual services")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2023-01-01T00:00:00Z",
                "version": "1.0.0",
                "uptime": 3600.0,
                "services": {
                    "storage": "healthy",
                    "background_jobs": "healthy",
                    "rate_limiter": "healthy"
                }
            }
        }
