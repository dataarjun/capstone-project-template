"""
Structured Logging Configuration

This module provides structured logging configuration for the application
with support for different log levels and output formats.
"""

import logging
import sys
from typing import Optional
from app.core.config_simple import settings


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance
    
    Args:
        name: Logger name (usually __name__)
        level: Log level override
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Set log level
        log_level = level or settings.LOG_LEVEL
        logger.setLevel(getattr(logging, log_level.upper()))
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Prevent duplicate logs
        logger.propagate = False
    
    return logger


class AuditLogger:
    """Audit logger for compliance and regulatory requirements"""
    
    def __init__(self):
        self.logger = get_logger("audit")
    
    def log_investigation_start(self, investigation_id: str, alert_id: str, user_id: str):
        """Log investigation start event"""
        self.logger.info(
            f"Investigation started - ID: {investigation_id}, Alert: {alert_id}, User: {user_id}"
        )
    
    def log_agent_execution(self, agent_name: str, investigation_id: str, status: str):
        """Log agent execution event"""
        self.logger.info(
            f"Agent execution - Agent: {agent_name}, Investigation: {investigation_id}, Status: {status}"
        )
    
    def log_investigation_complete(self, investigation_id: str, risk_level: str, findings: dict):
        """Log investigation completion"""
        self.logger.info(
            f"Investigation completed - ID: {investigation_id}, Risk: {risk_level}, Findings: {findings}"
        )


# Global audit logger instance
audit_logger = AuditLogger()
