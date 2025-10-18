"""
Input Validators

This module contains input validation functions for the
Multi-Agent AML Investigation System.
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from app.core.logger import get_logger
from app.core.exceptions import AMLInvestigationException

logger = get_logger(__name__)


class InputValidator:
    """
    Input validator for AML investigation system
    
    This validator provides comprehensive input validation for
    all system inputs including investigation data, agent inputs, and API requests.
    """
    
    @staticmethod
    def validate_investigation_input(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate investigation input data
        
        Args:
            data: Investigation input data
            
        Returns:
            Validated data
            
        Raises:
            AMLInvestigationException: If validation fails
        """
        try:
            errors = []
            
            # Validate required fields
            required_fields = ["alert_id", "transaction_id"]
            for field in required_fields:
                if field not in data or not data[field]:
                    errors.append(f"Missing required field: {field}")
            
            # Validate alert ID format
            if "alert_id" in data:
                alert_id = data["alert_id"]
                if not alert_id.startswith("ALT"):
                    errors.append("Alert ID must start with 'ALT'")
                if len(alert_id) < 6:
                    errors.append("Alert ID must be at least 6 characters")
            
            # Validate transaction ID format
            if "transaction_id" in data:
                transaction_id = data["transaction_id"]
                if not transaction_id.startswith("T"):
                    errors.append("Transaction ID must start with 'T'")
                if len(transaction_id) < 6:
                    errors.append("Transaction ID must be at least 6 characters")
            
            # Validate priority
            if "priority" in data:
                priority = data["priority"]
                valid_priorities = ["low", "medium", "high", "critical"]
                if priority not in valid_priorities:
                    errors.append(f"Priority must be one of: {valid_priorities}")
            
            if errors:
                raise AMLInvestigationException(
                    "Input validation failed",
                    {"errors": errors, "input_data": data}
                )
            
            return data
            
        except Exception as e:
            logger.error(f"Investigation input validation failed: {str(e)}")
            raise
    
    @staticmethod
    def validate_agent_input(agent_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate agent input data
        
        Args:
            agent_name: Name of the agent
            data: Agent input data
            
        Returns:
            Validated data
            
        Raises:
            AMLInvestigationException: If validation fails
        """
        try:
            errors = []
            
            # Validate agent name
            valid_agents = [
                "coordinator", "data_enrichment", "pattern_analyst", 
                "risk_assessor", "report_synthesizer"
            ]
            if agent_name not in valid_agents:
                errors.append(f"Invalid agent name. Must be one of: {valid_agents}")
            
            # Validate based on agent type
            if agent_name == "coordinator":
                errors.extend(InputValidator._validate_coordinator_input(data))
            elif agent_name == "data_enrichment":
                errors.extend(InputValidator._validate_data_enrichment_input(data))
            elif agent_name == "pattern_analyst":
                errors.extend(InputValidator._validate_pattern_analyst_input(data))
            elif agent_name == "risk_assessor":
                errors.extend(InputValidator._validate_risk_assessor_input(data))
            elif agent_name == "report_synthesizer":
                errors.extend(InputValidator._validate_report_synthesizer_input(data))
            
            if errors:
                raise AMLInvestigationException(
                    f"Agent {agent_name} input validation failed",
                    {"errors": errors, "input_data": data}
                )
            
            return data
            
        except Exception as e:
            logger.error(f"Agent {agent_name} input validation failed: {str(e)}")
            raise
    
    @staticmethod
    def _validate_coordinator_input(data: Dict[str, Any]) -> List[str]:
        """Validate coordinator agent input"""
        errors = []
        
        # Coordinator requires investigation state
        if "investigation_state" not in data:
            errors.append("Coordinator requires investigation_state")
        
        return errors
    
    @staticmethod
    def _validate_data_enrichment_input(data: Dict[str, Any]) -> List[str]:
        """Validate data enrichment agent input"""
        errors = []
        
        # Data enrichment requires investigation state
        if "investigation_state" not in data:
            errors.append("Data enrichment requires investigation_state")
        
        return errors
    
    @staticmethod
    def _validate_pattern_analyst_input(data: Dict[str, Any]) -> List[str]:
        """Validate pattern analyst agent input"""
        errors = []
        
        # Pattern analyst requires enriched data
        if "investigation_state" not in data:
            errors.append("Pattern analyst requires investigation_state")
        elif "enriched_data" not in data.get("investigation_state", {}):
            errors.append("Pattern analyst requires enriched_data in investigation_state")
        
        return errors
    
    @staticmethod
    def _validate_risk_assessor_input(data: Dict[str, Any]) -> List[str]:
        """Validate risk assessor agent input"""
        errors = []
        
        # Risk assessor requires pattern analysis
        if "investigation_state" not in data:
            errors.append("Risk assessor requires investigation_state")
        elif "pattern_analysis" not in data.get("investigation_state", {}):
            errors.append("Risk assessor requires pattern_analysis in investigation_state")
        
        return errors
    
    @staticmethod
    def _validate_report_synthesizer_input(data: Dict[str, Any]) -> List[str]:
        """Validate report synthesizer agent input"""
        errors = []
        
        # Report synthesizer requires risk assessment
        if "investigation_state" not in data:
            errors.append("Report synthesizer requires investigation_state")
        elif "risk_assessment" not in data.get("investigation_state", {}):
            errors.append("Report synthesizer requires risk_assessment in investigation_state")
        
        return errors
    
# RAG validators removed - not using RAG functionality
    
    @staticmethod
    def validate_monitoring_request(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate monitoring request input
        
        Args:
            data: Monitoring request data
            
        Returns:
            Validated data
            
        Raises:
            AMLInvestigationException: If validation fails
        """
        try:
            errors = []
            
            # Validate period
            if "period" in data:
                period = data["period"]
                valid_periods = ["last_24h", "last_7d", "last_30d"]
                if period not in valid_periods:
                    errors.append(f"Period must be one of: {valid_periods}")
            
            # Validate limit
            if "limit" in data:
                limit = data["limit"]
                if not isinstance(limit, int) or limit < 1 or limit > 1000:
                    errors.append("Limit must be an integer between 1 and 1000")
            
            if errors:
                raise AMLInvestigationException(
                    "Monitoring request validation failed",
                    {"errors": errors, "input_data": data}
                )
            
            return data
            
        except Exception as e:
            logger.error(f"Monitoring request validation failed: {str(e)}")
            raise
    
    @staticmethod
    def validate_risk_level(risk_level: str) -> bool:
        """
        Validate risk level
        
        Args:
            risk_level: Risk level to validate
            
        Returns:
            True if valid, False otherwise
        """
        valid_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        return risk_level.upper() in valid_levels
    
    @staticmethod
    def validate_priority(priority: str) -> bool:
        """
        Validate priority level
        
        Args:
            priority: Priority to validate
            
        Returns:
            True if valid, False otherwise
        """
        valid_priorities = ["low", "medium", "high", "critical"]
        return priority.lower() in valid_priorities
    
    @staticmethod
    def sanitize_input(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize input data
        
        Args:
            data: Input data to sanitize
            
        Returns:
            Sanitized data
        """
        try:
            sanitized = {}
            
            for key, value in data.items():
                # Sanitize string values
                if isinstance(value, str):
                    # Remove potentially dangerous characters
                    sanitized_value = value.strip()
                    # Remove HTML tags
                    import re
                    sanitized_value = re.sub(r'<[^>]+>', '', sanitized_value)
                    sanitized[key] = sanitized_value
                elif isinstance(value, dict):
                    # Recursively sanitize nested dictionaries
                    sanitized[key] = InputValidator.sanitize_input(value)
                elif isinstance(value, list):
                    # Sanitize list items
                    sanitized[key] = [
                        InputValidator.sanitize_input(item) if isinstance(item, dict) else item
                        for item in value
                    ]
                else:
                    # Keep other types as-is
                    sanitized[key] = value
            
            return sanitized
            
        except Exception as e:
            logger.error(f"Input sanitization failed: {str(e)}")
            return data  # Return original data if sanitization fails
