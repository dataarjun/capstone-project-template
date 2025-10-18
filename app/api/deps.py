"""
API Dependencies

This module contains FastAPI dependencies for dependency injection,
authentication, and common functionality across API routes.
"""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config_simple import settings
from app.core.logger import get_logger
from app.db.session import get_db
from app.services.investigation_service import InvestigationService
# RAG service removed - not using RAG functionality
from app.services.monitoring_service import MonitoringService

logger = get_logger(__name__)


def get_investigation_service(db: Session = Depends(get_db)) -> InvestigationService:
    """Get investigation service dependency"""
    return InvestigationService(db)


# RAG service dependency removed - not using RAG functionality


def get_monitoring_service() -> MonitoringService:
    """Get monitoring service dependency"""
    return MonitoringService()


def validate_api_key(api_key: Optional[str] = None) -> bool:
    """
    Validate API key for external access
    
    Args:
        api_key: API key to validate
        
    Returns:
        True if valid, raises exception if invalid
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    # In production, implement proper API key validation
    if api_key != settings.SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return True


def get_current_user(user_id: Optional[str] = None) -> str:
    """
    Get current user ID (placeholder for authentication)
    
    Args:
        user_id: User ID from request
        
    Returns:
        User ID string
    """
    # In production, implement proper user authentication
    return user_id or "system"
