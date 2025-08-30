"""
API Router configuration for Link Dive AI v1 endpoints.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import health, backlinks, analysis, campaigns

# Create the main API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(backlinks.router, prefix="/backlinks", tags=["backlinks"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
api_router.include_router(campaigns.router, tags=["campaigns"])  # Note: no prefix for campaigns
