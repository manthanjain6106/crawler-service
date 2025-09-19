from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class CrawlStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ErrorType(str, Enum):
    TRANSIENT = "transient"  # 502, 503, timeout, connection errors
    PERMANENT = "permanent"  # 404, 403, 401, 400
    UNKNOWN = "unknown"      # Other errors


class CrawlError(BaseModel):
    error_type: ErrorType
    status_code: Optional[int] = None
    message: str
    url: str
    timestamp: datetime
    retry_attempts: int = 0
    max_retries: int = 3
    is_retryable: bool = True


class CrawlRequest(BaseModel):
    url: HttpUrl
    max_depth: int = 10  # Increased default from 1 to 10, 0 = unlimited depth
    follow_links: bool = True
    extract_text: bool = True
    extract_images: bool = True
    extract_links: bool = True
    extract_headings: bool = True  # Extract h1, h2, h3 headings
    extract_image_alt_text: bool = True  # Extract alt text from images
    extract_canonical_url: bool = True  # Extract canonical URL
    custom_headers: Optional[Dict[str, str]] = None
    timeout: int = 30


class CrawledPage(BaseModel):
    url: str
    title: Optional[str] = None
    text_content: Optional[str] = None
    images: List[str] = []
    links: List[str] = []
    meta_description: Optional[str] = None
    headings: Dict[str, List[str]] = {}  # h1, h2, h3 headings organized by level
    image_alt_text: List[str] = []  # Alt text from images
    canonical_url: Optional[str] = None  # Canonical URL to avoid duplicate content
    status_code: int
    response_time: float
    crawled_at: datetime
    depth: int = 0  # Track the depth at which this page was found
    error: Optional[CrawlError] = None
    retry_attempts: int = 0


class CrawlResult(BaseModel):
    task_id: str
    status: CrawlStatus
    total_pages: int = 0
    pages: List[CrawledPage] = []
    errors: List[str] = []  # Keep for backward compatibility
    structured_errors: List[CrawlError] = []  # New structured error tracking
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None
    retry_stats: Dict[str, int] = {}  # Track retry statistics


class CrawlTask(BaseModel):
    task_id: str
    request: CrawlRequest
    status: CrawlStatus
    result: Optional[CrawlResult] = None
    job_id: Optional[str] = None  # Background job ID
    created_at: datetime
    updated_at: datetime


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str = "1.0.0"
    uptime: float
