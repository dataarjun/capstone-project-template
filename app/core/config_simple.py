"""
Simple Application Configuration

This module handles all application settings for the Multi-Agent AML
Investigation System without complex environment variable parsing.
"""

import os
from typing import List
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

# Ensure .env is loaded again to handle any import order issues
load_dotenv()


class Settings:
    """Application settings"""
    
    def __init__(self):
        # Application settings
        self.APP_NAME: str = "Multi-Agent AML Investigation System"
        self.APP_VERSION: str = "1.0.0"
        self.DEBUG: bool = False
        
        # API settings
        self.API_V1_STR: str = "/api"
        self.ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "0.0.0.0", "testserver"]
        
        # Database settings - ensure .env is loaded before getting values
        load_dotenv(env_path)  # Reload to ensure fresh values
        self.DATABASE_URL: str = f"sqlite:///{Path(__file__).parent.parent.parent / 'data' / 'aml_database.db'}"
        self.POSTGRES_URL: str = os.getenv("POSTGRES_URL", "")
        self.VECTOR_DB_PATH: str = "./data/kyc_vectordb"
        
        # OpenAI settings
        self.OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
        self.OPENAI_MODEL: str = "gpt-4"
        self.OPENAI_EMBEDDING_MODEL: str = "text-embedding-ada-002"
        
        # LangSmith settings
        self.LANGSMITH_API_KEY: str = os.getenv("LANGSMITH_API_KEY", "")
        self.LANGSMITH_PROJECT: str = "aml-investigation"
        self.LANGSMITH_TRACING: bool = True
        
        # Memory settings
        self.MEM0_API_KEY: str = os.getenv("MEM0_API_KEY", "")
        self.SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
        self.SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
        
        # Security settings
        self.SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
        
        # Monitoring settings
        self.LOG_LEVEL: str = "INFO"
        self.ENABLE_METRICS: bool = True
        
        # Agent settings
        self.MAX_CONCURRENT_INVESTIGATIONS: int = 10
        self.INVESTIGATION_TIMEOUT_SECONDS: int = 300
        
        # Debug: Log critical settings
        if not self.POSTGRES_URL:
            print(f"⚠️  WARNING: POSTGRES_URL is empty! Environment variables may not be loaded correctly.")
        else:
            # Mask password in log
            masked_url = self.POSTGRES_URL
            if '@' in masked_url and ':' in masked_url:
                parts = masked_url.split('@')
                if len(parts) == 2:
                    user_pass = parts[0]
                    rest = parts[1]
                    if ':' in user_pass:
                        user_part, pass_part = user_pass.rsplit(':', 1)
                        masked_url = f"{user_part}:***@{rest}"
            print(f"✅ POSTGRES_URL loaded: {masked_url}")


# Create settings instance
settings = Settings()
