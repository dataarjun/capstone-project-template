"""
AML Reports API Routes

This module provides RESTful API endpoints for AML investigation management,
including investigation triggers, Human-in-the-Loop approval workflow,
and multi-format report generation.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.core.logger import get_logger
from app.models.aml_models import (
    InvestigationSummary, BatchProcessingResult, ApprovalRequest, ApprovalResponse
)
from app.services.batch_processor import batch_processor, run_operational_demo, run_hi_trans_demo
from app.services.report_exporter import report_exporter
from app.utils.aml_data_loader import AMLDataLoader
from app.agents.aml_workflow import run_aml_investigation
from app.agents.tools.hitl_tools_simple import approval_workflow_manager

logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/aml", tags=["AML Investigations"])

# Global data loader
data_loader = AMLDataLoader()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class InvestigationRequest(BaseModel):
    """Request model for starting investigation"""
    alert_id: Optional[str] = None
    transaction_id: Optional[str] = None
    customer_id: Optional[str] = None
    priority: str = Field(default="medium", description="Investigation priority")
    enable_mock_approval: bool = Field(default=True, description="Enable mock approval for testing")


class BatchProcessingRequest(BaseModel):
    """Request model for batch processing"""
    dataset: str = Field(..., description="Dataset to process: 'operational' or 'hi_trans'")
    batch_size: int = Field(default=100, description="Batch size for processing")
    max_batches: Optional[int] = Field(None, description="Maximum batches to process")
    offset: int = Field(default=0, description="Starting offset")
    enable_mock_approval: bool = Field(default=True, description="Enable mock approval")


class ApprovalRequestModel(BaseModel):
    """Request model for manual approval"""
    case_id: str
    approver: str = Field(..., description="Name of approver")
    comments: Optional[str] = Field(None, description="Approval comments")


class InvestigationResponse(BaseModel):
    """Response model for investigation"""
    investigation_id: str
    status: str
    risk_level: str
    risk_score: int
    case_id: Optional[str]
    approval_status: Optional[str]
    execution_time: float
    created_at: datetime


# ============================================================================
# INVESTIGATION ENDPOINTS
# ============================================================================

@router.post("/investigate", response_model=InvestigationResponse)
async def start_investigation(
    request: InvestigationRequest,
    background_tasks: BackgroundTasks
) -> InvestigationResponse:
    """
    Start AML investigation from alert or transaction
    
    Args:
        request: Investigation request parameters
        background_tasks: FastAPI background tasks
        
    Returns:
        Investigation response with basic details
    """
    try:
        start_time = datetime.utcnow()
        
        # Enable mock approval if requested
        if request.enable_mock_approval:
            approval_workflow_manager.enable_mock_mode(auto_approve_threshold=70)
        
        if request.alert_id:
            # Load operational alert
            alert, transaction, customer = data_loader.load_operational_alert(request.alert_id)
            
            if not all([alert, transaction, customer]):
                raise HTTPException(
                    status_code=404,
                    detail=f"Alert {request.alert_id} not found or missing related data"
                )
            
            investigation_id = f"INV_{request.alert_id}"
            
        elif request.transaction_id and request.customer_id:
            # Direct transaction investigation
            transaction = {
                "transaction_id": request.transaction_id,
                "customer_id": request.customer_id,
                "amount": 0,  # Default values
                "currency": "USD",
                "transaction_type": "unknown",
                "location": "Unknown",
                "country": "US",
                "description": "Direct investigation"
            }
            
            customer = {
                "customer_id": request.customer_id,
                "customer_name": "Unknown",
                "customer_type": "LEG",
                "risk_level": "low",
                "kyc_status": "unknown",
                "location": "Unknown",
                "country": "US"
            }
            
            investigation_id = f"INV_{request.transaction_id}"
            
        else:
            raise HTTPException(
                status_code=400,
                detail="Either alert_id or (transaction_id + customer_id) must be provided"
            )
        
        # Run investigation in background
        background_tasks.add_task(
            _run_investigation_background,
            investigation_id,
            transaction,
            customer,
            request.alert_id
        )
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        return InvestigationResponse(
            investigation_id=investigation_id,
            status="started",
            risk_level="Unknown",
            risk_score=0,
            case_id=None,
            approval_status=None,
            execution_time=execution_time,
            created_at=start_time
        )
        
    except Exception as e:
        logger.error(f"Failed to start investigation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/investigations/{investigation_id}")
async def get_investigation(investigation_id: str) -> Dict[str, Any]:
    """
    Get investigation details by ID
    
    Args:
        investigation_id: Investigation ID
        
    Returns:
        Investigation details
    """
    try:
        # In a real implementation, this would fetch from database
        # For now, return a mock response
        return {
            "investigation_id": investigation_id,
            "status": "completed",
            "message": "Investigation details would be fetched from database"
        }
        
    except Exception as e:
        logger.error(f"Failed to get investigation {investigation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-process")
async def start_batch_processing(
    request: BatchProcessingRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Start batch processing of transactions
    
    Args:
        request: Batch processing request
        background_tasks: FastAPI background tasks
        
    Returns:
        Batch processing status
    """
    try:
        # Enable mock approval if requested
        if request.enable_mock_approval:
            approval_workflow_manager.enable_mock_mode(auto_approve_threshold=70)
        
        # Start batch processing in background
        background_tasks.add_task(
            _run_batch_processing_background,
            request.dataset,
            request.batch_size,
            request.max_batches,
            request.offset
        )
        
        return {
            "status": "started",
            "dataset": request.dataset,
            "batch_size": request.batch_size,
            "max_batches": request.max_batches,
            "offset": request.offset,
            "message": "Batch processing started in background"
        }
        
    except Exception as e:
        logger.error(f"Failed to start batch processing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# HUMAN APPROVAL ENDPOINTS
# ============================================================================

@router.get("/pending-approvals")
async def get_pending_approvals() -> Dict[str, Any]:
    """
    Get list of cases awaiting human approval
    
    Returns:
        List of pending approval requests
    """
    try:
        dashboard_data = approval_workflow_manager.get_approval_dashboard_data()
        
        return {
            "pending_approvals": dashboard_data["pending_approvals"],
            "stats": dashboard_data["stats"],
            "mock_mode": dashboard_data["mock_mode"]
        }
        
    except Exception as e:
        logger.error(f"Failed to get pending approvals: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approvals/{case_id}/approve")
async def approve_case(
    case_id: str,
    request: ApprovalRequestModel
) -> Dict[str, Any]:
    """
    Approve a case
    
    Args:
        case_id: Case ID to approve
        request: Approval request details
        
    Returns:
        Approval confirmation
    """
    try:
        success = approval_workflow_manager.approve_case(
            case_id=case_id,
            approver=request.approver,
            comments=request.comments
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Case {case_id} not found in pending approvals"
            )
        
        return {
            "status": "approved",
            "case_id": case_id,
            "approver": request.approver,
            "approved_at": datetime.utcnow().isoformat(),
            "comments": request.comments
        }
        
    except Exception as e:
        logger.error(f"Failed to approve case {case_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approvals/{case_id}/reject")
async def reject_case(
    case_id: str,
    request: ApprovalRequestModel
) -> Dict[str, Any]:
    """
    Reject a case
    
    Args:
        case_id: Case ID to reject
        request: Rejection request details
        
    Returns:
        Rejection confirmation
    """
    try:
        success = approval_workflow_manager.reject_case(
            case_id=case_id,
            approver=request.approver,
            comments=request.comments
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Case {case_id} not found in pending approvals"
            )
        
        return {
            "status": "rejected",
            "case_id": case_id,
            "approver": request.approver,
            "rejected_at": datetime.utcnow().isoformat(),
            "comments": request.comments
        }
        
    except Exception as e:
        logger.error(f"Failed to reject case {case_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/approvals/{case_id}/details")
async def get_approval_details(case_id: str) -> Dict[str, Any]:
    """
    Get approval details for a specific case
    
    Args:
        case_id: Case ID
        
    Returns:
        Approval details
    """
    try:
        # In a real implementation, this would fetch from database
        return {
            "case_id": case_id,
            "status": "pending",
            "message": "Approval details would be fetched from database"
        }
        
    except Exception as e:
        logger.error(f"Failed to get approval details for {case_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# REPORT EXPORT ENDPOINTS
# ============================================================================

@router.get("/cases/{case_id}")
async def get_case_details(case_id: str) -> Dict[str, Any]:
    """
    Get case details by ID
    
    Args:
        case_id: Case ID
        
    Returns:
        Case details
    """
    try:
        # In a real implementation, this would fetch from database
        return {
            "case_id": case_id,
            "status": "completed",
            "message": "Case details would be fetched from database"
        }
        
    except Exception as e:
        logger.error(f"Failed to get case {case_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/{case_id}/export")
async def export_case_report(
    case_id: str,
    format: str = Query(..., description="Export format: json, csv, markdown, pdf")
) -> FileResponse:
    """
    Export case report in specified format
    
    Args:
        case_id: Case ID
        format: Export format
        
    Returns:
        File response with exported report
    """
    try:
        # In a real implementation, this would fetch case data from database
        # For demo, create mock case data
        mock_case_data = [{
            "case_id": case_id,
            "risk_level": "High",
            "risk_score": 75,
            "status": "SAR_FILED",
            "transaction": {
                "amount": 50000,
                "currency": "USD",
                "type": "wire"
            }
        }]
        
        if format == "json":
            filepath = await report_exporter.export_json(mock_case_data, f"case_{case_id}.json")
        elif format == "csv":
            filepath = await report_exporter.export_csv(mock_case_data, f"case_{case_id}.csv")
        elif format == "markdown":
            filepath = await report_exporter.export_markdown(mock_case_data, f"case_{case_id}.md")
        elif format == "pdf":
            filepath = await report_exporter.export_pdf(mock_case_data, f"case_{case_id}.pdf")
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
        
        return FileResponse(
            path=filepath,
            filename=f"case_{case_id}.{format}",
            media_type="application/octet-stream"
        )
        
    except Exception as e:
        logger.error(f"Failed to export case {case_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reports/batch-export")
async def export_batch_reports(
    format: str = Query(..., description="Export format: json, csv, markdown, pdf"),
    limit: int = Query(10, description="Number of cases to export")
) -> FileResponse:
    """
    Export batch of reports in specified format
    
    Args:
        format: Export format
        limit: Number of cases to export
        
    Returns:
        File response with exported reports
    """
    try:
        # In a real implementation, this would fetch from database
        # For demo, create mock batch data
        mock_batch_data = []
        for i in range(limit):
            mock_batch_data.append({
                "case_id": f"CASE_{i:03d}",
                "risk_level": "High" if i % 2 == 0 else "Medium",
                "risk_score": 70 + (i * 3),
                "status": "SAR_FILED" if i % 2 == 0 else "REVIEW_COMPLETED"
            })
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        if format == "json":
            filepath = await report_exporter.export_json(mock_batch_data, f"batch_report_{timestamp}.json")
        elif format == "csv":
            filepath = await report_exporter.export_csv(mock_batch_data, f"batch_report_{timestamp}.csv")
        elif format == "markdown":
            filepath = await report_exporter.export_markdown(mock_batch_data, f"batch_report_{timestamp}.md")
        elif format == "pdf":
            filepath = await report_exporter.export_pdf(mock_batch_data, f"batch_report_{timestamp}.pdf")
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
        
        return FileResponse(
            path=filepath,
            filename=f"batch_report_{timestamp}.{format}",
            media_type="application/octet-stream"
        )
        
    except Exception as e:
        logger.error(f"Failed to export batch reports: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DEMO ENDPOINTS
# ============================================================================

@router.post("/demo/operational")
async def run_operational_demo_api(
    limit: int = Query(5, description="Number of alerts to process")
) -> Dict[str, Any]:
    """
    Run operational alerts demo
    
    Args:
        limit: Number of alerts to process
        
    Returns:
        Demo results
    """
    try:
        results = await run_operational_demo(limit=limit)
        return results
        
    except Exception as e:
        logger.error(f"Operational demo failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/demo/hi-trans")
async def run_hi_trans_demo_api(
    batch_size: int = Query(100, description="Transactions per batch"),
    max_batches: int = Query(2, description="Maximum batches to process")
) -> Dict[str, Any]:
    """
    Run HI-Small_Trans demo
    
    Args:
        batch_size: Transactions per batch
        max_batches: Maximum batches to process
        
    Returns:
        Demo results
    """
    try:
        results = await run_hi_trans_demo(batch_size=batch_size, max_batches=max_batches)
        return results
        
    except Exception as e:
        logger.error(f"HI-Trans demo failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BACKGROUND TASKS
# ============================================================================

async def _run_investigation_background(
    investigation_id: str,
    transaction: Dict[str, Any],
    customer: Dict[str, Any],
    alert_id: Optional[str]
):
    """Background task for running investigation"""
    try:
        logger.info(f"Starting background investigation: {investigation_id}")
        
        result = await run_aml_investigation(
            transaction_data=transaction,
            customer_data=customer,
            alert_id=alert_id
        )
        
        logger.info(f"Background investigation completed: {investigation_id}")
        
    except Exception as e:
        logger.error(f"Background investigation failed {investigation_id}: {str(e)}")


async def _run_batch_processing_background(
    dataset: str,
    batch_size: int,
    max_batches: Optional[int],
    offset: int
):
    """Background task for batch processing"""
    try:
        logger.info(f"Starting background batch processing: {dataset}")
        
        results, summary = await batch_processor.process_with_progress_tracking(
            dataset=dataset,
            batch_size=batch_size,
            max_batches=max_batches,
            offset=offset,
            enable_mock_approval=True
        )
        
        logger.info(f"Background batch processing completed: {dataset}")
        
    except Exception as e:
        logger.error(f"Background batch processing failed {dataset}: {str(e)}")


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for AML service
    
    Returns:
        Service health status
    """
    return {
        "status": "healthy",
        "service": "AML Investigation API",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
