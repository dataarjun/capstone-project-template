"""
Application Configuration

This module handles all application settings and environment variables
for the Multi-Agent AML Investigation System.
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application settings
    APP_NAME: str = "Multi-Agent AML Investigation System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API settings
    API_V1_STR: str = "/api"
    ALLOWED_HOSTS: str = "localhost,127.0.0.1,0.0.0.0"
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./data/aml_database.db"
    VECTOR_DB_PATH: str = "./data/kyc_vectordb"
    
    # OpenAI settings
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-ada-002"
    
    # LangSmith settings
    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_PROJECT: str = "aml-investigation"
    LANGSMITH_TRACING: bool = True
    
    # Memory settings
    MEM0_API_KEY: Optional[str] = None
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    
    # Security settings
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Monitoring settings
    LOG_LEVEL: str = "INFO"
    ENABLE_METRICS: bool = True
    
    # Agent settings
    MAX_CONCURRENT_INVESTIGATIONS: int = 10
    INVESTIGATION_TIMEOUT_SECONDS: int = 300
    
    @validator("ALLOWED_HOSTS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()
