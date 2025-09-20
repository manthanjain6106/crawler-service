#!/usr/bin/env python3
"""
Startup script for the crawler microservice.
Handles different deployment modes and configurations.
"""

import os
import sys
import argparse
import asyncio
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger


def start_api_server():
    """Start the FastAPI server."""
    import uvicorn
    
    settings = get_settings()
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers if not settings.debug else 1,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )


def start_worker():
    """Start the background job worker."""
    from app.services.background_jobs import start_worker
    
    asyncio.run(start_worker())


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Crawler Microservice")
    parser.add_argument(
        "mode",
        choices=["api", "worker"],
        help="Mode to run: 'api' for the API server, 'worker' for background job worker"
    )
    parser.add_argument(
        "--config",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Override log level"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    configure_logging()
    logger = get_logger(__name__)
    
    # Override log level if specified
    if args.log_level:
        os.environ["LOG_LEVEL"] = args.log_level
    
    logger.info(f"Starting crawler microservice in {args.mode} mode")
    
    try:
        if args.mode == "api":
            start_api_server()
        elif args.mode == "worker":
            start_worker()
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Failed to start service: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
