import pytest
import asyncio
from crawler_service import WebCrawler
from models import CrawlRequest


@pytest.mark.asyncio
async def test_crawl_single_url():
    """Test crawling a single URL"""
    request = CrawlRequest(
        url="https://httpbin.org/html",
        max_depth=0,
        follow_links=False,
        extract_text=True,
        extract_images=True,
        extract_links=True
    )
    
    async with WebCrawler() as crawler:
        result = await crawler.crawl_website(request)
    
    assert result.status == "completed"
    assert result.total_pages >= 1
    assert len(result.pages) >= 1
    
    page = result.pages[0]
    assert page.url == "https://httpbin.org/html"
    assert page.status_code == 200
    assert page.title is not None
    assert page.text_content is not None


@pytest.mark.asyncio
async def test_crawl_with_depth():
    """Test crawling with depth > 0"""
    request = CrawlRequest(
        url="https://httpbin.org/links/2/0",
        max_depth=1,
        follow_links=True,
        extract_text=True,
        extract_links=True
    )
    
    async with WebCrawler() as crawler:
        result = await crawler.crawl_website(request)
    
    assert result.status == "completed"
    assert result.total_pages >= 1


@pytest.mark.asyncio
async def test_crawl_depth_tracking():
    """Test that depth is properly tracked in crawled pages"""
    request = CrawlRequest(
        url="https://httpbin.org/links/2/0",
        max_depth=2,
        follow_links=True,
        extract_text=True,
        extract_links=True
    )
    
    async with WebCrawler() as crawler:
        result = await crawler.crawl_website(request)
    
    assert result.status == "completed"
    assert result.total_pages >= 1
    
    # Check that depth is tracked
    for page in result.pages:
        assert hasattr(page, 'depth')
        assert isinstance(page.depth, int)
        assert page.depth >= 0


@pytest.mark.asyncio
async def test_crawl_unlimited_depth():
    """Test crawling with unlimited depth (max_depth=0)"""
    request = CrawlRequest(
        url="https://httpbin.org/links/1/0",
        max_depth=0,  # Unlimited depth
        follow_links=True,
        extract_text=True,
        extract_links=True
    )
    
    async with WebCrawler() as crawler:
        result = await crawler.crawl_website(request)
    
    assert result.status == "completed"
    assert result.total_pages >= 1


@pytest.mark.asyncio
async def test_internal_link_filtering():
    """Test that only internal links are followed"""
    request = CrawlRequest(
        url="https://httpbin.org/links/2/0",
        max_depth=1,
        follow_links=True,
        extract_text=True,
        extract_links=True
    )
    
    async with WebCrawler() as crawler:
        result = await crawler.crawl_website(request)
    
    assert result.status == "completed"
    
    # All crawled pages should be from the same domain
    base_domain = "httpbin.org"
    for page in result.pages:
        assert base_domain in page.url


if __name__ == "__main__":
    # Run a simple test
    async def main():
        request = CrawlRequest(
            url="https://httpbin.org/html",
            max_depth=0,
            follow_links=False,
            extract_text=True
        )
        
        async with WebCrawler() as crawler:
            result = await crawler.crawl_website(request)
        
        print(f"Status: {result.status}")
        print(f"Total pages: {result.total_pages}")
        if result.pages:
            page = result.pages[0]
            print(f"URL: {page.url}")
            print(f"Title: {page.title}")
            print(f"Status Code: {page.status_code}")
    
    asyncio.run(main())
