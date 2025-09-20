"""
Main FastAPI application for the crawler microservice.
"""

import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.dependencies import initialize_dependencies, shutdown_dependencies
from app.api.v1 import crawl, health, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    configure_logging()
    logger = get_logger(__name__)
    logger.info("Starting crawler microservice")
    
    await initialize_dependencies()
    logger.info("Crawler microservice started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down crawler microservice")
    await shutdown_dependencies()
    logger.info("Crawler microservice shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    # Create FastAPI app
    app = FastAPI(
        title="Web Crawler Microservice",
        description="A scalable, production-ready microservice for web crawling and data extraction",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    # Rate limiting
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )
    
    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log all HTTP requests with structured logging."""
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Log request
        logger = get_logger("api")
        logger.info(
            "API request",
            method=request.method,
            endpoint=str(request.url.path),
            status_code=response.status_code,
            response_time=response_time,
            client_ip=request.client.host if request.client else None,
            event_type="api_request"
        )
        
        return response
    
    # Include routers
    app.include_router(crawl.router, prefix=settings.api_prefix)
    app.include_router(health.router, prefix=settings.api_prefix)
    app.include_router(admin.router, prefix=settings.api_prefix)
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "message": "Web Crawler Microservice",
            "version": "1.0.0",
            "docs": "/docs",
            "health": f"{settings.api_prefix}/health"
        }
    
    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers,
        reload=settings.debug
    )
