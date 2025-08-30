#!/usr/bin/env python3
"""
Database initialization script for Link Dive AI
"""
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import create_tables, engine, Base
import structlog

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

def main():
    """Initialize the database with all tables."""
    try:
        logger.info("Starting database initialization...")
        
        # Import all models to ensure they're registered with Base
        from app.database.models import (
            Campaign, 
            CampaignKeyword, 
            BacklinkResult, 
            SerpRanking, 
            BackgroundTask,
            DomainBlacklist
        )
        
        logger.info("Models imported successfully")
        
        # Create all tables
        logger.info("Creating database tables...")
        create_tables()
        
        logger.info("Database initialization completed successfully!")
        
        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        logger.info(f"Created tables: {tables}")
        
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
    else:
        print("✅ Database initialized successfully!")
