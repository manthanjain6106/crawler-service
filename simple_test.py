#!/usr/bin/env python3
"""
Simple test to verify the crawler works
"""
import asyncio
from crawler_service import WebCrawler
from models import CrawlRequest

async def test_crawler():
    """Test the crawler directly"""
    print("Testing crawler service...")
    
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
    
    print(f"Status: {result.status}")
    print(f"Total pages: {result.total_pages}")
    print(f"Errors: {result.errors}")
    
    if result.pages:
        page = result.pages[0]
        print(f"URL: {page.url}")
        print(f"Title: {page.title}")
        print(f"Status Code: {page.status_code}")
        print(f"Response Time: {page.response_time:.2f}s")

if __name__ == "__main__":
    asyncio.run(test_crawler())
