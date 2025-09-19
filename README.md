# Web Crawler Microservice

A high-performance web crawler microservice built with Python and FastAPI. This service provides RESTful APIs for crawling websites and extracting structured data including text content, images, links, and metadata.

## Features

- 🚀 **Fast and Async**: Built with FastAPI and asyncio for high performance
- 🔄 **Advanced Concurrency**: Optimized concurrent request handling (30+ concurrent requests with dynamic adjustment)
- 📊 **Structured Data Extraction**: Extract text, images, links, and metadata
- 🕷️ **Advanced Depth Handling**: Queue-based BFS crawling with unlimited depth support
- 🔗 **Smart Link Filtering**: Only follows internal links to stay within target website
- 📈 **Depth Tracking**: Track crawling depth for each page
- 🚫 **Duplicate URL Avoidance**: Intelligent URL normalization prevents crawling the same page multiple times
- 🛡️ **Rate Limiting**: Built-in rate limiting to prevent abuse
- 💾 **Flexible Storage**: Multiple storage backends (JSON, MongoDB, Elasticsearch)
- 🔍 **Advanced Search**: Full-text search and filtering capabilities
- 📈 **Health Monitoring**: Health check endpoints for monitoring
- 🐳 **Docker Ready**: Complete Docker and Docker Compose setup
- 📝 **API Documentation**: Auto-generated OpenAPI/Swagger documentation
- 🔧 **Configurable**: Environment-based configuration
- 🔄 **Data Migration**: Easy migration between storage backends

## 🚀 Scalability & Deployment Features

- **Background Job Processing**: Redis Queue (RQ) for long-running crawl tasks
- **Horizontal Scaling**: Scale workers independently for increased throughput
- **Structured Logging**: JSON logging with DEBUG/INFO levels for development/production
- **Production Ready**: Nginx load balancer, SSL termination, and security headers
- **Container Orchestration**: Docker Compose for development and production
- **Job Management**: Monitor, cancel, and manage background jobs
- **Resource Management**: Memory and CPU limits for optimal performance
- **Health Monitoring**: Comprehensive health checks and metrics

## Quick Start

### Using Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd crawler-service
```

2. Start the service:
```bash
# Development
./deploy.sh development
# or on Windows
deploy.bat development

# Production
./deploy.sh production
# or on Windows
deploy.bat production
```

3. Access the API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

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
- `POST /crawl` - Start a new crawl task (uses background jobs)
- `GET /crawl/{task_id}` - Get crawl task status
- `GET /crawl/{task_id}/result` - Get crawl results
- `GET /crawl` - List all crawl tasks
- `DELETE /crawl/{task_id}` - Delete a crawl task

### Background Job Management

- `GET /jobs/queue/stats` - Get job queue statistics
- `GET /jobs/{job_id}/status` - Get job status
- `POST /jobs/{job_id}/cancel` - Cancel a job

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
| `MAX_CONCURRENT_REQUESTS` | `30` | Maximum concurrent requests (increased from 10) |
| `DEFAULT_TIMEOUT` | `30` | Request timeout in seconds |
| `MAX_DEPTH` | `10` | Maximum crawl depth (0 = unlimited) |
| `CONCURRENCY_BURST_LIMIT` | `50` | Maximum burst concurrency limit |
| `CONCURRENCY_GRADUAL_INCREASE` | `true` | Enable gradual concurrency adjustment |
| `RATE_LIMIT_PER_MINUTE` | `10` | Rate limit per minute |
| `LOG_LEVEL` | `INFO` | Logging level |

## Concurrency Optimization

The crawler service has been optimized for high-performance concurrent crawling:

### Key Improvements
- **Increased Default Concurrency**: Raised from 10 to 30 concurrent requests
- **Burst Protection**: Additional semaphore (50 limit) prevents overwhelming target servers
- **Dynamic Adjustment**: Automatically adjusts concurrency based on success rates
- **Dual Semaphore System**: Main semaphore for controlled concurrency + burst semaphore for protection

### Performance Benefits
- **7.9x Efficiency**: Concurrent crawling is ~8x faster than sequential
- **Adaptive Scaling**: Automatically increases concurrency when success rate > 90%
- **Graceful Degradation**: Reduces concurrency when success rate < 70%
- **Resource Management**: Tracks active requests and prevents resource exhaustion

### Configuration Options
- `MAX_CONCURRENT_REQUESTS`: Base concurrency limit (default: 30)
- `CONCURRENCY_BURST_LIMIT`: Maximum burst limit (default: 50)
- `CONCURRENCY_GRADUAL_INCREASE`: Enable dynamic adjustment (default: true)

## 🚀 Deployment & Scalability

### Background Job Processing

The service uses Redis Queue (RQ) for background job processing:

```bash
# Start background workers
python manage_workers.py start --count 3

# Monitor workers
python manage_workers.py monitor

# Check worker status
python manage_workers.py status
```

### Scaling

Scale the service horizontally:

```bash
# Scale workers
docker-compose up --scale crawler-worker=5 -d

# Scale API service
docker-compose up --scale crawler-service=3 -d
```

### Production Deployment

For production deployment, use the production Docker Compose configuration:

```bash
# Deploy to production
./deploy.sh production

