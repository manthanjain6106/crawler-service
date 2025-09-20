# Crawler Microservice Architecture

## Overview

This document describes the architecture of the Web Crawler Microservice, a production-ready service built with FastAPI that provides web crawling and data extraction capabilities.

## Project Structure

```
crawler-service/
├── app/                                    # Main application package
│   ├── __init__.py
│   ├── main.py                            # Application entry point
│   ├── api/                               # API layer
│   │   ├── __init__.py
│   │   └── v1/                           # API version 1
│   │       ├── __init__.py
│   │       ├── admin.py                  # Admin endpoints
│   │       ├── crawl.py                  # Crawling endpoints
│   │       └── health.py                 # Health check endpoints
│   ├── core/                             # Core application logic
│   │   ├── __init__.py
│   │   ├── config.py                     # Configuration settings
│   │   ├── dependencies.py               # Dependency injection
│   │   ├── exceptions.py                 # Custom exceptions
│   │   └── logging.py                    # Logging configuration
│   ├── middleware/                       # Custom middleware
│   │   ├── __init__.py
│   │   └── logging.py                    # Logging middleware
│   ├── models/                           # Data models
│   │   ├── __init__.py
│   │   └── crawl_models.py              # Crawling data models
│   └── services/                         # Business logic services
│       ├── __init__.py
│       ├── crawler.py                    # Main crawler service
│       └── rate_limiter.py              # Rate limiting service
├── scripts/                              # Utility scripts
│   ├── start.bat                        # Windows startup script
│   └── start.sh                         # Linux/Mac startup script
├── ARCHITECTURE.md                       # Architecture documentation
├── docker-compose.yml                    # Docker Compose configuration
├── Dockerfile                           # Docker container definition
├── env.example                          # Environment variables template
├── README.md                            # Project documentation
├── requirements.txt                     # Python dependencies
└── start.py                             # Application startup script
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Layer                             │
├─────────────────────────────────────────────────────────────────┤
│  Web Browser  │  Mobile App  │  API Client  │  Monitoring     │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway                              │
├─────────────────────────────────────────────────────────────────┤
│  Load Balancer  │  Rate Limiting  │  CORS  │  Authentication  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Application                        │
├─────────────────────────────────────────────────────────────────┤
│  API Routes  │  Middleware  │  Dependency Injection  │  Config │
│  • /api/v1/crawl    │  Logging      │  Service Container  │  Env │
│  • /api/v1/health   │  CORS         │  Lifecycle Mgmt     │  Pydantic │
│  • /api/v1/admin    │  Rate Limit   │  Error Handling     │  Validation │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Service Layer                              │
├─────────────────────────────────────────────────────────────────┤
│  Crawler Service  │  Rate Limiter  │  Logging Middleware       │
│  • Web Crawling   │  • Per-Domain  │  • Request/Response       │
│  • Data Extract   │  • Sliding Win │  • Structured Logging     │
│  • Concurrency    │  • Configurable│  • Error Tracking         │
│  • Retry Logic    │  • Statistics  │  • Performance Metrics    │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                 │
├─────────────────────────────────────────────────────────────────┤
│  In-Memory Storage  │  File System  │  External APIs           │
│  • Task Management  │  • Log Files  │  • Target Websites       │
│  • Rate Limiting    │  • Config     │  • Health Checks         │
│  • Session State    │  • Temp Data  │  • Monitoring            │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. API Layer (`app/api/`)

**Purpose**: Handle HTTP requests and responses, route management, and API versioning.

**Components**:
- `v1/crawl.py` - Crawl operation endpoints
- `v1/health.py` - Health check and monitoring endpoints  
- `v1/admin.py` - Administrative and management endpoints

**Key Features**:
- RESTful API design
- OpenAPI/Swagger documentation
- Request validation using Pydantic
- Proper HTTP status codes
- Rate limiting per endpoint

### 2. Core Layer (`app/core/`)

**Purpose**: Application foundation, configuration, and cross-cutting concerns.

**Components**:
- `config.py` - Environment-based configuration management
- `dependencies.py` - Dependency injection container
- `exceptions.py` - Custom exception hierarchy
- `logging.py` - Structured logging configuration

**Key Features**:
- Environment-specific configurations
- Type-safe configuration with Pydantic
- Centralized dependency management
- Structured error handling
- JSON-formatted logging

### 3. Service Layer (`app/services/`)

**Purpose**: Business logic implementation and external service integration.

**Components**:
- `crawler.py` - Web crawling logic and data extraction
- `rate_limiter.py` - Per-domain rate limiting

**Key Features**:
- Separation of concerns
- Async/await patterns
- Error handling and retry logic
- Configurable concurrency
- Service abstraction

### 4. Models Layer (`app/models/`)

**Purpose**: Data models and validation schemas.

**Components**:
- `crawl_models.py` - Crawl-related data models

**Key Features**:
- Pydantic models for validation
- Type hints throughout
- JSON serialization
- API documentation generation

### 5. Middleware Layer (`app/middleware/`)

**Purpose**: Request/response processing and cross-cutting concerns.

**Components**:
- `logging.py` - Request/response logging middleware

**Key Features**:
- Structured logging
- Request/response tracking
- Performance metrics
- Error tracking

## Data Flow

### 1. Crawl Request Flow

```
Client Request → API Gateway → FastAPI App → Crawler Service → Response
     ↓              ↓            ↓             ↓              ↓
   HTTP POST    Rate Limit   Validation   Web Crawling   Return Results
     ↓              ↓            ↓             ↓              ↓
   JSON Body    Check Limits  Parse Data   Extract Data   JSON Response
     ↓              ↓            ↓             ↓              ↓
   Response ←   Allow/Deny  ← Valid/Invalid ← Crawl Result ← Success/Error
