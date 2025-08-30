"""
Core configuration module for Link Dive AI application.
"""
import logging
import os
from pathlib import Path
from typing import Dict, Any

import structlog
from rich.console import Console
from rich.logging import RichHandler

from config.settings import settings


def setup_logging() -> None:
    """Configure structured logging with rich formatting."""
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="ISO"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if settings.log_format == "json" else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(message)s",
        handlers=[
            RichHandler(console=Console(stderr=True), rich_tracebacks=True),
            logging.FileHandler(settings.log_file),
        ],
    )


def get_cors_config() -> Dict[str, Any]:
    """Get CORS configuration for FastAPI."""
    return {
        "allow_origins": settings.allowed_origins,
        "allow_credentials": True,
        "allow_methods": settings.allowed_methods,
        "allow_headers": settings.allowed_headers,
    }


def get_api_metadata() -> Dict[str, Any]:
    """Get API metadata for OpenAPI documentation."""
    return {
        "title": settings.app_name,
        "description": """
        Link Dive AI is a comprehensive SEO backlink analysis platform that integrates 
        multiple APIs to provide deep insights into website backlink profiles.
        
        ## Features
        - Multi-source backlink data aggregation
        - Advanced SEO analytics and insights
        - Real-time competitor analysis
        - Comprehensive reporting and exports
        - Beautiful data visualizations
        
        ## API Integrations
        - Ahrefs API for premium backlink data
        - DataForSEO API for comprehensive SEO metrics
        - Custom data processing and analysis
        """,
        "version": settings.app_version,
        "contact": {
            "name": "LinkDive Team",
            "email": "tools@linkdive.ai",
            "url": "http://linkdive.ai",
        },
        "license_info": {
            "name": "Proprietary",
        },
        "tags_metadata": [
            {
                "name": "health",
                "description": "Health check and system status endpoints",
            },
            {
                "name": "backlinks",
                "description": "Backlink analysis and data retrieval",
            },
            {
                "name": "analysis",
                "description": "SEO analysis and insights generation",
            },
            {
                "name": "websites",
                "description": "Website information and metrics",
            },
        ],
    }


# Initialize logging
setup_logging()

# Get logger instance
logger = structlog.get_logger(__name__)
