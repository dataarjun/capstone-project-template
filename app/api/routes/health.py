"""
Health Check Routes

This module contains health check endpoints for monitoring
application status and dependencies.
"""

from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.logger import get_logger
from app.core.security import security_manager
from app.db.session import get_db
from sqlalchemy.orm import Session

logger = get_logger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint
    
    Returns:
        Health status and timestamp
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Multi-Agent AML Investigation System"
    }


@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Detailed health check with dependency validation
    
    Args:
        db: Database session dependency
        
    Returns:
        Detailed health status including dependencies
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Multi-Agent AML Investigation System",
        "dependencies": {}
    }
    
    try:
        # Validate environment
        security_manager.validate_environment()
        health_status["dependencies"]["environment"] = "healthy"
        
        # Test database connection
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        health_status["dependencies"]["database"] = "healthy"
        
        # Test vector database (if configured)
        # This would be implemented when vector DB is set up
        health_status["dependencies"]["vector_db"] = "not_configured"
        
        # Test external services
        health_status["dependencies"]["openai"] = "configured" if security_manager.api_validator.validate_openai_key() else "not_configured"
        health_status["dependencies"]["langsmith"] = "configured" if security_manager.api_validator.validate_langsmith_key() else "not_configured"
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)
        
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_status
        )
    
    return health_status
