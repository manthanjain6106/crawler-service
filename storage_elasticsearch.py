"""
Elasticsearch storage backend for the crawler service.
Provides fast search and analytics capabilities for large scale deployments.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from elasticsearch import AsyncElasticsearch
from elasticsearch.exceptions import NotFoundError, RequestError
import json

from models import CrawlTask, CrawlResult, CrawledPage
from storage import StorageBackend

logger = logging.getLogger(__name__)


class ElasticsearchStorage(StorageBackend):
    """Elasticsearch storage backend for large scale deployments with advanced search."""
    
    def __init__(self, hosts: List[str] = None, cloud_id: str = None, 
                 api_key: str = None, username: str = None, password: str = None,
                 index_prefix: str = "crawler", **kwargs):
        self.hosts = hosts or ["localhost:9200"]
        self.cloud_id = cloud_id
        self.api_key = api_key
        self.username = username
        self.password = password
        self.index_prefix = index_prefix
        
        # Index names
        self.tasks_index = f"{index_prefix}_tasks"
        self.results_index = f"{index_prefix}_results"
        self.pages_index = f"{index_prefix}_pages"
        
        # Initialize connection
        self.client: Optional[AsyncElasticsearch] = None
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize Elasticsearch connection."""
        try:
            # Build connection config
            config = {}
            if self.cloud_id:
                config["cloud_id"] = self.cloud_id
                if self.api_key:
                    config["api_key"] = self.api_key
                elif self.username and self.password:
                    config["basic_auth"] = (self.username, self.password)
            else:
                config["hosts"] = self.hosts
                if self.username and self.password:
                    config["basic_auth"] = (self.username, self.password)
                elif self.api_key:
                    config["api_key"] = self.api_key
            
            self.client = AsyncElasticsearch(**config)
            logger.info(f"Connected to Elasticsearch: {self.hosts}")
        except Exception as e:
            logger.error(f"Failed to connect to Elasticsearch: {e}")
            raise
    
    def _serialize_datetime(self, obj):
        """Convert datetime objects to ISO format for JSON serialization."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        return obj
    
    def _prepare_document(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare document for Elasticsearch storage."""
        # Convert to dict if it's a Pydantic model
        if hasattr(data, 'dict'):
            data = data.dict()
        
        # Serialize datetime objects
        def serialize_recursive(obj):
            if isinstance(obj, dict):
                return {k: serialize_recursive(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize_recursive(item) for item in obj]
            elif isinstance(obj, datetime):
                return obj.isoformat()
            else:
                return obj
        
        return serialize_recursive(data)
    
    async def save_task(self, task: CrawlTask) -> bool:
        """Save a crawl task to Elasticsearch."""
        try:
            task_data = self._prepare_document(task)
            
            await self.client.index(
                index=self.tasks_index,
                id=task.task_id,
                body=task_data
            )
            return True
        except Exception as e:
            logger.error(f"Error saving task {task.task_id}: {e}")
            return False
    
    async def get_task(self, task_id: str) -> Optional[CrawlTask]:
        """Get a crawl task by ID."""
        try:
            response = await self.client.get(
                index=self.tasks_index,
                id=task_id
            )
            task_data = response['_source']
            return CrawlTask(**task_data)
        except NotFoundError:
            return None
        except Exception as e:
            logger.error(f"Error getting task {task_id}: {e}")
            return None
    
    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update a crawl task."""
        try:
            prepared_updates = self._prepare_document(updates)
            prepared_updates['updated_at'] = datetime.now().isoformat()
            
            await self.client.update(
                index=self.tasks_index,
                id=task_id,
                body={"doc": prepared_updates}
            )
            return True
        except Exception as e:
            logger.error(f"Error updating task {task_id}: {e}")
            return False
    
    async def delete_task(self, task_id: str) -> bool:
        """Delete a crawl task."""
        try:
            await self.client.delete(
                index=self.tasks_index,
                id=task_id
            )
            return True
        except NotFoundError:
            return False
        except Exception as e:
            logger.error(f"Error deleting task {task_id}: {e}")
            return False
    
    async def list_tasks(self, limit: Optional[int] = None, offset: int = 0) -> List[CrawlTask]:
        """List crawl tasks with pagination."""
        try:
            query = {
                "query": {"match_all": {}},
                "sort": [{"created_at": {"order": "desc"}}],
                "from": offset
            }
            if limit:
                query["size"] = limit
            
            response = await self.client.search(
                index=self.tasks_index,
                body=query
            )
            
            tasks = []
            for hit in response['hits']['hits']:
                try:
                    task = CrawlTask(**hit['_source'])
                    tasks.append(task)
                except Exception as e:
                    logger.warning(f"Error parsing task: {e}")
                    continue
            
            return tasks
        except Exception as e:
            logger.error(f"Error listing tasks: {e}")
            return []
    
    async def search_tasks(self, query: Dict[str, Any], limit: Optional[int] = None) -> List[CrawlTask]:
        """Search crawl tasks by criteria."""
        try:
            # Build Elasticsearch query
            es_query = {"query": {"bool": {"must": []}}}
            
            for field, value in query.items():
                if field == "status":
                    es_query["query"]["bool"]["must"].append({"term": {"status": value}})
                elif field == "url":
                    es_query["query"]["bool"]["must"].append({
                        "wildcard": {"request.url": f"*{value}*"}
                    })
                elif field == "created_after":
                    es_query["query"]["bool"]["must"].append({
                        "range": {"created_at": {"gte": value}}
                    })
                elif field == "created_before":
                    es_query["query"]["bool"]["must"].append({
                        "range": {"created_at": {"lte": value}}
                    })
                else:
                    es_query["query"]["bool"]["must"].append({"term": {field: value}})
            
            es_query["sort"] = [{"created_at": {"order": "desc"}}]
            if limit:
                es_query["size"] = limit
            
            response = await self.client.search(
                index=self.tasks_index,
                body=es_query
            )
            
            tasks = []
            for hit in response['hits']['hits']:
                try:
                    task = CrawlTask(**hit['_source'])
                    tasks.append(task)
                except Exception as e:
                    logger.warning(f"Error parsing task: {e}")
                    continue
            
            return tasks
        except Exception as e:
            logger.error(f"Error searching tasks: {e}")
            return []
    
    async def save_crawl_result(self, result: CrawlResult) -> bool:
        """Save a crawl result separately."""
        try:
            result_data = self._prepare_document(result)
            
            await self.client.index(
                index=self.results_index,
                id=result.task_id,
                body=result_data
            )
            
            # Also save individual pages for better querying
            await self._save_pages(result)
            
            return True
        except Exception as e:
            logger.error(f"Error saving result {result.task_id}: {e}")
            return False
    
    async def _save_pages(self, result: CrawlResult):
        """Save individual pages for better querying."""
        try:
            pages_data = []
            for i, page in enumerate(result.pages):
                page_data = self._prepare_document(page)
                page_data['task_id'] = result.task_id
                page_data['page_index'] = i
                pages_data.append({
                    "_index": self.pages_index,
                    "_id": f"{result.task_id}_{i}",
                    "_source": page_data
                })
            
            if pages_data:
                # Use bulk operations for efficiency
                await self.client.bulk(body=pages_data)
        except Exception as e:
            logger.warning(f"Error saving pages for result {result.task_id}: {e}")
    
    async def get_crawl_result(self, task_id: str) -> Optional[CrawlResult]:
        """Get a crawl result by task ID."""
        try:
            response = await self.client.get(
                index=self.results_index,
                id=task_id
            )
            result_data = response['_source']
            return CrawlResult(**result_data)
        except NotFoundError:
            return None
        except Exception as e:
            logger.error(f"Error getting result {task_id}: {e}")
            return None
    
    async def search_pages(self, query: Dict[str, Any], limit: Optional[int] = None) -> List[CrawledPage]:
        """Search crawled pages by criteria."""
        try:
            # Build Elasticsearch query
            es_query = {"query": {"bool": {"must": []}}}
            
            for field, value in query.items():
                if field == "url":
                    es_query["query"]["bool"]["must"].append({
                        "wildcard": {"url": f"*{value}*"}
                    })
                elif field == "title":
                    es_query["query"]["bool"]["must"].append({
                        "match": {"title": value}
                    })
                elif field == "status_code":
                    es_query["query"]["bool"]["must"].append({
                        "term": {"status_code": value}
                    })
                elif field == "task_id":
                    es_query["query"]["bool"]["must"].append({
                        "term": {"task_id": value}
                    })
                elif field == "crawled_after":
                    es_query["query"]["bool"]["must"].append({
                        "range": {"crawled_at": {"gte": value}}
                    })
                elif field == "crawled_before":
                    es_query["query"]["bool"]["must"].append({
                        "range": {"crawled_at": {"lte": value}}
                    })
                elif field == "text_content":
                    es_query["query"]["bool"]["must"].append({
                        "match": {"text_content": value}
                    })
                else:
                    es_query["query"]["bool"]["must"].append({"term": {field: value}})
            
            es_query["sort"] = [{"crawled_at": {"order": "desc"}}]
            if limit:
                es_query["size"] = limit
            
            response = await self.client.search(
                index=self.pages_index,
                body=es_query
            )
            
            pages = []
            for hit in response['hits']['hits']:
                try:
                    page_data = hit['_source'].copy()
                    page_data.pop('task_id', None)  # Remove task_id as it's not part of CrawledPage
                    page_data.pop('page_index', None)  # Remove page_index as it's not part of CrawledPage
                    page = CrawledPage(**page_data)
                    pages.append(page)
                except Exception as e:
                    logger.warning(f"Error parsing page: {e}")
                    continue
            
            return pages
        except Exception as e:
            logger.error(f"Error searching pages: {e}")
            return []
    
    async def search_pages_fulltext(self, search_text: str, limit: Optional[int] = None) -> List[CrawledPage]:
        """Full-text search across page content."""
        try:
            query = {
                "query": {
                    "multi_match": {
                        "query": search_text,
                        "fields": ["title^2", "text_content", "meta_description", "image_alt_text"]
                    }
                },
                "sort": [{"crawled_at": {"order": "desc"}}]
            }
            if limit:
                query["size"] = limit
            
            response = await self.client.search(
                index=self.pages_index,
                body=query
            )
            
            pages = []
            for hit in response['hits']['hits']:
                try:
                    page_data = hit['_source'].copy()
                    page_data.pop('task_id', None)
                    page_data.pop('page_index', None)
                    page = CrawledPage(**page_data)
                    pages.append(page)
                except Exception as e:
                    logger.warning(f"Error parsing page: {e}")
                    continue
            
            return pages
        except Exception as e:
            logger.error(f"Error in fulltext search: {e}")
            return []
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        try:
            # Get index stats
            tasks_stats = await self.client.count(index=self.tasks_index)
            results_stats = await self.client.count(index=self.results_index)
            pages_stats = await self.client.count(index=self.pages_index)
            
            # Get status breakdown
            query = {
                "size": 0,
                "aggs": {
                    "status_breakdown": {
                        "terms": {"field": "status"}
                    }
                }
            }
            response = await self.client.search(
                index=self.tasks_index,
                body=query
            )
            
            status_breakdown = {}
            for bucket in response['aggregations']['status_breakdown']['buckets']:
                status_breakdown[bucket['key']] = bucket['doc_count']
            
            # Get index info
            indices_info = await self.client.indices.get(index=f"{self.index_prefix}_*")
            
            total_size = 0
            for index_name, index_info in indices_info.items():
                stats = await self.client.indices.stats(index=index_name)
                total_size += stats['indices'][index_name]['total']['store']['size_in_bytes']
            
            return {
                "storage_type": "Elasticsearch",
                "index_prefix": self.index_prefix,
                "total_tasks": tasks_stats['count'],
                "total_results": results_stats['count'],
                "total_pages": pages_stats['count'],
                "status_breakdown": status_breakdown,
                "total_size_bytes": total_size,
                "indices": {
                    "tasks": tasks_stats['count'],
                    "results": results_stats['count'],
                    "pages": pages_stats['count']
                }
            }
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {
                "storage_type": "Elasticsearch",
                "error": str(e)
            }
    
    async def create_indexes(self):
        """Create indexes with proper mappings for better search performance."""
        try:
            # Tasks index mapping
            tasks_mapping = {
                "mappings": {
                    "properties": {
                        "task_id": {"type": "keyword"},
                        "status": {"type": "keyword"},
                        "created_at": {"type": "date"},
                        "updated_at": {"type": "date"},
                        "request": {
                            "properties": {
                                "url": {"type": "keyword"},
                                "max_depth": {"type": "integer"},
                                "follow_links": {"type": "boolean"},
                                "extract_text": {"type": "boolean"},
                                "extract_images": {"type": "boolean"},
                                "extract_links": {"type": "boolean"},
                                "extract_headings": {"type": "boolean"},
                                "extract_image_alt_text": {"type": "boolean"},
                                "extract_canonical_url": {"type": "boolean"},
                                "timeout": {"type": "integer"}
                            }
                        }
                    }
                }
            }
            
            # Results index mapping
            results_mapping = {
                "mappings": {
                    "properties": {
                        "task_id": {"type": "keyword"},
                        "status": {"type": "keyword"},
                        "total_pages": {"type": "integer"},
                        "started_at": {"type": "date"},
                        "completed_at": {"type": "date"},
                        "duration": {"type": "float"}
                    }
                }
            }
            
            # Pages index mapping
            pages_mapping = {
                "mappings": {
                    "properties": {
                        "task_id": {"type": "keyword"},
                        "url": {"type": "keyword"},
                        "title": {"type": "text", "analyzer": "standard"},
                        "text_content": {"type": "text", "analyzer": "standard"},
                        "meta_description": {"type": "text", "analyzer": "standard"},
                        "status_code": {"type": "integer"},
                        "response_time": {"type": "float"},
                        "crawled_at": {"type": "date"},
                        "depth": {"type": "integer"},
                        "images": {"type": "keyword"},
                        "links": {"type": "keyword"},
                        "headings": {
                            "properties": {
                                "h1": {"type": "text"},
                                "h2": {"type": "text"},
                                "h3": {"type": "text"}
                            }
                        },
                        "image_alt_text": {"type": "text", "analyzer": "standard"},
                        "canonical_url": {"type": "keyword"}
                    }
                }
            }
            
            # Create indexes if they don't exist
            if not await self.client.indices.exists(index=self.tasks_index):
                await self.client.indices.create(index=self.tasks_index, body=tasks_mapping)
            
            if not await self.client.indices.exists(index=self.results_index):
                await self.client.indices.create(index=self.results_index, body=results_mapping)
            
            if not await self.client.indices.exists(index=self.pages_index):
                await self.client.indices.create(index=self.pages_index, body=pages_mapping)
            
            logger.info("Elasticsearch indexes created successfully")
        except Exception as e:
            logger.warning(f"Error creating indexes: {e}")
    
    async def close(self):
        """Close Elasticsearch connection."""
        if self.client:
            await self.client.close()
            logger.info("Elasticsearch connection closed")
