"""
Storage service for the crawler microservice.
Provides a unified interface for different storage backends.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging

from app.models.crawl_models import CrawlTask, CrawlResult, CrawledPage
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.exceptions import StorageError


class StorageBackend(ABC):
    """Abstract base class for storage backends."""
    
    @abstractmethod
    async def save_task(self, task: CrawlTask) -> bool:
        """Save a crawl task."""
        pass
    
    @abstractmethod
    async def get_task(self, task_id: str) -> Optional[CrawlTask]:
        """Get a crawl task by ID."""
        pass
    
    @abstractmethod
    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update a crawl task."""
        pass
    
    @abstractmethod
    async def delete_task(self, task_id: str) -> bool:
        """Delete a crawl task."""
        pass
    
    @abstractmethod
    async def list_tasks(self, limit: Optional[int] = None, offset: int = 0) -> List[CrawlTask]:
        """List crawl tasks with pagination."""
        pass
    
    @abstractmethod
    async def search_tasks(self, query: Dict[str, Any], limit: Optional[int] = None) -> List[CrawlTask]:
        """Search crawl tasks by criteria."""
        pass
    
    @abstractmethod
    async def save_crawl_result(self, result: CrawlResult) -> bool:
        """Save a crawl result separately for better querying."""
        pass
    
    @abstractmethod
    async def get_crawl_result(self, task_id: str) -> Optional[CrawlResult]:
        """Get a crawl result by task ID."""
        pass
    
    @abstractmethod
    async def search_pages(self, query: Dict[str, Any], limit: Optional[int] = None) -> List[CrawledPage]:
        """Search crawled pages by criteria."""
        pass
    
    @abstractmethod
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        pass


