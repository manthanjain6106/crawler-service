#!/usr/bin/env python3
"""
Demonstration script for improved depth handling in the crawler service.
This script shows the difference between shallow and deep crawling.
"""

import asyncio
import sys
from crawler_service import WebCrawler
from models import CrawlRequest


async def demo_depth_handling():
    """Demonstrate the improved depth handling capabilities"""
    
    # Test URL that has multiple levels of links
    test_url = "https://httpbin.org/links/3/0"  # Creates 3 levels of links
    
    print("🕷️  Web Crawler Depth Handling Demo")
    print("=" * 50)
    print(f"Test URL: {test_url}")
    print()
    
    # Test 1: Shallow crawling (depth = 1)
    print("📊 Test 1: Shallow Crawling (max_depth=1)")
    print("-" * 30)
    
    request_shallow = CrawlRequest(
        url=test_url,
        max_depth=1,
        follow_links=True,
        extract_text=False,  # Skip text extraction for faster demo
        extract_images=False,
        extract_links=True
    )
    
    async with WebCrawler() as crawler:
        result_shallow = await crawler.crawl_website(request_shallow)
    
    print(f"Status: {result_shallow.status}")
    print(f"Total pages crawled: {result_shallow.total_pages}")
    print("Pages by depth:")
    for page in result_shallow.pages:
        print(f"  Depth {page.depth}: {page.url}")
    print()
    
    # Test 2: Deep crawling (depth = 3)
    print("📊 Test 2: Deep Crawling (max_depth=3)")
    print("-" * 30)
    
    request_deep = CrawlRequest(
        url=test_url,
        max_depth=3,
        follow_links=True,
        extract_text=False,
        extract_images=False,
        extract_links=True
    )
    
    async with WebCrawler() as crawler:
        result_deep = await crawler.crawl_website(request_deep)
    
    print(f"Status: {result_deep.status}")
    print(f"Total pages crawled: {result_deep.total_pages}")
    print("Pages by depth:")
    for page in result_deep.pages:
        print(f"  Depth {page.depth}: {page.url}")
    print()
    
    # Test 3: Unlimited depth (max_depth=0)
    print("📊 Test 3: Unlimited Depth (max_depth=0)")
    print("-" * 30)
    
    request_unlimited = CrawlRequest(
        url=test_url,
        max_depth=0,  # Unlimited depth
        follow_links=True,
        extract_text=False,
        extract_images=False,
        extract_links=True
    )
    
    async with WebCrawler() as crawler:
        result_unlimited = await crawler.crawl_website(request_unlimited)
    
    print(f"Status: {result_unlimited.status}")
    print(f"Total pages crawled: {result_unlimited.total_pages}")
    print("Pages by depth:")
    for page in result_unlimited.pages:
        print(f"  Depth {page.depth}: {page.url}")
    print()
    
    # Summary
    print("📈 Summary")
    print("-" * 30)
    print(f"Shallow crawling (depth=1): {result_shallow.total_pages} pages")
    print(f"Deep crawling (depth=3): {result_deep.total_pages} pages")
    print(f"Unlimited depth: {result_unlimited.total_pages} pages")
    print()
    print("✅ Key improvements:")
    print("  • Queue-based BFS crawling for better performance")
    print("  • Support for unlimited depth (max_depth=0)")
    print("  • Enhanced internal link filtering")
    print("  • Depth tracking for each crawled page")
    print("  • Higher default max_depth (10 instead of 3)")


async def demo_internal_link_filtering():
    """Demonstrate internal link filtering"""
    
    print("\n🔗 Internal Link Filtering Demo")
    print("=" * 50)
    
    # Test with a URL that might have external links
    test_url = "https://httpbin.org/html"
    
    request = CrawlRequest(
        url=test_url,
        max_depth=2,
        follow_links=True,
        extract_text=False,
        extract_images=False,
        extract_links=True
    )
    
    async with WebCrawler() as crawler:
        result = await crawler.crawl_website(request)
    
    print(f"Test URL: {test_url}")
    print(f"Status: {result.status}")
    print(f"Total pages crawled: {result.total_pages}")
    print()
    print("All crawled pages (should be internal only):")
    for page in result.pages:
        print(f"  {page.url}")
    
    # Check if all URLs are from the same domain
    base_domain = "httpbin.org"
    all_internal = all(base_domain in page.url for page in result.pages)
    print(f"\n✅ All pages are internal: {all_internal}")


if __name__ == "__main__":
    print("Starting depth handling demonstration...")
    print("This may take a moment to complete.\n")
    
    try:
        asyncio.run(demo_depth_handling())
        asyncio.run(demo_internal_link_filtering())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nDemo failed with error: {e}")
        sys.exit(1)
    
    print("\n🎉 Demo completed successfully!")
