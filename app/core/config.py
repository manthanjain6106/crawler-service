"""
Configuration management for the crawler microservice.
Supports environment-specific configurations and validation.
"""

import os
from typing import List, Dict, Any, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with validation and environment variable support."""
    
    # Application
    app_name: str = Field(default="Web Crawler Microservice", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_workers: int = Field(default=1, env="API_WORKERS")
    api_prefix: str = Field(default="/api/v1", env="API_PREFIX")
    
    # CORS Configuration
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: List[str] = Field(default=["*"], env="CORS_ALLOW_METHODS")
    cors_allow_headers: List[str] = Field(default=["*"], env="CORS_ALLOW_HEADERS")
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=10, env="RATE_LIMIT_PER_MINUTE")
    enable_per_domain_rate_limiting: bool = Field(default=True, env="ENABLE_PER_DOMAIN_RATE_LIMITING")
    default_domain_rate_limit: int = Field(default=10, env="DEFAULT_DOMAIN_RATE_LIMIT")
    domain_rate_limit_window: int = Field(default=60, env="DOMAIN_RATE_LIMIT_WINDOW")
    domain_specific_limits: Dict[str, int] = Field(default_factory=dict, env="DOMAIN_SPECIFIC_LIMITS")
    
    # Crawler Configuration
    max_concurrent_requests: int = Field(default=30, env="MAX_CONCURRENT_REQUESTS")
    concurrency_burst_limit: int = Field(default=50, env="CONCURRENCY_BURST_LIMIT")
    concurrency_gradual_increase: bool = Field(default=True, env="CONCURRENCY_GRADUAL_INCREASE")
    default_timeout: int = Field(default=30, env="DEFAULT_TIMEOUT")
    max_depth: int = Field(default=0, env="MAX_DEPTH")
    
    # Retry Configuration
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    retry_delay_base: float = Field(default=1.0, env="RETRY_DELAY_BASE")
    retry_delay_max: float = Field(default=10.0, env="RETRY_DELAY_MAX")
    retry_backoff_multiplier: float = Field(default=2.0, env="RETRY_BACKOFF_MULTIPLIER")
    retry_on_timeout: bool = Field(default=True, env="RETRY_ON_TIMEOUT")
    retry_on_connection_error: bool = Field(default=True, env="RETRY_ON_CONNECTION_ERROR")
    
    # Note: Storage and background jobs are disabled - no data persistence
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    # Security
    secret_key: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Monitoring
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("cors_allow_methods", pre=True)
    def parse_cors_methods(cls, v):
        if isinstance(v, str):
            return [method.strip() for method in v.split(",")]
        return v
    
    @validator("cors_allow_headers", pre=True)
    def parse_cors_headers(cls, v):
        if isinstance(v, str):
            return [header.strip() for header in v.split(",")]
        return v
    
    @validator("domain_specific_limits", pre=True)
    def parse_domain_limits(cls, v):
        if isinstance(v, str):
            limits = {}
            for limit_config in v.split(","):
                if ":" in limit_config:
                    domain, limit = limit_config.strip().split(":", 1)
                    limits[domain.strip()] = int(limit.strip())
            return limits
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


# Global settings instance
settings = get_settings()
