#!/usr/bin/env python3
"""
Data Enrichment Demo for Ads Generation
======================================

This script demonstrates the enhanced crawler service with data enrichment features
specifically designed for generating better ad copies. It extracts:

- Page titles
- Meta descriptions  
- Headings (h1, h2, h3)
- Image alt text
- Canonical URLs

These enriched data points are essential for creating compelling ad content.
"""

import asyncio
import sys
import os
from datetime import datetime
from models import CrawlRequest
from crawler_service import WebCrawler

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def print_section(title, content=""):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"🎯 {title}")
    print('='*60)
    if content:
        print(content)

def print_data_summary(page):
    """Print a summary of extracted data for ad generation"""
    print(f"\n📊 Data Summary for Ad Generation:")
    print(f"   Title: {'✅' if page.title else '❌'} {page.title or 'Not available'}")
    print(f"   Meta Description: {'✅' if page.meta_description else '❌'} {page.meta_description or 'Not available'}")
    print(f"   Canonical URL: {'✅' if page.canonical_url else '❌'} {page.canonical_url or 'Not available'}")
    
    total_headings = sum(len(headings) for headings in page.headings.values())
    print(f"   Headings: {'✅' if total_headings > 0 else '❌'} {total_headings} found")
    
    print(f"   Images: {'✅' if page.images else '❌'} {len(page.images)} found")
    print(f"   Image Alt Text: {'✅' if page.image_alt_text else '❌'} {len(page.image_alt_text)} found")
    
    # Calculate alt text coverage
    if page.images:
        coverage = len(page.image_alt_text) / len(page.images) * 100
        print(f"   Alt Text Coverage: {coverage:.1f}%")

def print_ad_generation_insights(page):
    """Print insights that would be useful for ad generation"""
    print(f"\n💡 Ad Generation Insights:")
    
    # Title insights
    if page.title:
        title_length = len(page.title)
        print(f"   📝 Title Length: {title_length} chars ({'Good' if 30 <= title_length <= 60 else 'Consider optimizing'})")
        print(f"   📝 Title Sample: '{page.title[:50]}{'...' if len(page.title) > 50 else ''}'")
    
    # Meta description insights
    if page.meta_description:
        desc_length = len(page.meta_description)
        print(f"   📄 Meta Description Length: {desc_length} chars ({'Good' if 120 <= desc_length <= 160 else 'Consider optimizing'})")
        print(f"   📄 Meta Description Sample: '{page.meta_description[:80]}{'...' if len(page.meta_description) > 80 else ''}'")
    
    # Headings insights
    if any(page.headings.values()):
        print(f"   📋 Content Structure:")
        for level, headings in page.headings.items():
            if headings:
                print(f"      {level.upper()}: {len(headings)} headings")
                if level == 'h1' and headings:
                    print(f"         Main Topic: '{headings[0]}'")
    
    # Image insights
    if page.images:
        print(f"   🖼️  Visual Content: {len(page.images)} images")
        if page.image_alt_text:
            print(f"   🖼️  Alt Text Quality: {len(page.image_alt_text)} images have descriptive alt text")
            # Show sample alt text
            for i, alt_text in enumerate(page.image_alt_text[:2], 1):
                print(f"      Sample {i}: '{alt_text}'")
    
    # Canonical URL insights
    if page.canonical_url:
        print(f"   🔗 Canonical URL: Available (helps avoid duplicate content issues)")
    else:
        print(f"   🔗 Canonical URL: Not found (may cause duplicate content issues)")

async def demo_basic_enrichment():
    """Demonstrate basic data enrichment features"""
    print_section("Basic Data Enrichment Demo")
    
    # Test with a real website
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
    
    print(f"🔍 Crawling: {test_url}")
    print(f"⚙️  Features enabled: All enrichment features")
    
    async with WebCrawler() as crawler:
        page = await crawler.crawl_url(test_url, request)
        
        if page.error:
            print(f"❌ Error: {page.error.message}")
            return
        
        print(f"✅ Successfully crawled in {page.response_time:.2f}s")
        print_data_summary(page)
        print_ad_generation_insights(page)

