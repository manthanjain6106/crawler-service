# Storage Layer Documentation

The crawler service now includes a comprehensive storage layer that supports multiple backends for different scale requirements.

## Overview

The storage layer provides:
- **Small Scale**: JSON file storage for simple deployments
- **Large Scale**: MongoDB for fast access and querying
- **Analytics Scale**: Elasticsearch for advanced search and analytics
- **Migration Tools**: Easy migration between storage backends
- **Unified API**: Consistent interface across all storage types

## Storage Backends

### 1. JSON File Storage (Small Scale)

**Best for**: Development, testing, small deployments (< 10,000 pages)

**Features**:
- Simple file-based storage
- No external dependencies
- Easy backup and migration
- Human-readable data format

**Configuration**:
```bash
STORAGE_TYPE=json
STORAGE_DATA_DIR=data
```

**Data Structure**:
```
data/
├── tasks.json      # Crawl tasks
├── results.json    # Crawl results
└── pages.json      # Individual pages (if enabled)
```

### 2. MongoDB Storage (Large Scale)

**Best for**: Production deployments, large datasets (10,000+ pages)

**Features**:
- Fast document-based storage
- Advanced querying capabilities
- Horizontal scaling
- Built-in indexing
- ACID transactions

**Configuration**:
```bash
STORAGE_TYPE=mongodb
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=crawler_service
```

**Collections**:
- `tasks`: Crawl tasks and metadata
- `results`: Crawl results and statistics
- `pages`: Individual crawled pages for advanced querying

### 3. Elasticsearch Storage (Analytics Scale)

**Best for**: Large-scale deployments requiring advanced search and analytics

**Features**:
- Full-text search capabilities
- Advanced analytics and aggregations
- Real-time search
- Scalable and distributed
- Rich query DSL

**Configuration**:
```bash
STORAGE_TYPE=elasticsearch
ELASTICSEARCH_HOSTS=localhost:9200
ELASTICSEARCH_INDEX_PREFIX=crawler
```

**Indices**:
- `crawler_tasks`: Task metadata and status
- `crawler_results`: Crawl results and statistics
- `crawler_pages`: Individual pages with full-text search

## API Endpoints

### Task Management
- `POST /crawl` - Start a new crawl task
- `GET /crawl/{task_id}` - Get task status
- `GET /crawl` - List all tasks (with pagination)
- `DELETE /crawl/{task_id}` - Delete a task

### Results
- `GET /crawl/{task_id}/result` - Get crawl result

### Search
- `GET /search/tasks` - Search tasks by criteria
- `GET /search/pages` - Search pages by criteria

### Storage
- `GET /storage/stats` - Get storage statistics

## Search Capabilities

### Task Search
```bash
GET /search/tasks?status=completed&url=example.com&limit=50
```

**Parameters**:
- `status`: Task status (pending, in_progress, completed, failed)
- `url`: URL pattern to match
- `created_after`: ISO timestamp
- `created_before`: ISO timestamp
- `limit`: Maximum results (default: 100)

### Page Search
```bash
GET /search/pages?title=example&status_code=200&limit=50
```

**Parameters**:
- `url`: URL pattern to match
- `title`: Title pattern to match
- `status_code`: HTTP status code
- `task_id`: Specific task ID
- `crawled_after`: ISO timestamp
- `crawled_before`: ISO timestamp
- `limit`: Maximum results (default: 100)

### Full-Text Search (Elasticsearch only)
```bash
GET /search/pages?q=search_term
```

## Migration Tools

### Command Line Migration
```bash
# Export JSON data
python storage_migration.py --export backup.json

# Import JSON data
python storage_migration.py --import backup.json
```

### Programmatic Migration
```python
from storage_migration import StorageMigrator, migrate_from_json_to_mongodb

# Migrate from JSON to MongoDB
result = await migrate_from_json_to_mongodb(
    json_data_dir="data",
    mongodb_url="mongodb://localhost:27017",
    database_name="crawler_service"
)
```

## Performance Comparison

| Storage Type | Write Speed | Read Speed | Search Speed | Storage Size |
|-------------|-------------|------------|--------------|--------------|
| JSON Files  | Medium      | Fast       | Slow         | Large        |
| MongoDB     | Fast        | Very Fast  | Fast         | Medium       |
| Elasticsearch| Fast       | Fast       | Very Fast    | Medium       |

## Configuration Examples

### Development (JSON)
```bash
STORAGE_TYPE=json
STORAGE_DATA_DIR=./data
```

