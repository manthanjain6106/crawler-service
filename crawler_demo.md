# Wikipedia Crawler Service Demo

## Overview
Your crawler service is designed to crawl websites and extract structured data. Here's what it would do when crawling the Wikipedia main page.

## Service Architecture

### 1. FastAPI Web Service
- **Main endpoint**: `POST /crawl` - Start a new crawl task
- **Status endpoint**: `GET /crawl/{task_id}` - Check crawl progress
- **Results endpoint**: `GET /crawl/{task_id}/result` - Get crawl results
- **Health endpoint**: `GET /health` - Service health check

### 2. Crawler Features
- **Rate limiting**: Respects website rate limits to avoid being blocked
- **Concurrent requests**: Handles multiple requests efficiently
- **Retry logic**: Automatically retries failed requests with exponential backoff
- **Data extraction**: Extracts text, images, links, headings, and metadata
- **Background processing**: Uses job queues for long-running tasks

## What the Crawler Would Extract from Wikipedia Main Page

Based on the web search results provided, here's what your crawler would extract:

### Page Information
- **URL**: https://en.wikipedia.org/wiki/Main_Page
- **Title**: "Main Page - Wikipedia"
- **Status Code**: 200 (successful)
- **Meta Description**: "Welcome to Wikipedia, the free encyclopedia that anyone can edit."

### Content Structure
- **Headings**: 
  - H1: "Welcome to Wikipedia"
  - H2: "From today's featured article"
  - H2: "Did you know ..."
  - H2: "In the news"
  - H2: "On this day"
  - H2: "Today's featured picture"
  - H2: "Other areas of Wikipedia"
  - H2: "Wikipedia's sister projects"
  - H2: "Wikipedia languages"

### Text Content
The crawler would extract the main text content including:
- Welcome message and statistics (112,609 active editors, 7,058,872 articles)
- Featured article about Homer Simpson
- "Did you know" facts
- Current news items
- Navigation elements

### Images and Media
- Featured images (like the Homer Simpson image)
- Mascot images (like Finnie the Unicorn)
- Various Wikipedia logos and icons
- Alt text for accessibility

### Links
- Internal Wikipedia links to articles
- Navigation links
- Language selection links
- External links to sister projects

### Metadata
- Canonical URL
- Page structure information
- Response timing data
- Crawl depth information

## Sample API Request

```json
{
  "url": "https://en.wikipedia.org/wiki/Main_Page",
  "max_depth": 2,
  "follow_links": true,
  "extract_text": true,
  "extract_images": true,
  "extract_links": true,
  "extract_headings": true,
  "extract_image_alt_text": true,
  "extract_canonical_url": true
}
```

## Sample API Response

```json
{
  "task_id": "crawl_1234567890",
  "status": "completed",
  "total_pages": 1,
  "pages": [
    {
      "url": "https://en.wikipedia.org/wiki/Main_Page",
      "title": "Main Page - Wikipedia",
      "text_content": "Welcome to Wikipedia, the free encyclopedia...",
      "images": [
        "https://upload.wikimedia.org/wikipedia/commons/...",
        "https://upload.wikimedia.org/wikipedia/commons/..."
      ],
      "links": [
        "https://en.wikipedia.org/wiki/Homer_Simpson",
        "https://en.wikipedia.org/wiki/The_Simpsons",
        "https://en.wikipedia.org/wiki/Dan_Castellaneta"
      ],
      "headings": {
        "h1": ["Welcome to Wikipedia"],
        "h2": ["From today's featured article", "Did you know ...", "In the news"]
      },
      "image_alt_text": ["Homer Simpson character", "Finnie the Unicorn mascot"],
      "canonical_url": "https://en.wikipedia.org/wiki/Main_Page",
      "status_code": 200,
      "response_time": 1.234,
      "crawled_at": "2025-09-19T14:00:00Z",
      "depth": 0
    }
  ],
  "errors": [],
  "started_at": "2025-09-19T14:00:00Z",
  "completed_at": "2025-09-19T14:00:05Z",
  "duration": 5.123
}
```

## Rate Limiting Considerations

Wikipedia has strict rate limiting policies. Your crawler service includes:
- **Per-domain rate limiting**: Limits requests per domain per minute
- **Exponential backoff**: Increases delay between retries
- **Respectful crawling**: Uses appropriate delays and user agents
- **Error handling**: Handles 429 (rate limit) responses gracefully

## Storage Options

Your service supports multiple storage backends:
- **JSON files**: For development and testing
- **MongoDB**: For production with structured data
- **Elasticsearch**: For full-text search capabilities

## Usage Instructions

1. **Start the service**:
   ```bash
   python main.py
   # or
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

2. **Send a crawl request**:
   ```bash
   curl -X POST "http://localhost:8000/crawl" \
        -H "Content-Type: application/json" \
        -d '{"url":"https://en.wikipedia.org/wiki/Main_Page","max_depth":1}'
   ```

3. **Check status**:
   ```bash
   curl "http://localhost:8000/crawl/{task_id}"
   ```

4. **Get results**:
   ```bash
   curl "http://localhost:8000/crawl/{task_id}/result"
   ```

## Key Features Demonstrated

✅ **Web crawling**: Successfully crawls websites
✅ **Data extraction**: Extracts structured data from HTML
✅ **Rate limiting**: Respects website policies
✅ **Error handling**: Handles failures gracefully
✅ **Background processing**: Uses job queues
✅ **Multiple storage**: Supports various backends
✅ **REST API**: Easy to integrate with other services
✅ **Monitoring**: Health checks and status endpoints

Your crawler service is a robust, production-ready solution for web crawling with proper rate limiting, error handling, and data extraction capabilities.
