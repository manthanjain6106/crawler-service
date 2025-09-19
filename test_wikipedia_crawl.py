#!/usr/bin/env python3
"""
Conservative Wikipedia crawl test with proper rate limiting
"""
import asyncio
import sys
import os
import time

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crawler_service import WebCrawler
from models import CrawlRequest

async def test_wikipedia_crawl():
    """Test crawling Wikipedia main page with conservative settings"""
    print("Starting conservative Wikipedia crawl test...")
    
    # Create crawl request with conservative settings
    request = CrawlRequest(
        url="https://en.wikipedia.org/wiki/Main_Page",
        max_depth=1,  # Only crawl the main page, don't follow links
        follow_links=False,  # Don't follow links to avoid rate limiting
        extract_text=True,
        extract_images=True,
        extract_links=True,
        extract_headings=True,
        extract_image_alt_text=True,
        extract_canonical_url=True
    )
    
    # Create crawler with conservative settings
    async with WebCrawler(max_concurrent_requests=1) as crawler:
        print("Crawling Wikipedia main page (single page only)...")
        start_time = time.time()
        
        result = await crawler.crawl_website(request)
        
        duration = time.time() - start_time
        print(f"\nCrawl completed!")
        print(f"Status: {result.status}")
        print(f"Total pages crawled: {result.total_pages}")
        print(f"Duration: {duration:.2f} seconds")
        
        if result.pages:
            print(f"\nPage details:")
            page = result.pages[0]
            print(f"URL: {page.url}")
            print(f"Title: {page.title}")
            print(f"Status Code: {page.status_code}")
            print(f"Response Time: {page.response_time:.2f}s")
            print(f"Images found: {len(page.images)}")
            print(f"Links found: {len(page.links)}")
            print(f"Headings found: {sum(len(headings) for headings in page.headings.values())}")
            
            if page.headings:
                print(f"\nSample headings:")
                for level, headings in page.headings.items():
                    if headings:
                        print(f"  {level.upper()}: {headings[0]}")
            
            if page.text_content:
                # Show first 200 characters of text content
                text_preview = page.text_content[:200].replace('\n', ' ').strip()
                print(f"\nText content preview: {text_preview}...")
            
            if page.images:
                print(f"\nSample images:")
                for img in page.images[:3]:  # Show first 3 images
                    print(f"  - {img}")
        
        if result.errors:
            print(f"\nErrors encountered: {len(result.errors)}")
            for error in result.errors[:3]:  # Show first 3 errors
                print(f"  - {error}")
        
        if result.retry_stats:
            print(f"\nRetry statistics:")
            for key, value in result.retry_stats.items():
                print(f"  {key}: {value}")

if __name__ == "__main__":
    asyncio.run(test_wikipedia_crawl())
