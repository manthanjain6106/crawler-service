# Web Crawler Microservice - Data Flow Diagram

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           WEB CRAWLER MICROSERVICE                              │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client/API    │    │   FastAPI       │    │   Background    │
│   Consumer      │◄──►│   Application   │◄──►│   Job Queue     │
│                 │    │   (main.py)     │    │   (Redis/RQ)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Storage Layer  │
                       │  (JSON/MongoDB/ │
                       │  Elasticsearch) │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Web Crawler    │
                       │  Engine         │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Rate Limiter   │
                       │  (Per Domain)   │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Target Websites│
                       │  (External)     │
                       └─────────────────┘
```

## Detailed Data Flow

### 1. Request Flow
```
Client Request → FastAPI → Rate Limiter → Background Queue → Storage
     │              │           │              │              │
     │              │           │              │              ▼
     │              │           │              │    ┌─────────────────┐
     │              │           │              │    │ Task Created    │
     │              │           │              │    │ (PENDING)       │
     │              │           │              │    └─────────────────┘
     │              │           │              │
     │              │           │              ▼
     │              │           │    ┌─────────────────┐
     │              │           │    │ Job Enqueued    │
     │              │           │    │ (Redis Queue)   │
     │              │           │    └─────────────────┘
     │              │           │
     │              │           ▼
     │              │    ┌─────────────────┐
     │              │    │ API Rate Limit  │
     │              │    │ Check           │
     │              │    └─────────────────┘
     │              │
     ▼              ▼
┌─────────────────┐
│ Task ID Returned│
│ (Immediate)     │
└─────────────────┘
```

### 2. Background Processing Flow
```
Background Worker → Web Crawler → Rate Limiter → HTTP Requests → Data Processing
       │                │              │              │              │
       │                │              │              │              ▼
       │                │              │              │    ┌─────────────────┐
       │                │              │              │    │ Parse HTML      │
       │                │              │              │    │ Extract Data    │
       │                │              │              │    └─────────────────┘
       │                │              │              │
       │                │              │              ▼
       │                │              │    ┌─────────────────┐
       │                │              │    │ HTTP Response   │
       │                │              │    │ (Success/Error) │
       │                │              │    └─────────────────┘
       │                │              │
       │                │              ▼
       │                │    ┌─────────────────┐
       │                │    │ Per-Domain      │
       │                │    │ Rate Limiting   │
       │                │    └─────────────────┘
       │                │
       │                ▼
       │    ┌─────────────────┐
       │    │ BFS Crawling    │
       │    │ Algorithm       │
       │    └─────────────────┘
       │
       ▼
┌─────────────────┐
│ Update Task     │
│ Status & Store  │
│ Results         │
└─────────────────┘
```

### 3. Data Storage Flow
```
Crawled Data → Storage Manager → Storage Backend → Persistent Storage
      │              │                │                    │
      │              │                │                    ▼
      │              │                │           ┌─────────────────┐
      │              │                │           │ JSON Files      │
      │              │                │           │ MongoDB         │
      │              │                │           │ Elasticsearch   │
      │              │                │           └─────────────────┘
      │              │                │
      │              │                ▼
      │              │    ┌─────────────────┐
      │              │    │ Task Metadata   │
      │              │    │ Crawl Results   │
      │              │    │ Page Data       │
      │              │    └─────────────────┘
      │              │
      ▼              ▼
┌─────────────────┐
│ CrawledPage     │
│ Objects         │
└─────────────────┘
```

## Component Interactions

### Core Components:

1. **FastAPI Application (main.py)**
   - Handles HTTP requests
   - Manages API endpoints
   - Implements rate limiting
   - Coordinates with storage and background jobs

2. **Web Crawler Engine (crawler_service.py)**
   - Performs actual web crawling
   - Implements BFS algorithm for link following
   - Handles retry logic and error management
   - Manages concurrency and rate limiting

3. **Background Job System (background_jobs.py)**
   - Uses Redis Queue (RQ) for job management
   - Processes crawl tasks asynchronously
   - Handles job status tracking and cleanup

4. **Storage Layer (storage.py)**
   - Abstract storage interface
   - Supports multiple backends (JSON, MongoDB, Elasticsearch)
   - Manages task and result persistence

5. **Rate Limiter (rate_limiter.py)**
   - Per-domain rate limiting
   - Sliding window algorithm
   - Configurable limits per domain

6. **Data Models (models.py)**
   - Pydantic models for data validation
   - Structured error handling
   - Type-safe data representation

## Data Flow States

### Task Lifecycle:
1. **PENDING** - Task created, waiting in queue
2. **IN_PROGRESS** - Background worker processing
3. **COMPLETED** - Crawling finished successfully
4. **FAILED** - Crawling failed with errors

### Data Processing Pipeline:
1. **URL Discovery** - Extract links from crawled pages
2. **Content Extraction** - Parse HTML and extract data
3. **Data Enrichment** - Add metadata and structure
4. **Storage** - Persist to configured backend
5. **Indexing** - Make data searchable (Elasticsearch)

## Key Features

- **Asynchronous Processing**: Non-blocking API with background jobs
- **Scalable Architecture**: Redis-based job queue with multiple workers
- **Rate Limiting**: Both API-level and per-domain rate limiting
- **Error Handling**: Comprehensive retry logic and structured error tracking
- **Multiple Storage Backends**: JSON, MongoDB, and Elasticsearch support
- **Concurrent Crawling**: Configurable concurrency with burst protection
- **Data Search**: Full-text search capabilities for crawled content
- **Monitoring**: Health checks, statistics, and job queue monitoring
