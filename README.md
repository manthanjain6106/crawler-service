# Web Crawler Microservice

A high-performance web crawler microservice built with Python and FastAPI. This service provides RESTful APIs for crawling websites and extracting structured data including text content, images, links, and metadata.

## Features

- 🚀 **Fast and Async**: Built with FastAPI and asyncio for high performance
- 🔄 **Concurrent Crawling**: Configurable concurrent request handling
- 📊 **Structured Data Extraction**: Extract text, images, links, and metadata
- 🛡️ **Rate Limiting**: Built-in rate limiting to prevent abuse
- 📈 **Health Monitoring**: Health check endpoints for monitoring
- 🐳 **Docker Ready**: Complete Docker and Docker Compose setup
- 📝 **API Documentation**: Auto-generated OpenAPI/Swagger documentation
- 🔧 **Configurable**: Environment-based configuration

## Quick Start

### Using Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd crawler-service
```

2. Start the service:
```bash
docker-compose up -d
```

3. Access the API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Manual Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the service:
```bash
python main.py
```

## API Endpoints

### Core Endpoints

- `GET /` - Service information
- `GET /health` - Health check
- `POST /crawl` - Start a new crawl task
- `GET /crawl/{task_id}` - Get crawl task status
- `GET /crawl/{task_id}/result` - Get crawl results
- `GET /crawl` - List all crawl tasks
- `DELETE /crawl/{task_id}` - Delete a crawl task

### Example Usage

#### Start a Crawl Task

```bash
curl -X POST "http://localhost:8000/crawl" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "max_depth": 2,
    "follow_links": true,
    "extract_text": true,
    "extract_images": true,
    "extract_links": true
  }'
```

#### Check Task Status

```bash
curl "http://localhost:8000/crawl/{task_id}"
```

#### Get Crawl Results

```bash
curl "http://localhost:8000/crawl/{task_id}/result"
```

## Configuration

The service can be configured using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `API_HOST` | `0.0.0.0` | API host address |
| `API_PORT` | `8000` | API port |
| `MAX_CONCURRENT_REQUESTS` | `10` | Maximum concurrent requests |
| `DEFAULT_TIMEOUT` | `30` | Request timeout in seconds |
| `MAX_DEPTH` | `3` | Maximum crawl depth |
| `RATE_LIMIT_PER_MINUTE` | `10` | Rate limit per minute |
| `LOG_LEVEL` | `INFO` | Logging level |

## Data Models

### CrawlRequest
- `url`: Target URL to crawl
- `max_depth`: Maximum crawl depth (default: 1)
- `follow_links`: Whether to follow internal links
- `extract_text`: Extract text content
- `extract_images`: Extract image URLs
- `extract_links`: Extract link URLs
- `custom_headers`: Custom HTTP headers
- `timeout`: Request timeout

### CrawlResult
- `task_id`: Unique task identifier
- `status`: Task status (pending, in_progress, completed, failed)
- `total_pages`: Number of pages crawled
- `pages`: List of crawled pages
- `errors`: List of errors encountered
- `duration`: Total crawl duration

### CrawledPage
- `url`: Page URL
- `title`: Page title
- `text_content`: Extracted text content
- `images`: List of image URLs
- `links`: List of link URLs
- `meta_description`: Meta description
- `status_code`: HTTP status code
- `response_time`: Response time
- `crawled_at`: Timestamp

## Development

### Project Structure

```
crawler-service/
├── main.py              # FastAPI application
├── models.py            # Pydantic data models
├── crawler_service.py   # Web crawler implementation
├── config.py            # Configuration settings
├── requirements.txt     # Python dependencies
├── Dockerfile          # Docker configuration
├── docker-compose.yml  # Docker Compose setup
└── README.md           # This file
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest
```

### Code Quality

```bash
# Install linting tools
pip install black flake8 mypy

# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

## Production Deployment

### Using Docker

1. Build the image:
```bash
docker build -t crawler-service .
```

2. Run the container:
```bash
docker run -p 8000:8000 crawler-service
```

### Using Docker Compose

```bash
docker-compose up -d
```

### Environment Variables

Create a `.env` file with your configuration:

```env
API_HOST=0.0.0.0
API_PORT=8000
MAX_CONCURRENT_REQUESTS=20
RATE_LIMIT_PER_MINUTE=50
LOG_LEVEL=INFO
```

## Monitoring

The service provides health check endpoints for monitoring:

- `GET /health` - Basic health check
- `GET /` - Service information

## Rate Limiting

The service implements rate limiting to prevent abuse:
- Default: 10 requests per minute per IP
- Configurable via `RATE_LIMIT_PER_MINUTE` environment variable

## Error Handling

The service includes comprehensive error handling:
- HTTP errors are properly mapped to status codes
- Crawl errors are captured and returned in results
- Timeout handling for slow responses
- Graceful degradation for failed requests

## License

This project is licensed under the MIT License.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Support

For issues and questions:
1. Check the API documentation at `/docs`
2. Review the logs for error details
3. Open an issue on GitHub
