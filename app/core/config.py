"""
Application configuration using Pydantic Settings
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # App info
    APP_NAME: str = "Bot SaaS API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/bot_saas",
        description="PostgreSQL connection URL"
    )
    
    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    
    # Security
    SECRET_KEY: str = Field(
        default="your-super-secret-key-change-in-production",
        description="JWT secret key"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Encryption
    CONFIG_ENCRYPTION_KEY: str = Field(
        default="",
        description="Fernet key for encrypting sensitive data"
    )
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Bot settings
    DEFAULT_CHECK_INTERVAL_MINUTES: int = 15
    DEFAULT_MAX_RETRIES: int = 3
    MAX_WORKERS_PER_TENANT: int = 5
    
    # Session storage
    SESSIONS_BASE_PATH: str = "/app/sessions"
    LOGS_BASE_PATH: str = "/app/logs"
    
    # Celery
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/0")
    
    # Sentry (optional)
    SENTRY_DSN: str = ""
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
