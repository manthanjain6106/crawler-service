# Deployment & Scalability Guide

This guide covers the deployment and scalability features of the Web Crawler Microservice.

## 🚀 Quick Start

### Development Deployment

```bash
# Using Docker Compose (recommended)
./deploy.sh development
# or on Windows
deploy.bat development

# Or manually
docker-compose up --build -d
```

### Production Deployment

```bash
# Using Docker Compose
./deploy.sh production
# or on Windows
deploy.bat production

# Or manually
docker-compose -f docker-compose.prod.yml up --build -d
```

## 🏗️ Architecture

The service is designed as a scalable microservice with the following components:

### Core Components

1. **API Service** (`crawler-service`)
   - FastAPI-based REST API
   - Handles HTTP requests and responses
   - Rate limiting and request validation
   - Health checks and monitoring

2. **Background Workers** (`crawler-worker`)
   - Process long-running crawl tasks
   - Uses Redis Queue (RQ) for job management
   - Horizontally scalable
   - Automatic retry and error handling

3. **Redis** (`redis`)
   - Job queue backend
   - Rate limiting storage
   - Session management
   - Caching layer

4. **Storage Backend** (configurable)
   - **JSON Files**: Development and testing
   - **MongoDB**: Production with persistence
   - **Elasticsearch**: Advanced search and analytics

5. **Nginx** (production only)
   - Load balancing
   - SSL termination
   - Rate limiting
   - Security headers

## 📊 Scalability Features

### Background Job Processing

The service uses Redis Queue (RQ) for background job processing:

- **Asynchronous Processing**: Long-running crawls don't block the API
- **Job Queue Management**: Tasks are queued and processed by workers
- **Horizontal Scaling**: Add more workers to increase throughput
- **Job Monitoring**: Track job status, progress, and results
- **Automatic Retries**: Failed jobs are automatically retried
- **Job Cancellation**: Cancel running or queued jobs

### Structured Logging

Comprehensive logging system with different levels:

- **DEBUG**: Detailed information for development and testing
- **INFO**: General information for production monitoring
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for failed operations
- **CRITICAL**: Critical errors that require immediate attention

Logs are structured in JSON format for easy parsing and analysis.

### Rate Limiting

Multi-level rate limiting system:

1. **API Rate Limiting**: Per-client request limiting
2. **Per-Domain Rate Limiting**: Respect target website limits
3. **Burst Protection**: Prevent overwhelming target servers
4. **Dynamic Adjustment**: Automatically adjust based on success rates

### Concurrency Management

- **Dynamic Concurrency**: Automatically adjust based on performance
- **Burst Limits**: Maximum concurrent requests per domain
- **Gradual Scaling**: Gradually increase concurrency for stability
- **Error-Based Backoff**: Reduce concurrency on errors

## 🐳 Docker Configuration

### Development Environment

```yaml
# docker-compose.yml
services:
  crawler-service:    # API service
  crawler-worker:     # Background worker (2 replicas)
  redis:             # Job queue and caching
```

### Production Environment

```yaml
# docker-compose.prod.yml
services:
  crawler-service:    # API service with resource limits
  crawler-worker:     # Background worker (3 replicas)
  redis:             # Redis with memory limits
  mongodb:           # Persistent storage
  nginx:             # Load balancer and SSL termination
```

## 🔧 Configuration

### Environment Variables

Key configuration options:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
MAX_CONCURRENT_REQUESTS=20

# Background Jobs
ENABLE_BACKGROUND_JOBS=true
MAX_WORKERS=3
JOB_TIMEOUT=3600

# Logging
LOG_LEVEL=INFO
ENVIRONMENT=production

# Redis
REDIS_URL=redis://redis:6379
USE_REDIS=true

# Storage
STORAGE_TYPE=mongodb
MONGODB_URL=mongodb://mongodb:27017
```

### Scaling Workers

Scale background workers for increased throughput:

```bash
# Scale to 5 workers
docker-compose -f docker-compose.prod.yml up --scale crawler-worker=5 -d
```

## 📈 Monitoring & Observability

### Health Checks

- **API Health**: `GET /health`
- **Job Queue Stats**: `GET /jobs/queue/stats`
- **Storage Stats**: `GET /storage/stats`

### Logging

Structured logs include:

- Request/response logging
- Job processing events
- Error tracking with context
- Performance metrics
- Rate limiting events

### Metrics

Key metrics to monitor:

- **Request Rate**: Requests per second
- **Job Queue Length**: Pending jobs
- **Worker Utilization**: Active workers
- **Error Rate**: Failed requests/jobs
- **Response Time**: API and crawl performance
- **Memory Usage**: Container resource usage

## 🚦 API Endpoints

### Core Endpoints

- `POST /crawl` - Start a new crawl task
- `GET /crawl/{task_id}` - Get task status
- `GET /crawl/{task_id}/result` - Get crawl results
- `GET /crawl` - List all tasks

### Job Management

- `GET /jobs/queue/stats` - Queue statistics
- `GET /jobs/{job_id}/status` - Job status
- `POST /jobs/{job_id}/cancel` - Cancel job

### Monitoring

- `GET /health` - Health check
- `GET /rate-limits` - Rate limiting info
- `GET /storage/stats` - Storage statistics

## 🔒 Security Features

### Production Security

- **HTTPS Support**: SSL/TLS termination via Nginx
- **Security Headers**: XSS protection, content type sniffing prevention
- **Rate Limiting**: Multiple levels of rate limiting
- **Input Validation**: Comprehensive request validation
- **Error Handling**: Secure error messages

### Container Security

- **Non-root User**: Containers run as non-root
- **Resource Limits**: Memory and CPU limits
- **Health Checks**: Automatic container health monitoring
- **Image Scanning**: Regular security updates

## 📋 Deployment Checklist

### Pre-deployment

- [ ] Configure environment variables
- [ ] Set up SSL certificates (production)
- [ ] Configure storage backend
- [ ] Set up monitoring and alerting
- [ ] Test in staging environment

### Deployment

- [ ] Run deployment script
- [ ] Verify all services are healthy
- [ ] Check job queue is processing
- [ ] Test API endpoints
- [ ] Monitor logs for errors

### Post-deployment

- [ ] Set up log aggregation
- [ ] Configure monitoring dashboards
- [ ] Set up alerting rules
- [ ] Test scaling operations
- [ ] Document any custom configurations

## 🛠️ Troubleshooting

### Common Issues

1. **Service Not Starting**
   - Check Docker and Docker Compose versions
   - Verify environment variables
   - Check port availability

2. **Jobs Not Processing**
   - Verify Redis connection
   - Check worker logs
   - Ensure workers are running

3. **High Memory Usage**
   - Adjust worker replicas
   - Check for memory leaks
   - Monitor job queue length

4. **Rate Limiting Issues**
   - Adjust rate limits
   - Check per-domain limits
   - Monitor target website responses

### Debug Commands

```bash
# View logs
docker-compose logs -f

# Check service status
docker-compose ps

# Scale workers
docker-compose up --scale crawler-worker=3 -d

# Check Redis
docker-compose exec redis redis-cli ping

# Check job queue
docker-compose exec redis redis-cli llen rq:queue:crawl_tasks
```

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Redis Queue Documentation](https://python-rq.org/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Nginx Configuration Guide](https://nginx.org/en/docs/)
