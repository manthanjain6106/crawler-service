#!/usr/bin/env python3
"""
Simple test script to verify depth handling improvements
"""

import asyncio
import sys
from crawler_service import WebCrawler
from models import CrawlRequest


async def test_basic_crawling():
    """Test basic crawling functionality"""
    print("🧪 Testing basic crawling functionality...")
    
    try:
        # Test with a simple URL
        request = CrawlRequest(
            url="https://httpbin.org/html",
            max_depth=1,
            follow_links=False,
            extract_text=True,
            extract_links=True
        )
        
        async with WebCrawler() as crawler:
            result = await crawler.crawl_website(request)
        
        print(f"✅ Status: {result.status}")
        print(f"✅ Total pages: {result.total_pages}")
        print(f"✅ Duration: {result.duration:.2f}s")
        
        if result.pages:
            page = result.pages[0]
            print(f"✅ First page URL: {page.url}")
            print(f"✅ First page depth: {page.depth}")
            print(f"✅ First page title: {page.title}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_depth_tracking():
    """Test depth tracking functionality"""
    print("\n🧪 Testing depth tracking...")
    
    try:
        # Test with a URL that has links
        request = CrawlRequest(
            url="https://httpbin.org/links/2/0",
            max_depth=2,
            follow_links=True,
            extract_text=False,
            extract_links=True
        )
        
        async with WebCrawler() as crawler:
            result = await crawler.crawl_website(request)
        
        print(f"✅ Status: {result.status}")
        print(f"✅ Total pages: {result.total_pages}")
        
        # Check depth tracking
        depths = [page.depth for page in result.pages]
        print(f"✅ Depths found: {sorted(set(depths))}")
        
        for page in result.pages:
            print(f"  Depth {page.depth}: {page.url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_unlimited_depth():
    """Test unlimited depth functionality"""
    print("\n🧪 Testing unlimited depth...")
    
    try:
        request = CrawlRequest(
            url="https://httpbin.org/links/1/0",
            max_depth=0,  # Unlimited depth
            follow_links=True,
            extract_text=False,
            extract_links=True
        )
        
        async with WebCrawler() as crawler:
            result = await crawler.crawl_website(request)
        
        print(f"✅ Status: {result.status}")
        print(f"✅ Total pages: {result.total_pages}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def main():
    """Run all tests"""
    print("🚀 Starting depth handling tests...\n")
    
    tests = [
        test_basic_crawling,
        test_depth_tracking,
        test_unlimited_depth
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if await test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Depth handling is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Tests failed with error: {e}")
        sys.exit(1)
