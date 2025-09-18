#!/usr/bin/env python3
"""
Example script demonstrating how to use the crawler service
"""
import requests
import json
import time

# Service URL
BASE_URL = "http://localhost:8000"

def start_crawl(url, max_depth=1):
    """Start a crawl task"""
    payload = {
        "url": url,
        "max_depth": max_depth,
        "follow_links": True,
        "extract_text": True,
        "extract_images": True,
        "extract_links": True
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
    
    # Example 1: Simple crawl
    print("\n1. Starting simple crawl...")
    task = start_crawl("https://httpbin.org/html", max_depth=0)
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
            print(f"Page URL: {page['url']}")
            print(f"Page Title: {page['title']}")
            print(f"Status Code: {page['status_code']}")
            print(f"Response Time: {page['response_time']:.2f}s")
            print(f"Images found: {len(page['images'])}")
            print(f"Links found: {len(page['links'])}")
    else:
        print(f"❌ Crawl failed: {final_status.get('result', {}).get('errors', [])}")
    
    # Example 2: Crawl with depth
    print("\n2. Starting crawl with depth...")
    task = start_crawl("https://httpbin.org/links/2/0", max_depth=1)
    task_id = task['task_id']
    print(f"Task ID: {task_id}")
    
    final_status = wait_for_completion(task_id)
    
    if final_status['status'] == 'completed':
        result = get_crawl_result(task_id)
        print(f"✅ Deep crawl completed!")
        print(f"Total pages: {result['total_pages']}")
        
        for i, page in enumerate(result['pages'][:3]):  # Show first 3 pages
            print(f"  Page {i+1}: {page['url']} (Status: {page['status_code']})")
    else:
        print(f"❌ Deep crawl failed: {final_status.get('result', {}).get('errors', [])}")
    
    # List all tasks
    print("\n3. Listing all tasks...")
    tasks_response = requests.get(f"{BASE_URL}/crawl")
    tasks = tasks_response.json()
    print(f"Total tasks: {len(tasks)}")
    
    for task in tasks[-3:]:  # Show last 3 tasks
        print(f"  Task {task['task_id'][:8]}... - {task['status']}")

if __name__ == "__main__":
    main()
