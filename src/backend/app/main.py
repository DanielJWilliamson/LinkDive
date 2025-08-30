"""
Main FastAPI application entry point for Link Dive AI.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import asyncio

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.api import api_router
from app.api.background import router as background_router
from app.core.config import get_cors_config, get_api_metadata
from app.services.background_processing_service import background_processing_service
from app.utils.port_manager import clear_port, is_port_available
from config.settings import settings

# Get logger
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    # Startup
    logger.info("Starting Link Dive AI application", version=settings.app_version)
    
    # Clear the port before starting
    logger.info(f"Ensuring port {settings.port} is available...")
    if not is_port_available(settings.port):
        logger.info(f"Port {settings.port} is in use, clearing it...")
        if clear_port(settings.port, force=True):
            logger.info(f"Port {settings.port} successfully cleared")
        else:
            logger.error(f"Failed to clear port {settings.port}")
    else:
        logger.info(f"Port {settings.port} is already available")
    
    # Start background processing worker
    logger.info("Starting background processing service")
    worker_task = asyncio.create_task(background_processing_service.start_worker())
    
    yield
    
    # Shutdown
    logger.info("Shutting down Link Dive AI application")
    
    # Stop background processing worker
    logger.info("Stopping background processing service")
    await background_processing_service.stop_worker()
    
    # Cancel worker task
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    # Get API metadata
    metadata = get_api_metadata()
    
    # Create FastAPI app
    app = FastAPI(
        lifespan=lifespan,
        debug=settings.debug,
        **metadata
    )
    
    # Add middleware
    setup_middleware(app)
    
    # Include routers
    app.include_router(api_router, prefix="/api/v1")
    app.include_router(background_router)
    
    # Include campaigns router (if it exists)
    try:
        from app.api.v1.endpoints.campaigns import router as campaigns_router
        app.include_router(campaigns_router, prefix="/api")
    except ImportError:
        logger.warning("Campaigns router not found, skipping")
    
    # Add root endpoint
    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint with basic application information."""
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "status": "running",
            "docs_url": "/docs",
            "api_prefix": "/api/v1"
        }
    
    return app


def setup_middleware(app: FastAPI) -> None:
    """Configure application middleware."""
    
    # CORS middleware
    cors_config = get_cors_config()
    app.add_middleware(CORSMiddleware, **cors_config)
    
    # Trusted host middleware
    if not settings.debug:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["linkdive.ai", "*.linkdive.ai", "localhost", "127.0.0.1"]
        )


# Create the application instance
app = create_application()

if __name__ == "__main__":
    import uvicorn
    
    # Clear the port before starting the server
    logger.info(f"Preparing to start server on port {settings.port}")
    
    if not is_port_available(settings.port):
        logger.info(f"Port {settings.port} is occupied, clearing it...")
        if clear_port(settings.port, force=True):
            logger.info(f"Port {settings.port} cleared successfully")
        else:
            logger.error(f"Failed to clear port {settings.port}, server may fail to start")
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=settings.workers if not settings.debug else 1,
        log_level=settings.log_level.lower(),
    )
