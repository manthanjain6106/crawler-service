# Crawler Microservice Architecture

## Overview

This document describes the architecture of the Web Crawler Microservice, a production-ready service built with FastAPI that provides web crawling and data extraction capabilities.

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
│  Crawler Service  │  Storage Service  │  Rate Limiter  │  Jobs │
│  • Web Crawling   │  • JSON Files     │  • Per-Domain  │  • Redis │
│  • Data Extract   │  • MongoDB        │  • Sliding Win │  • Async │
│  • Concurrency    │  • Elasticsearch  │  • Configurable│  • Queue │
│  • Retry Logic    │  • Abstraction    │  • Statistics  │  • Workers│
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Storage Layer                              │
├─────────────────────────────────────────────────────────────────┤
│  JSON Files  │  MongoDB  │  Elasticsearch  │  Redis Queue      │
│  • Development │  • Production │  • Search & Analytics │  • Jobs │
│  • Simple     │  • Scalable  │  • Full-text Search    │  • State │
│  • File-based │  • ACID     │  • Aggregations        │  • Cache │
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
- `storage.py` - Storage abstraction and management
- `rate_limiter.py` - Per-domain rate limiting
- `background_jobs.py` - Asynchronous job processing

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

### 5. Storage Layer (`app/storage/`)

**Purpose**: Data persistence and retrieval abstraction.

**Components**:
- `json_storage.py` - File-based storage
- `mongodb_storage.py` - MongoDB storage (to be implemented)
- `elasticsearch_storage.py` - Elasticsearch storage (to be implemented)

**Key Features**:
- Storage backend abstraction
- Multiple storage options
- Async operations
- Error handling

## Data Flow

### 1. Crawl Request Flow

```
Client Request → API Gateway → FastAPI App → Crawler Service → Storage
     ↓              ↓            ↓             ↓              ↓
   HTTP POST    Rate Limit   Validation   Web Crawling   Save Results
     ↓              ↓            ↓             ↓              ↓
   JSON Body    Check Limits  Parse Data   Extract Data   Persist Data
     ↓              ↓            ↓             ↓              ↓
   Response ←   Allow/Deny  ← Valid/Invalid ← Crawl Result ← Success/Error
```

### 2. Background Job Flow

```
API Request → Task Creation → Job Queue → Worker Process → Result Storage
     ↓             ↓             ↓            ↓              ↓
   Start Crawl   Create Task   Enqueue Job  Process Job   Save Results
     ↓             ↓             ↓            ↓              ↓
   Return Task   Store Task   Redis Queue  Async Worker   Update Task
     ID           Metadata      State        Execution      Status
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
STORAGE_TYPE=json  # json, mongodb, elasticsearch
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
  "max_depth": 2
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
│  JSON Storage   │
│  Redis (opt)    │
└─────────────────┘
```

### Production

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   API Servers   │    │   Worker Nodes  │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│  Nginx/HAProxy  │───▶│  FastAPI Apps   │    │  Background     │
│  SSL Termination│    │  Multiple Inst  │    │  Job Workers    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Data Layer    │    │   Job Queue     │
                       ├─────────────────┤    ├─────────────────┤
                       │  MongoDB/ES     │    │     Redis       │
                       │  Persistent     │    │  Job Processing │
                       │  Storage        │    │  State Mgmt     │
                       └─────────────────┘    └─────────────────┘
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
- Shared Redis for job queue
- External storage backends
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
- Storage backend testing
- Background job testing
- End-to-end workflow testing

### Performance Tests

- Load testing
- Concurrency testing
- Memory usage testing
- Response time testing
