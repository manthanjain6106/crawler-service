"""
MongoDB storage backend for the crawler service.
Provides fast access and querying for large scale deployments.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import DuplicateKeyError, OperationFailure
import json

from models import CrawlTask, CrawlResult, CrawledPage
from storage import StorageBackend

logger = logging.getLogger(__name__)


class MongoDBStorage(StorageBackend):
    """MongoDB storage backend for large scale deployments."""
    
    def __init__(self, connection_string: str = "mongodb://localhost:27017", 
                 database_name: str = "crawler_service", **kwargs):
        self.connection_string = connection_string
        self.database_name = database_name
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        
        # Collection names
        self.tasks_collection_name = "tasks"
        self.results_collection_name = "results"
        self.pages_collection_name = "pages"
        
        # Initialize connection
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize MongoDB connection."""
        try:
            self.client = AsyncIOMotorClient(self.connection_string)
            self.db = self.client[self.database_name]
            logger.info(f"Connected to MongoDB: {self.database_name}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    @property
    def tasks_collection(self) -> AsyncIOMotorCollection:
        """Get tasks collection."""
        return self.db[self.tasks_collection_name]
    
    @property
    def results_collection(self) -> AsyncIOMotorCollection:
        """Get results collection."""
        return self.db[self.results_collection_name]
    
    @property
    def pages_collection(self) -> AsyncIOMotorCollection:
        """Get pages collection."""
        return self.db[self.pages_collection_name]
    
    def _serialize_datetime(self, obj):
        """Convert datetime objects to ISO format for JSON serialization."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        return obj
    
    def _prepare_document(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare document for MongoDB storage."""
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
        """Save a crawl task to MongoDB."""
        try:
            task_data = self._prepare_document(task)
            task_data['_id'] = task.task_id  # Use task_id as document ID
            
            await self.tasks_collection.replace_one(
                {"_id": task.task_id},
                task_data,
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Error saving task {task.task_id}: {e}")
            return False
    
    async def get_task(self, task_id: str) -> Optional[CrawlTask]:
        """Get a crawl task by ID."""
        try:
            task_data = await self.tasks_collection.find_one({"_id": task_id})
            if task_data:
                # Remove MongoDB's _id field
                task_data.pop('_id', None)
                return CrawlTask(**task_data)
            return None
        except Exception as e:
            logger.error(f"Error getting task {task_id}: {e}")
            return None
    
    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update a crawl task."""
        try:
            # Prepare updates
            prepared_updates = self._prepare_document(updates)
            prepared_updates['updated_at'] = datetime.now().isoformat()
            
            result = await self.tasks_collection.update_one(
                {"_id": task_id},
                {"$set": prepared_updates}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating task {task_id}: {e}")
            return False
    
    async def delete_task(self, task_id: str) -> bool:
        """Delete a crawl task."""
        try:
            result = await self.tasks_collection.delete_one({"_id": task_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting task {task_id}: {e}")
            return False
    
    async def list_tasks(self, limit: Optional[int] = None, offset: int = 0) -> List[CrawlTask]:
        """List crawl tasks with pagination."""
        try:
            cursor = self.tasks_collection.find().sort("created_at", -1).skip(offset)
            if limit:
                cursor = cursor.limit(limit)
            
            tasks = []
            async for task_data in cursor:
                task_data.pop('_id', None)
                try:
                    task = CrawlTask(**task_data)
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
            # Build MongoDB query
            mongo_query = {}
            for field, value in query.items():
                if field == "status":
                    mongo_query["status"] = value
                elif field == "url":
                    mongo_query["request.url"] = {"$regex": value, "$options": "i"}
                elif field == "created_after":
                    mongo_query["created_at"] = {"$gte": value}
                elif field == "created_before":
                    mongo_query["created_at"] = {"$lte": value}
                else:
                    mongo_query[field] = value
            
            cursor = self.tasks_collection.find(mongo_query).sort("created_at", -1)
            if limit:
                cursor = cursor.limit(limit)
            
            tasks = []
            async for task_data in cursor:
                task_data.pop('_id', None)
                try:
                    task = CrawlTask(**task_data)
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
            result_data['_id'] = result.task_id
            
            await self.results_collection.replace_one(
                {"_id": result.task_id},
                result_data,
                upsert=True
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
            for page in result.pages:
                page_data = self._prepare_document(page)
                page_data['task_id'] = result.task_id
                page_data['_id'] = f"{result.task_id}_{page.url}"
                pages_data.append(page_data)
            
            if pages_data:
                # Use bulk operations for efficiency
                await self.pages_collection.insert_many(pages_data, ordered=False)
        except Exception as e:
            logger.warning(f"Error saving pages for result {result.task_id}: {e}")
    
    async def get_crawl_result(self, task_id: str) -> Optional[CrawlResult]:
        """Get a crawl result by task ID."""
        try:
            result_data = await self.results_collection.find_one({"_id": task_id})
            if result_data:
                result_data.pop('_id', None)
                return CrawlResult(**result_data)
            return None
        except Exception as e:
            logger.error(f"Error getting result {task_id}: {e}")
            return None
    
    async def search_pages(self, query: Dict[str, Any], limit: Optional[int] = None) -> List[CrawledPage]:
        """Search crawled pages by criteria."""
        try:
            # Build MongoDB query
            mongo_query = {}
            for field, value in query.items():
                if field == "url":
                    mongo_query["url"] = {"$regex": value, "$options": "i"}
                elif field == "title":
                    mongo_query["title"] = {"$regex": value, "$options": "i"}
                elif field == "status_code":
                    mongo_query["status_code"] = value
                elif field == "task_id":
                    mongo_query["task_id"] = value
                elif field == "crawled_after":
                    mongo_query["crawled_at"] = {"$gte": value}
                elif field == "crawled_before":
                    mongo_query["crawled_at"] = {"$lte": value}
                else:
                    mongo_query[field] = value
            
            cursor = self.pages_collection.find(mongo_query).sort("crawled_at", -1)
            if limit:
                cursor = cursor.limit(limit)
            
            pages = []
            async for page_data in cursor:
                page_data.pop('_id', None)
                page_data.pop('task_id', None)  # Remove task_id as it's not part of CrawledPage
                try:
                    page = CrawledPage(**page_data)
                    pages.append(page)
                except Exception as e:
                    logger.warning(f"Error parsing page: {e}")
                    continue
            
            return pages
        except Exception as e:
            logger.error(f"Error searching pages: {e}")
            return []
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        try:
            # Get collection stats
            tasks_count = await self.tasks_collection.count_documents({})
            results_count = await self.results_collection.count_documents({})
            pages_count = await self.pages_collection.count_documents({})
            
            # Get status breakdown
            pipeline = [
                {"$group": {"_id": "$status", "count": {"$sum": 1}}}
            ]
            status_breakdown = {}
            async for doc in self.tasks_collection.aggregate(pipeline):
                status_breakdown[doc["_id"]] = doc["count"]
            
            # Get database stats
            db_stats = await self.db.command("dbStats")
            
            return {
                "storage_type": "MongoDB",
                "database_name": self.database_name,
                "total_tasks": tasks_count,
                "total_results": results_count,
                "total_pages": pages_count,
                "status_breakdown": status_breakdown,
                "database_size_bytes": db_stats.get("dataSize", 0),
                "index_size_bytes": db_stats.get("indexSize", 0),
                "collections": {
                    "tasks": tasks_count,
                    "results": results_count,
                    "pages": pages_count
                }
            }
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {
                "storage_type": "MongoDB",
                "error": str(e)
            }
    
    async def create_indexes(self):
        """Create useful indexes for better query performance."""
        try:
            # Tasks collection indexes
            await self.tasks_collection.create_index("status")
            await self.tasks_collection.create_index("created_at")
            await self.tasks_collection.create_index("request.url")
            
            # Results collection indexes
            await self.results_collection.create_index("status")
            await self.results_collection.create_index("started_at")
            await self.results_collection.create_index("completed_at")
            
            # Pages collection indexes
            await self.pages_collection.create_index("url")
            await self.pages_collection.create_index("task_id")
            await self.pages_collection.create_index("crawled_at")
            await self.pages_collection.create_index("status_code")
            await self.pages_collection.create_index("title")
            
            logger.info("MongoDB indexes created successfully")
        except Exception as e:
            logger.warning(f"Error creating indexes: {e}")
    
    async def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
