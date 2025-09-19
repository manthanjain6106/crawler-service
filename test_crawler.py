#!/usr/bin/env python3
"""
Simple test script to crawl Wikipedia main page using the crawler service
"""
import asyncio
import sys
import os
from urllib.parse import urlparse

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crawler_service import WebCrawler
from models import CrawlRequest

async def test_crawl():
    """Test crawling Wikipedia main page"""
    print("Starting Wikipedia crawl test...")
    
    # Create crawl request
    request = CrawlRequest(
        url="https://en.wikipedia.org/wiki/Main_Page",
        max_depth=2,
        follow_links=True,
        extract_text=True,
        extract_images=True,
        extract_links=True,
        extract_headings=True,
        extract_image_alt_text=True,
        extract_canonical_url=True
    )
    
    # Create crawler and run
    async with WebCrawler() as crawler:
        print("Crawling Wikipedia main page...")
        result = await crawler.crawl_website(request)
        
        print(f"\nCrawl completed!")
        print(f"Status: {result.status}")
        print(f"Total pages crawled: {result.total_pages}")
        print(f"Duration: {result.duration:.2f} seconds")
        
        if result.pages:
            print(f"\nFirst page details:")
            first_page = result.pages[0]
            print(f"URL: {first_page.url}")
            print(f"Title: {first_page.title}")
            print(f"Status Code: {first_page.status_code}")
            print(f"Response Time: {first_page.response_time:.2f}s")
            print(f"Images found: {len(first_page.images)}")
            print(f"Links found: {len(first_page.links)}")
            print(f"Headings found: {sum(len(headings) for headings in first_page.headings.values())}")
            
            if first_page.headings:
                print(f"\nSample headings:")
                for level, headings in first_page.headings.items():
                    if headings:
                        print(f"  {level.upper()}: {headings[0]}")
        
        if result.errors:
            print(f"\nErrors encountered: {len(result.errors)}")
            for error in result.errors[:3]:  # Show first 3 errors
                print(f"  - {error}")
        
        if result.retry_stats:
            print(f"\nRetry statistics:")
            for key, value in result.retry_stats.items():
                print(f"  {key}: {value}")

if __name__ == "__main__":
    asyncio.run(test_crawl())
