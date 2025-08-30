"""
Configuration settings for LinkDive application.
"""
import os
from typing import List, Optional, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = Field(default="LinkDive", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=1, env="WORKERS")
    
    # Database
    database_url: str = Field(default="postgresql://linkdive:password@localhost:5432/linkdive_db", env="DATABASE_URL")
    database_host: str = Field(default="localhost", env="DATABASE_HOST")
    database_port: int = Field(default=5432, env="DATABASE_PORT")
    database_user: str = Field(default="linkdive", env="DATABASE_USER")
    database_password: str = Field(default="password", env="DATABASE_PASSWORD")
    database_name: str = Field(default="linkdive_db", env="DATABASE_NAME")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # External APIs
    ahrefs_api_key: Optional[str] = Field(default=None, env="AHREFS_API_KEY")
    AHREFS_API_KEY: Optional[str] = Field(default=None, env="AHREFS_API_KEY")  # Alias for service compatibility
    dataforseo_username: Optional[str] = Field(default=None, env="DATAFORSEO_USERNAME")
    DATAFORSEO_USERNAME: Optional[str] = Field(default=None, env="DATAFORSEO_USERNAME")  # Alias
    dataforseo_password: Optional[str] = Field(default=None, env="DATAFORSEO_PASSWORD")
    DATAFORSEO_PASSWORD: Optional[str] = Field(default=None, env="DATAFORSEO_PASSWORD")  # Alias
    ahrefs_base_url: str = Field(default="https://api.ahrefs.com/v3", env="AHREFS_BASE_URL")
    dataforseo_base_url: str = Field(default="https://api.dataforseo.com/v3", env="DATAFORSEO_BASE_URL")
    
    # Security
    secret_key: str = Field(default="dev-secret-key-change-in-production", env="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    
    # CORS
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        env="ALLOWED_ORIGINS"
    )
    allowed_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        env="ALLOWED_METHODS"
    )
    allowed_headers: List[str] = Field(default=["*"], env="ALLOWED_HEADERS")
    
    @field_validator('allowed_origins', 'allowed_methods', 'allowed_headers', mode='before')
    @classmethod
    def parse_cors_lists(cls, v):
        """Parse comma-separated strings into lists for CORS settings."""
        if isinstance(v, str):
            return [item.strip() for item in v.split(',') if item.strip()]
        return v
    
    # Rate Limiting
    rate_limit_requests_per_minute: int = Field(default=60, env="RATE_LIMIT_REQUESTS_PER_MINUTE")
    rate_limit_burst: int = Field(default=10, env="RATE_LIMIT_BURST")
    
    # Caching
    cache_ttl_seconds: int = Field(default=3600, env="CACHE_TTL_SECONDS")
    backlink_cache_ttl: int = Field(default=86400, env="BACKLINK_CACHE_TTL")
    analysis_cache_ttl: int = Field(default=7200, env="ANALYSIS_CACHE_TTL")
    
    # Celery
    celery_broker_url: str = Field(default="redis://localhost:6379/1", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/2", env="CELERY_RESULT_BACKEND")
    
    # Feature Flags
    enable_caching: bool = Field(default=True, env="ENABLE_CACHING")
    enable_rate_limiting: bool = Field(default=True, env="ENABLE_RATE_LIMITING")
    enable_background_tasks: bool = Field(default=True, env="ENABLE_BACKGROUND_TASKS")
    
    # Monitoring
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    log_file: str = Field(default="logs/app.log", env="LOG_FILE")

    class Config:
        # Temporarily disable .env file loading to fix parsing issues
        # env_file = ".env"
        # env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL for SQLAlchemy."""
        return self.database_url.replace("postgresql://", "postgresql+psycopg2://")

    @property
    def database_url_async(self) -> str:
        """Get asynchronous database URL for SQLAlchemy."""
        return self.database_url.replace("postgresql://", "postgresql+asyncpg://")


# Global settings instance
settings = Settings()