### Production (MongoDB)
```bash
STORAGE_TYPE=mongodb
MONGODB_URL=mongodb://user:pass@cluster.mongodb.net:27017
MONGODB_DATABASE=crawler_prod
```

### Analytics (Elasticsearch)
```bash
STORAGE_TYPE=elasticsearch
ELASTICSEARCH_HOSTS=es1.example.com:9200,es2.example.com:9200
ELASTICSEARCH_USERNAME=elastic
ELASTICSEARCH_PASSWORD=password
ELASTICSEARCH_INDEX_PREFIX=crawler_prod
```

## Docker Compose Examples

### JSON Storage
```yaml
version: '3.8'
services:
  crawler-service:
    build: .
    environment:
      - STORAGE_TYPE=json
      - STORAGE_DATA_DIR=/app/data
    volumes:
      - ./data:/app/data
```

### MongoDB Storage
```yaml
version: '3.8'
services:
  crawler-service:
    build: .
    environment:
      - STORAGE_TYPE=mongodb
      - MONGODB_URL=mongodb://mongodb:27017
      - MONGODB_DATABASE=crawler_service
    depends_on:
      - mongodb

  mongodb:
    image: mongo:7
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db

volumes:
  mongodb_data:
```

### Elasticsearch Storage
```yaml
version: '3.8'
services:
  crawler-service:
    build: .
    environment:
      - STORAGE_TYPE=elasticsearch
      - ELASTICSEARCH_HOSTS=elasticsearch:9200
      - ELASTICSEARCH_INDEX_PREFIX=crawler
    depends_on:
      - elasticsearch

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

volumes:
  elasticsearch_data:
```

## Monitoring and Statistics

### Storage Statistics Endpoint
```bash
GET /storage/stats
```

**Response**:
```json
{
  "storage_type": "MongoDB",
  "total_tasks": 1250,
  "total_results": 1200,
  "total_pages": 45000,
  "status_breakdown": {
    "completed": 1200,
    "failed": 50
  },
  "database_size_bytes": 104857600,
  "collections": {
    "tasks": 1250,
    "results": 1200,
    "pages": 45000
  }
}
```

## Best Practices

### 1. Choose the Right Storage Backend
- **JSON**: Development, testing, small datasets
- **MongoDB**: Production, large datasets, complex queries
- **Elasticsearch**: Analytics, full-text search, large-scale deployments

### 2. Indexing Strategy
- MongoDB: Create indexes on frequently queried fields
- Elasticsearch: Configure proper mappings for search fields

### 3. Data Retention
- Implement data retention policies
- Archive old data to cold storage
- Regular cleanup of failed tasks

### 4. Backup Strategy
- Regular backups of storage data
- Test restore procedures
- Cross-region replication for production

### 5. Monitoring
- Monitor storage usage and performance
- Set up alerts for storage issues
- Track query performance

## Troubleshooting

### Common Issues

1. **MongoDB Connection Failed**
   - Check MongoDB is running
   - Verify connection string
   - Check network connectivity

2. **Elasticsearch Index Creation Failed**
   - Check Elasticsearch is running
   - Verify index permissions
   - Check disk space

3. **JSON File Permission Errors**
   - Check directory permissions
   - Ensure write access to data directory

### Debug Mode
```bash
LOG_LEVEL=DEBUG
```

This will provide detailed logging of storage operations.

## Migration Guide

### From In-Memory to JSON
1. Set `STORAGE_TYPE=json`
2. Restart the service
3. Data will be automatically saved to JSON files

### From JSON to MongoDB
1. Install MongoDB
2. Run migration script
3. Update configuration
4. Restart service

### From MongoDB to Elasticsearch
1. Install Elasticsearch
2. Run migration script
3. Update configuration
4. Restart service

## API Examples

### Start a Crawl
```bash
curl -X POST "http://localhost:8000/crawl" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "max_depth": 3,
    "follow_links": true,
    "extract_text": true
  }'
```

### Search Tasks
```bash
curl "http://localhost:8000/search/tasks?status=completed&limit=10"
```

### Search Pages
```bash
curl "http://localhost:8000/search/pages?title=example&status_code=200"
```

### Get Storage Stats
```bash
curl "http://localhost:8000/storage/stats"
```

This storage layer provides a robust, scalable foundation for the crawler service, supporting everything from simple development setups to large-scale production deployments with advanced search and analytics capabilities.
