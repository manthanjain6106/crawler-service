"""
Demo script showcasing the storage layer capabilities.
Demonstrates JSON, MongoDB, and Elasticsearch storage backends.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import List

from storage import StorageManager, create_storage_backend
from models import CrawlRequest, CrawlTask, CrawlStatus, CrawledPage, CrawlResult
from storage_migration import StorageMigrator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_json_storage():
    """Demonstrate JSON file storage capabilities."""
    print("\n=== JSON File Storage Demo ===")
    
    # Create JSON storage backend
    storage_backend = create_storage_backend("json", data_dir="demo_data")
    storage_manager = StorageManager(storage_backend)
    
    # Create sample data
    sample_request = CrawlRequest(
        url="https://example.com",
        max_depth=2,
        follow_links=True,
        extract_text=True,
        extract_images=True
    )
    
    sample_task = CrawlTask(
        task_id="demo_task_1",
        request=sample_request,
        status=CrawlStatus.COMPLETED,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    sample_page = CrawledPage(
        url="https://example.com",
        title="Example Domain",
        text_content="This domain is for use in illustrative examples in documents.",
        status_code=200,
        response_time=0.5,
        crawled_at=datetime.now(),
        depth=0
    )
    
    sample_result = CrawlResult(
        task_id="demo_task_1",
        status=CrawlStatus.COMPLETED,
        total_pages=1,
        pages=[sample_page],
        started_at=datetime.now(),
        completed_at=datetime.now(),
        duration=1.0
    )
    
    # Save data
    await storage_manager.save_task(sample_task)
    await storage_manager.save_crawl_result(sample_result)
    
    # Retrieve data
    retrieved_task = await storage_manager.get_task("demo_task_1")
    retrieved_result = await storage_manager.get_crawl_result("demo_task_1")
    
    print(f"Retrieved task: {retrieved_task.task_id if retrieved_task else 'None'}")
    print(f"Retrieved result: {retrieved_result.task_id if retrieved_result else 'None'}")
    
    # Search data
    tasks = await storage_manager.search_tasks({"status": "completed"})
    pages = await storage_manager.search_pages({"title": "Example"})
    
    print(f"Found {len(tasks)} completed tasks")
    print(f"Found {len(pages)} pages with 'Example' in title")
    
    # Get storage stats
    stats = await storage_manager.get_storage_stats()
    print(f"Storage stats: {json.dumps(stats, indent=2, default=str)}")


async def demo_mongodb_storage():
    """Demonstrate MongoDB storage capabilities."""
    print("\n=== MongoDB Storage Demo ===")
    
    try:
        # Create MongoDB storage backend
        storage_backend = create_storage_backend(
            "mongodb", 
            connection_string="mongodb://localhost:27017",
            database_name="crawler_demo"
        )
        storage_manager = StorageManager(storage_backend)
        
        # Create indexes for better performance
        if hasattr(storage_backend, 'create_indexes'):
            await storage_backend.create_indexes()
        
        # Create sample data
        sample_request = CrawlRequest(
            url="https://httpbin.org",
            max_depth=1,
            follow_links=True,
            extract_text=True
        )
        
        sample_task = CrawlTask(
            task_id="mongodb_demo_task",
            request=sample_request,
            status=CrawlStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        sample_page = CrawledPage(
            url="https://httpbin.org",
            title="httpbin.org",
            text_content="A simple HTTP Request & Response Service",
            status_code=200,
            response_time=0.3,
            crawled_at=datetime.now(),
            depth=0
        )
        
        sample_result = CrawlResult(
            task_id="mongodb_demo_task",
            status=CrawlStatus.COMPLETED,
            total_pages=1,
            pages=[sample_page],
            started_at=datetime.now(),
            completed_at=datetime.now(),
            duration=0.5
        )
        
        # Save data
        await storage_manager.save_task(sample_task)
        await storage_manager.save_crawl_result(sample_result)
        
        # Demonstrate advanced search
        tasks = await storage_manager.search_tasks({
            "status": "completed",
            "url": "httpbin"
        })
        
        pages = await storage_manager.search_pages({
            "title": "httpbin",
            "status_code": 200
        })
        
        print(f"Found {len(tasks)} tasks matching search criteria")
        print(f"Found {len(pages)} pages matching search criteria")
        
        # Get storage stats
        stats = await storage_manager.get_storage_stats()
        print(f"MongoDB storage stats: {json.dumps(stats, indent=2, default=str)}")
        
        # Close connection
        if hasattr(storage_backend, 'close'):
            await storage_backend.close()
            
    except Exception as e:
        print(f"MongoDB demo failed (MongoDB not running?): {e}")


async def demo_elasticsearch_storage():
    """Demonstrate Elasticsearch storage capabilities."""
    print("\n=== Elasticsearch Storage Demo ===")
    
    try:
        # Create Elasticsearch storage backend
        storage_backend = create_storage_backend(
            "elasticsearch",
            hosts=["localhost:9200"],
            index_prefix="crawler_demo"
        )
        storage_manager = StorageManager(storage_backend)
        
        # Create indexes with proper mappings
        if hasattr(storage_backend, 'create_indexes'):
            await storage_backend.create_indexes()
        
        # Create sample data
        sample_request = CrawlRequest(
            url="https://jsonplaceholder.typicode.com",
            max_depth=1,
            follow_links=True,
            extract_text=True
        )
        
        sample_task = CrawlTask(
            task_id="elasticsearch_demo_task",
            request=sample_request,
            status=CrawlStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        sample_page = CrawledPage(
            url="https://jsonplaceholder.typicode.com",
            title="JSONPlaceholder",
            text_content="Fake Online REST API for Testing and Prototyping",
            status_code=200,
            response_time=0.4,
            crawled_at=datetime.now(),
            depth=0
        )
        
        sample_result = CrawlResult(
            task_id="elasticsearch_demo_task",
            status=CrawlStatus.COMPLETED,
            total_pages=1,
            pages=[sample_page],
            started_at=datetime.now(),
            completed_at=datetime.now(),
            duration=0.6
        )
        
        # Save data
        await storage_manager.save_task(sample_task)
        await storage_manager.save_crawl_result(sample_result)
        
        # Demonstrate full-text search
        if hasattr(storage_backend, 'search_pages_fulltext'):
            pages = await storage_backend.search_pages_fulltext("REST API")
            print(f"Found {len(pages)} pages with full-text search")
        
        # Demonstrate advanced search
        tasks = await storage_manager.search_tasks({
            "status": "completed",
            "url": "jsonplaceholder"
        })
        
        pages = await storage_manager.search_pages({
            "title": "JSONPlaceholder",
            "status_code": 200
        })
        
        print(f"Found {len(tasks)} tasks matching search criteria")
        print(f"Found {len(pages)} pages matching search criteria")
        
        # Get storage stats
        stats = await storage_manager.get_storage_stats()
        print(f"Elasticsearch storage stats: {json.dumps(stats, indent=2, default=str)}")
        
        # Close connection
        if hasattr(storage_backend, 'close'):
            await storage_backend.close()
            
    except Exception as e:
        print(f"Elasticsearch demo failed (Elasticsearch not running?): {e}")


async def demo_migration():
    """Demonstrate data migration between storage backends."""
    print("\n=== Storage Migration Demo ===")
    
    try:
        # Create source (JSON) and target (MongoDB) backends
        source_backend = create_storage_backend("json", data_dir="demo_data")
        target_backend = create_storage_backend(
            "mongodb",
            connection_string="mongodb://localhost:27017",
            database_name="crawler_migrated"
        )
        
        source_manager = StorageManager(source_backend)
        target_manager = StorageManager(target_backend)
        
        # Create migrator
        migrator = StorageMigrator(source_manager, target_manager)
        
        # Perform migration
        migration_stats = await migrator.migrate_all_data()
        print(f"Migration completed: {json.dumps(migration_stats, indent=2, default=str)}")
        
        # Verify migration
        verification_stats = await migrator.verify_migration()
        print(f"Verification results: {json.dumps(verification_stats, indent=2, default=str)}")
        
        # Close connections
        if hasattr(target_backend, 'close'):
            await target_backend.close()
            
    except Exception as e:
        print(f"Migration demo failed: {e}")


async def demo_performance_comparison():
    """Compare performance between different storage backends."""
    print("\n=== Performance Comparison Demo ===")
    
    # Create sample data
    sample_tasks = []
    for i in range(100):
        task = CrawlTask(
            task_id=f"perf_task_{i}",
            request=CrawlRequest(url=f"https://example{i}.com"),
            status=CrawlStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        sample_tasks.append(task)
    
    # Test JSON storage performance
    print("Testing JSON storage performance...")
    json_backend = create_storage_backend("json", data_dir="perf_demo_data")
    json_manager = StorageManager(json_backend)
    
    start_time = datetime.now()
    for task in sample_tasks:
        await json_manager.save_task(task)
    json_save_time = (datetime.now() - start_time).total_seconds()
    
    start_time = datetime.now()
    tasks = await json_manager.list_tasks(limit=100)
    json_read_time = (datetime.now() - start_time).total_seconds()
    
    print(f"JSON - Save 100 tasks: {json_save_time:.3f}s")
    print(f"JSON - Read 100 tasks: {json_read_time:.3f}s")
    
    # Test MongoDB performance (if available)
    try:
        print("Testing MongoDB storage performance...")
        mongodb_backend = create_storage_backend(
            "mongodb",
            connection_string="mongodb://localhost:27017",
            database_name="crawler_perf"
        )
        mongodb_manager = StorageManager(mongodb_backend)
        
        start_time = datetime.now()
        for task in sample_tasks:
            await mongodb_manager.save_task(task)
        mongodb_save_time = (datetime.now() - start_time).total_seconds()
        
        start_time = datetime.now()
        tasks = await mongodb_manager.list_tasks(limit=100)
        mongodb_read_time = (datetime.now() - start_time).total_seconds()
        
        print(f"MongoDB - Save 100 tasks: {mongodb_save_time:.3f}s")
        print(f"MongoDB - Read 100 tasks: {mongodb_read_time:.3f}s")
        
        if hasattr(mongodb_backend, 'close'):
            await mongodb_backend.close()
            
    except Exception as e:
        print(f"MongoDB performance test failed: {e}")


async def main():
    """Run all storage demos."""
    print("Storage Layer Demo - Comprehensive Testing")
    print("=" * 50)
    
    # Run individual demos
    await demo_json_storage()
    await demo_mongodb_storage()
    await demo_elasticsearch_storage()
    await demo_migration()
    await demo_performance_comparison()
    
    print("\n=== Demo Complete ===")
    print("All storage backends have been demonstrated!")
    print("\nKey Features Demonstrated:")
    print("- JSON file storage for small scale deployments")
    print("- MongoDB storage for large scale with fast querying")
    print("- Elasticsearch storage for advanced search and analytics")
    print("- Data migration between storage backends")
    print("- Performance comparison between backends")
    print("- Search and filtering capabilities")
    print("- Storage statistics and monitoring")


if __name__ == "__main__":
    asyncio.run(main())
