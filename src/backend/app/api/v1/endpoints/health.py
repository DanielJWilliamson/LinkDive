"""
Health check endpoints for monitoring and system status.
"""
from datetime import datetime, timedelta, timezone
from time import perf_counter
from typing import Dict, Any

from fastapi import APIRouter, status
from pydantic import BaseModel

from config.settings import settings

router = APIRouter()


class HealthResponse(BaseModel):
    """Basic health check response model.

    Kept intentionally lightweight for liveness endpoints / external load balancer checks.
    """
    status: str
    timestamp: datetime
    version: str
    environment: str
    services: Dict[str, str]


class DetailedHealthResponse(BaseModel):
    """Detailed health check response model including metrics snapshot."""
    status: str
    timestamp: datetime
    version: str
    environment: str
    uptime: str
    services: Dict[str, Dict[str, Any]]
    system_info: Dict[str, Any]
    metrics: Dict[str, Any]


# Track application start time for uptime calculation (module import time)
START_TIME = datetime.now(timezone.utc)

def _format_uptime(delta: timedelta) -> str:
    days = delta.days
    hours, rem = divmod(delta.seconds, 3600)
    minutes, _ = divmod(rem, 60)
    return f"{days}d {hours}h {minutes}m"

def _db_connectivity_check() -> Dict[str, Any]:
    """Perform a lightweight database connectivity check (SELECT 1)."""
    from sqlalchemy import text
    from app.core.database import engine
    start = perf_counter()
    status_val = "healthy"
    error_msg = None
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:  # pragma: no cover - edge failure path
        status_val = "unhealthy"
        error_msg = str(e)
    latency_ms = round((perf_counter() - start) * 1000, 2)
    payload: Dict[str, Any] = {"status": status_val, "latency_ms": latency_ms}
    if error_msg:
        payload["error"] = error_msg
    return payload


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
        timestamp=datetime.now(timezone.utc),
        version=settings.app_version,
        environment="development" if settings.debug else "production",
        services={
            "api": "healthy",
            "database": _db_connectivity_check().get("status", "unknown"),
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
    from app.core.metrics import metrics
    
    # Get system information
    system_info = {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
    }
    
    db_status = _db_connectivity_check()
    # TODO: Replace redis stub with actual client ping once integrated
    services = {
        "api": {"status": "healthy"},
        "database": db_status,
        "redis": {"status": "healthy", "note": "stub"},
        "external_apis": {
            "ahrefs": "stub",  # future enhancement
            "dataforseo": "stub"
        }
    }

    metric_snapshot = metrics.snapshot()
    
    return DetailedHealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc),
        version=settings.app_version,
        environment="development" if settings.debug else "production",
    uptime=_format_uptime(datetime.now(timezone.utc) - START_TIME),
        services=services,
        system_info=system_info,
        metrics={
            "counters": metric_snapshot.get("counters", {}),
            "gauges": metric_snapshot.get("gauges", {}),
            "timestamps": metric_snapshot.get("timestamps", {})
        }
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
