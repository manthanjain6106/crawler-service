"""
Admin API endpoints for the crawler microservice.
Provides administrative functions and monitoring.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import (
    get_settings_dependency,
    get_logger_dependency,
    get_storage_service_dependency,
    get_background_job_service_dependency,
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
async def get_storage_stats(
    storage_service=Depends(get_storage_service_dependency)
):
    """Get storage statistics."""
    try:
        stats = await storage_service.get_storage_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/queue/stats")
async def get_job_queue_stats(
    settings=Depends(get_settings_dependency),
    background_job_service=Depends(get_background_job_service_dependency)
):
    """Get background job queue statistics."""
    try:
        if not settings.enable_background_jobs or background_job_service is None:
            return {"status": "disabled", "message": "Background jobs are disabled"}
        
        stats = await background_job_service.get_queue_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}/status")
async def get_job_status(
    job_id: str,
    settings=Depends(get_settings_dependency),
    background_job_service=Depends(get_background_job_service_dependency)
):
    """Get the status of a background job."""
    try:
        if not settings.enable_background_jobs or background_job_service is None:
            raise HTTPException(status_code=400, detail="Background jobs are disabled")
        
        status = await background_job_service.get_job_status(job_id)
        if not status:
            raise HTTPException(status_code=404, detail="Job not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    settings=Depends(get_settings_dependency),
    background_job_service=Depends(get_background_job_service_dependency)
):
    """Cancel a background job."""
    try:
        if not settings.enable_background_jobs or background_job_service is None:
            raise HTTPException(status_code=400, detail="Background jobs are disabled")
        
        success = await background_job_service.cancel_job(job_id)
        if success:
            return {"message": "Job cancelled successfully"}
        else:
            raise HTTPException(status_code=400, detail="Job could not be cancelled")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/cleanup")
async def cleanup_old_jobs(
    max_age_hours: int = 24,
    settings=Depends(get_settings_dependency),
    background_job_service=Depends(get_background_job_service_dependency)
):
    """Clean up old completed and failed jobs."""
    try:
        if not settings.enable_background_jobs or background_job_service is None:
            raise HTTPException(status_code=400, detail="Background jobs are disabled")
        
        cleaned_count = await background_job_service.cleanup_old_jobs(max_age_hours)
        return {
            "message": f"Cleaned up {cleaned_count} old jobs",
            "cleaned_count": cleaned_count,
            "max_age_hours": max_age_hours
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
