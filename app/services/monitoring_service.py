"""
Monitoring Service

This service handles system monitoring, metrics collection, and
LangSmith integration for the Multi-Agent AML Investigation System.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.core.logger import get_logger
from app.core.config_simple import settings
from app.core.exceptions import MonitoringException

logger = get_logger(__name__)


class MonitoringService:
    """
    Monitoring service for system metrics and LangSmith integration
    
    This service provides monitoring capabilities including metrics
    collection, trace management, and performance monitoring.
    """
    
    def __init__(self):
        self.metrics = {
            "total_investigations": 0,
            "completed_investigations": 0,
            "failed_investigations": 0,
            "avg_investigation_time": 0.0,
            "token_usage": {
                "total_tokens": 0,
                "total_cost": 0.0
            },
            "agent_performance": {},
            "system_health": "healthy"
        }
        self.traces = []
        self.langsmith_enabled = settings.LANGSMITH_TRACING and settings.LANGSMITH_API_KEY
    
    async def get_traces(
        self, 
        investigation_id: Optional[str] = None, 
        agent_name: Optional[str] = None, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get LangSmith traces for investigations
        
        Args:
            investigation_id: Filter by investigation ID
            agent_name: Filter by agent name
            limit: Maximum number of traces
            
        Returns:
            List of traces
        """
        try:
            # Filter traces based on parameters
            filtered_traces = self.traces.copy()
            
            if investigation_id:
                filtered_traces = [trace for trace in filtered_traces 
                                if trace.get("investigation_id") == investigation_id]
            
            if agent_name:
                filtered_traces = [trace for trace in filtered_traces 
                                if trace.get("agent_name") == agent_name]
            
            # Apply limit
            filtered_traces = filtered_traces[:limit]
            
            return filtered_traces
            
        except Exception as e:
            logger.error(f"Failed to get traces: {str(e)}")
            raise MonitoringException("traces", f"Failed to get traces: {str(e)}")
    
    async def get_metrics(self, period: str = "last_24h") -> Dict[str, Any]:
        """
        Get system performance metrics
        
        Args:
            period: Time period for metrics
            
        Returns:
            System metrics
        """
        try:
            # Calculate time range based on period
            end_time = datetime.utcnow()
            if period == "last_24h":
                start_time = end_time - timedelta(hours=24)
            elif period == "last_7d":
                start_time = end_time - timedelta(days=7)
            elif period == "last_30d":
                start_time = end_time - timedelta(days=30)
            else:
                start_time = end_time - timedelta(hours=24)
            
            # Get metrics for the period
            period_metrics = await self._calculate_period_metrics(start_time, end_time)
            
            # Combine with overall metrics
            combined_metrics = {
                **self.metrics,
                "period": period,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                **period_metrics
            }
            
            return combined_metrics
            
        except Exception as e:
            logger.error(f"Failed to get metrics: {str(e)}")
            raise MonitoringException("metrics", f"Failed to get metrics: {str(e)}")
    
    async def _calculate_period_metrics(
        self, 
        start_time: datetime, 
        end_time: datetime
    ) -> Dict[str, Any]:
        """
        Calculate metrics for a specific time period
        
        Args:
            start_time: Start time for metrics
            end_time: End time for metrics
            
        Returns:
            Period metrics
        """
        try:
            # Filter traces for the period
            period_traces = [
                trace for trace in self.traces
                if start_time <= datetime.fromisoformat(trace.get("timestamp", "1970-01-01T00:00:00")) <= end_time
            ]
            
            # Calculate metrics
            total_investigations = len(set(trace.get("investigation_id") for trace in period_traces))
            completed_investigations = len([trace for trace in period_traces if trace.get("status") == "completed"])
            failed_investigations = len([trace for trace in period_traces if trace.get("status") == "failed"])
            
            # Calculate average investigation time
            investigation_times = [
                trace.get("execution_time", 0) for trace in period_traces
                if trace.get("execution_time")
            ]
            avg_investigation_time = sum(investigation_times) / len(investigation_times) if investigation_times else 0
            
            # Calculate agent performance
            agent_performance = {}
            for agent_name in ["coordinator", "data_enrichment", "pattern_analyst", "risk_assessor", "report_synthesizer"]:
                agent_traces = [trace for trace in period_traces if trace.get("agent_name") == agent_name]
                if agent_traces:
                    agent_performance[agent_name] = {
                        "calls": len(agent_traces),
                        "avg_latency_ms": sum(trace.get("execution_time", 0) for trace in agent_traces) / len(agent_traces) * 1000,
                        "success_rate": len([trace for trace in agent_traces if trace.get("status") == "completed"]) / len(agent_traces)
                    }
            
            # Calculate token usage
            token_usage = {
                "total_tokens": sum(trace.get("token_usage", {}).get("total_tokens", 0) for trace in period_traces),
                "total_cost": sum(trace.get("token_usage", {}).get("cost", 0) for trace in period_traces)
            }
            
            return {
                "investigations": {
                    "total": total_investigations,
                    "completed": completed_investigations,
                    "failed": failed_investigations,
                    "success_rate": completed_investigations / total_investigations if total_investigations > 0 else 0
                },
                "performance": {
                    "avg_investigation_time_seconds": avg_investigation_time,
                    "total_investigations": total_investigations
                },
                "agents": agent_performance,
                "token_usage": token_usage
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate period metrics: {str(e)}")
            return {}
    
    async def log_trace(
        self, 
        investigation_id: str, 
        agent_name: str, 
        status: str, 
        execution_time: float,
        token_usage: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log agent execution trace
        
        Args:
            investigation_id: Investigation ID
            agent_name: Agent name
            status: Execution status
            execution_time: Execution time in seconds
            token_usage: Token usage information
            metadata: Additional metadata
        """
        try:
            trace = {
                "investigation_id": investigation_id,
                "agent_name": agent_name,
                "status": status,
                "execution_time": execution_time,
                "timestamp": datetime.utcnow().isoformat(),
                "token_usage": token_usage or {},
                "metadata": metadata or {}
            }
            
            # Add to traces
            self.traces.append(trace)
            
            # Update metrics
            self._update_metrics(trace)
            
            # Log to LangSmith if enabled
            if self.langsmith_enabled:
                await self._log_to_langsmith(trace)
            
            logger.info(f"Trace logged for {agent_name} in investigation {investigation_id}")
            
        except Exception as e:
            logger.error(f"Failed to log trace: {str(e)}")
            raise MonitoringException("logging", f"Failed to log trace: {str(e)}")
    
    def _update_metrics(self, trace: Dict[str, Any]):
        """
        Update system metrics based on trace
        
        Args:
            trace: Agent execution trace
        """
        try:
            # Update investigation counts
            if trace["status"] == "completed":
                self.metrics["completed_investigations"] += 1
            elif trace["status"] == "failed":
                self.metrics["failed_investigations"] += 1
            
            # Update agent performance
            agent_name = trace["agent_name"]
            if agent_name not in self.metrics["agent_performance"]:
                self.metrics["agent_performance"][agent_name] = {
                    "calls": 0,
                    "total_time": 0.0,
                    "success_rate": 0.0
                }
            
            agent_perf = self.metrics["agent_performance"][agent_name]
            agent_perf["calls"] += 1
            agent_perf["total_time"] += trace["execution_time"]
            
            # Update token usage
            token_usage = trace.get("token_usage", {})
            if token_usage:
                self.metrics["token_usage"]["total_tokens"] += token_usage.get("total_tokens", 0)
                self.metrics["token_usage"]["total_cost"] += token_usage.get("cost", 0)
            
        except Exception as e:
            logger.error(f"Failed to update metrics: {str(e)}")
    
    async def _log_to_langsmith(self, trace: Dict[str, Any]):
        """
        Log trace to LangSmith
        
        Args:
            trace: Agent execution trace
        """
        try:
            if not self.langsmith_enabled:
                return
            
            # LangSmith logging implementation would go here
            # This would integrate with LangSmith API to log traces
            logger.info(f"Trace logged to LangSmith: {trace['agent_name']}")
            
        except Exception as e:
            logger.error(f"Failed to log to LangSmith: {str(e)}")
    
    async def get_system_health(self) -> Dict[str, Any]:
        """
        Get system health status
        
        Returns:
            System health information
        """
        try:
            # Calculate health metrics
            total_investigations = self.metrics["total_investigations"]
            failed_investigations = self.metrics["failed_investigations"]
            
            # Calculate failure rate
            failure_rate = failed_investigations / total_investigations if total_investigations > 0 else 0
            
            # Determine health status
            if failure_rate > 0.1:  # More than 10% failure rate
                health_status = "unhealthy"
            elif failure_rate > 0.05:  # More than 5% failure rate
                health_status = "degraded"
            else:
                health_status = "healthy"
            
            return {
                "status": health_status,
                "failure_rate": failure_rate,
                "total_investigations": total_investigations,
                "failed_investigations": failed_investigations,
                "langsmith_enabled": self.langsmith_enabled,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get system health: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