```

### 2. Logging Flow

```
Request → Logging Middleware → Structured Log → File System
    ↓             ↓                ↓              ↓
  HTTP Req    Add Metadata    JSON Format    Write to File
    ↓             ↓                ↓              ↓
  Response    Performance     Error Tracking   Log Rotation
    ↓             ↓                ↓              ↓
  Log Entry   Request ID      Status Codes    Archive Old
```

## Configuration Management

### Environment Variables

The service uses environment variables for configuration:

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

# Storage
# Note: Current implementation uses in-memory storage
# Future: Add persistent storage backends as needed
```

### Configuration Classes

- `Settings` - Main configuration class using Pydantic
- Environment variable validation
- Type conversion and defaults
- Configuration inheritance

## Error Handling

### Exception Hierarchy

```
CrawlerServiceException (Base)
├── CrawlTaskNotFoundError
├── CrawlTaskAlreadyExistsError
├── CrawlTaskInProgressError
├── InvalidCrawlRequestError
├── RateLimitExceededError
├── StorageError
├── BackgroundJobError
└── ConfigurationError
```

### Error Response Format

```json
{
  "error_code": "TASK_NOT_FOUND",
  "message": "Crawl task 'uuid' not found",
  "details": {
    "task_id": "uuid"
  }
}
```

## Logging Strategy

### Structured Logging

All logs are structured JSON for production:

```json
{
  "timestamp": "2023-01-01T00:00:00Z",
  "level": "info",
  "service": "crawler-service",
  "version": "1.0.0",
  "event_type": "crawl_started",
  "task_id": "uuid",
  "url": "https://example.com",
  "max_depth": 0
}
```

### Log Levels

- `DEBUG` - Detailed debugging information
- `INFO` - General application flow
- `WARNING` - Warning conditions
- `ERROR` - Error conditions
- `CRITICAL` - Critical errors

## Monitoring and Health Checks

### Health Endpoints

- `GET /api/v1/health/` - Comprehensive health check
- `GET /api/v1/health/ready` - Readiness check (Kubernetes)
- `GET /api/v1/health/live` - Liveness check (Kubernetes)
- `GET /api/v1/health/metrics` - Service metrics

### Metrics Collected

- Request count and duration
- Crawl task statistics
- Storage operation metrics
- Background job queue status
- Rate limiting statistics
- Error rates and types

## Deployment Architecture

### Development

```
┌─────────────────┐
│   Local Machine │
├─────────────────┤
│  FastAPI App    │
│  In-Memory      │
│  File Logging   │
└─────────────────┘
```

### Production

```
┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   API Servers   │
├─────────────────┤    ├─────────────────┤
│  Nginx/HAProxy  │───▶│  FastAPI Apps   │
│  SSL Termination│    │  Multiple Inst  │
└─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Data Layer    │
                       ├─────────────────┤
                       │  In-Memory      │
                       │  File Logging   │
                       │  Rate Limiting  │
                       └─────────────────┘
```

## Security Considerations

### Rate Limiting

- API-level rate limiting (requests per minute)
- Per-domain rate limiting for crawling
- Configurable limits and windows
- Redis-based distributed rate limiting

### Input Validation

- Pydantic model validation
- URL validation and sanitization
- Request size limits
- SQL injection prevention

### Error Handling

- No sensitive information in error responses
- Structured error logging
- Proper HTTP status codes
- Error rate monitoring

## Scalability

### Horizontal Scaling

- Stateless API servers
- In-memory rate limiting (per instance)
- File-based logging
- Load balancer distribution

### Vertical Scaling

- Configurable concurrency limits
- Memory-efficient processing
- Async I/O operations
- Resource monitoring

## Testing Strategy

### Unit Tests

- Service layer testing
- Model validation testing
- Configuration testing
- Error handling testing

### Integration Tests

- API endpoint testing
- Service layer testing
- Middleware testing
- End-to-end workflow testing

### Performance Tests

- Load testing
- Concurrency testing
- Memory usage testing
- Response time testing
