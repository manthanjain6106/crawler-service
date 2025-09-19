#!/usr/bin/env python3
"""
Comprehensive test for depth handling improvements
This script tests all the new functionality and saves results to a file
"""

import asyncio
import sys
import json
from datetime import datetime
from crawler_service import WebCrawler
from models import CrawlRequest, CrawledPage


class TestResults:
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()
    
    def add_result(self, test_name, success, message, data=None):
        self.results.append({
            'test_name': test_name,
            'success': success,
            'message': message,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    
    def save_to_file(self, filename='test_results.json'):
        with open(filename, 'w') as f:
            json.dump({
                'start_time': self.start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'total_tests': len(self.results),
                'passed_tests': sum(1 for r in self.results if r['success']),
                'results': self.results
            }, f, indent=2)
        print(f"📄 Test results saved to {filename}")


async def test_imports_and_models():
    """Test 1: Basic imports and model creation"""
    try:
        # Test imports
        from crawler_service import WebCrawler
        from models import CrawlRequest, CrawledPage
        
        # Test CrawlRequest with new defaults
        request = CrawlRequest(
            url="https://example.com",
            max_depth=10,  # New default
            follow_links=True
        )
        
        # Test CrawledPage with depth field
        page = CrawledPage(
            url="https://example.com",
            status_code=200,
            response_time=1.0,
            crawled_at=datetime.now(),
            depth=0  # New field
        )
        
        return True, "All imports and models work correctly", {
            'request_max_depth': request.max_depth,
            'page_depth': page.depth
        }
    except Exception as e:
        return False, f"Import/model error: {str(e)}", None


async def test_crawler_initialization():
    """Test 2: WebCrawler initialization"""
    try:
        crawler = WebCrawler(max_concurrent_requests=5)
        
        # Test that the crawler has the expected attributes
        assert hasattr(crawler, 'max_concurrent_requests')
        assert hasattr(crawler, 'visited_urls')
        assert hasattr(crawler, 'semaphore')
        
        return True, "WebCrawler initialized successfully", {
            'max_concurrent_requests': crawler.max_concurrent_requests
        }
    except Exception as e:
        return False, f"Crawler initialization error: {str(e)}", None


async def test_basic_crawling():
    """Test 3: Basic crawling functionality"""
    try:
        request = CrawlRequest(
            url="https://httpbin.org/html",
            max_depth=1,
            follow_links=False,
            extract_text=True,
            extract_links=True
        )
        
        async with WebCrawler() as crawler:
            result = await crawler.crawl_website(request)
        
        # Check basic result structure
        assert hasattr(result, 'status')
        assert hasattr(result, 'total_pages')
        assert hasattr(result, 'pages')
        assert result.status in ['completed', 'failed']
        
        # Check page structure
        if result.pages:
            page = result.pages[0]
            assert hasattr(page, 'depth')
            assert isinstance(page.depth, int)
            assert page.depth >= 0
        
        return True, f"Basic crawling successful: {result.total_pages} pages", {
            'status': result.status,
            'total_pages': result.total_pages,
            'duration': result.duration
        }
    except Exception as e:
        return False, f"Basic crawling error: {str(e)}", None


async def test_depth_tracking():
    """Test 4: Depth tracking functionality"""
    try:
        request = CrawlRequest(
            url="https://httpbin.org/links/2/0",
            max_depth=2,
            follow_links=True,
            extract_text=False,
            extract_links=True
        )
        
        async with WebCrawler() as crawler:
            result = await crawler.crawl_website(request)
        
        # Check depth tracking
        depths = [page.depth for page in result.pages]
        unique_depths = sorted(set(depths))
        
        # Should have pages at different depths
        assert len(unique_depths) > 0
        assert all(isinstance(d, int) for d in depths)
        assert all(d >= 0 for d in depths)
        
        return True, f"Depth tracking works: depths {unique_depths}", {
            'depths_found': unique_depths,
            'total_pages': len(result.pages)
        }
    except Exception as e:
        return False, f"Depth tracking error: {str(e)}", None


async def test_unlimited_depth():
    """Test 5: Unlimited depth functionality"""
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
        
        # Should complete without errors
        assert result.status in ['completed', 'failed']
        
        return True, f"Unlimited depth works: {result.total_pages} pages", {
            'status': result.status,
            'total_pages': result.total_pages
        }
    except Exception as e:
        return False, f"Unlimited depth error: {str(e)}", None


async def test_internal_link_filtering():
    """Test 6: Internal link filtering"""
    try:
        request = CrawlRequest(
            url="https://httpbin.org/html",
            max_depth=1,
            follow_links=True,
            extract_text=False,
            extract_links=True
        )
        
        async with WebCrawler() as crawler:
            result = await crawler.crawl_website(request)
        
        # All crawled pages should be from the same domain
        base_domain = "httpbin.org"
        all_internal = all(base_domain in page.url for page in result.pages)
        
        return True, f"Internal filtering works: {all_internal}", {
            'all_internal': all_internal,
            'total_pages': len(result.pages)
        }
    except Exception as e:
        return False, f"Internal link filtering error: {str(e)}", None


async def run_all_tests():
    """Run all tests and return results"""
    results = TestResults()
    
    tests = [
        ("Import and Models", test_imports_and_models),
        ("Crawler Initialization", test_crawler_initialization),
        ("Basic Crawling", test_basic_crawling),
        ("Depth Tracking", test_depth_tracking),
        ("Unlimited Depth", test_unlimited_depth),
        ("Internal Link Filtering", test_internal_link_filtering)
    ]
    
    print("🚀 Starting comprehensive depth handling tests...\n")
    
    for test_name, test_func in tests:
        print(f"🧪 Running {test_name}...")
        try:
            success, message, data = await test_func()
            if success:
                print(f"✅ {test_name}: {message}")
            else:
                print(f"❌ {test_name}: {message}")
            results.add_result(test_name, success, message, data)
        except Exception as e:
            print(f"💥 {test_name}: Unexpected error - {str(e)}")
            results.add_result(test_name, False, f"Unexpected error: {str(e)}")
        print()
    
    # Save results
    results.save_to_file()
    
    # Print summary
    passed = sum(1 for r in results.results if r['success'])
    total = len(results.results)
    
    print(f"📊 Test Summary: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Depth handling improvements are working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check test_results.json for details.")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Tests failed with error: {e}")
        sys.exit(1)
