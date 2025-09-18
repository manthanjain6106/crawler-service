#!/usr/bin/env python3
"""
Simple test script for the crawler API
"""
import requests
import json
import time

def test_api():
    """Test the crawler API"""
    base_url = "http://localhost:8000"
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Health check: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Health check failed: {e}")
        return
    
    # Test root endpoint
    try:
        response = requests.get(f"{base_url}/")
        print(f"Root endpoint: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Root endpoint failed: {e}")
        return
    
    # Test crawl endpoint
    try:
        payload = {
            "url": "https://httpbin.org/html",
            "max_depth": 0,
            "follow_links": False,
            "extract_text": True,
            "extract_images": True,
            "extract_links": True
        }
        
        print(f"Sending crawl request: {payload}")
        response = requests.post(f"{base_url}/crawl", json=payload)
        print(f"Crawl request: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Task created: {result['task_id']}")
            print(f"Status: {result['status']}")
            
            # Wait a bit and check status
            time.sleep(2)
            task_id = result['task_id']
            
            status_response = requests.get(f"{base_url}/crawl/{task_id}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"Task status: {status_data['status']}")
                
                if status_data['status'] in ['completed', 'failed']:
                    result_response = requests.get(f"{base_url}/crawl/{task_id}/result")
                    if result_response.status_code == 200:
                        result_data = result_response.json()
                        print(f"Result: {result_data}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Crawl test failed: {e}")

if __name__ == "__main__":
    test_api()
