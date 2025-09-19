"""
Demonstration of error handling and retry logic in the crawler service.
This script shows how the crawler handles different types of errors and retries.
"""
import asyncio
import logging
from crawler_service import WebCrawler
from models import CrawlRequest
from config import settings

# Set up logging to see retry attempts
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_error_handling():
    """Demonstrate error handling and retry functionality"""
    print("=== Error Handling & Retry Demo ===\n")
    
    # Display current retry configuration
    print("Retry Configuration:")
    print(f"  Max Retries: {settings.MAX_RETRIES}")
    print(f"  Base Delay: {settings.RETRY_DELAY_BASE}s")
    print(f"  Max Delay: {settings.RETRY_DELAY_MAX}s")
    print(f"  Backoff Multiplier: {settings.RETRY_BACKOFF_MULTIPLIER}")
    print(f"  Retry on Timeout: {settings.RETRY_ON_TIMEOUT}")
    print(f"  Retry on Connection Error: {settings.RETRY_ON_CONNECTION_ERROR}")
    print()
    
    async with WebCrawler() as crawler:
        # Test 1: Crawl a working website
        print("Test 1: Crawling a working website (httpbin.org)")
        print("-" * 50)
        
        request1 = CrawlRequest(
            url="https://httpbin.org/html",
            max_depth=0,
            follow_links=False,
            extract_text=True,
            extract_images=False,
            extract_links=False
        )
        
        result1 = await crawler.crawl_website(request1)
        print(f"Status: {result1.status}")
        print(f"Pages crawled: {result1.total_pages}")
        print(f"Errors: {len(result1.errors)}")
        print(f"Structured errors: {len(result1.structured_errors)}")
        print(f"Retry stats: {result1.retry_stats}")
        print()
        
        # Test 2: Crawl a website that returns 404 (permanent error)
        print("Test 2: Crawling a non-existent page (404 - permanent error)")
        print("-" * 50)
        
        request2 = CrawlRequest(
            url="https://httpbin.org/status/404",
            max_depth=0,
            follow_links=False,
            extract_text=True,
            extract_images=False,
            extract_links=False
        )
        
        result2 = await crawler.crawl_website(request2)
        print(f"Status: {result2.status}")
        print(f"Pages crawled: {result2.total_pages}")
        print(f"Errors: {len(result2.errors)}")
        print(f"Structured errors: {len(result2.structured_errors)}")
        if result2.structured_errors:
            error = result2.structured_errors[0]
            print(f"  Error type: {error.error_type}")
            print(f"  Status code: {error.status_code}")
            print(f"  Retry attempts: {error.retry_attempts}")
            print(f"  Is retryable: {error.is_retryable}")
        print(f"Retry stats: {result2.retry_stats}")
        print()
        
        # Test 3: Crawl a website that returns 502 (transient error)
        print("Test 3: Crawling a page that returns 502 (transient error)")
        print("-" * 50)
        
        request3 = CrawlRequest(
            url="https://httpbin.org/status/502",
            max_depth=0,
            follow_links=False,
            extract_text=True,
            extract_images=False,
            extract_links=False
        )
        
        result3 = await crawler.crawl_website(request3)
        print(f"Status: {result3.status}")
        print(f"Pages crawled: {result3.total_pages}")
        print(f"Errors: {len(result3.errors)}")
        print(f"Structured errors: {len(result3.structured_errors)}")
        if result3.structured_errors:
            error = result3.structured_errors[0]
            print(f"  Error type: {error.error_type}")
            print(f"  Status code: {error.status_code}")
            print(f"  Retry attempts: {error.retry_attempts}")
            print(f"  Is retryable: {error.is_retryable}")
        print(f"Retry stats: {result3.retry_stats}")
        print()
        
        # Test 4: Crawl a website with timeout (transient error)
        print("Test 4: Crawling a slow website (timeout - transient error)")
        print("-" * 50)
        
        request4 = CrawlRequest(
            url="https://httpbin.org/delay/5",  # 5 second delay
            max_depth=0,
            follow_links=False,
            extract_text=True,
            extract_images=False,
            extract_links=False,
            timeout=2  # 2 second timeout
        )
        
        result4 = await crawler.crawl_website(request4)
        print(f"Status: {result4.status}")
        print(f"Pages crawled: {result4.total_pages}")
        print(f"Errors: {len(result4.errors)}")
        print(f"Structured errors: {len(result4.structured_errors)}")
        if result4.structured_errors:
            error = result4.structured_errors[0]
            print(f"  Error type: {error.error_type}")
            print(f"  Status code: {error.status_code}")
            print(f"  Retry attempts: {error.retry_attempts}")
            print(f"  Is retryable: {error.is_retryable}")
        print(f"Retry stats: {result4.retry_stats}")
        print()
        
        # Display final retry statistics
        print("Final Retry Statistics:")
        print("-" * 50)
        final_stats = crawler.get_retry_stats()
        for key, value in final_stats.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    asyncio.run(demo_error_handling())
