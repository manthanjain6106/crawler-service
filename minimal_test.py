#!/usr/bin/env python3
"""
Minimal test to verify the crawler works
"""

def test_imports():
    """Test that all imports work"""
    try:
        from crawler_service import WebCrawler
        from models import CrawlRequest, CrawledPage
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_model_creation():
    """Test that models can be created"""
    try:
        from models import CrawlRequest, CrawledPage
        from datetime import datetime
        
        # Test CrawlRequest creation
        request = CrawlRequest(
            url="https://example.com",
            max_depth=5,
            follow_links=True
        )
        print(f"✅ CrawlRequest created: max_depth={request.max_depth}")
        
        # Test CrawledPage creation
        page = CrawledPage(
            url="https://example.com",
            status_code=200,
            response_time=1.0,
            crawled_at=datetime.now(),
            depth=0
        )
        print(f"✅ CrawledPage created: depth={page.depth}")
        
        return True
    except Exception as e:
        print(f"❌ Model creation error: {e}")
        return False

def test_crawler_initialization():
    """Test that WebCrawler can be initialized"""
    try:
        from crawler_service import WebCrawler
        
        crawler = WebCrawler(max_concurrent_requests=5)
        print(f"✅ WebCrawler initialized: max_concurrent={crawler.max_concurrent_requests}")
        
        return True
    except Exception as e:
        print(f"❌ Crawler initialization error: {e}")
        return False

def main():
    """Run minimal tests"""
    print("🧪 Running minimal tests...\n")
    
    tests = [
        test_imports,
        test_model_creation,
        test_crawler_initialization
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All minimal tests passed!")
        return True
    else:
        print("⚠️  Some tests failed")
        return False

if __name__ == "__main__":
    main()
