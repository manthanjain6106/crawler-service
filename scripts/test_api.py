#!/usr/bin/env python3
"""
Test script for the Crawler Service API
Demonstrates how to use all the API endpoints
"""

import requests
import json
import time
from typing import Dict, Any

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

def test_health_endpoints():
    """Test all health check endpoints"""
    print("=== Testing Health Endpoints ===")
    
    # Test main health endpoint
    try:
        response = requests.get(f"{BASE_URL}/health/")
        print(f"Health Check: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Status: {data.get('status')}")
            print(f"Version: {data.get('version')}")
            print(f"Uptime: {data.get('uptime')} seconds")
        print()
    except Exception as e:
        print(f"Health check failed: {e}")
    
    # Test readiness check
    try:
        response = requests.get(f"{BASE_URL}/health/ready")
        print(f"Readiness Check: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        print()
    except Exception as e:
        print(f"Readiness check failed: {e}")
    
    # Test liveness check
    try:
        response = requests.get(f"{BASE_URL}/health/live")
        print(f"Liveness Check: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        print()
    except Exception as e:
        print(f"Liveness check failed: {e}")
    
    # Test metrics endpoint
    try:
        response = requests.get(f"{BASE_URL}/health/metrics")
        print(f"Metrics Check: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Uptime: {data.get('uptime')} seconds")
            print(f"Rate Limiter: {data.get('rate_limiter', {}).get('total_requests', 0)} requests")
        print()
    except Exception as e:
        print(f"Metrics check failed: {e}")

def test_crawl_endpoint():
    """Test the crawl endpoint"""
    print("=== Testing Crawl Endpoint ===")
    
    # Test data
    crawl_request = {
        "url": "https://httpbin.org/html",
        "max_depth": 0,
        "follow_links": False,
        "extract_text": True,
        "extract_images": False,
        "extract_links": True,
        "extract_headings": True,
        "extract_image_alt_text": False,
        "extract_canonical_url": True,
        "timeout": 30
    }
    
    try:
        print("Sending crawl request...")
        response = requests.post(
            f"{BASE_URL}/crawl",
            json=crawl_request,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Crawl Response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Task ID: {data.get('task_id')}")
            print(f"Status: {data.get('status')}")
            print(f"Total Pages: {data.get('total_pages')}")
            print(f"Duration: {data.get('duration')} seconds")
            
            if data.get('pages'):
                page = data['pages'][0]
                print(f"Page URL: {page.get('url')}")
                print(f"Page Title: {page.get('title')}")
                print(f"Status Code: {page.get('status_code')}")
                print(f"Response Time: {page.get('response_time')} seconds")
                print(f"Links Found: {len(page.get('links', []))}")
                print(f"Headings Found: {sum(len(headings) for headings in page.get('headings', {}).values())}")
        else:
            print(f"Error: {response.text}")
        print()
        
    except Exception as e:
        print(f"Crawl request failed: {e}")
        print()

def test_admin_endpoints():
    """Test admin endpoints"""
    print("=== Testing Admin Endpoints ===")
    
    # Test stats endpoint
    try:
        response = requests.get(f"{BASE_URL}/admin/stats")
        print(f"Stats Response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Service Name: {data.get('service_info', {}).get('name')}")
            print(f"Service Version: {data.get('service_info', {}).get('version')}")
            print(f"Uptime: {data.get('service_info', {}).get('uptime_seconds')} seconds")
            print(f"Max Concurrent Requests: {data.get('crawling_stats', {}).get('max_concurrent_requests')}")
            print(f"API Rate Limit: {data.get('rate_limiting', {}).get('api_rate_limit')}")
        else:
            print(f"Error: {response.text}")
        print()
        
    except Exception as e:
        print(f"Stats request failed: {e}")
        print()

def test_rate_limiting():
    """Test rate limiting by making multiple requests"""
    print("=== Testing Rate Limiting ===")
    
    crawl_request = {
        "url": "https://httpbin.org/delay/1",
        "max_depth": 0,
        "timeout": 5
    }
    
    print("Making multiple requests to test rate limiting...")
    
    for i in range(5):
        try:
            response = requests.post(
                f"{BASE_URL}/crawl",
                json=crawl_request,
                headers={"Content-Type": "application/json"}
            )
            print(f"Request {i+1}: {response.status_code}")
            
            if response.status_code == 429:
                print("Rate limit hit!")
                break
                
        except Exception as e:
            print(f"Request {i+1} failed: {e}")
        
        time.sleep(1)  # Wait 1 second between requests
    
    print()

def main():
    """Run all tests"""
    print("Crawler Service API Test Suite")
    print("=" * 40)
    print()
    
    # Wait for service to be ready
    print("Waiting for service to be ready...")
    time.sleep(2)
    
    # Run tests
    test_health_endpoints()
    test_crawl_endpoint()
    test_admin_endpoints()
    test_rate_limiting()
    
    print("Test suite completed!")

if __name__ == "__main__":
    main()
