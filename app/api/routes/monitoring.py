"""
Monitoring Routes

This module contains API routes for system monitoring and metrics
in the Multi-Agent AML Investigation System.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.core.logger import get_logger
from app.models.response_models import MonitoringTracesResponse, MonitoringMetricsResponse
from app.services.monitoring_service import MonitoringService
from app.api.deps import get_monitoring_service

logger = get_logger(__name__)
router = APIRouter()


@router.get("/traces")
async def get_traces(
    investigation_id: Optional[str] = Query(None, description="Filter by investigation ID"),
    agent_name: Optional[str] = Query(None, description="Filter by agent name"),
    limit: int = Query(100, description="Maximum number of traces"),
    monitoring_service: MonitoringService = Depends(get_monitoring_service)
) -> MonitoringTracesResponse:
    """
    Get LangSmith traces for investigations
    
    Args:
        investigation_id: Filter by investigation ID
        agent_name: Filter by agent name
        limit: Maximum number of traces
        monitoring_service: Monitoring service dependency
        
    Returns:
        LangSmith traces
    """
    try:
        # Get traces
        traces = await monitoring_service.get_traces(
            investigation_id=investigation_id,
            agent_name=agent_name,
            limit=limit
        )
        
        return MonitoringTracesResponse(traces=traces)
        
    except Exception as e:
        logger.error(f"Failed to get traces: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get traces: {str(e)}"
        )


@router.get("/metrics")
async def get_metrics(
    period: str = Query("last_24h", description="Time period for metrics"),
    monitoring_service: MonitoringService = Depends(get_monitoring_service)
) -> MonitoringMetricsResponse:
    """
    Get system performance metrics
    
    Args:
        period: Time period for metrics
        monitoring_service: Monitoring service dependency
        
    Returns:
        System metrics
    """
    try:
        # Get metrics
        metrics = await monitoring_service.get_metrics(period=period)
        
        return MonitoringMetricsResponse(**metrics)
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}"
        )
