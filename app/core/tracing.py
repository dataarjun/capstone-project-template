"""
Tracing and Monitoring for AML Agents

This module provides comprehensive tracing and monitoring capabilities
for all AML agents using LangSmith integration.
"""

import os
import uuid
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from functools import wraps
from langsmith import Client
from langchain_core.runnables import RunnableLambda
from app.core.logger import get_logger

logger = get_logger(__name__)


class AMLTracer:
    """
    Comprehensive tracing for AML multi-agent system
    """
    
    def __init__(self):
        self.client = Client()
        self.project_name = "aml-multi-agent-system"
        self.session_id = str(uuid.uuid4())
        
        # Agent performance metrics
        self.agent_metrics = {
            "risk_assessor": {"calls": 0, "avg_time": 0, "errors": 0},
            "pattern_analyst": {"calls": 0, "avg_time": 0, "errors": 0},
            "report_synthesizer": {"calls": 0, "avg_time": 0, "errors": 0},
            "data_enrichment": {"calls": 0, "avg_time": 0, "errors": 0},
            "coordinator": {"calls": 0, "avg_time": 0, "errors": 0}
        }
    
    def trace_agent_call(self, agent_name: str, operation: str = "process"):
        """
        Decorator to trace agent function calls
        """
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = datetime.utcnow()
                call_id = str(uuid.uuid4())
                
                try:
                    # Log agent call start
                    logger.info(f"Agent {agent_name} {operation} started (call_id: {call_id})")
                    
                    # Execute the function
                    result = await func(*args, **kwargs)
                    
                    # Calculate execution time
                    execution_time = (datetime.utcnow() - start_time).total_seconds()
                    
                    # Update metrics
                    self._update_agent_metrics(agent_name, execution_time, success=True)
                    
                    # Log success
                    logger.info(f"Agent {agent_name} {operation} completed in {execution_time:.2f}s")
                    
                    return result
                    
                except Exception as e:
                    # Update error metrics
                    self._update_agent_metrics(agent_name, 0, success=False)
                    
                    # Log error
                    logger.error(f"Agent {agent_name} {operation} failed: {e}")
                    raise
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = datetime.utcnow()
                call_id = str(uuid.uuid4())
                
                try:
                    # Log agent call start
                    logger.info(f"Agent {agent_name} {operation} started (call_id: {call_id})")
                    
                    # Execute the function
                    result = func(*args, **kwargs)
                    
                    # Calculate execution time
                    execution_time = (datetime.utcnow() - start_time).total_seconds()
                    
                    # Update metrics
                    self._update_agent_metrics(agent_name, execution_time, success=True)
                    
                    # Log success
                    logger.info(f"Agent {agent_name} {operation} completed in {execution_time:.2f}s")
                    
                    return result
                    
                except Exception as e:
                    # Update error metrics
                    self._update_agent_metrics(agent_name, 0, success=False)
                    
                    # Log error
                    logger.error(f"Agent {agent_name} {operation} failed: {e}")
                    raise
            
            # Return appropriate wrapper based on function type
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    def _update_agent_metrics(self, agent_name: str, execution_time: float, success: bool):
        """Update agent performance metrics"""
        if agent_name in self.agent_metrics:
            metrics = self.agent_metrics[agent_name]
            metrics["calls"] += 1
            
            if success:
                # Update average execution time
                total_time = metrics["avg_time"] * (metrics["calls"] - 1) + execution_time
                metrics["avg_time"] = total_time / metrics["calls"]
            else:
                metrics["errors"] += 1
    
    def create_agent_chain_with_tracing(self, agent_name: str, chain, 
                                       metadata: Optional[Dict[str, Any]] = None):
        """
        Wrap a chain with tracing capabilities
        
        Args:
            agent_name: Name of the agent
            chain: LangChain chain to wrap
            metadata: Optional metadata to include in traces
            
        Returns:
            Traced chain
        """
        def trace_inputs(inputs: Dict[str, Any]) -> Dict[str, Any]:
            """Log chain inputs"""
            logger.info(f"Agent {agent_name} inputs: {list(inputs.keys())}")
            return inputs
        
        def trace_outputs(outputs: Any) -> Any:
            """Log chain outputs"""
            logger.info(f"Agent {agent_name} outputs generated")
            return outputs
        
        # Create traced chain
        traced_chain = (
            RunnableLambda(trace_inputs) 
            | chain 
            | RunnableLambda(trace_outputs)
        )
        
        return traced_chain
    
    def get_agent_metrics(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get performance metrics for agents
        
        Args:
            agent_name: Optional specific agent name
            
        Returns:
            Performance metrics
        """
        if agent_name:
            return self.agent_metrics.get(agent_name, {})
        else:
            return self.agent_metrics
    
    def get_session_traces(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get traces for the current session
        
        Args:
            limit: Maximum number of traces to return
            
        Returns:
            List of trace information
        """
        try:
            # This would integrate with LangSmith to get actual traces
            # For now, return session information
            return {
                "session_id": self.session_id,
                "project": self.project_name,
                "agent_metrics": self.agent_metrics,
                "message": "Traces would be retrieved from LangSmith"
            }
        except Exception as e:
            logger.error(f"Failed to get session traces: {e}")
            return {}
    
    def create_investigation_trace(self, case_id: str, investigation_data: Dict[str, Any]):
        """
        Create a trace for an entire investigation
        
        Args:
            case_id: Investigation case ID
            investigation_data: Investigation data to trace
        """
        try:
            trace_data = {
                "case_id": case_id,
                "session_id": self.session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "investigation_data": investigation_data,
                "agents_involved": list(self.agent_metrics.keys())
            }
            
            logger.info(f"Created investigation trace for case {case_id}")
            return trace_data
            
        except Exception as e:
            logger.error(f"Failed to create investigation trace: {e}")
            return {}


# Global tracer instance
aml_tracer = AMLTracer()


# Convenience decorators for agents
def trace_risk_assessor(operation: str = "assess_risk"):
    """Decorator for risk assessor tracing"""
    return aml_tracer.trace_agent_call("risk_assessor", operation)


def trace_pattern_analyst(operation: str = "analyze_patterns"):
    """Decorator for pattern analyst tracing"""
    return aml_tracer.trace_agent_call("pattern_analyst", operation)


def trace_report_synthesizer(operation: str = "synthesize_report"):
    """Decorator for report synthesizer tracing"""
    return aml_tracer.trace_agent_call("report_synthesizer", operation)


def trace_data_enrichment(operation: str = "enrich_data"):
    """Decorator for data enrichment tracing"""
    return aml_tracer.trace_agent_call("data_enrichment", operation)


def trace_coordinator(operation: str = "coordinate"):
    """Decorator for coordinator tracing"""
    return aml_tracer.trace_agent_call("coordinator", operation)
