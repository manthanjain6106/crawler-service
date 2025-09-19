"""
Storage migration utilities for the crawler service.
Provides tools to migrate data between different storage backends.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime

from storage import StorageManager, create_storage_backend
from models import CrawlTask, CrawlResult, CrawledPage

logger = logging.getLogger(__name__)


class StorageMigrator:
    """Utility class for migrating data between storage backends."""
    
    def __init__(self, source_backend: StorageManager, target_backend: StorageManager):
        self.source = source_backend
        self.target = target_backend
    
    async def migrate_all_data(self, batch_size: int = 100) -> Dict[str, Any]:
        """Migrate all data from source to target backend."""
        logger.info("Starting data migration...")
        
        migration_stats = {
            "tasks_migrated": 0,
            "results_migrated": 0,
            "pages_migrated": 0,
            "errors": [],
            "started_at": datetime.now().isoformat(),
            "completed_at": None
        }
        
        try:
            # Migrate tasks
            logger.info("Migrating tasks...")
            tasks = await self.source.list_tasks(limit=None)
            for i in range(0, len(tasks), batch_size):
                batch = tasks[i:i + batch_size]
                for task in batch:
                    try:
                        await self.target.save_task(task)
                        migration_stats["tasks_migrated"] += 1
                    except Exception as e:
                        error_msg = f"Error migrating task {task.task_id}: {str(e)}"
                        logger.error(error_msg)
                        migration_stats["errors"].append(error_msg)
            
            # Migrate results
            logger.info("Migrating results...")
            results = await self.source.list_tasks(limit=None)
            for task in results:
                if task.result:
                    try:
                        await self.target.save_crawl_result(task.result)
                        migration_stats["results_migrated"] += 1
                    except Exception as e:
                        error_msg = f"Error migrating result for task {task.task_id}: {str(e)}"
                        logger.error(error_msg)
                        migration_stats["errors"].append(error_msg)
            
            # Migrate pages (if they exist separately)
            logger.info("Migrating pages...")
            try:
                # Try to get pages from source (this might not be available for all backends)
                pages = await self.source.search_pages({}, limit=None)
                for i in range(0, len(pages), batch_size):
                    batch = pages[i:i + batch_size]
                    for page in batch:
                        try:
                            # Create a temporary result with just this page for migration
                            temp_result = CrawlResult(
                                task_id=f"migration_{page.url}",
                                status="completed",
                                pages=[page],
                                started_at=datetime.now(),
                                completed_at=datetime.now()
                            )
                            await self.target.save_crawl_result(temp_result)
                            migration_stats["pages_migrated"] += 1
                        except Exception as e:
                            error_msg = f"Error migrating page {page.url}: {str(e)}"
                            logger.error(error_msg)
                            migration_stats["errors"].append(error_msg)
            except Exception as e:
                logger.warning(f"Could not migrate pages separately: {e}")
            
            migration_stats["completed_at"] = datetime.now().isoformat()
            logger.info(f"Migration completed. Stats: {migration_stats}")
            
        except Exception as e:
            error_msg = f"Migration failed: {str(e)}"
            logger.error(error_msg)
            migration_stats["errors"].append(error_msg)
            migration_stats["completed_at"] = datetime.now().isoformat()
        
        return migration_stats
    
    async def verify_migration(self) -> Dict[str, Any]:
        """Verify that migration was successful by comparing counts."""
        logger.info("Verifying migration...")
        
        verification_stats = {
            "source_tasks": 0,
            "target_tasks": 0,
            "source_results": 0,
            "target_results": 0,
            "verification_passed": False
        }
        
        try:
            # Count tasks
            source_tasks = await self.source.list_tasks(limit=None)
            target_tasks = await self.target.list_tasks(limit=None)
            
            verification_stats["source_tasks"] = len(source_tasks)
            verification_stats["target_tasks"] = len(target_tasks)
            
            # Count results
            source_results = 0
            target_results = 0
            
            for task in source_tasks:
                if task.result:
                    source_results += 1
            
            for task in target_tasks:
                result = await self.target.get_crawl_result(task.task_id)
                if result:
                    target_results += 1
            
            verification_stats["source_results"] = source_results
            verification_stats["target_results"] = target_results
            
            # Check if migration was successful
            verification_stats["verification_passed"] = (
                verification_stats["source_tasks"] == verification_stats["target_tasks"] and
                verification_stats["source_results"] == verification_stats["target_results"]
            )
            
            logger.info(f"Verification completed: {verification_stats}")
            
        except Exception as e:
            logger.error(f"Verification failed: {str(e)}")
            verification_stats["error"] = str(e)
        
        return verification_stats


async def migrate_from_json_to_mongodb(json_data_dir: str, mongodb_url: str, database_name: str):
    """Convenience function to migrate from JSON to MongoDB."""
    logger.info(f"Migrating from JSON ({json_data_dir}) to MongoDB ({mongodb_url})")
    
    # Create source and target backends
    source_backend = create_storage_backend("json", data_dir=json_data_dir)
    target_backend = create_storage_backend("mongodb", connection_string=mongodb_url, database_name=database_name)
    
    source_manager = StorageManager(source_backend)
    target_manager = StorageManager(target_backend)
    
    # Create migrator
    migrator = StorageMigrator(source_manager, target_manager)
    
    # Perform migration
    migration_stats = await migrator.migrate_all_data()
    
    # Verify migration
    verification_stats = await migrator.verify_migration()
    
    return {
        "migration": migration_stats,
        "verification": verification_stats
    }


async def migrate_from_json_to_elasticsearch(json_data_dir: str, elasticsearch_hosts: List[str], index_prefix: str):
    """Convenience function to migrate from JSON to Elasticsearch."""
    logger.info(f"Migrating from JSON ({json_data_dir}) to Elasticsearch ({elasticsearch_hosts})")
    
    # Create source and target backends
    source_backend = create_storage_backend("json", data_dir=json_data_dir)
    target_backend = create_storage_backend("elasticsearch", hosts=elasticsearch_hosts, index_prefix=index_prefix)
    
    source_manager = StorageManager(source_backend)
    target_manager = StorageManager(target_backend)
    
    # Create migrator
    migrator = StorageMigrator(source_manager, target_manager)
    
    # Perform migration
    migration_stats = await migrator.migrate_all_data()
    
    # Verify migration
    verification_stats = await migrator.verify_migration()
    
    return {
        "migration": migration_stats,
        "verification": verification_stats
    }


async def migrate_from_mongodb_to_elasticsearch(mongodb_url: str, database_name: str, 
                                               elasticsearch_hosts: List[str], index_prefix: str):
    """Convenience function to migrate from MongoDB to Elasticsearch."""
    logger.info(f"Migrating from MongoDB ({mongodb_url}) to Elasticsearch ({elasticsearch_hosts})")
    
    # Create source and target backends
    source_backend = create_storage_backend("mongodb", connection_string=mongodb_url, database_name=database_name)
    target_backend = create_storage_backend("elasticsearch", hosts=elasticsearch_hosts, index_prefix=index_prefix)
    
    source_manager = StorageManager(source_backend)
    target_manager = StorageManager(target_backend)
    
    # Create migrator
    migrator = StorageMigrator(source_manager, target_manager)
    
    # Perform migration
    migration_stats = await migrator.migrate_all_data()
    
    # Verify migration
    verification_stats = await migrator.verify_migration()
    
    return {
        "migration": migration_stats,
        "verification": verification_stats
    }


def export_json_data(data_dir: str, output_file: str):
    """Export all data from JSON storage to a single file."""
    logger.info(f"Exporting JSON data from {data_dir} to {output_file}")
    
    data_dir = Path(data_dir)
    tasks_file = data_dir / "tasks.json"
    results_file = data_dir / "results.json"
    
    export_data = {
        "exported_at": datetime.now().isoformat(),
        "tasks": {},
        "results": {}
    }
    
    # Load tasks
    if tasks_file.exists():
        with open(tasks_file, 'r') as f:
            export_data["tasks"] = json.load(f)
    
    # Load results
    if results_file.exists():
        with open(results_file, 'r') as f:
            export_data["results"] = json.load(f)
    
    # Save export
    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2, default=str)
    
    logger.info(f"Export completed: {output_file}")


def import_json_data(input_file: str, data_dir: str):
    """Import data from a JSON export file."""
    logger.info(f"Importing JSON data from {input_file} to {data_dir}")
    
    data_dir = Path(data_dir)
    data_dir.mkdir(exist_ok=True)
    
    with open(input_file, 'r') as f:
        import_data = json.load(f)
    
    # Save tasks
    tasks_file = data_dir / "tasks.json"
    with open(tasks_file, 'w') as f:
        json.dump(import_data.get("tasks", {}), f, indent=2, default=str)
    
    # Save results
    results_file = data_dir / "results.json"
    with open(results_file, 'w') as f:
        json.dump(import_data.get("results", {}), f, indent=2, default=str)
    
    logger.info(f"Import completed: {data_dir}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Storage migration utilities")
    parser.add_argument("--source", required=True, help="Source storage type (json, mongodb, elasticsearch)")
    parser.add_argument("--target", required=True, help="Target storage type (json, mongodb, elasticsearch)")
    parser.add_argument("--source-config", help="Source configuration (JSON string)")
    parser.add_argument("--target-config", help="Target configuration (JSON string)")
    parser.add_argument("--export", help="Export JSON data to file")
    parser.add_argument("--import", dest="import_file", help="Import JSON data from file")
    
    args = parser.parse_args()
    
    if args.export:
        export_json_data("data", args.export)
    elif args.import_file:
        import_json_data(args.import_file, "data")
    else:
        print("Migration functionality requires configuration. Use the Python API directly.")
