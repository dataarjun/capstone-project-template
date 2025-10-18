"""
Investigation Routes

This module contains API routes for investigation management
in the Multi-Agent AML Investigation System.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query

from app.core.logger import get_logger
from app.models.request_models import InvestigationStartRequest
from app.models.response_models import InvestigationResponse, InvestigationListResponse
from app.services.investigation_service import InvestigationService
from app.api.deps import get_investigation_service, get_current_user

logger = get_logger(__name__)
router = APIRouter()


@router.post("/start")
async def start_investigation(
    request: InvestigationStartRequest,
    background_tasks: BackgroundTasks,
    investigation_service: InvestigationService = Depends(get_investigation_service),
    user_id: str = Depends(get_current_user)
) -> InvestigationResponse:
    """
    Start a new investigation for an alert
    
    Args:
        request: Investigation start request
        background_tasks: FastAPI background tasks
        investigation_service: Investigation service dependency
        user_id: Current user ID
        
    Returns:
        Investigation response
    """
    try:
        # Start investigation
        investigation = await investigation_service.start_investigation(
            alert_id=request.alert_id,
            transaction_id=request.transaction_id,
            priority=request.priority,
            user_id=user_id,
            background_tasks=background_tasks
        )
        
        return InvestigationResponse(
            investigation_id=investigation["investigation_id"],
            status=investigation["status"],
            alert_id=investigation["alert_id"],
            created_at=investigation["created_at"]
        )
        
    except Exception as e:
        logger.error(f"Failed to start investigation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start investigation: {str(e)}"
        )


@router.get("/{investigation_id}")
async def get_investigation(
    investigation_id: str,
    investigation_service: InvestigationService = Depends(get_investigation_service)
) -> InvestigationResponse:
    """
    Get investigation status and results
    
    Args:
        investigation_id: Investigation ID
        investigation_service: Investigation service dependency
        
    Returns:
        Investigation response with results
    """
    try:
        # Get investigation details
        investigation = await investigation_service.get_investigation(investigation_id)
        
        if not investigation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Investigation {investigation_id} not found"
            )
        
        return InvestigationResponse(**investigation)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get investigation {investigation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get investigation: {str(e)}"
        )


@router.get("/")
async def list_investigations(
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    limit: int = Query(50, description="Maximum number of results"),
    offset: int = Query(0, description="Number of results to skip"),
    investigation_service: InvestigationService = Depends(get_investigation_service)
) -> InvestigationListResponse:
    """
    List investigations with filtering
    
    Args:
        status: Filter by investigation status
        priority: Filter by priority level
        limit: Maximum number of results
        offset: Number of results to skip
        investigation_service: Investigation service dependency
        
    Returns:
        List of investigations
    """
    try:
        # Get filtered investigations
        investigations = await investigation_service.list_investigations(
            status=status,
            priority=priority,
            limit=limit,
            offset=offset
        )
        
        return InvestigationListResponse(
            investigations=investigations,
            total=len(investigations),
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        logger.error(f"Failed to list investigations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list investigations: {str(e)}"
        )