# Or manually
docker-compose -f docker-compose.prod.yml up -d
```

This includes:
- Nginx load balancer
- SSL termination
- MongoDB for persistence
- Resource limits
- Health checks

### Monitoring

Monitor the service health and performance:

```bash
# Test deployment
python test_deployment.py

# Check logs
docker-compose logs -f

# Monitor job queue
curl http://localhost:8000/jobs/queue/stats
```

For detailed deployment information, see [DEPLOYMENT.md](DEPLOYMENT.md).

## Data Models

### CrawlRequest
- `url`: Target URL to crawl
- `max_depth`: Maximum crawl depth (default: 10, 0 = unlimited)
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
- `depth`: Crawling depth (0 = root page)

## Depth Handling

The crawler now features advanced depth handling capabilities:

### Queue-Based BFS Crawling
- Uses a breadth-first search (BFS) approach with a queue for efficient crawling
- Processes URLs level by level, ensuring systematic coverage
- Better memory management compared to recursive depth-first approaches

### Flexible Depth Limits
- **Default depth**: 10 levels (increased from 3)
- **Unlimited depth**: Set `max_depth=0` for unlimited crawling
- **Custom depth**: Set any positive integer for specific depth limits

### Smart Link Filtering
- Only follows internal links (same domain) to stay within target website
- Filters out non-content URLs (PDFs, images, CSS, JS, etc.)
- Skips URLs with fragments (anchors) to avoid duplicate content

### Depth Tracking
- Each crawled page includes a `depth` field showing its level
- Root page has depth 0, linked pages have depth 1, 2, etc.
- Useful for analyzing website structure and content distribution

### Example Usage

```python
# Shallow crawling (depth 1)
request = CrawlRequest(url="https://example.com", max_depth=1)

# Deep crawling (depth 10)
request = CrawlRequest(url="https://example.com", max_depth=10)

# Unlimited depth crawling
request = CrawlRequest(url="https://example.com", max_depth=0)
```

## Duplicate URL Avoidance

The crawler now includes intelligent duplicate URL avoidance to prevent crawling the same page multiple times:

### URL Normalization
- **Case normalization**: Converts URLs to lowercase for consistent comparison
- **Port normalization**: Removes default ports (80 for HTTP, 443 for HTTPS)
- **Path normalization**: Removes trailing slashes from root paths
- **Fragment removal**: Strips URL fragments (anchors) as they typically point to the same content
- **Query preservation**: Keeps query parameters as they may be important for content differentiation

### Duplicate Detection
- **Visited URL tracking**: Maintains a set of normalized URLs that have been crawled
- **Queue deduplication**: Prevents adding duplicate URLs to the crawl queue
- **Real-time checking**: Checks for duplicates before crawling each URL

### Benefits
- **Efficiency**: Prevents unnecessary duplicate requests
- **Resource savings**: Reduces bandwidth and processing time
- **Better coverage**: Ensures more unique pages are discovered
- **Consistent results**: Eliminates duplicate entries in crawl results

### Example Normalization

```python
# These URLs are considered duplicates:
"https://example.com/"           → "https://example.com"
"https://example.com"            → "https://example.com"
"https://example.com:443/"       → "https://example.com"
"https://example.com/path/"      → "https://example.com/path"
"https://example.com/path#section" → "https://example.com/path"

# These URLs are considered different:
"https://example.com/path"       → "https://example.com/path"
"https://example.com/path?param=value" → "https://example.com/path?param=value"
```

## Storage Layer

The crawler service includes a comprehensive storage layer supporting multiple backends:

### Storage Backends

1. **JSON Files** (Small Scale)
   - Simple file-based storage
   - No external dependencies
   - Perfect for development and testing

2. **MongoDB** (Large Scale)
   - Fast document-based storage
   - Advanced querying capabilities
   - Horizontal scaling support

3. **Elasticsearch** (Analytics Scale)
   - Full-text search capabilities
   - Advanced analytics and aggregations
   - Real-time search and monitoring

### Configuration

```bash
# JSON Storage (Default)
STORAGE_TYPE=json
STORAGE_DATA_DIR=data

# MongoDB Storage
STORAGE_TYPE=mongodb
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=crawler_service

# Elasticsearch Storage
STORAGE_TYPE=elasticsearch
ELASTICSEARCH_HOSTS=localhost:9200
ELASTICSEARCH_INDEX_PREFIX=crawler
```

### Search Capabilities

- **Task Search**: Find tasks by status, URL, date range
- **Page Search**: Search pages by title, content, status code
- **Full-Text Search**: Advanced content search (Elasticsearch only)

### Migration Tools

Easy migration between storage backends with built-in tools:

```python
from storage_migration import migrate_from_json_to_mongodb

# Migrate data between backends
result = await migrate_from_json_to_mongodb(
    json_data_dir="data",
    mongodb_url="mongodb://localhost:27017",
    database_name="crawler_service"
)
```

For detailed storage documentation, see [STORAGE_README.md](STORAGE_README.md).

## Development

### Project Structure

```
crawler-service/
├── main.py              # FastAPI application
├── models.py            # Pydantic data models
├── crawler_service.py   # Web crawler implementation
├── config.py            # Configuration settings
├── storage.py           # Storage interface and JSON backend
├── storage_mongodb.py   # MongoDB storage backend
├── storage_elasticsearch.py # Elasticsearch storage backend
├── storage_migration.py # Data migration utilities
├── storage_demo.py      # Storage layer demonstration
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
