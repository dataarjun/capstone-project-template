"""
Custom Exception Classes

This module defines custom exception classes for the Multi-Agent AML
Investigation System to provide better error handling and user feedback.
"""

from typing import Optional, Dict, Any


class AMLInvestigationException(Exception):
    """Base exception for AML investigation system"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class AgentExecutionException(AMLInvestigationException):
    """Exception raised when agent execution fails"""
    
    def __init__(self, agent_name: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.agent_name = agent_name
        super().__init__(f"Agent {agent_name} execution failed: {message}", details)


class InvestigationTimeoutException(AMLInvestigationException):
    """Exception raised when investigation times out"""
    
    def __init__(self, investigation_id: str, timeout_seconds: int):
        self.investigation_id = investigation_id
        self.timeout_seconds = timeout_seconds
        super().__init__(
            f"Investigation {investigation_id} timed out after {timeout_seconds} seconds"
        )


class DatabaseConnectionException(AMLInvestigationException):
    """Exception raised when database connection fails"""
    
    def __init__(self, database_type: str, message: str):
        self.database_type = database_type
        super().__init__(f"Database connection failed ({database_type}): {message}")


class VectorDatabaseException(AMLInvestigationException):
    """Exception raised when vector database operations fail"""
    
    def __init__(self, operation: str, message: str):
        self.operation = operation
        super().__init__(f"Vector database operation failed ({operation}): {message}")


# RAG exceptions removed - not using RAG functionality


class MonitoringException(AMLInvestigationException):
    """Exception raised when monitoring/logging fails"""
    
    def __init__(self, service: str, message: str):
        self.service = service
        super().__init__(f"Monitoring service {service} failed: {message}")


class ConfigurationException(AMLInvestigationException):
    """Exception raised when configuration is invalid"""
    
    def __init__(self, setting: str, message: str):
        self.setting = setting
        super().__init__(f"Configuration error for {setting}: {message}")
