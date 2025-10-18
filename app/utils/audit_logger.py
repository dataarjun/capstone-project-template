"""
Audit Logger

This module provides audit logging functionality for compliance
and regulatory requirements in the AML investigation system.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from app.core.logger import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class AuditLogger:
    """
    Audit logger for compliance and regulatory requirements
    
    This logger provides structured audit logging for all investigation
    activities to meet regulatory compliance requirements.
    """
    
    def __init__(self):
        self.audit_entries = []
        self.logger = get_logger("audit")
    
    def log_investigation_start(
        self, 
        investigation_id: str, 
        alert_id: str, 
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log investigation start event
        
        Args:
            investigation_id: Investigation ID
            alert_id: Alert ID
            user_id: User ID who started the investigation
            metadata: Additional metadata
        """
        try:
            audit_entry = {
                "event_type": "investigation_start",
                "investigation_id": investigation_id,
                "alert_id": alert_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            
            self._log_audit_entry(audit_entry)
            
        except Exception as e:
            logger.error(f"Failed to log investigation start: {str(e)}")
    
    def log_agent_execution(
        self, 
        investigation_id: str, 
        agent_name: str, 
        status: str,
        execution_time: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log agent execution event
        
        Args:
            investigation_id: Investigation ID
            agent_name: Agent name
            status: Execution status
            execution_time: Execution time in seconds
            metadata: Additional metadata
        """
        try:
            audit_entry = {
                "event_type": "agent_execution",
                "investigation_id": investigation_id,
                "agent_name": agent_name,
                "status": status,
                "execution_time": execution_time,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            
            self._log_audit_entry(audit_entry)
            
        except Exception as e:
            logger.error(f"Failed to log agent execution: {str(e)}")
    
    def log_investigation_complete(
        self, 
        investigation_id: str, 
        risk_level: str, 
        findings: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log investigation completion
        
        Args:
            investigation_id: Investigation ID
            risk_level: Final risk level
            findings: Investigation findings
            metadata: Additional metadata
        """
        try:
            audit_entry = {
                "event_type": "investigation_complete",
                "investigation_id": investigation_id,
                "risk_level": risk_level,
                "findings": findings,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            
            self._log_audit_entry(audit_entry)
            
        except Exception as e:
            logger.error(f"Failed to log investigation completion: {str(e)}")
    
    def log_data_access(
        self, 
        user_id: str, 
        data_type: str, 
        access_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log data access event
        
        Args:
            user_id: User ID
            data_type: Type of data accessed
            access_type: Type of access (read, write, delete)
            metadata: Additional metadata
        """
        try:
            audit_entry = {
                "event_type": "data_access",
                "user_id": user_id,
                "data_type": data_type,
                "access_type": access_type,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            
            self._log_audit_entry(audit_entry)
            
        except Exception as e:
            logger.error(f"Failed to log data access: {str(e)}")
    
    def log_system_event(
        self, 
        event_type: str, 
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log system event
        
        Args:
            event_type: Type of system event
            description: Event description
            metadata: Additional metadata
        """
        try:
            audit_entry = {
                "event_type": "system_event",
                "system_event_type": event_type,
                "description": description,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            
            self._log_audit_entry(audit_entry)
            
        except Exception as e:
            logger.error(f"Failed to log system event: {str(e)}")
    
    def _log_audit_entry(self, audit_entry: Dict[str, Any]):
        """
        Log audit entry to both logger and internal storage
        
        Args:
            audit_entry: Audit entry to log
        """
        try:
            # Log to structured logger
            self.logger.info(
                f"Audit: {audit_entry['event_type']} - {audit_entry.get('investigation_id', 'N/A')}",
                extra=audit_entry
            )
            
            # Store in internal audit entries
            self.audit_entries.append(audit_entry)
            
            # Keep only last 1000 entries in memory
            if len(self.audit_entries) > 1000:
                self.audit_entries = self.audit_entries[-1000:]
                
        except Exception as e:
            logger.error(f"Failed to log audit entry: {str(e)}")
    
    def get_audit_trail(
        self, 
        investigation_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get audit trail entries
        
        Args:
            investigation_id: Filter by investigation ID
            event_type: Filter by event type
            limit: Maximum number of entries
            
        Returns:
            List of audit entries
        """
        try:
            filtered_entries = self.audit_entries.copy()
            
            if investigation_id:
                filtered_entries = [
                    entry for entry in filtered_entries
                    if entry.get("investigation_id") == investigation_id
                ]
            
            if event_type:
                filtered_entries = [
                    entry for entry in filtered_entries
                    if entry.get("event_type") == event_type
                ]
            
            # Sort by timestamp (newest first)
            filtered_entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            return filtered_entries[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get audit trail: {str(e)}")
            return []
    
    def export_audit_trail(
        self, 
        investigation_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Export audit trail for compliance reporting
        
        Args:
            investigation_id: Filter by investigation ID
            start_date: Start date filter
            end_date: End date filter
            
        Returns:
            List of audit entries for export
        """
        try:
            filtered_entries = self.audit_entries.copy()
            
            if investigation_id:
                filtered_entries = [
                    entry for entry in filtered_entries
                    if entry.get("investigation_id") == investigation_id
                ]
            
            if start_date:
                filtered_entries = [
                    entry for entry in filtered_entries
                    if datetime.fromisoformat(entry.get("timestamp", "1970-01-01T00:00:00")) >= start_date
                ]
            
            if end_date:
                filtered_entries = [
                    entry for entry in filtered_entries
                    if datetime.fromisoformat(entry.get("timestamp", "1970-01-01T00:00:00")) <= end_date
                ]
            
            # Sort by timestamp
            filtered_entries.sort(key=lambda x: x.get("timestamp", ""))
            
            return filtered_entries
            
        except Exception as e:
            logger.error(f"Failed to export audit trail: {str(e)}")
            return []


# Global audit logger instance
audit_logger = AuditLogger()