class StorageService:
    """Unified storage service that manages different storage backends."""
    
    def __init__(self):
        self.backend: Optional[StorageBackend] = None
        self.logger = get_logger(__name__)
        self.settings = get_settings()
    
    async def initialize(self) -> None:
        """Initialize the storage backend."""
        try:
            self.backend = self._create_backend()
            self.logger.info(f"Storage service initialized with backend: {self.settings.storage_type}")
        except Exception as e:
            self.logger.error(f"Failed to initialize storage service: {e}")
            raise StorageError("initialization", str(e))
    
    def _create_backend(self) -> StorageBackend:
        """Create the appropriate storage backend based on configuration."""
        storage_type = self.settings.storage_type.lower()
        
        if storage_type == "json":
            from app.storage.json_storage import JSONFileStorage
            return JSONFileStorage(data_dir=self.settings.storage_data_dir)
        
        elif storage_type == "mongodb":
            from app.storage.mongodb_storage import MongoDBStorage
            return MongoDBStorage(
                connection_string=self.settings.mongodb_url,
                database_name=self.settings.mongodb_database
            )
        
        elif storage_type == "elasticsearch":
            from app.storage.elasticsearch_storage import ElasticsearchStorage
            return ElasticsearchStorage(
                hosts=self.settings.elasticsearch_hosts,
                cloud_id=self.settings.elasticsearch_cloud_id,
                api_key=self.settings.elasticsearch_api_key,
                username=self.settings.elasticsearch_username,
                password=self.settings.elasticsearch_password,
                index_prefix=self.settings.elasticsearch_index_prefix
            )
        
        else:
            raise ValueError(f"Unsupported storage type: {storage_type}")
    
    async def save_task(self, task: CrawlTask) -> bool:
        """Save a crawl task."""
        try:
            result = await self.backend.save_task(task)
            self.logger.debug(f"Task saved: {task.task_id}")
            return result
        except Exception as e:
            self.logger.error(f"Failed to save task {task.task_id}: {e}")
            raise StorageError("save_task", str(e), {"task_id": task.task_id})
    
    async def get_task(self, task_id: str) -> Optional[CrawlTask]:
        """Get a crawl task by ID."""
        try:
            task = await self.backend.get_task(task_id)
            if task:
                self.logger.debug(f"Task retrieved: {task_id}")
            else:
                self.logger.debug(f"Task not found: {task_id}")
            return task
        except Exception as e:
            self.logger.error(f"Failed to get task {task_id}: {e}")
            raise StorageError("get_task", str(e), {"task_id": task_id})
    
    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update a crawl task."""
        try:
            result = await self.backend.update_task(task_id, updates)
            self.logger.debug(f"Task updated: {task_id}")
            return result
        except Exception as e:
            self.logger.error(f"Failed to update task {task_id}: {e}")
            raise StorageError("update_task", str(e), {"task_id": task_id})
    
    async def delete_task(self, task_id: str) -> bool:
        """Delete a crawl task."""
        try:
            result = await self.backend.delete_task(task_id)
            self.logger.debug(f"Task deleted: {task_id}")
            return result
        except Exception as e:
            self.logger.error(f"Failed to delete task {task_id}: {e}")
            raise StorageError("delete_task", str(e), {"task_id": task_id})
    
    async def list_tasks(self, limit: Optional[int] = None, offset: int = 0) -> List[CrawlTask]:
        """List crawl tasks with pagination."""
        try:
            tasks = await self.backend.list_tasks(limit, offset)
            self.logger.debug(f"Listed {len(tasks)} tasks")
            return tasks
        except Exception as e:
            self.logger.error(f"Failed to list tasks: {e}")
            raise StorageError("list_tasks", str(e))
    
    async def search_tasks(self, query: Dict[str, Any], limit: Optional[int] = None) -> List[CrawlTask]:
        """Search crawl tasks by criteria."""
        try:
            tasks = await self.backend.search_tasks(query, limit)
            self.logger.debug(f"Found {len(tasks)} tasks matching query")
            return tasks
        except Exception as e:
            self.logger.error(f"Failed to search tasks: {e}")
            raise StorageError("search_tasks", str(e), {"query": query})
    
    async def save_crawl_result(self, result: CrawlResult) -> bool:
        """Save a crawl result separately."""
        try:
            success = await self.backend.save_crawl_result(result)
            self.logger.debug(f"Crawl result saved: {result.task_id}")
            return success
        except Exception as e:
            self.logger.error(f"Failed to save crawl result {result.task_id}: {e}")
            raise StorageError("save_crawl_result", str(e), {"task_id": result.task_id})
    
    async def get_crawl_result(self, task_id: str) -> Optional[CrawlResult]:
        """Get a crawl result by task ID."""
        try:
            result = await self.backend.get_crawl_result(task_id)
            if result:
                self.logger.debug(f"Crawl result retrieved: {task_id}")
            else:
                self.logger.debug(f"Crawl result not found: {task_id}")
            return result
        except Exception as e:
            self.logger.error(f"Failed to get crawl result {task_id}: {e}")
            raise StorageError("get_crawl_result", str(e), {"task_id": task_id})
    
    async def search_pages(self, query: Dict[str, Any], limit: Optional[int] = None) -> List[CrawledPage]:
        """Search crawled pages by criteria."""
        try:
            pages = await self.backend.search_pages(query, limit)
            self.logger.debug(f"Found {len(pages)} pages matching query")
            return pages
        except Exception as e:
            self.logger.error(f"Failed to search pages: {e}")
            raise StorageError("search_pages", str(e), {"query": query})
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        try:
            stats = await self.backend.get_storage_stats()
            self.logger.debug("Storage stats retrieved")
            return stats
        except Exception as e:
            self.logger.error(f"Failed to get storage stats: {e}")
            raise StorageError("get_storage_stats", str(e))
    
    async def shutdown(self) -> None:
        """Shutdown the storage service."""
        if hasattr(self.backend, 'shutdown'):
            await self.backend.shutdown()
        self.logger.info("Storage service shutdown complete")
