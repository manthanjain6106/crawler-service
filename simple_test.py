#!/usr/bin/env python3
"""
Simple test to verify we can access Wikipedia
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def test_wikipedia_access():
    """Test basic access to Wikipedia"""
    print("Testing Wikipedia access...")
    
    url = "https://en.wikipedia.org/wiki/Main_Page"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                print(f"Status Code: {response.status}")
                print(f"Content Type: {response.headers.get('content-type', 'Unknown')}")
                
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    title = soup.find('title')
                    title_text = title.get_text().strip() if title else "No title found"
                    print(f"Page Title: {title_text}")
                    
                    # Count some basic elements
                    links = soup.find_all('a', href=True)
                    images = soup.find_all('img')
                    headings = soup.find_all(['h1', 'h2', 'h3'])
                    
                    print(f"Links found: {len(links)}")
                    print(f"Images found: {len(images)}")
                    print(f"Headings found: {len(headings)}")
                    
                    # Show some sample links
                    print(f"\nSample links:")
                    for i, link in enumerate(links[:5]):
                        href = link.get('href', '')
                        text = link.get_text().strip()[:50]
                        print(f"  {i+1}. {text} -> {href}")
                    
                    print(f"\nSuccessfully crawled Wikipedia main page!")
                else:
                    print(f"Failed to access Wikipedia. Status: {response.status}")
                    
    except Exception as e:
        print(f"Error accessing Wikipedia: {e}")

if __name__ == "__main__":
    asyncio.run(test_wikipedia_access())
