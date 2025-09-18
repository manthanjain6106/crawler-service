from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class CrawlStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class CrawlRequest(BaseModel):
    url: HttpUrl
    max_depth: int = 1
    follow_links: bool = True
    extract_text: bool = True
    extract_images: bool = True
    extract_links: bool = True
    custom_headers: Optional[Dict[str, str]] = None
    timeout: int = 30


class CrawledPage(BaseModel):
    url: str
    title: Optional[str] = None
    text_content: Optional[str] = None
    images: List[str] = []
    links: List[str] = []
    meta_description: Optional[str] = None
    status_code: int
    response_time: float
    crawled_at: datetime


class CrawlResult(BaseModel):
    task_id: str
    status: CrawlStatus
    total_pages: int = 0
    pages: List[CrawledPage] = []
    errors: List[str] = []
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None


class CrawlTask(BaseModel):
    task_id: str
    request: CrawlRequest
    status: CrawlStatus
    result: Optional[CrawlResult] = None
    created_at: datetime
    updated_at: datetime


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str = "1.0.0"
    uptime: float
