"""
Database configuration for Link Dive AI (dev SQLite / prod Postgres).

Uses config.settings to ensure a single source of truth for DATABASE_URL.
For SQLite, converts relative paths to an absolute file path anchored to the
backend directory so all scripts and the server point to the same DB.
"""
import os
from pathlib import Path
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from config.settings import settings

def _resolve_database_url() -> str:
    """Resolve the database URL from settings and normalize SQLite paths.

    - Reads from pydantic settings (which loads src/backend/.env).
    - If it's a SQLite URL with a relative path, convert it to an absolute path
      rooted at the backend directory so different CWDs don't create separate DBs.
    """
    url = settings.database_url
    if url.startswith("sqlite"):
        # Extract path portion after sqlite:///
        try:
            prefix = "sqlite:///"
            if url.startswith(prefix):
                db_path = url[len(prefix):]
                # If relative, anchor to backend directory (two levels up from this file)
                p = Path(db_path)
                if not p.is_absolute():
                    backend_dir = Path(__file__).resolve().parents[2]
                    abs_path = backend_dir / p
                    return f"sqlite:///{abs_path.as_posix()}"
        except Exception:
            pass
    return url

# Database URL configuration (single source of truth)
DATABASE_URL = _resolve_database_url()

# For production PostgreSQL:
# DATABASE_URL = "postgresql+asyncpg://user:password@localhost/link_dive_ai"

# Create engine
if DATABASE_URL.startswith("sqlite"):
    # SQLite configuration for development
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=True  # Set to False in production
    )
else:
    # PostgreSQL configuration for production
    engine = create_engine(
        DATABASE_URL,
        echo=True  # Set to False in production
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()

def get_db():
    """Database dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """Drop all database tables (use with caution!)"""
    Base.metadata.drop_all(bind=engine)
