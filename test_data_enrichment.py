#!/usr/bin/env python3
"""
Test script for data enrichment features in the crawler service.
Tests the extraction of headings, image alt text, and canonical URLs.
"""

import asyncio
import sys
import os
from datetime import datetime
from models import CrawlRequest
from crawler_service import WebCrawler

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_data_enrichment():
    """Test the new data enrichment features"""
    print("🧪 Testing Data Enrichment Features")
    print("=" * 50)
    
    # Test URL with rich content for data extraction
    test_url = "https://example.com"  # We'll use a mock HTML content
    
    # Create a test request with all enrichment features enabled
    request = CrawlRequest(
        url=test_url,
        max_depth=0,  # Only test the main page
        follow_links=False,
        extract_text=True,
        extract_images=True,
        extract_links=True,
        extract_headings=True,
        extract_image_alt_text=True,
        extract_canonical_url=True
    )
    
    print(f"📋 Test Request Configuration:")
    print(f"   URL: {request.url}")
    print(f"   Extract Headings: {request.extract_headings}")
    print(f"   Extract Image Alt Text: {request.extract_image_alt_text}")
    print(f"   Extract Canonical URL: {request.extract_canonical_url}")
    print()
    
    # Test with a real website that has rich content
    test_urls = [
        "https://httpbin.org/html",  # Simple HTML page for testing
        "https://example.com",       # Basic example page
    ]
    
    async with WebCrawler() as crawler:
        for test_url in test_urls:
            print(f"🔍 Testing URL: {test_url}")
            print("-" * 30)
            
            try:
                # Create a new request for each URL
                test_request = CrawlRequest(
                    url=test_url,
                    max_depth=0,
                    follow_links=False,
                    extract_text=True,
                    extract_images=True,
                    extract_links=True,
                    extract_headings=True,
                    extract_image_alt_text=True,
                    extract_canonical_url=True
                )
                
                # Crawl the URL
                page = await crawler.crawl_url(test_url, test_request)
                
                # Display results
                print(f"✅ Status Code: {page.status_code}")
                print(f"⏱️  Response Time: {page.response_time:.2f}s")
                print(f"📄 Title: {page.title}")
                print(f"📝 Meta Description: {page.meta_description}")
                print(f"🔗 Canonical URL: {page.canonical_url}")
                
                # Test headings extraction
                print(f"\n📋 Headings:")
                for level, headings in page.headings.items():
                    if headings:
                        print(f"   {level.upper()}: {len(headings)} found")
                        for i, heading in enumerate(headings[:3], 1):  # Show first 3
                            print(f"     {i}. {heading}")
                        if len(headings) > 3:
                            print(f"     ... and {len(headings) - 3} more")
                    else:
                        print(f"   {level.upper()}: None found")
                
                # Test image alt text extraction
                print(f"\n🖼️  Images & Alt Text:")
                print(f"   Total Images: {len(page.images)}")
                print(f"   Images with Alt Text: {len(page.image_alt_text)}")
                
                if page.images:
                    print("   Image URLs:")
                    for i, img_url in enumerate(page.images[:3], 1):  # Show first 3
                        print(f"     {i}. {img_url}")
                    if len(page.images) > 3:
                        print(f"     ... and {len(page.images) - 3} more")
                
                if page.image_alt_text:
                    print("   Alt Text:")
                    for i, alt_text in enumerate(page.image_alt_text[:3], 1):  # Show first 3
                        print(f"     {i}. {alt_text}")
                    if len(page.image_alt_text) > 3:
                        print(f"     ... and {len(page.image_alt_text) - 3} more")
                
                # Test links extraction
                print(f"\n🔗 Links:")
                print(f"   Total Links: {len(page.links)}")
                if page.links:
                    print("   Sample Links:")
                    for i, link in enumerate(page.links[:3], 1):  # Show first 3
                        print(f"     {i}. {link}")
                    if len(page.links) > 3:
                        print(f"     ... and {len(page.links) - 3} more")
                
                # Test text content
                if page.text_content:
                    print(f"\n📄 Text Content:")
                    print(f"   Length: {len(page.text_content)} characters")
                    print(f"   Preview: {page.text_content[:200]}...")
                
                if page.error:
                    print(f"\n❌ Error: {page.error.message}")
                    print(f"   Error Type: {page.error.error_type}")
                    print(f"   Retryable: {page.error.is_retryable}")
                
            except Exception as e:
                print(f"❌ Error testing {test_url}: {str(e)}")
            
            print("\n" + "=" * 50 + "\n")

