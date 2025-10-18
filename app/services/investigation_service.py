"""
Investigation Service

This service handles investigation business logic including
workflow orchestration, agent management, and result processing.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks
from app.core.logger import get_logger
from app.core.exceptions import InvestigationTimeoutException
from app.agents import production_workflow, analyze_transaction, query_investigations
from app.models.response_models import AgentStatusResponse

logger = get_logger(__name__)


class InvestigationService:
    """
    Investigation service for managing AML investigations
    
    This service coordinates the multi-agent investigation process
    and manages investigation state and results.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.workflow = production_workflow
        self.active_investigations = {}
    
    async def start_investigation(
        self, 
        alert_id: str, 
        transaction_id: str, 
        priority: str, 
        user_id: str,
        background_tasks: BackgroundTasks
    ) -> Dict[str, Any]:
        """
        Start a new investigation
        
        Args:
            alert_id: Alert ID
            transaction_id: Transaction ID
            priority: Investigation priority
            user_id: User ID
            background_tasks: FastAPI background tasks
            
        Returns:
            Investigation details
        """
        try:
            # Generate investigation ID
            investigation_id = f"INV{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            # Create investigation record
            investigation = {
                "investigation_id": investigation_id,
                "alert_id": alert_id,
                "transaction_id": transaction_id,
                "priority": priority,
                "status": "running",
                "created_at": datetime.utcnow().isoformat(),
                "user_id": user_id
            }
            
            # Store in active investigations
            self.active_investigations[investigation_id] = investigation
            
            # Start investigation in background
            background_tasks.add_task(
                self._run_investigation,
                investigation_id,
                alert_id,
                transaction_id,
                priority
            )
            
            logger.info(f"Investigation {investigation_id} started for alert {alert_id}")
            
            return investigation
            
        except Exception as e:
            logger.error(f"Failed to start investigation: {str(e)}")
            raise
    
    async def _run_investigation(
        self, 
        investigation_id: str, 
        alert_id: str, 
        transaction_id: str, 
        priority: str
    ):
        """
        Run investigation in background
        
        Args:
            investigation_id: Investigation ID
            alert_id: Alert ID
            transaction_id: Transaction ID
            priority: Investigation priority
        """
        try:
            # Execute investigation workflow using production workflow
            # Note: This is a simplified implementation - in production you'd need
            # to fetch transaction and customer data from the database
            transaction_data = {
                "transaction_id": transaction_id,
                "amount": 0,  # Would be fetched from database
                "currency": "USD",
                "transaction_type": "unknown",
                "transaction_date": datetime.utcnow().isoformat(),
                "status": "completed"
            }
            customer_data = {
                "name": f"Customer_{transaction_id}",
                "account_age_days": 30,
                "transaction_history": []
            }
            
            result = analyze_transaction(
                transaction=transaction_data,
                customer=customer_data
            )
            
            # Update investigation record
            self.active_investigations[investigation_id].update(result)
            
            logger.info(f"Investigation {investigation_id} completed")
            
        except Exception as e:
            logger.error(f"Investigation {investigation_id} failed: {str(e)}")
            # Update investigation with error
            self.active_investigations[investigation_id].update({
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.utcnow().isoformat()
            })
    
    async def get_investigation(self, investigation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get investigation details
        
        Args:
            investigation_id: Investigation ID
            
        Returns:
            Investigation details or None if not found
        """
        try:
            investigation = self.active_investigations.get(investigation_id)
            
            if not investigation:
                # Try to get from database
                # This would be implemented when database is set up
                return None
            
            return investigation
            
        except Exception as e:
            logger.error(f"Failed to get investigation {investigation_id}: {str(e)}")
            raise
    
    async def list_investigations(
        self, 
        status: Optional[str] = None, 
        priority: Optional[str] = None, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List investigations with filtering
        
        Args:
            status: Filter by status
            priority: Filter by priority
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of investigations
        """
        try:
            investigations = list(self.active_investigations.values())
            
            # Apply filters
            if status:
                investigations = [inv for inv in investigations if inv.get("status") == status]
            
            if priority:
                investigations = [inv for inv in investigations if inv.get("priority") == priority]
            
            # Apply pagination
            investigations = investigations[offset:offset + limit]
            
            return investigations
            
        except Exception as e:
            logger.error(f"Failed to list investigations: {str(e)}")
            raise
    
    async def execute_agent(
        self, 
        agent_name: str, 
        input_data: Dict[str, Any], 
        background_tasks: BackgroundTasks
    ) -> Dict[str, Any]:
        """
        Execute a specific agent
        
        Args:
            agent_name: Name of the agent to execute
            input_data: Input data for the agent
            background_tasks: FastAPI background tasks
            
        Returns:
            Agent execution results
        """
        try:
            # Execute agent using production workflow
            # Note: The production workflow doesn't support single agent execution
            # This would need to be implemented if required
            logger.warning(f"Single agent execution not supported in production workflow: {agent_name}")
            return {
                "error": "Single agent execution not supported in production workflow",
                "agent_name": agent_name,
                "message": "Use the full investigation workflow instead"
            }
            
        except Exception as e:
            logger.error(f"Failed to execute agent {agent_name}: {str(e)}")
            raise
    
    async def get_agent_status(self, agent_name: str) -> AgentStatusResponse:
        """
        Get status of specific agent
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Agent status response
        """
        try:
            # Get agent status from production workflow
            # Note: The production workflow doesn't expose individual agent status
            # This would need to be implemented if required
            logger.warning(f"Individual agent status not available in production workflow: {agent_name}")
            return AgentStatusResponse(
                name=agent_name,
                status="unknown",
                last_execution=None,
                current_task="Production workflow doesn't expose individual agent status"
            )
            
        except Exception as e:
            logger.error(f"Failed to get agent status: {str(e)}")
            raise
    
    async def get_agent_statuses(self) -> List[AgentStatusResponse]:
        """
        Get status of all agents
        
        Returns:
            List of agent status responses
        """
        try:
            # Get all agent statuses from production workflow
            # Note: The production workflow doesn't expose individual agent statuses
            # This would need to be implemented if required
            logger.warning("Individual agent statuses not available in production workflow")
            return [
                AgentStatusResponse(
                    name="production_workflow",
                    status="active",
                    last_execution=None,
                    current_task="Production workflow with integrated agents"
                )
            ]
            
        except Exception as e:
            logger.error(f"Failed to get agent statuses: {str(e)}")
            raise
    
    async def get_workflow_info(self) -> Dict[str, Any]:
        """
        Get workflow information
        
        Returns:
            Workflow information
        """
        try:
            # Get workflow info from production workflow
            return {
                "workflow_type": "production_workflow",
                "description": "Production-ready AML investigation workflow with integrated agents",
                "agents": [
                    "router_agent",
                    "pattern_analyst",
                    "behavioral_analyst", 
                    "geographic_analyst",
                    "network_analyst",
                    "risk_assessor",
                    "report_synthesizer",
                    "chat_agent"
                ],
                "features": [
                    "Memory persistence",
                    "Chat functionality",
                    "Intelligent routing",
                    "Comprehensive error handling"
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get workflow info: {str(e)}")
            raise