async def demo_selective_extraction():
    """Demonstrate selective data extraction"""
    print_section("Selective Data Extraction Demo")
    
    test_url = "https://httpbin.org/html"
    
    # Test 1: Only headings
    print("📋 Test 1: Extracting only headings...")
    request_headings = CrawlRequest(
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
        page = await crawler.crawl_url(test_url, request_headings)
        total_headings = sum(len(h) for h in page.headings.values())
        print(f"   Result: {total_headings} headings extracted, {len(page.images)} images, {len(page.links)} links")
    
    # Test 2: Only meta data
    print("\n📄 Test 2: Extracting only meta data...")
    request_meta = CrawlRequest(
        url=test_url,
        max_depth=0,
        follow_links=False,
        extract_text=False,
        extract_images=False,
        extract_links=False,
        extract_headings=False,
        extract_image_alt_text=False,
        extract_canonical_url=True
    )
    
    async with WebCrawler() as crawler:
        page = await crawler.crawl_url(test_url, request_meta)
        print(f"   Result: Title={bool(page.title)}, Meta={bool(page.meta_description)}, Canonical={bool(page.canonical_url)}")

async def demo_website_crawl():
    """Demonstrate crawling a real website with enrichment"""
    print_section("Real Website Crawl Demo")
    
    # Use a website that's likely to have rich content
    test_url = "https://example.com"
    
    request = CrawlRequest(
        url=test_url,
        max_depth=1,  # Crawl one level deep
        follow_links=True,
        extract_text=True,
        extract_images=True,
        extract_links=True,
        extract_headings=True,
        extract_image_alt_text=True,
        extract_canonical_url=True
    )
    
    print(f"🌐 Crawling website: {test_url}")
    print(f"📊 Depth: {request.max_depth} levels")
    
    async with WebCrawler() as crawler:
        result = await crawler.crawl_website(request)
        
        print(f"✅ Crawl completed in {result.duration:.2f}s")
        print(f"📄 Total pages crawled: {result.total_pages}")
        
        if result.pages:
            print(f"\n📊 Enrichment Summary Across All Pages:")
            total_headings = sum(sum(len(h) for h in page.headings.values()) for page in result.pages)
            total_images = sum(len(page.images) for page in result.pages)
            total_alt_text = sum(len(page.image_alt_text) for page in result.pages)
            pages_with_titles = sum(1 for page in result.pages if page.title)
            pages_with_meta = sum(1 for page in result.pages if page.meta_description)
            pages_with_canonical = sum(1 for page in result.pages if page.canonical_url)
            
            print(f"   📝 Pages with titles: {pages_with_titles}/{result.total_pages}")
            print(f"   📄 Pages with meta descriptions: {pages_with_meta}/{result.total_pages}")
            print(f"   🔗 Pages with canonical URLs: {pages_with_canonical}/{result.total_pages}")
            print(f"   📋 Total headings: {total_headings}")
            print(f"   🖼️  Total images: {total_images}")
            print(f"   🖼️  Images with alt text: {total_alt_text}")
            
            if total_images > 0:
                alt_coverage = total_alt_text / total_images * 100
                print(f"   📊 Alt text coverage: {alt_coverage:.1f}%")
            
            # Show details for the first page
            if result.pages:
                print(f"\n📄 First Page Details:")
                print_data_summary(result.pages[0])

async def demo_performance_comparison():
    """Demonstrate performance impact of enrichment features"""
    print_section("Performance Comparison Demo")
    
    test_url = "https://httpbin.org/html"
    
    # Test without enrichment
    print("⚡ Testing without enrichment features...")
    request_basic = CrawlRequest(
        url=test_url,
        max_depth=0,
        follow_links=False,
        extract_text=True,
        extract_images=True,
        extract_links=True,
        extract_headings=False,
        extract_image_alt_text=False,
        extract_canonical_url=False
    )
    
    async with WebCrawler() as crawler:
        start_time = asyncio.get_event_loop().time()
        page_basic = await crawler.crawl_url(test_url, request_basic)
        basic_time = asyncio.get_event_loop().time() - start_time
        
        print(f"   ⏱️  Basic extraction: {basic_time:.3f}s")
        print(f"   📊 Data points: {len(page_basic.images)} images, {len(page_basic.links)} links")
    
    # Test with enrichment
    print("\n🚀 Testing with all enrichment features...")
    request_enriched = CrawlRequest(
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
        start_time = asyncio.get_event_loop().time()
        page_enriched = await crawler.crawl_url(test_url, request_enriched)
        enriched_time = asyncio.get_event_loop().time() - start_time
        
        total_headings = sum(len(h) for h in page_enriched.headings.values())
        print(f"   ⏱️  Enriched extraction: {enriched_time:.3f}s")
        print(f"   📊 Data points: {len(page_enriched.images)} images, {len(page_enriched.links)} links, {total_headings} headings, {len(page_enriched.image_alt_text)} alt texts")
        
        overhead = ((enriched_time - basic_time) / basic_time) * 100
        print(f"   📈 Performance overhead: {overhead:.1f}%")

async def main():
    """Run all demos"""
    print("🚀 Data Enrichment for Ads Generation - Demo Suite")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nThis demo showcases enhanced data extraction features")
    print("designed to improve ad copy generation quality.")
    
    try:
        await demo_basic_enrichment()
        await demo_selective_extraction()
        await demo_website_crawl()
        await demo_performance_comparison()
        
        print_section("Demo Complete", "🎉 All demos completed successfully!")
        print("\n💡 Key Benefits for Ad Generation:")
        print("   • Rich content structure (headings) for better targeting")
        print("   • Meta descriptions for compelling ad copy")
        print("   • Image alt text for visual ad descriptions")
        print("   • Canonical URLs to avoid duplicate content issues")
        print("   • Flexible extraction options for different use cases")
        
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
