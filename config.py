import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self):
        # API Settings
        self.API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
        self.API_PORT: int = int(os.getenv("API_PORT", "8000"))
        self.API_WORKERS: int = int(os.getenv("API_WORKERS", "1"))
        
        # Crawler Settings
        self.MAX_CONCURRENT_REQUESTS: int = int(os.getenv("MAX_CONCURRENT_REQUESTS", "30"))  # Increased from 10 to 30 for better performance
        self.DEFAULT_TIMEOUT: int = int(os.getenv("DEFAULT_TIMEOUT", "30"))
        self.MAX_DEPTH: int = int(os.getenv("MAX_DEPTH", "10"))  # Increased default from 3 to 10, 0 = unlimited
        
        # Advanced Concurrency Settings
        self.CONCURRENCY_BURST_LIMIT: int = int(os.getenv("CONCURRENCY_BURST_LIMIT", "50"))  # Maximum burst concurrency
        self.CONCURRENCY_GRADUAL_INCREASE: bool = os.getenv("CONCURRENCY_GRADUAL_INCREASE", "true").lower() == "true"  # Gradually increase concurrency
        
        # Rate Limiting
        self.RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
        
        # Per-Domain Rate Limiting
        self.ENABLE_PER_DOMAIN_RATE_LIMITING: bool = os.getenv("ENABLE_PER_DOMAIN_RATE_LIMITING", "true").lower() == "true"
        self.DEFAULT_DOMAIN_RATE_LIMIT: int = int(os.getenv("DEFAULT_DOMAIN_RATE_LIMIT", "10"))  # requests per minute per domain
        self.DOMAIN_RATE_LIMIT_WINDOW: int = int(os.getenv("DOMAIN_RATE_LIMIT_WINDOW", "60"))  # time window in seconds
        
        # Domain-specific rate limits (comma-separated: domain:limit,domain:limit)
        self.DOMAIN_SPECIFIC_LIMITS: dict = {}
        
        # Parse domain-specific limits from environment variable
        domain_limits_str = os.getenv("DOMAIN_SPECIFIC_LIMITS", "")
        if domain_limits_str:
            for limit_config in domain_limits_str.split(","):
                if ":" in limit_config:
                    domain, limit = limit_config.strip().split(":", 1)
                    self.DOMAIN_SPECIFIC_LIMITS[domain.strip()] = int(limit.strip())
        
        # Redis Settings (for production)
        self.REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.USE_REDIS: bool = os.getenv("USE_REDIS", "false").lower() == "true"
        
        # Background Job Processing
        self.ENABLE_BACKGROUND_JOBS: bool = os.getenv("ENABLE_BACKGROUND_JOBS", "true").lower() == "true"
        self.MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "2"))
        self.JOB_TIMEOUT: int = int(os.getenv("JOB_TIMEOUT", "3600"))  # 1 hour
        
        # Logging
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
        self.ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
        
        # Security
        self.ALLOWED_ORIGINS: list = os.getenv("ALLOWED_ORIGINS", "*").split(",")
        
        # Error Handling & Retry Settings
        self.MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
        self.RETRY_DELAY_BASE: float = float(os.getenv("RETRY_DELAY_BASE", "1.0"))  # Base delay in seconds
        self.RETRY_DELAY_MAX: float = float(os.getenv("RETRY_DELAY_MAX", "10.0"))  # Maximum delay in seconds
        self.RETRY_BACKOFF_MULTIPLIER: float = float(os.getenv("RETRY_BACKOFF_MULTIPLIER", "2.0"))  # Exponential backoff multiplier
        self.RETRY_ON_TIMEOUT: bool = os.getenv("RETRY_ON_TIMEOUT", "true").lower() == "true"
        self.RETRY_ON_CONNECTION_ERROR: bool = os.getenv("RETRY_ON_CONNECTION_ERROR", "true").lower() == "true"
        
        # Storage Settings
        self.STORAGE_TYPE: str = os.getenv("STORAGE_TYPE", "json")  # json, mongodb, elasticsearch
        self.STORAGE_DATA_DIR: str = os.getenv("STORAGE_DATA_DIR", "data")  # For JSON storage
        
        # MongoDB Settings
        self.MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        self.MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "crawler_service")
        
        # Elasticsearch Settings
        self.ELASTICSEARCH_HOSTS: list = os.getenv("ELASTICSEARCH_HOSTS", "localhost:9200").split(",")
        self.ELASTICSEARCH_CLOUD_ID: str = os.getenv("ELASTICSEARCH_CLOUD_ID", "")
        self.ELASTICSEARCH_API_KEY: str = os.getenv("ELASTICSEARCH_API_KEY", "")
        self.ELASTICSEARCH_USERNAME: str = os.getenv("ELASTICSEARCH_USERNAME", "")
        self.ELASTICSEARCH_PASSWORD: str = os.getenv("ELASTICSEARCH_PASSWORD", "")
        self.ELASTICSEARCH_INDEX_PREFIX: str = os.getenv("ELASTICSEARCH_INDEX_PREFIX", "crawler")

settings = Settings()
