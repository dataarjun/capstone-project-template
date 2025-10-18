"""
Security Configuration

This module handles API key validation, authentication, and security
measures for the Multi-Agent AML Investigation System.
"""

from typing import Optional
from fastapi import HTTPException, status
from app.core.config_simple import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class APIKeyValidator:
    """API key validation for external service access"""
    
    @staticmethod
    def validate_openai_key() -> bool:
        """Validate OpenAI API key is present and valid"""
        if not settings.OPENAI_API_KEY:
            logger.error("OpenAI API key not configured")
            return False
        return True
    
    @staticmethod
    def validate_langsmith_key() -> bool:
        """Validate LangSmith API key is present"""
        if not settings.LANGSMITH_API_KEY:
            logger.warning("LangSmith API key not configured - tracing disabled")
            return False
        return True
    
    @staticmethod
    def validate_memory_keys() -> bool:
        """Validate memory service API keys"""
        if not settings.MEM0_API_KEY:
            logger.warning("Mem0 API key not configured - short-term memory disabled")
            return False
        return True


class SecurityManager:
    """Main security manager for the application"""
    
    def __init__(self):
        self.api_validator = APIKeyValidator()
    
    def validate_environment(self) -> bool:
        """Validate all required environment variables and API keys"""
        try:
            # Validate OpenAI key (required)
            if not self.api_validator.validate_openai_key():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="OpenAI API key not configured"
                )
            
            # Validate optional keys
            self.api_validator.validate_langsmith_key()
            self.api_validator.validate_memory_keys()
            
            logger.info("Environment validation completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Environment validation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Environment validation failed: {str(e)}"
            )


# Global security manager instance
security_manager = SecurityManager()
