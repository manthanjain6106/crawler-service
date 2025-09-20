"""
JSON file-based storage backend for the crawler microservice.
Suitable for small-scale deployments and development.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from app.models.crawl_models import CrawlTask, CrawlResult, CrawledPage
from app.core.logging import get_logger


class JSONFileStorage:
    """JSON file-based storage for small scale deployments."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.tasks_file = self.data_dir / "tasks.json"
        self.results_file = self.data_dir / "results.json"
        self.pages_file = self.data_dir / "pages.json"
        self.logger = get_logger(__name__)
        
        # Ensure data directory exists
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize files if they don't exist
        self._initialize_files()
    
    def _initialize_files(self):
        """Initialize JSON files if they don't exist."""
        for file_path in [self.tasks_file, self.results_file, self.pages_file]:
            if not file_path.exists():
                with open(file_path, 'w') as f:
                    json.dump({}, f)
    
    def _load_json(self, file_path: Path) -> Dict[str, Any]:
        """Load JSON data from file."""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.warning(f"Error loading {file_path}: {e}")
            return {}
    
    def _save_json(self, file_path: Path, data: Dict[str, Any]) -> bool:
        """Save JSON data to file."""
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            return True
        except Exception as e:
            self.logger.error(f"Error saving {file_path}: {e}")
            return False
    
    async def save_task(self, task: CrawlTask) -> bool:
        """Save a crawl task to JSON file."""
        tasks = self._load_json(self.tasks_file)
        tasks[task.task_id] = task.dict()
        return self._save_json(self.tasks_file, tasks)
    
    async def get_task(self, task_id: str) -> Optional[CrawlTask]:
        """Get a crawl task by ID."""
        tasks = self._load_json(self.tasks_file)
        task_data = tasks.get(task_id)
        if task_data:
            return CrawlTask(**task_data)
        return None
    
    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update a crawl task."""
        tasks = self._load_json(self.tasks_file)
        if task_id in tasks:
            tasks[task_id].update(updates)
            return self._save_json(self.tasks_file, tasks)
        return False
    
    async def delete_task(self, task_id: str) -> bool:
        """Delete a crawl task."""
        tasks = self._load_json(self.tasks_file)
        if task_id in tasks:
            del tasks[task_id]
            return self._save_json(self.tasks_file, tasks)
        return False
    
    async def list_tasks(self, limit: Optional[int] = None, offset: int = 0) -> List[CrawlTask]:
        """List crawl tasks with pagination."""
        tasks = self._load_json(self.tasks_file)
        task_list = []
        
        for task_id, task_data in tasks.items():
            try:
                task = CrawlTask(**task_data)
                task_list.append(task)
            except Exception as e:
                self.logger.warning(f"Error parsing task {task_id}: {e}")
                continue
        
        # Sort by creation time (newest first)
        task_list.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply pagination
        start = offset
        end = offset + limit if limit else len(task_list)
        return task_list[start:end]
    
    async def search_tasks(self, query: Dict[str, Any], limit: Optional[int] = None) -> List[CrawlTask]:
        """Search crawl tasks by criteria."""
        tasks = self._load_json(self.tasks_file)
        results = []
        
        for task_id, task_data in tasks.items():
            try:
                task = CrawlTask(**task_data)
                
                # Simple field matching
                matches = True
                for field, value in query.items():
                    if hasattr(task, field):
                        task_value = getattr(task, field)
                        if isinstance(value, str) and isinstance(task_value, str):
                            if value.lower() not in task_value.lower():
                                matches = False
                                break
                        elif task_value != value:
                            matches = False
                            break
                    else:
                        matches = False
                        break
                
                if matches:
                    results.append(task)
                    
            except Exception as e:
                self.logger.warning(f"Error parsing task {task_id}: {e}")
                continue
        
        # Sort by creation time (newest first)
        results.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply limit
        if limit:
            results = results[:limit]
        
        return results
    
    async def save_crawl_result(self, result: CrawlResult) -> bool:
        """Save a crawl result separately."""
        results = self._load_json(self.results_file)
        results[result.task_id] = result.dict()
        return self._save_json(self.results_file, results)
    
    async def get_crawl_result(self, task_id: str) -> Optional[CrawlResult]:
        """Get a crawl result by task ID."""
        results = self._load_json(self.results_file)
        result_data = results.get(task_id)
        if result_data:
            return CrawlResult(**result_data)
        return None
    
    async def search_pages(self, query: Dict[str, Any], limit: Optional[int] = None) -> List[CrawledPage]:
        """Search crawled pages by criteria."""
        results = self._load_json(self.results_file)
        pages = []
        
        for task_id, result_data in results.items():
            try:
                result = CrawlResult(**result_data)
                for page_data in result.pages:
                    try:
                        page = CrawledPage(**page_data)
                        
                        # Simple field matching
                        matches = True
                        for field, value in query.items():
                            if hasattr(page, field):
                                page_value = getattr(page, field)
                                if isinstance(value, str) and isinstance(page_value, str):
                                    if value.lower() not in page_value.lower():
                                        matches = False
                                        break
                                elif page_value != value:
                                    matches = False
                                    break
                            else:
                                matches = False
                                break
                        
                        if matches:
                            pages.append(page)
                            
                    except Exception as e:
                        self.logger.warning(f"Error parsing page: {e}")
                        continue
                        
            except Exception as e:
                self.logger.warning(f"Error parsing result {task_id}: {e}")
                continue
        
        # Sort by crawl time (newest first)
        pages.sort(key=lambda x: x.crawled_at, reverse=True)
        
        # Apply limit
        if limit:
            pages = pages[:limit]
        
        return pages
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        tasks = self._load_json(self.tasks_file)
        results = self._load_json(self.results_file)
        
        # Count tasks by status
        status_counts = {}
        for task_data in tasks.values():
            status = task_data.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Count total pages
        total_pages = 0
        for result_data in results.values():
            pages = result_data.get('pages', [])
            total_pages += len(pages)
        
        return {
            "storage_type": "JSON File",
            "total_tasks": len(tasks),
            "total_results": len(results),
            "total_pages": total_pages,
            "status_breakdown": status_counts,
            "data_directory": str(self.data_dir),
            "file_sizes": {
                "tasks_file": self.tasks_file.stat().st_size if self.tasks_file.exists() else 0,
                "results_file": self.results_file.stat().st_size if self.results_file.exists() else 0,
                "pages_file": self.pages_file.stat().st_size if self.pages_file.exists() else 0
            }
        }
    
    async def shutdown(self) -> None:
        """Shutdown the storage backend."""
        self.logger.info("JSON file storage shutdown complete")
