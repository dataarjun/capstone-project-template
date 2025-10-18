"""
Agent Routes

This module contains API routes for agent management and execution
in the Multi-Agent AML Investigation System.
"""

from typing import List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks

from app.core.logger import get_logger
from app.models.request_models import AgentExecutionRequest
from app.models.response_models import AgentStatusResponse, AgentExecutionResponse
from app.services.investigation_service import InvestigationService
from app.api.deps import get_investigation_service

logger = get_logger(__name__)
router = APIRouter()


@router.get("/status")
async def get_agent_status(
    investigation_service: InvestigationService = Depends(get_investigation_service)
) -> List[AgentStatusResponse]:
    """
    Get status of all agents
    
    Args:
        investigation_service: Investigation service dependency
        
    Returns:
        List of agent statuses
    """
    try:
        # Get agent statuses from investigation service
        agent_statuses = await investigation_service.get_agent_statuses()
        return agent_statuses
        
    except Exception as e:
        logger.error(f"Failed to get agent status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent status: {str(e)}"
        )


@router.post("/testing/execute")
async def execute_agent_testing(
    request: AgentExecutionRequest,
    background_tasks: BackgroundTasks,
    investigation_service: InvestigationService = Depends(get_investigation_service)
) -> AgentExecutionResponse:
    """
    Execute agent testing with given input data
    
    Args:
        request: Agent execution request
        background_tasks: FastAPI background tasks
        investigation_service: Investigation service dependency
        
    Returns:
        Agent execution response
    """
    try:
        # For testing, we'll execute the coordinator agent by default
        agent_name = "coordinator"
        
        # Add default values for required fields if not provided
        test_input_data = request.input_data.copy()
        if "alert_id" not in test_input_data:
            test_input_data["alert_id"] = "ALT001"  # Use first alert from database
        if "transaction_id" not in test_input_data:
            test_input_data["transaction_id"] = "TXN000001"  # Use first transaction
        if "investigation_id" not in test_input_data:
            test_input_data["investigation_id"] = f"INV_TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Execute agent
        result = await investigation_service.execute_agent(
            agent_name=agent_name,
            input_data=test_input_data,
            background_tasks=background_tasks
        )
        
        return AgentExecutionResponse(
            agent_name=agent_name,
            status="executed",
            result=result,
            execution_time=result.get("execution_time", 0)
        )
        
    except Exception as e:
        logger.error(f"Failed to execute agent testing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute agent testing: {str(e)}"
        )


@router.post("/{agent_name}/execute")
async def execute_agent(
    agent_name: str,
    request: AgentExecutionRequest,
    background_tasks: BackgroundTasks,
    investigation_service: InvestigationService = Depends(get_investigation_service)
) -> AgentExecutionResponse:
    """
    Execute a specific agent with given input data
    
    Args:
        agent_name: Name of the agent to execute
        request: Agent execution request
        background_tasks: FastAPI background tasks
        investigation_service: Investigation service dependency
        
    Returns:
        Agent execution response
    """
    try:
        # Validate agent name
        valid_agents = ["coordinator", "data_enrichment", "pattern_analyst", "risk_assessor", "report_synthesizer"]
        if agent_name not in valid_agents:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid agent name. Must be one of: {valid_agents}"
            )
        
        # Execute agent
        result = await investigation_service.execute_agent(
            agent_name=agent_name,
            input_data=request.input_data,
            background_tasks=background_tasks
        )
        
        return AgentExecutionResponse(
            agent_name=agent_name,
            status="executed",
            result=result,
            execution_time=result.get("execution_time", 0)
        )
        
    except Exception as e:
        logger.error(f"Failed to execute agent {agent_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute agent {agent_name}: {str(e)}"
        )


@router.get("/{agent_name}/status")
async def get_agent_status(
    agent_name: str,
    investigation_service: InvestigationService = Depends(get_investigation_service)
) -> AgentStatusResponse:
    """
    Get status of a specific agent
    
    Args:
        agent_name: Name of the agent
        investigation_service: Investigation service dependency
        
    Returns:
        Agent status response
    """
    try:
        # Get specific agent status
        status = await investigation_service.get_agent_status(agent_name)
        return status
        
    except Exception as e:
        logger.error(f"Failed to get status for agent {agent_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status for agent {agent_name}: {str(e)}"
        )
