import secrets
from typing import Any, Dict, List, Optional, Union
from pydantic import AnyHttpUrl, PostgresDsn, field_validator
from pydantic_settings import BaseSettings
import json
import os
from loguru import logger


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Visually Impaired Assistant API"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[Union[str, AnyHttpUrl]] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse CORS origins from string to list."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        if isinstance(v, str):
            return json.loads(v)
        return v

    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"
    
    # Database
    DATABASE_URL: Optional[PostgresDsn] = None
    
    # Vision Model settings
    VISION_MODEL_PROVIDER: str = "openai"  # openai, google, huggingface
    VISION_MODEL_NAME: str = "gpt-4-vision-preview"
    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    HUGGINGFACE_API_KEY: Optional[str] = None
    
    # LLM settings
    LLM_PROVIDER: str = "openai"  # openai, google, huggingface
    LLM_MODEL_NAME: str = "gpt-4-turbo"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 1000
    
    # Storage configuration
    STORAGE_PROVIDER: str = "local"  # local, gcs, s3
    STORAGE_PATH: str = "./storage"
    GCS_BUCKET_NAME: Optional[str] = None
    GCS_CREDENTIALS_FILE: Optional[str] = None
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: Optional[str] = None
    AWS_BUCKET_NAME: Optional[str] = None
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Initialize settings
settings = Settings()

# Configure Loguru logger
logger.remove()
logger.add(
    "logs/app.log",
    rotation="10 MB",
    retention="30 days",
    level=settings.LOG_LEVEL,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
)
logger.add(
    lambda msg: print(msg),
    level=settings.LOG_LEVEL,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
) 