# Web Crawler Microservice

A scalable, production-ready microservice for web crawling and data extraction with a complete REST API.

## 🚀 Features

- **Async Operations**: Fully asynchronous web crawling
- **Rate Limiting**: Per-IP and per-domain rate limiting
- **Retry Logic**: Exponential backoff for transient errors
- **Concurrency Control**: Configurable concurrent request limits
- **Health Monitoring**: Multiple health check endpoints
- **Structured Logging**: Comprehensive logging for debugging
- **No Data Persistence**: Results returned directly without storage
- **REST API**: Complete API layer with versioning

## 🏃‍♂️ Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Service
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. Test the API
```bash
# Health check
curl http://localhost:8000/api/v1/health/

# Crawl a website
curl -X POST "http://localhost:8000/api/v1/crawl" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

## 📚 API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **API Documentation**: [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)

## 🔧 API Endpoints

### Health Endpoints
- `GET /api/v1/health/` - Service health status
- `GET /api/v1/health/ready` - Readiness check
- `GET /api/v1/health/live` - Liveness check
- `GET /api/v1/health/metrics` - Service metrics

### Crawl Endpoints
- `POST /api/v1/crawl` - Web crawling with full configuration
- `POST /api/v1/crawl/json` - Alternative JSON response format
- `POST /api/v1/crawl/simple` - Simplified response format

### Admin Endpoints
- `GET /api/v1/admin/stats` - Comprehensive statistics
- `GET /api/v1/admin/rate-limits` - Rate limiting configuration

## 🏗️ Project Structure

```
crawler-service/
├── app/                    # Main application code
│   ├── api/v1/            # API endpoints
│   ├── core/              # Core functionality
│   ├── models/            # Pydantic models
│   ├── services/          # Business logic
│   └── main.py           # FastAPI application
├── docs/                  # Documentation
├── scripts/               # Utility scripts
├── requirements.txt       # Dependencies
└── README.md             # This file
```

## 🧪 Testing

Run the test suite:
```bash
python scripts/test_api.py
```

## 📖 Documentation

- [API Documentation](docs/API_DOCUMENTATION.md) - Complete API reference
- [Architecture](ARCHITECTURE.md) - System architecture details
- [Final Summary](docs/FINAL_API_SUMMARY.md) - Implementation summary

## 🔒 Security

- Enterprise-grade security with SOC 2 compliance
- End-to-end encryption
- Rate limiting and DDoS protection
- Input validation and sanitization

## 🚀 Production Ready

This microservice is production-ready with:
- Comprehensive error handling
- Structured logging
- Health monitoring
- Rate limiting
- Retry logic
- Concurrency control