"""
Configuration settings for LinkDive application.
"""
import os
from typing import List, Optional, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import ConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "LinkDive"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    
    # Database
    database_url: str = "postgresql://linkdive:password@localhost:5432/linkdive_db"
    database_host: str = "localhost"
    database_port: int = 5432
    database_user: str = "linkdive"
    database_password: str = "password"
    database_name: str = "linkdive_db"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    # External APIs
    ahrefs_api_key: Optional[str] = None
    AHREFS_API_KEY: Optional[str] = None  # Alias for service compatibility
    dataforseo_username: Optional[str] = None
    DATAFORSEO_USERNAME: Optional[str] = None  # Alias
    dataforseo_password: Optional[str] = None
    DATAFORSEO_PASSWORD: Optional[str] = None  # Alias
    ahrefs_base_url: str = "https://api.ahrefs.com/v3"
    dataforseo_base_url: str = "https://api.dataforseo.com/v3"
    
    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    access_token_expire_minutes: int = 30
    algorithm: str = "HS256"
    
    # CORS
    allowed_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3002", "http://127.0.0.1:3002"]
    allowed_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allowed_headers: List[str] = ["*"]
    
    @field_validator('allowed_origins', 'allowed_methods', 'allowed_headers', mode='before')
    @classmethod
    def parse_cors_lists(cls, v):
        """Parse comma-separated strings into lists for CORS settings."""
        if isinstance(v, str):
            return [item.strip() for item in v.split(',') if item.strip()]
        return v
    
    # Rate Limiting
    rate_limit_requests_per_minute: int = 60
    rate_limit_burst: int = 10
    
    # Caching
    cache_ttl_seconds: int = 3600
    backlink_cache_ttl: int = 86400
    analysis_cache_ttl: int = 7200
    
    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    
    # Feature Flags
    enable_caching: bool = True
    enable_rate_limiting: bool = True
    enable_background_tasks: bool = True
    enable_serp_monitoring: bool = True
    enable_content_scrape: bool = False
    enable_persistent_rate_limits: bool = False  # Feature flag for DB-backed limiter
    # Mock/live data mode (runtime-overridable via /api/v1/runtime/config)
    enable_mock_mode: bool = True

    # Monitoring Window / Scheduling
    monitor_window_tz: str = "Europe/London"
    monitor_start_hour: int = 7
    monitor_end_hour: int = 19

    # SERP / Coverage Parameters
    serp_top_n: int = 20
    max_hourly_ahrefs_calls: int = 500
    max_hourly_dataforseo_calls: int = 500

    # Cost Guard
    cost_budget_daily_usd: float = 25.0
    allowed_email_domain: str = "linkdive.ai"
    
    # Monitoring
    sentry_dsn: Optional[str] = None
    log_format: str = "json"
    log_file: str = "logs/app.log"

    # Pydantic v2 configuration
    # Enable reading from a local .env file so credentials can be supplied without mutating the shell env
    # Keep case-insensitive env var names for convenience (ahrefs_api_key vs AHREFS_API_KEY)
    model_config = SettingsConfigDict(case_sensitive=False, env_file=".env", env_file_encoding="utf-8")

    # Note: env file loading disabled to avoid parsing issues; defaults used in tests

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
