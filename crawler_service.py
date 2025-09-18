import asyncio
import aiohttp
import time
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from typing import List, Set, Optional
import logging
from datetime import datetime
from models import CrawlRequest, CrawledPage, CrawlResult, CrawlStatus
import re

logger = logging.getLogger(__name__)


class WebCrawler:
    def __init__(self, max_concurrent_requests: int = 10):
        self.max_concurrent_requests = max_concurrent_requests
        self.session: Optional[aiohttp.ClientSession] = None
        self.visited_urls: Set[str] = set()
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)

    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def crawl_url(self, url: str, request: CrawlRequest) -> CrawledPage:
        """Crawl a single URL and extract data"""
        async with self.semaphore:
            start_time = time.time()
            
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                if request.custom_headers:
                    headers.update(request.custom_headers)

                async with self.session.get(url, headers=headers) as response:
                    response_time = time.time() - start_time
                    content = await response.text()
                    
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
                    
                    # Extract images
                    images = []
                    if request.extract_images:
                        img_tags = soup.find_all('img')
                        for img in img_tags:
                            src = img.get('src')
                            if src:
                                # Convert relative URLs to absolute
                                absolute_url = urljoin(url, src)
                                images.append(absolute_url)
                    
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
                    
                    return CrawledPage(
                        url=url,
                        title=title_text,
                        text_content=text_content,
                        images=images,
                        links=links,
                        meta_description=meta_description,
                        status_code=response.status,
                        response_time=response_time,
                        crawled_at=datetime.now()
                    )
                    
            except Exception as e:
                logger.error(f"Error crawling {url}: {str(e)}")
                return CrawledPage(
                    url=url,
                    status_code=0,
                    response_time=time.time() - start_time,
                    crawled_at=datetime.now()
                )

    async def crawl_website(self, request: CrawlRequest) -> CrawlResult:
        """Crawl a website with the given parameters"""
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
            
            # Start with the main URL
            urls_to_crawl = [str(request.url)]
            crawled_pages = []
            errors = []
            
            for depth in range(request.max_depth + 1):
                if not urls_to_crawl:
                    break
                
                # Filter out already visited URLs
                new_urls = [url for url in urls_to_crawl if url not in self.visited_urls]
                urls_to_crawl = []
                
                if not new_urls:
                    break
                
                # Crawl URLs at current depth
                tasks = [self.crawl_url(url, request) for url in new_urls]
                pages = await asyncio.gather(*tasks, return_exceptions=True)
                
                for page in pages:
                    if isinstance(page, Exception):
                        errors.append(f"Error crawling URL: {str(page)}")
                        continue
                    
                    crawled_pages.append(page)
                    self.visited_urls.add(page.url)
                    
                    # Add links for next depth if following links
                    if request.follow_links and depth < request.max_depth:
                        for link in page.links:
                            # Only add links from the same domain
                            if self._is_same_domain(str(request.url), link):
                                urls_to_crawl.append(link)
            
            # Update result
            result.pages = crawled_pages
            result.total_pages = len(crawled_pages)
            result.errors = errors
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

    def _is_same_domain(self, base_url: str, url: str) -> bool:
        """Check if two URLs are from the same domain"""
        try:
            base_domain = urlparse(base_url).netloc
            url_domain = urlparse(url).netloc
            return base_domain == url_domain
        except Exception:
            return False
