"""
Health check API endpoints for the crawler microservice.
"""

import time
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from app.models.crawl_models import HealthResponse
from app.core.dependencies import (
    get_settings_dependency,
    get_logger_dependency,
    get_storage_service_dependency,
    get_background_job_service_dependency,
    get_rate_limiter_dependency
)

# Create router
router = APIRouter(prefix="/health", tags=["health"])

# Store app start time
app_start_time = time.time()


@router.get("/", response_model=HealthResponse)
async def health_check(
    settings=Depends(get_settings_dependency),
    logger=Depends(get_logger_dependency),
    storage_service=Depends(get_storage_service_dependency),
    background_job_service=Depends(get_background_job_service_dependency),
    rate_limiter=Depends(get_rate_limiter_dependency)
):
    """Comprehensive health check endpoint."""
    try:
        # Check individual services
        services = {}
        
        # Check storage service
        try:
            await storage_service.get_storage_stats()
            services["storage"] = "healthy"
        except Exception as e:
            logger.warning(f"Storage service health check failed: {e}")
            services["storage"] = "unhealthy"
        
        # Check background job service
        if settings.enable_background_jobs and background_job_service is not None:
            try:
                await background_job_service.get_queue_stats()
                services["background_jobs"] = "healthy"
            except Exception as e:
                logger.warning(f"Background job service health check failed: {e}")
                services["background_jobs"] = "unhealthy"
        else:
            services["background_jobs"] = "disabled"
        
        # Check rate limiter
        try:
            rate_limiter.get_all_domain_stats()
            services["rate_limiter"] = "healthy"
        except Exception as e:
            logger.warning(f"Rate limiter health check failed: {e}")
            services["rate_limiter"] = "unhealthy"
        
        # Determine overall health
        overall_status = "healthy" if all(status == "healthy" for status in services.values()) else "degraded"
        
        return HealthResponse(
            status=overall_status,
            timestamp=datetime.now(),
            version=settings.app_version,
            uptime=time.time() - app_start_time,
            services=services
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Health check failed"
        )


@router.get("/ready")
async def readiness_check(
    storage_service=Depends(get_storage_service_dependency)
):
    """Readiness check for Kubernetes/Docker health checks."""
    try:
        # Simple check to see if storage is accessible
        await storage_service.get_storage_stats()
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )


@router.get("/live")
async def liveness_check():
    """Liveness check for Kubernetes/Docker health checks."""
    return {"status": "alive"}


@router.get("/metrics")
async def get_metrics(
    storage_service=Depends(get_storage_service_dependency),
    background_job_service=Depends(get_background_job_service_dependency),
    rate_limiter=Depends(get_rate_limiter_dependency)
):
    """Get service metrics for monitoring."""
    try:
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "uptime": time.time() - app_start_time
        }
        
        # Storage metrics
        try:
            storage_stats = await storage_service.get_storage_stats()
            metrics["storage"] = storage_stats
        except Exception as e:
            metrics["storage"] = {"error": str(e)}
        
        # Background job metrics
        if settings.enable_background_jobs and background_job_service is not None:
            try:
                job_stats = await background_job_service.get_queue_stats()
                metrics["background_jobs"] = job_stats
            except Exception as e:
                metrics["background_jobs"] = {"error": str(e)}
        else:
            metrics["background_jobs"] = {"status": "disabled"}
        
        # Rate limiter metrics
        try:
            rate_stats = rate_limiter.get_all_domain_stats()
            metrics["rate_limiter"] = rate_stats
        except Exception as e:
            metrics["rate_limiter"] = {"error": str(e)}
        
        return metrics
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}"
        )
