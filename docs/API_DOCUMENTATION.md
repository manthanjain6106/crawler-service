# Crawler Service API Documentation

## Overview

The Crawler Service is a FastAPI microservice that provides web crawling capabilities with rate limiting, retry logic, and comprehensive error handling. The API is versioned at `/api/v1/` and includes health checks, crawling endpoints, and administrative functions.

## Base URL

```
http://localhost:8000/api/v1
```

## API Endpoints

### Health Endpoints

#### GET /api/v1/health/
**Description**: Returns comprehensive service health status

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2023-01-01T00:00:00Z",
  "version": "1.0.0",
  "uptime": 3600.0,
  "services": {
    "rate_limiter": "healthy",
    "storage": "disabled",
    "background_jobs": "disabled"
  }
}
```

#### GET /api/v1/health/ready
**Description**: Readiness check for Kubernetes/Docker health checks

**Response**:
```json
{
  "status": "ready"
}
```

#### GET /api/v1/health/live
**Description**: Liveness check for Kubernetes/Docker health checks

**Response**:
```json
{
  "status": "alive"
}
```

#### GET /api/v1/health/metrics
**Description**: Returns service metrics for monitoring

**Response**:
```json
{
  "timestamp": "2023-01-01T00:00:00Z",
  "uptime": 3600.0,
  "storage": {
    "status": "disabled"
  },
  "background_jobs": {
    "status": "disabled"
  },
  "rate_limiter": {
    "domain_stats": {},
    "total_requests": 0
  }
}
```

### Crawl Endpoints

#### POST /api/v1/crawl
**Description**: Crawl a website and return results

**Request Body**:
```json
{
  "url": "https://example.com",
  "max_depth": 0,
  "follow_links": false,
  "extract_text": true,
  "extract_images": false,
  "extract_links": true,
  "extract_headings": true,
  "extract_image_alt_text": false,
  "extract_canonical_url": true,
  "custom_headers": {
    "User-Agent": "Custom Bot 1.0"
  },
  "timeout": 30
}
```

**Response**:
```json
{
  "task_id": "crawl_1234567890",
  "status": "completed",
  "total_pages": 1,
  "pages": [
    {
      "url": "https://example.com",
      "title": "Example Domain",
      "text_content": "This domain is for use in illustrative examples...",
      "images": [],
      "links": ["https://www.iana.org/domains/example"],
      "meta_description": "Example domain for documentation",
      "headings": {
        "h1": ["Example Domain"],
        "h2": [],
        "h3": []
      },
      "image_alt_text": [],
      "canonical_url": "https://example.com",
      "status_code": 200,
      "response_time": 0.5,
      "crawled_at": "2023-01-01T00:00:00Z",
      "depth": 0,
      "error": null,
      "retry_attempts": 0
    }
  ],
  "errors": [],
  "structured_errors": [],
  "started_at": "2023-01-01T00:00:00Z",
  "completed_at": "2023-01-01T00:00:01Z",
  "duration": 1.0,
  "retry_stats": {
    "total_retries": 0,
    "successful_retries": 0,
    "failed_retries": 0,
    "transient_errors": 0,
    "permanent_errors": 0
  }
}
```

### Admin Endpoints

#### GET /api/v1/admin/stats
**Description**: Returns crawling statistics and service metrics

**Response**:
```json
{
  "service_info": {
    "name": "Web Crawler Microservice",
    "version": "1.0.0",
    "environment": "development",
    "uptime_seconds": 3600.0
  },
  "crawling_stats": {
    "max_concurrent_requests": 30,
    "default_timeout": 30,
    "max_depth": 0,
    "retry_configuration": {
      "max_retries": 3,
      "retry_delay_base": 1.0,
      "retry_delay_max": 10.0,
      "retry_backoff_multiplier": 2.0
    }
  },
  "rate_limiting": {
    "api_rate_limit": "10/minute",
    "per_domain_enabled": true,
    "default_domain_limit": 10,
    "domain_specific_limits": {},
    "current_stats": {}
  },
  "retry_statistics": {
    "total_retries": 0,
    "successful_retries": 0,
    "failed_retries": 0,
    "transient_errors": 0,
    "permanent_errors": 0
  },
  "storage": {
    "status": "disabled",
    "message": "No data persistence - results returned directly"
  }
}
```

## Error Handling

The API uses structured error handling with appropriate HTTP status codes:

- **400 Bad Request**: Invalid request parameters
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server-side errors
- **503 Service Unavailable**: Service health check failures

Error responses include:
```json
{
  "error_code": "RATE_LIMIT_EXCEEDED",
  "message": "Rate limit exceeded for domain 'example.com': 10 requests per minute",
  "details": {
    "domain": "example.com",
    "limit": 10,
    "retry_after": 60
  }
}
```

## Rate Limiting

- **API Rate Limit**: 10 requests per minute per IP address
- **Per-Domain Rate Limiting**: Configurable limits per domain
- **Burst Protection**: Additional semaphore-based protection

## Features

- **Async Operations**: All endpoints are fully asynchronous
- **Pydantic Validation**: Request/response validation with detailed error messages
- **Dependency Injection**: Clean separation of concerns
- **Structured Logging**: Comprehensive logging for debugging and monitoring
- **Retry Logic**: Automatic retry with exponential backoff for transient errors
- **Rate Limiting**: Per-IP and per-domain rate limiting
- **Health Checks**: Multiple health check endpoints for different monitoring needs

## Usage Examples

### Basic Crawl Request
```bash
curl -X POST "http://localhost:8000/api/v1/crawl" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### Health Check
```bash
curl -X GET "http://localhost:8000/api/v1/health/"
```

### Get Statistics
```bash
curl -X GET "http://localhost:8000/api/v1/admin/stats"
```

## Configuration

The service can be configured via environment variables:

- `API_HOST`: Host to bind to (default: 0.0.0.0)
- `API_PORT`: Port to bind to (default: 8000)
- `RATE_LIMIT_PER_MINUTE`: API rate limit (default: 10)
- `MAX_CONCURRENT_REQUESTS`: Max concurrent crawl requests (default: 30)
- `DEFAULT_TIMEOUT`: Request timeout in seconds (default: 30)
- `MAX_RETRIES`: Maximum retry attempts (default: 3)

## Integration

This microservice is designed to be called by:
- Main applications
- Frontend applications
- Other microservices
- Monitoring systems

The API returns data directly without persistence, making it suitable for real-time crawling operations.
