# Web Crawler Microservice

A scalable, production-ready microservice for web crawling and data extraction built with FastAPI.

## 🏗️ Architecture

This microservice follows a clean, organized architecture with clear separation of concerns:

```
app/
├── core/                   # Core application components
│   ├── config.py          # Configuration management
│   ├── dependencies.py    # Dependency injection container
│   ├── exceptions.py      # Custom exceptions
│   └── logging.py         # Structured logging
├── models/                # Data models
│   ├── crawl_models.py    # Crawl-related models
│   └── __init__.py
├── services/              # Business logic layer
│   ├── crawler.py         # Web crawling service
│   ├── storage.py         # Storage abstraction
│   ├── rate_limiter.py    # Rate limiting service
│   ├── background_jobs.py # Background job processing
│   └── __init__.py
├── api/                   # API layer
│   └── v1/               # API version 1
│       ├── crawl.py      # Crawl endpoints
│       ├── health.py     # Health check endpoints
│       ├── admin.py      # Admin endpoints
│       └── __init__.py
├── storage/              # Storage backends
│   ├── json_storage.py   # JSON file storage
│   ├── mongodb_storage.py # MongoDB storage
│   ├── elasticsearch_storage.py # Elasticsearch storage
│   └── __init__.py
├── middleware/           # Custom middleware
│   ├── logging.py        # Request logging middleware
│   └── __init__.py
└── main.py              # FastAPI application
```

## 🚀 Features

### Core Features
- **Web Crawling**: Extract text, images, links, headings, and metadata from websites
- **Rate Limiting**: Per-domain rate limiting with configurable limits
- **Background Jobs**: Asynchronous processing using Redis Queue
- **Multiple Storage Backends**: JSON files, MongoDB, and Elasticsearch
- **Structured Logging**: Comprehensive logging with structured data
- **Health Checks**: Kubernetes-ready health and readiness endpoints
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation

### Advanced Features
- **Concurrent Processing**: Configurable concurrency with dynamic adjustment
- **Retry Logic**: Exponential backoff with jitter for failed requests
- **Error Classification**: Structured error handling with retry strategies
- **URL Normalization**: Duplicate URL detection and normalization
- **Internal Link Following**: Smart internal link detection and crawling
- **Monitoring**: Comprehensive metrics and statistics

## 📋 Prerequisites

- Python 3.8+
- Redis (for background jobs)
- MongoDB (optional, for persistent storage)
- Elasticsearch (optional, for search capabilities)

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd crawler-service
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

## ⚙️ Configuration

The service is configured through environment variables. See `env.example` for all available options.

### Key Configuration Options

```bash
# Application
APP_NAME=Web Crawler Microservice
ENVIRONMENT=development
DEBUG=false

# API
API_HOST=0.0.0.0
API_PORT=8000
API_PREFIX=/api/v1

# Crawler
MAX_CONCURRENT_REQUESTS=30
DEFAULT_TIMEOUT=30
MAX_DEPTH=10

# Rate Limiting
RATE_LIMIT_PER_MINUTE=10
ENABLE_PER_DOMAIN_RATE_LIMITING=true
DEFAULT_DOMAIN_RATE_LIMIT=10

# Storage
STORAGE_TYPE=json  # json, mongodb, elasticsearch
STORAGE_DATA_DIR=data

# Background Jobs
ENABLE_BACKGROUND_JOBS=true
REDIS_URL=redis://localhost:6379
```

## 🚀 Running the Service

### Development Mode
```bash
python -m app.main
```

### Production Mode
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### With Docker
```bash
docker-compose up -d
```

## 📚 API Usage

### Start a Crawl
```bash
curl -X POST "http://localhost:8000/api/v1/crawl/" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "max_depth": 2,
    "follow_links": true,
    "extract_text": true,
    "extract_images": true
  }'
```

### Get Crawl Status
```bash
curl "http://localhost:8000/api/v1/crawl/{task_id}"
```

### Get Crawl Results
```bash
curl "http://localhost:8000/api/v1/crawl/{task_id}/result"
```

### Health Check
```bash
curl "http://localhost:8000/api/v1/health/"
```

## 🔧 Storage Backends

### JSON File Storage (Default)
Suitable for development and small deployments:
```bash
STORAGE_TYPE=json
STORAGE_DATA_DIR=data
```

### MongoDB Storage
For production deployments requiring persistence:
```bash
STORAGE_TYPE=mongodb
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=crawler_service
```

### Elasticsearch Storage
For advanced search and analytics:
```bash
STORAGE_TYPE=elasticsearch
ELASTICSEARCH_HOSTS=localhost:9200
ELASTICSEARCH_INDEX_PREFIX=crawler
```

## 🔄 Background Jobs

The service supports background job processing using Redis Queue:

1. **Start Redis**
   ```bash
   redis-server
   ```

2. **Start Worker**
   ```bash
   python -m app.services.background_jobs
   ```

3. **Configure Background Jobs**
   ```bash
   ENABLE_BACKGROUND_JOBS=true
   REDIS_URL=redis://localhost:6379
   ```

## 📊 Monitoring

### Health Endpoints
- `GET /api/v1/health/` - Comprehensive health check
- `GET /api/v1/health/ready` - Readiness check
- `GET /api/v1/health/live` - Liveness check
- `GET /api/v1/health/metrics` - Service metrics

### Admin Endpoints
- `GET /api/v1/admin/rate-limits` - Rate limiting statistics
- `GET /api/v1/admin/storage/stats` - Storage statistics
- `GET /api/v1/admin/jobs/queue/stats` - Job queue statistics

## 🧪 Testing

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_crawler.py
```

## 🐳 Docker Deployment

### Using Docker Compose
```bash
docker-compose up -d
```

### Custom Docker Build
```bash
docker build -t crawler-service .
docker run -p 8000:8000 crawler-service
```

## 📈 Scaling

### Horizontal Scaling
- Deploy multiple instances behind a load balancer
- Use Redis for shared job queue
- Use external storage (MongoDB/Elasticsearch) for data persistence

### Vertical Scaling
- Increase `MAX_CONCURRENT_REQUESTS`
- Increase `API_WORKERS`
- Increase `MAX_WORKERS` for background jobs

## 🔒 Security

- Rate limiting to prevent abuse
- CORS configuration for cross-origin requests
- Input validation using Pydantic models
- Structured error handling without information leakage

## 📝 Logging

The service uses structured logging with JSON format in production:

```json
{
  "timestamp": "2023-01-01T00:00:00Z",
  "level": "info",
  "service": "crawler-service",
  "version": "1.0.0",
  "event_type": "crawl_started",
  "task_id": "uuid",
  "url": "https://example.com"
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/docs`
- Review the health endpoints for service status