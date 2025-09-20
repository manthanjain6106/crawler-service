"""
Admin API endpoints for the crawler microservice.
Provides administrative functions and monitoring.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import (
    get_settings_dependency,
    get_logger_dependency,
    get_rate_limiter_dependency,
    get_crawler_service_dependency
)

# Create router
router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/rate-limits")
async def get_rate_limits(
    settings=Depends(get_settings_dependency),
    crawler_service=Depends(get_crawler_service_dependency)
):
    """Get current rate limiting configuration and statistics."""
    try:
        rate_stats = crawler_service.get_rate_limiting_stats()
        
        return {
            "api_rate_limit": f"{settings.rate_limit_per_minute}/minute",
            "per_domain_rate_limiting": {
                "enabled": settings.enable_per_domain_rate_limiting,
                "default_limit": settings.default_domain_rate_limit,
                "window_size": settings.domain_rate_limit_window,
                "domain_specific_limits": settings.domain_specific_limits
            },
            "current_stats": rate_stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/storage/stats")
async def get_storage_stats():
    """Get storage statistics - storage is disabled."""
    return {
        "status": "disabled",
        "message": "Data storage is disabled - no data is persisted"
    }


# Note: Background job endpoints removed since we don't use background jobs anymore
# All crawling is done synchronously and results are returned directly


@router.get("/rate-limiter/stats")
async def get_rate_limiter_stats(
    rate_limiter=Depends(get_rate_limiter_dependency)
):
    """Get detailed rate limiter statistics."""
    try:
        stats = rate_limiter.get_all_domain_stats()
        return {
            "enabled": rate_limiter.enabled,
            "default_limit": rate_limiter.default_limit,
            "window_size": rate_limiter.window_size,
            "domain_stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rate-limiter/domain/{domain}/limit")
async def set_domain_rate_limit(
    domain: str,
    limit: int,
    rate_limiter=Depends(get_rate_limiter_dependency)
):
    """Set a custom rate limit for a specific domain."""
    try:
        if limit <= 0:
            raise HTTPException(status_code=400, detail="Limit must be positive")
        
        rate_limiter.set_domain_limit(domain, limit)
        return {
            "message": f"Rate limit set for domain {domain}",
            "domain": domain,
            "limit": limit
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/rate-limiter/domain/{domain}/limit")
async def remove_domain_rate_limit(
    domain: str,
    rate_limiter=Depends(get_rate_limiter_dependency)
):
    """Remove custom rate limit for a domain (revert to default)."""
    try:
        rate_limiter.remove_domain_limit(domain)
        return {
            "message": f"Custom rate limit removed for domain {domain}",
            "domain": domain
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_crawling_stats(
    settings=Depends(get_settings_dependency),
    crawler_service=Depends(get_crawler_service_dependency),
    rate_limiter=Depends(get_rate_limiter_dependency)
):
    """Get crawling statistics and service metrics."""
    try:
        # Get rate limiter stats
        rate_stats = crawler_service.get_rate_limiting_stats()
        
        # Get retry statistics
        retry_stats = crawler_service.get_retry_stats()
        
        # Calculate uptime (using app start time from health module)
        import time
        from app.api.v1.health import app_start_time
        uptime = time.time() - app_start_time
        
        return {
            "service_info": {
                "name": settings.app_name,
                "version": settings.app_version,
                "environment": settings.environment,
                "uptime_seconds": uptime
            },
            "crawling_stats": {
                "max_concurrent_requests": settings.max_concurrent_requests,
                "default_timeout": settings.default_timeout,
                "max_depth": settings.max_depth,
                "retry_configuration": {
                    "max_retries": settings.max_retries,
                    "retry_delay_base": settings.retry_delay_base,
                    "retry_delay_max": settings.retry_delay_max,
                    "retry_backoff_multiplier": settings.retry_backoff_multiplier
                }
            },
            "rate_limiting": {
                "api_rate_limit": f"{settings.rate_limit_per_minute}/minute",
                "per_domain_enabled": settings.enable_per_domain_rate_limiting,
                "default_domain_limit": settings.default_domain_rate_limit,
                "domain_specific_limits": settings.domain_specific_limits,
                "current_stats": rate_stats
            },
            "retry_statistics": retry_stats,
            "storage": {
                "status": "disabled",
                "message": "No data persistence - results returned directly"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")