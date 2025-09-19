#!/usr/bin/env python3
"""
Example script demonstrating how to use the crawler service
"""
import requests
import json
import time

# Service URL
BASE_URL = "http://localhost:8000"

def start_crawl(url, max_depth=1, enable_enrichment=True):
    """Start a crawl task with optional data enrichment features"""
    payload = {
        "url": url,
        "max_depth": max_depth,
        "follow_links": True,
        "extract_text": True,
        "extract_images": True,
        "extract_links": True,
        "extract_headings": enable_enrichment,
        "extract_image_alt_text": enable_enrichment,
        "extract_canonical_url": enable_enrichment
    }
    
    response = requests.post(f"{BASE_URL}/crawl", json=payload)
    response.raise_for_status()
    return response.json()

def get_task_status(task_id):
    """Get task status"""
    response = requests.get(f"{BASE_URL}/crawl/{task_id}")
    response.raise_for_status()
    return response.json()

def get_crawl_result(task_id):
    """Get crawl result"""
    response = requests.get(f"{BASE_URL}/crawl/{task_id}/result")
    response.raise_for_status()
    return response.json()

def wait_for_completion(task_id, max_wait=60):
    """Wait for task completion"""
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        status = get_task_status(task_id)
        print(f"Task {task_id} status: {status['status']}")
        
        if status['status'] in ['completed', 'failed']:
            return status
        
        time.sleep(2)
    
    raise TimeoutError("Task did not complete within the timeout period")

def main():
    """Main example function"""
    print("Web Crawler Service Example")
    print("=" * 40)
    
    # Check if service is running
    try:
        health_response = requests.get(f"{BASE_URL}/health")
        health_response.raise_for_status()
        print("✅ Service is running")
        print(f"Health: {health_response.json()['status']}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Service is not running: {e}")
        print("Please start the service with: python main.py")
        return
    
    # Example 1: Simple crawl with data enrichment
    print("\n1. Starting crawl with data enrichment...")
    task = start_crawl("https://httpbin.org/html", max_depth=0, enable_enrichment=True)
    task_id = task['task_id']
    print(f"Task ID: {task_id}")
    
    # Wait for completion
    final_status = wait_for_completion(task_id)
    
    if final_status['status'] == 'completed':
        result = get_crawl_result(task_id)
        print(f"✅ Crawl completed successfully!")
        print(f"Total pages: {result['total_pages']}")
        
        if result['pages']:
            page = result['pages'][0]
            print(f"\n📄 Page Details:")
            print(f"   URL: {page['url']}")
            print(f"   Title: {page['title']}")
            print(f"   Meta Description: {page['meta_description']}")
            print(f"   Canonical URL: {page['canonical_url']}")
            print(f"   Status Code: {page['status_code']}")
            print(f"   Response Time: {page['response_time']:.2f}s")
            
            print(f"\n📋 Headings:")
            for level, headings in page['headings'].items():
                if headings:
                    print(f"   {level.upper()}: {len(headings)} found")
                    for i, heading in enumerate(headings[:2], 1):
                        print(f"     {i}. {heading}")
                    if len(headings) > 2:
                        print(f"     ... and {len(headings) - 2} more")
                else:
                    print(f"   {level.upper()}: None found")
            
            print(f"\n🖼️  Images & Alt Text:")
            print(f"   Total Images: {len(page['images'])}")
            print(f"   Images with Alt Text: {len(page['image_alt_text'])}")
            if page['image_alt_text']:
                print("   Alt Text Samples:")
                for i, alt_text in enumerate(page['image_alt_text'][:3], 1):
                    print(f"     {i}. {alt_text}")
            
            print(f"\n🔗 Links: {len(page['links'])} found")
    else:
        print(f"❌ Crawl failed: {final_status.get('result', {}).get('errors', [])}")
    
    # Example 2: Selective data extraction
    print("\n2. Testing selective data extraction...")
    print("   (Only extracting headings, no images or links)")
    
    # Create a custom payload for selective extraction
    selective_payload = {
        "url": "https://httpbin.org/html",
        "max_depth": 0,
        "follow_links": False,
        "extract_text": False,
        "extract_images": False,
        "extract_links": False,
        "extract_headings": True,
        "extract_image_alt_text": False,
        "extract_canonical_url": True
    }
    
    response = requests.post(f"{BASE_URL}/crawl", json=selective_payload)
    response.raise_for_status()
    task = response.json()
    task_id = task['task_id']
    print(f"Task ID: {task_id}")
    
    final_status = wait_for_completion(task_id)
    
    if final_status['status'] == 'completed':
        result = get_crawl_result(task_id)
        print(f"✅ Selective extraction completed!")
        
        if result['pages']:
            page = result['pages'][0]
            print(f"   Headings extracted: {sum(len(h) for h in page['headings'].values())}")
            print(f"   Images extracted: {len(page['images'])}")
            print(f"   Links extracted: {len(page['links'])}")
            print(f"   Canonical URL: {page['canonical_url']}")
    else:
        print(f"❌ Selective extraction failed: {final_status.get('result', {}).get('errors', [])}")
    
    # Example 3: Crawl with depth
    print("\n3. Starting crawl with depth...")
    task = start_crawl("https://httpbin.org/links/2/0", max_depth=1, enable_enrichment=True)
    task_id = task['task_id']
    print(f"Task ID: {task_id}")
    
    final_status = wait_for_completion(task_id)
    
    if final_status['status'] == 'completed':
        result = get_crawl_result(task_id)
        print(f"✅ Deep crawl completed!")
        print(f"Total pages: {result['total_pages']}")
        
        for i, page in enumerate(result['pages'][:3]):  # Show first 3 pages
            print(f"  Page {i+1}: {page['url']} (Status: {page['status_code']})")
            if page['headings']:
                total_headings = sum(len(h) for h in page['headings'].values())
                print(f"    Headings: {total_headings}, Images: {len(page['images'])}")
    else:
        print(f"❌ Deep crawl failed: {final_status.get('result', {}).get('errors', [])}")
    
    # List all tasks
    print("\n4. Listing all tasks...")
    tasks_response = requests.get(f"{BASE_URL}/crawl")
    tasks = tasks_response.json()
    print(f"Total tasks: {len(tasks)}")
    
    for task in tasks[-3:]:  # Show last 3 tasks
        print(f"  Task {task['task_id'][:8]}... - {task['status']}")

if __name__ == "__main__":
    main()
