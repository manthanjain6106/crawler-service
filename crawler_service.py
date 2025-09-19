import asyncio
import aiohttp
import time
from urllib.parse import urljoin, urlparse, urlunparse
from bs4 import BeautifulSoup
from typing import List, Set, Optional, Tuple
import logging
from datetime import datetime
from models import CrawlRequest, CrawledPage, CrawlResult, CrawlStatus, CrawlError, ErrorType
import re
from collections import deque
from config import settings
from rate_limiter import RateLimitManager
import random
from logging_config import crawler_logger

logger = logging.getLogger(__name__)


class WebCrawler:
    def __init__(self, max_concurrent_requests: Optional[int] = None):
        self.max_concurrent_requests = max_concurrent_requests or settings.MAX_CONCURRENT_REQUESTS
        self.burst_limit = settings.CONCURRENCY_BURST_LIMIT
        self.gradual_increase = settings.CONCURRENCY_GRADUAL_INCREASE
        self.session: Optional[aiohttp.ClientSession] = None
        self.visited_urls: Set[str] = set()
        self.semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        self.burst_semaphore = asyncio.Semaphore(self.burst_limit)
        self.active_requests = 0
        self.request_lock = asyncio.Lock()
        
        # Initialize rate limiter
        self.rate_limiter = RateLimitManager()
        
        # Retry statistics tracking
        self.retry_stats = {
            "total_retries": 0,
            "successful_retries": 0,
            "failed_retries": 0,
            "transient_errors": 0,
            "permanent_errors": 0
        }

    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _adjust_concurrency(self, success_rate: float, total_requests: int):
        """Dynamically adjust concurrency based on success rate and performance"""
        if not self.gradual_increase or total_requests < 10:
            return
        
        async with self.request_lock:
            # If success rate is high (>90%) and we have capacity, increase concurrency
            if success_rate > 0.9 and self.max_concurrent_requests < self.burst_limit:
                new_limit = min(self.max_concurrent_requests + 5, self.burst_limit)
                if new_limit != self.max_concurrent_requests:
                    self.max_concurrent_requests = new_limit
                    # Create new semaphore with updated limit
                    self.semaphore = asyncio.Semaphore(self.max_concurrent_requests)
                    logger.info(f"Increased concurrency to {self.max_concurrent_requests}")
            
            # If success rate is low (<70%), decrease concurrency
            elif success_rate < 0.7 and self.max_concurrent_requests > 5:
                new_limit = max(self.max_concurrent_requests - 3, 5)
                if new_limit != self.max_concurrent_requests:
                    self.max_concurrent_requests = new_limit
                    self.semaphore = asyncio.Semaphore(self.max_concurrent_requests)
                    logger.info(f"Decreased concurrency to {self.max_concurrent_requests}")

    async def crawl_url(self, url: str, request: CrawlRequest, depth: int = 0) -> CrawledPage:
        """Crawl a single URL with retry logic for transient errors"""
        # Check rate limiting before making request
        await self.rate_limiter.wait_if_needed(url)
        
        # Use burst semaphore for additional protection against overwhelming the target
        async with self.burst_semaphore:
            # Use main semaphore for controlled concurrency
            async with self.semaphore:
                start_time = time.time()
                
                # Track active requests for monitoring
                async with self.request_lock:
                    self.active_requests += 1
                
                try:
                    retry_attempts = 0
                    last_error = None
                    
                    while retry_attempts <= settings.MAX_RETRIES:
                        try:
                            headers = {
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                            }
                        
                            if request.custom_headers:
                                headers.update(request.custom_headers)

                            async with self.session.get(url, headers=headers) as response:
                                response_time = time.time() - start_time
                                
                                # Check for HTTP error status codes
                                if response.status >= 400:
                                    error = aiohttp.ClientResponseError(
                                        request_info=response.request_info,
                                        history=response.history,
                                        status=response.status,
                                        message=f"HTTP {response.status}"
                                    )
                                    crawl_error = self._create_crawl_error(url, error, response.status, retry_attempts)
                                    
                                    # Update retry statistics
                                    if crawl_error.error_type == ErrorType.TRANSIENT:
                                        self.retry_stats["transient_errors"] += 1
                                    else:
                                        self.retry_stats["permanent_errors"] += 1
                                    
                                    # If it's a permanent error or not retryable, return error page
                                    if not crawl_error.is_retryable:
                                        self._log_structured_error(crawl_error, "warning")
                                        return CrawledPage(
                                            url=url,
                                            status_code=response.status,
                                            response_time=response_time,
                                            crawled_at=datetime.now(),
                                            depth=depth,
                                            error=crawl_error,
                                            retry_attempts=retry_attempts,
                                            headings={},
                                            image_alt_text=[],
                                            canonical_url=None
                                        )
                                    
                                    # If retryable, prepare for retry
                                    last_error = crawl_error
                                    self.retry_stats["total_retries"] += 1
                                    
                                    # Wait before retry
                                    if retry_attempts < settings.MAX_RETRIES:
                                        delay = self._calculate_retry_delay(retry_attempts + 1)
                                        self._log_structured_error(crawl_error, "warning")
                                        logger.info(f"Retrying {url} in {delay:.2f} seconds (attempt {retry_attempts + 1}/{settings.MAX_RETRIES})")
                                        await asyncio.sleep(delay)
                                        retry_attempts += 1
                                        continue
                                    else:
                                        # Max retries reached
                                        self.retry_stats["failed_retries"] += 1
                                        self._log_structured_error(crawl_error, "error")
                                        return CrawledPage(
                                            url=url,
                                            status_code=response.status,
                                            response_time=response_time,
                                            crawled_at=datetime.now(),
                                            depth=depth,
                                            error=crawl_error,
                                            retry_attempts=retry_attempts,
                                            headings={},
                                            image_alt_text=[],
                                            canonical_url=None
                                        )
                                
                                # Success - process the response
                                content = await response.text()
                                
                                # Record successful request for rate limiting
                                await self.rate_limiter.record_request(url)
                                
                                # Update retry statistics for successful retry
                                if retry_attempts > 0:
                                    self.retry_stats["successful_retries"] += 1
                                
                                soup = BeautifulSoup(content, 'html.parser')
                                
                                # Extract basic information
                                title = soup.find('title')
                                title_text = title.get_text().strip() if title else None
                                
                                # Extract meta description
                                meta_desc = soup.find('meta', attrs={'name': 'description'})
                                meta_description = meta_desc.get('content', '').strip() if meta_desc else None
                                
                                # Extract text content
                                text_content = None
                                if request.extract_text:
                                    # Remove script and style elements
                                    for script in soup(["script", "style"]):
                                        script.decompose()
                                    text_content = soup.get_text()
                                    # Clean up text
                                    text_content = re.sub(r'\s+', ' ', text_content).strip()
                                
                                # Extract images and their alt text
                                images = []
                                image_alt_text = []
                                if request.extract_images:
                                    img_tags = soup.find_all('img')
                                    for img in img_tags:
                                        src = img.get('src')
                                        if src:
                                            # Convert relative URLs to absolute
                                            absolute_url = urljoin(url, src)
                                            images.append(absolute_url)
                                        
                                        # Extract alt text if requested
                                        if request.extract_image_alt_text:
                                            alt_text = img.get('alt', '').strip()
                                            if alt_text:
                                                image_alt_text.append(alt_text)
                                
                                # Extract links
                                links = []
                                if request.extract_links:
                                    link_tags = soup.find_all('a', href=True)
                                    for link in link_tags:
                                        href = link.get('href')
                                        if href:
                                            # Convert relative URLs to absolute
                                            absolute_url = urljoin(url, href)
                                            # Only include HTTP/HTTPS links
                                            if absolute_url.startswith(('http://', 'https://')):
                                                links.append(absolute_url)
                                
                                # Extract headings (h1, h2, h3)
                                headings = {"h1": [], "h2": [], "h3": []}
                                if request.extract_headings:
                                    for level in ["h1", "h2", "h3"]:
                                        heading_tags = soup.find_all(level)
                                        for heading in heading_tags:
                                            heading_text = heading.get_text().strip()
                                            if heading_text:
                                                headings[level].append(heading_text)
                                
                                # Extract canonical URL
                                canonical_url = None
                                if request.extract_canonical_url:
                                    canonical_tag = soup.find('link', rel='canonical')
                                    if canonical_tag and canonical_tag.get('href'):
                                        canonical_url = urljoin(url, canonical_tag.get('href'))
                                
                                return CrawledPage(
                                    url=url,
                                    title=title_text,
                                    text_content=text_content,
                                    images=images,
                                    links=links,
                                    meta_description=meta_description,
                                    headings=headings,
                                    image_alt_text=image_alt_text,
                                    canonical_url=canonical_url,
                                    status_code=response.status,
                                    response_time=response_time,
                                    crawled_at=datetime.now(),
                                    depth=depth,
                                    retry_attempts=retry_attempts
                                )
                            
                        except Exception as e:
                            crawl_error = self._create_crawl_error(url, e, None, retry_attempts)
                            
                            # Update retry statistics
                            if crawl_error.error_type == ErrorType.TRANSIENT:
                                self.retry_stats["transient_errors"] += 1
                            else:
                                self.retry_stats["permanent_errors"] += 1
                            
                            # If it's a permanent error or not retryable, return error page
                            if not crawl_error.is_retryable:
                                self._log_structured_error(crawl_error, "error")
                                return CrawledPage(
                                    url=url,
                                    status_code=0,
                                    response_time=time.time() - start_time,
                                    crawled_at=datetime.now(),
                                    depth=depth,
                                    error=crawl_error,
                                    retry_attempts=retry_attempts,
                                    headings={},
                                    image_alt_text=[],
                                    canonical_url=None
                                )
                            
                            # If retryable, prepare for retry
                            last_error = crawl_error
                            self.retry_stats["total_retries"] += 1
                            
                            # Wait before retry
                            if retry_attempts < settings.MAX_RETRIES:
                                delay = self._calculate_retry_delay(retry_attempts + 1)
                                self._log_structured_error(crawl_error, "warning")
                                logger.info(f"Retrying {url} in {delay:.2f} seconds (attempt {retry_attempts + 1}/{settings.MAX_RETRIES})")
                                await asyncio.sleep(delay)
                                retry_attempts += 1
                                continue
                            else:
                                # Max retries reached
                                self.retry_stats["failed_retries"] += 1
                                self._log_structured_error(crawl_error, "error")
                                return CrawledPage(
                                    url=url,
                                    status_code=0,
                                    response_time=time.time() - start_time,
                                    crawled_at=datetime.now(),
                                    depth=depth,
                                    error=crawl_error,
                                    retry_attempts=retry_attempts,
                                    headings={},
                                    image_alt_text=[],
                                    canonical_url=None
                                )
                    
                    # This should never be reached, but just in case
                    if last_error:
                        self.retry_stats["failed_retries"] += 1
                        self._log_structured_error(last_error, "error")
                        return CrawledPage(
                            url=url,
                            status_code=0,
                            response_time=time.time() - start_time,
                            crawled_at=datetime.now(),
                            depth=depth,
                            error=last_error,
                            retry_attempts=retry_attempts,
                            headings={},
                            image_alt_text=[],
                            canonical_url=None
                        )
                
                finally:
                    # Decrement active requests counter
                    async with self.request_lock:
                        self.active_requests -= 1

    async def crawl_website(self, request: CrawlRequest) -> CrawlResult:
        """Crawl a website with queue-based BFS approach and improved concurrency"""
        task_id = f"crawl_{int(time.time())}"
        start_time = time.time()
        
        result = CrawlResult(
            task_id=task_id,
            status=CrawlStatus.IN_PROGRESS,
            started_at=datetime.now()
        )
        
        try:
            # Reset visited URLs for this crawl
            self.visited_urls.clear()
            
            # Initialize queue with (url, depth) tuples
            # Use deque for efficient BFS operations
            initial_url = str(request.url)
            url_queue = deque([(initial_url, 0)])
            crawled_pages = []
            errors = []  # Keep for backward compatibility
            structured_errors = []  # New structured error tracking
            successful_requests = 0
            total_requests = 0
            
            # Process queue until empty or max depth reached
            while url_queue:
                # Get next URL and its depth
                current_url, current_depth = url_queue.popleft()
                
                # Normalize URL for duplicate checking
                normalized_url = self._normalize_url(current_url)
                
                # Skip if already visited (using normalized URL)
                if normalized_url in self.visited_urls:
                    continue
                
                # Check depth limit (0 means unlimited)
                if request.max_depth > 0 and current_depth > request.max_depth:
                    continue
                
                # Mark as visited (using normalized URL)
                self.visited_urls.add(normalized_url)
                
                # Crawl the URL
                try:
                    page = await self.crawl_url(current_url, request, current_depth)
                    crawled_pages.append(page)
                    total_requests += 1
                    
                    # Count successful requests for concurrency adjustment
                    if page.status_code and page.status_code < 400:
                        successful_requests += 1
                    
                    # Track structured errors if any
                    if page.error:
                        structured_errors.append(page.error)
                        # Also add to legacy errors list for backward compatibility
                        error_msg = f"Error crawling {current_url}: {page.error.message}"
                        errors.append(error_msg)
                    
                    # Add links to queue if following links and within depth limit
                    if (request.follow_links and 
                        (request.max_depth == 0 or current_depth < request.max_depth)):
                        
                        for link in page.links:
                            # Only add internal links from the same domain
                            if self._is_internal_link(str(request.url), link):
                                # Normalize the link for duplicate checking
                                normalized_link = self._normalize_url(link)
                                
                                # Check if not already visited or queued
                                if normalized_link not in self.visited_urls:
                                    # Check if already in queue (using normalized URLs)
                                    if not any(self._normalize_url(url) == normalized_link for url, _ in url_queue):
                                        url_queue.append((link, current_depth + 1))
                    
                    # Periodically adjust concurrency based on performance
                    if total_requests > 0 and total_requests % 20 == 0:
                        success_rate = successful_requests / total_requests
                        await self._adjust_concurrency(success_rate, total_requests)
                    
                except Exception as e:
                    error_msg = f"Error crawling {current_url}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
                    total_requests += 1
            
            # Final concurrency adjustment
            if total_requests > 0:
                success_rate = successful_requests / total_requests
                await self._adjust_concurrency(success_rate, total_requests)
            
            # Update result
            result.pages = crawled_pages
            result.total_pages = len(crawled_pages)
            result.errors = errors
            result.structured_errors = structured_errors
            result.retry_stats = self.retry_stats.copy()
            result.status = CrawlStatus.COMPLETED
            result.completed_at = datetime.now()
            result.duration = time.time() - start_time
            
        except Exception as e:
            logger.error(f"Error in crawl_website: {str(e)}")
            result.status = CrawlStatus.FAILED
            result.errors.append(str(e))
            result.completed_at = datetime.now()
            result.duration = time.time() - start_time
        
        return result

    def _normalize_url(self, url: str) -> str:
        """Normalize URL to avoid duplicates"""
        try:
            parsed = urlparse(url)
            
            # Convert to lowercase for scheme and netloc
            scheme = parsed.scheme.lower()
            netloc = parsed.netloc.lower()
            
            # Remove default ports
            if scheme == 'http' and netloc.endswith(':80'):
                netloc = netloc[:-3]
            elif scheme == 'https' and netloc.endswith(':443'):
                netloc = netloc[:-4]
            
            # Normalize path
            path = parsed.path
            # Remove trailing slash for root paths, keep for others
            if path == '/':
                path = ''
            elif path.endswith('/') and len(path) > 1:
                path = path.rstrip('/')
            
            # Remove fragment (anchor) as it's usually same page content
            fragment = ''
            
            # Keep query parameters as they might be important
            query = parsed.query
            
            # Reconstruct normalized URL
            normalized = urlunparse((scheme, netloc, path, parsed.params, query, fragment))
            
            return normalized
            
        except Exception as e:
            logger.warning(f"Failed to normalize URL {url}: {e}")
            return url

    def _is_same_domain(self, base_url: str, url: str) -> bool:
        """Check if two URLs are from the same domain"""
        try:
            base_domain = urlparse(base_url).netloc
            url_domain = urlparse(url).netloc
            return base_domain == url_domain
        except Exception:
            return False
    
    def _is_internal_link(self, base_url: str, url: str) -> bool:
        """Check if a URL is an internal link (same domain) and valid for crawling"""
        try:
            # Parse both URLs
            base_parsed = urlparse(base_url)
            url_parsed = urlparse(url)
            
            # Must be HTTP or HTTPS
            if url_parsed.scheme not in ['http', 'https']:
                return False
            
            # Must be same domain
            if base_parsed.netloc != url_parsed.netloc:
                return False
            
            # Skip common non-content URLs
            path = url_parsed.path.lower()
            skip_patterns = [
                '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                '.zip', '.rar', '.tar', '.gz', '.jpg', '.jpeg', '.png', '.gif',
                '.svg', '.ico', '.css', '.js', '.xml', '.txt', '.csv'
            ]
            
            for pattern in skip_patterns:
                if path.endswith(pattern):
                    return False
            
            # Skip URLs with fragments (anchors) as they're usually same page
            if url_parsed.fragment:
                return False
            
            return True
            
        except Exception:
            return False
    
    def get_duplicate_avoidance_stats(self) -> dict:
        """Get statistics about duplicate URL avoidance"""
        return {
            "total_visited_urls": len(self.visited_urls),
            "visited_urls_sample": list(self.visited_urls)[:10]  # First 10 for debugging
        }
    
    def get_rate_limiting_stats(self) -> dict:
        """Get statistics about rate limiting"""
        return {
            "enabled": self.rate_limiter.enabled,
            "domain_stats": self.rate_limiter.get_all_domain_stats(),
            "default_limit": self.rate_limiter.default_limit,
            "window_size": self.rate_limiter.window_size
        }
    
    def _classify_error(self, exception: Exception, status_code: Optional[int] = None) -> Tuple[ErrorType, bool]:
        """Classify error as transient or permanent and determine if retryable"""
        if isinstance(exception, aiohttp.ClientTimeout):
            return ErrorType.TRANSIENT, settings.RETRY_ON_TIMEOUT
        
        if isinstance(exception, (aiohttp.ClientConnectionError, aiohttp.ClientConnectorError)):
            return ErrorType.TRANSIENT, settings.RETRY_ON_CONNECTION_ERROR
        
        if status_code is not None:
            # 5xx errors are typically transient
            if 500 <= status_code < 600:
                return ErrorType.TRANSIENT, True
            # 4xx errors are typically permanent (except 429 which is rate limiting)
            elif 400 <= status_code < 500:
                if status_code == 429:  # Rate limiting - retryable
                    return ErrorType.TRANSIENT, True
                return ErrorType.PERMANENT, False
        
        # Default to unknown for other exceptions
        return ErrorType.UNKNOWN, False
    
    def _calculate_retry_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with jitter"""
        if attempt <= 0:
            return 0
        
        # Exponential backoff: base_delay * (multiplier ^ (attempt - 1))
        delay = settings.RETRY_DELAY_BASE * (settings.RETRY_BACKOFF_MULTIPLIER ** (attempt - 1))
        
        # Cap at maximum delay
        delay = min(delay, settings.RETRY_DELAY_MAX)
        
        # Add jitter (±25% random variation)
        jitter = delay * 0.25 * (2 * random.random() - 1)
        delay += jitter
        
        return max(0, delay)
    
    def _create_crawl_error(self, url: str, exception: Exception, status_code: Optional[int] = None, 
                           retry_attempts: int = 0) -> CrawlError:
        """Create a structured CrawlError object"""
        error_type, is_retryable = self._classify_error(exception, status_code)
        
        return CrawlError(
            error_type=error_type,
            status_code=status_code,
            message=str(exception),
            url=url,
            timestamp=datetime.now(),
            retry_attempts=retry_attempts,
            max_retries=settings.MAX_RETRIES,
            is_retryable=is_retryable and retry_attempts < settings.MAX_RETRIES
        )
    
    def _log_structured_error(self, error: CrawlError, level: str = "error"):
        """Log error in structured format for debugging"""
        log_data = {
            "error_type": error.error_type.value,
            "status_code": error.status_code,
            "url": error.url,
            "retry_attempts": error.retry_attempts,
            "is_retryable": error.is_retryable,
            "timestamp": error.timestamp.isoformat(),
            "message": error.message
        }
        
        if level == "error":
            logger.error(f"Structured error: {log_data}")
        elif level == "warning":
            logger.warning(f"Structured error: {log_data}")
        else:
            logger.info(f"Structured error: {log_data}")
    
    def get_retry_stats(self) -> dict:
        """Get retry statistics"""
        return self.retry_stats.copy()