async def test_selective_extraction():
    """Test selective extraction of enrichment features"""
    print("🎯 Testing Selective Data Extraction")
    print("=" * 50)
    
    test_url = "https://httpbin.org/html"
    
    # Test with only headings enabled
    print("📋 Testing with only headings extraction enabled...")
    request_headings_only = CrawlRequest(
        url=test_url,
        max_depth=0,
        follow_links=False,
        extract_text=False,
        extract_images=False,
        extract_links=False,
        extract_headings=True,
        extract_image_alt_text=False,
        extract_canonical_url=False
    )
    
    async with WebCrawler() as crawler:
        page = await crawler.crawl_url(test_url, request_headings_only)
        
        print(f"✅ Headings extracted: {len(page.headings.get('h1', [])) + len(page.headings.get('h2', [])) + len(page.headings.get('h3', []))}")
        print(f"❌ Images extracted: {len(page.images)}")
        print(f"❌ Alt text extracted: {len(page.image_alt_text)}")
        print(f"❌ Canonical URL extracted: {page.canonical_url is not None}")
    
    print("\n" + "=" * 50 + "\n")

async def test_data_quality():
    """Test the quality and completeness of extracted data"""
    print("🔍 Testing Data Quality and Completeness")
    print("=" * 50)
    
    test_url = "https://httpbin.org/html"
    
    request = CrawlRequest(
        url=test_url,
        max_depth=0,
        follow_links=False,
        extract_text=True,
        extract_images=True,
        extract_links=True,
        extract_headings=True,
        extract_image_alt_text=True,
        extract_canonical_url=True
    )
    
    async with WebCrawler() as crawler:
        page = await crawler.crawl_url(test_url, request)
        
        # Data quality checks
        quality_checks = {
            "Title extracted": page.title is not None and len(page.title.strip()) > 0,
            "Meta description extracted": page.meta_description is not None and len(page.meta_description.strip()) > 0,
            "Headings structure correct": isinstance(page.headings, dict) and all(level in page.headings for level in ['h1', 'h2', 'h3']),
            "Image alt text is list": isinstance(page.image_alt_text, list),
            "Canonical URL is string or None": page.canonical_url is None or isinstance(page.canonical_url, str),
            "No empty headings": all(len(headings) == 0 or all(len(h.strip()) > 0 for h in headings) for headings in page.headings.values()),
            "No empty alt text": all(len(alt.strip()) > 0 for alt in page.image_alt_text),
        }
        
        print("📊 Data Quality Checks:")
        for check, passed in quality_checks.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {check}")
        
        # Summary statistics
        total_headings = sum(len(headings) for headings in page.headings.values())
        print(f"\n📈 Summary Statistics:")
        print(f"   Total Headings: {total_headings}")
        print(f"   Images with Alt Text: {len(page.image_alt_text)}")
        print(f"   Total Images: {len(page.images)}")
        print(f"   Alt Text Coverage: {len(page.image_alt_text)/max(len(page.images), 1)*100:.1f}%")
        print(f"   Has Canonical URL: {'Yes' if page.canonical_url else 'No'}")

async def main():
    """Run all tests"""
    print("🚀 Starting Data Enrichment Tests")
    print("=" * 60)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        await test_data_enrichment()
        await test_selective_extraction()
        await test_data_quality()
        
        print("🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
