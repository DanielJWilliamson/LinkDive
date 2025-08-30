"""
Health check endpoints for monitoring and system status.
"""
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, status
from pydantic import BaseModel

from config.settings import settings

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime
    version: str
    environment: str
    services: Dict[str, str]


class DetailedHealthResponse(BaseModel):
    """Detailed health check response model."""
    status: str
    timestamp: datetime
    version: str
    environment: str
    uptime: str
    services: Dict[str, Dict[str, Any]]
    system_info: Dict[str, Any]


@router.get(
    "/",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Basic health check",
    description="Returns basic application health status"
)
async def health_check() -> HealthResponse:
    """Basic health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.app_version,
        environment="development" if settings.debug else "production",
        services={
            "api": "healthy",
            "database": "healthy",  # TODO: Add actual database check
            "redis": "healthy",     # TODO: Add actual Redis check
        }
    )


@router.get(
    "/detailed",
    response_model=DetailedHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Detailed health check",
    description="Returns detailed application health status with system information"
)
async def detailed_health_check() -> DetailedHealthResponse:
    """Detailed health check endpoint with system information."""
    import psutil
    import platform
    
    # Get system information
    system_info = {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
    }
    
    # TODO: Add actual service health checks
    services = {
        "api": {
            "status": "healthy",
            "response_time_ms": 5,
        },
        "database": {
            "status": "healthy",
            "connection_pool": "active",
            "response_time_ms": 10,
        },
        "redis": {
            "status": "healthy",
            "connection_count": 1,
            "response_time_ms": 2,
        },
        "external_apis": {
            "ahrefs": "healthy",
            "dataforseo": "healthy",
        }
    }
    
    return DetailedHealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.app_version,
        environment="development" if settings.debug else "production",
        uptime="0 days, 0 hours, 0 minutes",  # TODO: Calculate actual uptime
        services=services,
        system_info=system_info
    )


@router.get(
    "/readiness",
    status_code=status.HTTP_200_OK,
    summary="Readiness probe",
    description="Kubernetes readiness probe endpoint"
)
async def readiness_check() -> Dict[str, str]:
    """Readiness probe for Kubernetes deployments."""
    # TODO: Add actual readiness checks
    # - Database connectivity
    # - External API availability
    # - Required services status
    
    return {"status": "ready"}


@router.get(
    "/liveness",
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
    description="Kubernetes liveness probe endpoint"
)
async def liveness_check() -> Dict[str, str]:
    """Liveness probe for Kubernetes deployments."""
    # This should be a simple check that the application is running
    return {"status": "alive"}
