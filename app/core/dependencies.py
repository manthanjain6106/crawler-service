"""
Dependency injection container for the crawler microservice.
Provides centralized dependency management and configuration.
"""

from typing import Optional, Dict, Any
from functools import lru_cache
import asyncio
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.crawler import CrawlerService
from app.services.storage import StorageService
from app.services.background_jobs import BackgroundJobService
from app.services.rate_limiter import RateLimitService


class DependencyContainer:
    """Centralized dependency injection container."""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._initialized = False
        self._logger = get_logger(__name__)
    
    async def initialize(self) -> None:
        """Initialize all services."""
        if self._initialized:
            return
        
        self._logger.info("Initializing dependency container")
        
        # Initialize core services
        self._services["settings"] = get_settings()
        self._services["logger"] = get_logger("crawler-service")
        
        # Initialize storage service
        self._services["storage"] = StorageService()
        await self._services["storage"].initialize()
        
        # Initialize rate limiter
        self._services["rate_limiter"] = RateLimitService()
        
        # Initialize background job service only if enabled
        settings = self._services["settings"]
        if settings.enable_background_jobs:
            self._services["background_jobs"] = BackgroundJobService()
            await self._services["background_jobs"].initialize()
        else:
            self._logger.info("Background jobs disabled - skipping initialization")
            self._services["background_jobs"] = None
        
        # Initialize crawler service
        self._services["crawler"] = CrawlerService(
            storage_service=self._services["storage"],
            rate_limiter=self._services["rate_limiter"]
        )
        
        self._initialized = True
        self._logger.info("Dependency container initialized successfully")
    
    async def shutdown(self) -> None:
        """Shutdown all services."""
        if not self._initialized:
            return
        
        self._logger.info("Shutting down dependency container")
        
        # Shutdown services in reverse order
        for service_name in reversed(self._services.keys()):
            if hasattr(self._services[service_name], 'shutdown'):
                await self._services[service_name].shutdown()
        
        self._services.clear()
        self._initialized = False
        self._logger.info("Dependency container shutdown complete")
    
    def get(self, service_name: str) -> Any:
        """Get a service by name."""
        if not self._initialized:
            raise RuntimeError("Dependency container not initialized")
        
        if service_name not in self._services:
            raise ValueError(f"Service '{service_name}' not found")
        
        return self._services[service_name]
    
    def get_settings(self):
        """Get application settings."""
        return self.get("settings")
    
    def get_logger(self):
        """Get application logger."""
        return self.get("logger")
    
    def get_storage_service(self) -> StorageService:
        """Get storage service."""
        return self.get("storage")
    
    def get_crawler_service(self) -> CrawlerService:
        """Get crawler service."""
        return self.get("crawler")
    
    def get_rate_limiter(self) -> RateLimitService:
        """Get rate limiter service."""
        return self.get("rate_limiter")
    
    def get_background_job_service(self) -> Optional[BackgroundJobService]:
        """Get background job service."""
        service = self.get("background_jobs")
        if service is None:
            raise RuntimeError("Background job service is not available (disabled or not initialized)")
        return service


# Global dependency container
_container: Optional[DependencyContainer] = None


def get_container() -> DependencyContainer:
    """Get the global dependency container."""
    global _container
    if _container is None:
        _container = DependencyContainer()
    return _container


async def initialize_dependencies() -> None:
    """Initialize the global dependency container."""
    container = get_container()
    await container.initialize()


async def shutdown_dependencies() -> None:
    """Shutdown the global dependency container."""
    global _container
    if _container is not None:
        await _container.shutdown()
        _container = None


# Dependency injection functions for FastAPI
def get_settings_dependency():
    """FastAPI dependency for settings."""
    return get_container().get_settings()


def get_logger_dependency():
    """FastAPI dependency for logger."""
    return get_container().get_logger()


def get_storage_service_dependency():
    """FastAPI dependency for storage service."""
    return get_container().get_storage_service()


def get_crawler_service_dependency():
    """FastAPI dependency for crawler service."""
    return get_container().get_crawler_service()


def get_rate_limiter_dependency():
    """FastAPI dependency for rate limiter."""
    return get_container().get_rate_limiter()


def get_background_job_service_dependency():
    """FastAPI dependency for background job service."""
    return get_container().get_background_job_service()
