import asyncio
import time
from typing import Dict, Optional
from urllib.parse import urlparse
import logging
from collections import defaultdict, deque
from config import settings

logger = logging.getLogger(__name__)


class RateLimitManager:
    """
    Manages per-domain rate limiting for web crawling.
    Uses a sliding window approach to track requests per domain.
    """
    
    def __init__(self):
        self.enabled = settings.ENABLE_PER_DOMAIN_RATE_LIMITING
        self.default_limit = settings.DEFAULT_DOMAIN_RATE_LIMIT
        self.window_size = settings.DOMAIN_RATE_LIMIT_WINDOW
        self.domain_limits = settings.DOMAIN_SPECIFIC_LIMITS.copy()
        
        # Per-domain request tracking: {domain: deque of timestamps}
        self.domain_requests: Dict[str, deque] = defaultdict(lambda: deque())
        self.locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        
        logger.info(f"RateLimitManager initialized - Enabled: {self.enabled}, "
                   f"Default limit: {self.default_limit}/min, "
                   f"Window: {self.window_size}s")
    
    def _get_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove port if present
            if ':' in domain:
                domain = domain.split(':')[0]
            return domain
        except Exception as e:
            logger.warning(f"Failed to parse domain from URL {url}: {e}")
            return "unknown"
    
    def _get_domain_limit(self, domain: str) -> int:
        """Get the rate limit for a specific domain"""
        return self.domain_limits.get(domain, self.default_limit)
    
    async def _cleanup_old_requests(self, domain: str):
        """Remove requests older than the window size"""
        current_time = time.time()
        cutoff_time = current_time - self.window_size
        
        # Remove old timestamps
        while (self.domain_requests[domain] and 
               self.domain_requests[domain][0] < cutoff_time):
            self.domain_requests[domain].popleft()
    
    async def can_make_request(self, url: str) -> bool:
        """
        Check if a request can be made to the given URL without exceeding rate limits.
        Returns True if request is allowed, False if rate limited.
        """
        if not self.enabled:
            return True
        
        domain = self._get_domain(url)
        limit = self._get_domain_limit(domain)
        
        async with self.locks[domain]:
            # Clean up old requests
            await self._cleanup_old_requests(domain)
            
            # Check if we're under the limit
            current_requests = len(self.domain_requests[domain])
            can_request = current_requests < limit
            
            if not can_request:
                logger.debug(f"Rate limit exceeded for domain {domain}: "
                           f"{current_requests}/{limit} requests in window")
            
            return can_request
    
    async def record_request(self, url: str) -> None:
        """
        Record a request to the given URL for rate limiting purposes.
        Should be called after a successful request.
        """
        if not self.enabled:
            return
        
        domain = self._get_domain(url)
        current_time = time.time()
        
        async with self.locks[domain]:
            # Clean up old requests first
            await self._cleanup_old_requests(domain)
            
            # Add current request timestamp
            self.domain_requests[domain].append(current_time)
            
            logger.debug(f"Recorded request for domain {domain}: "
                        f"{len(self.domain_requests[domain])}/{self._get_domain_limit(domain)}")
    
    async def get_wait_time(self, url: str) -> float:
        """
        Get the time to wait before the next request to the given URL can be made.
        Returns 0 if no wait is needed.
        """
        if not self.enabled:
            return 0.0
        
        domain = self._get_domain(url)
        limit = self._get_domain_limit(domain)
        
        async with self.locks[domain]:
            await self._cleanup_old_requests(domain)
            
            current_requests = len(self.domain_requests[domain])
            if current_requests < limit:
                return 0.0
            
            # Calculate wait time based on oldest request in window
            if self.domain_requests[domain]:
                oldest_request = self.domain_requests[domain][0]
                wait_time = (oldest_request + self.window_size) - time.time()
                return max(0.0, wait_time)
            
            return 0.0
    
    async def wait_if_needed(self, url: str) -> None:
        """
        Wait if necessary to respect rate limits for the given URL.
        This is a convenience method that combines can_make_request and get_wait_time.
        """
        if not self.enabled:
            return
        
        wait_time = await self.get_wait_time(url)
        if wait_time > 0:
            logger.info(f"Rate limiting: waiting {wait_time:.2f}s before request to {url}")
            await asyncio.sleep(wait_time)
    
    def get_domain_stats(self, domain: str) -> Dict[str, int]:
        """Get current statistics for a domain"""
        if not self.enabled:
            return {"limit": 0, "current": 0, "remaining": 0}
        
        limit = self._get_domain_limit(domain)
        current = len(self.domain_requests[domain])
        return {
            "limit": limit,
            "current": current,
            "remaining": max(0, limit - current)
        }
    
    def get_all_domain_stats(self) -> Dict[str, Dict[str, int]]:
        """Get statistics for all domains"""
        if not self.enabled:
            return {}
        
        stats = {}
        for domain in self.domain_requests.keys():
            stats[domain] = self.get_domain_stats(domain)
        return stats
    
    def set_domain_limit(self, domain: str, limit: int) -> None:
        """Set a custom rate limit for a specific domain"""
        self.domain_limits[domain] = limit
        logger.info(f"Set custom rate limit for {domain}: {limit} requests per {self.window_size}s")
    
    def remove_domain_limit(self, domain: str) -> None:
        """Remove custom rate limit for a domain (revert to default)"""
        if domain in self.domain_limits:
            del self.domain_limits[domain]
            logger.info(f"Removed custom rate limit for {domain}, using default: {self.default_limit}")
