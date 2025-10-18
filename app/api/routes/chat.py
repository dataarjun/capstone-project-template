"""
Chat API Routes for Production AML Workflow

This module provides chat functionality for the production AML workflow,
allowing users to interact with investigation results and ask questions.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import json
import asyncio

from app.core.logger import get_logger
from app.agents import production_workflow, analyze_transaction, query_investigations

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ChatMessage(BaseModel):
    """Chat message model"""
    prompt: str = Field(..., description="User prompt/query (first message starts new conversation)")
    thread_id: Optional[str] = Field(None, description="Thread ID for conversation continuity")
    investigation_id: Optional[str] = Field(None, description="Investigation ID for context")

class ChatResponse(BaseModel):
    """Chat response model"""
    prompt: str = Field(..., description="User prompt")
    response: str = Field(..., description="Assistant response")
    thread_id: str = Field(..., description="Thread ID for conversation continuity")
    investigation_id: Optional[str] = Field(None, description="Investigation ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    context: Optional[Dict[str, Any]] = Field(None, description="Investigation context")

class InvestigationRequest(BaseModel):
    """Investigation request model"""
    transaction_id: str = Field(..., description="Transaction ID to investigate")
    user_query: Optional[str] = Field(None, description="Initial user query")
    thread_id: Optional[str] = Field(None, description="Thread ID for conversation continuity")

class InvestigationResponse(BaseModel):
    """Investigation response model"""
    investigation_id: str = Field(..., description="Investigation ID")
    thread_id: str = Field(..., description="Thread ID for conversation continuity")
    status: str = Field(..., description="Investigation status")
    results: Optional[Dict[str, Any]] = Field(None, description="Investigation results")
    chat_ready: bool = Field(..., description="Whether chat is ready")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")

class ThreadInfo(BaseModel):
    """Thread information model"""
    thread_id: str = Field(..., description="Thread ID")
    investigation_id: Optional[str] = Field(None, description="Investigation ID")
    created_at: datetime = Field(..., description="Thread creation timestamp")
    last_activity: datetime = Field(..., description="Last activity timestamp")
    message_count: int = Field(..., description="Number of messages in thread")
    status: str = Field(..., description="Thread status")

class ThreadCreateRequest(BaseModel):
    """Request to create a new chat thread"""
    investigation_ids: Optional[List[str]] = Field(None, description="Optional list of investigation IDs to load")

# ============================================================================
# CHAT ENDPOINTS
# ============================================================================

@router.post("/message", response_model=ChatResponse)
async def send_message(
    message: ChatMessage,
    background_tasks: BackgroundTasks
) -> ChatResponse:
    """
    Send a chat message to the AML investigation assistant.
    
    This endpoint allows users to chat with the AML investigation system,
    ask questions about investigations, and get explanations about findings.
    """
    try:
        logger.info(f"=== CHAT MESSAGE REQUEST ===")
        logger.info(f"Prompt: {message.prompt[:100]}...")
        logger.info(f"Thread ID: {message.thread_id}")
        logger.info(f"Investigation ID: {message.investigation_id}")
        
        # Auto-create thread if not provided
        if not message.thread_id:
            logger.info("No thread_id provided, creating new thread")
            # The query_investigations function will handle thread creation
        
        # Get chat response
        logger.info(f"Calling query_investigations with prompt='{message.prompt[:50]}...', thread_id='{message.thread_id}'")
        result = query_investigations(
            prompt=message.prompt,
            thread_id=message.thread_id
        )
        
        logger.info(f"query_investigations returned: {type(result)}")
        if isinstance(result, dict):
            logger.info(f"Result keys: {list(result.keys())}")
            logger.info(f"Has error: {'error' in result}")
            if 'error' in result:
                logger.error(f"Error in result: {result['error']}")
        else:
            logger.info(f"Result type: {type(result)}, value: {str(result)[:200]}...")
        
        if "error" in result:
            logger.error(f"Error in query_investigations result: {result['error']}")
            raise HTTPException(
                status_code=500,
                detail=f"Chat error: {result['error']}"
            )
        
        # Extract response from result
        chat_history = result.get("chat_history", [])
        logger.info(f"Chat history length: {len(chat_history)}")
        
        if not chat_history:
            logger.warning("No chat history returned, using fallback response")
            response_text = "I'm sorry, I couldn't process your message. Please try again."
        else:
            # Get the last AI message
            last_message = chat_history[-1]
            logger.info(f"Last message type: {type(last_message)}")
            logger.info(f"Last message has content attr: {hasattr(last_message, 'content')}")
            
            if hasattr(last_message, 'content'):
                response_text = last_message.content
                logger.info(f"Response text length: {len(response_text)}")
            else:
                response_text = str(last_message)
                logger.info(f"Response text (str): {len(response_text)}")
        
        # Get investigation context
        investigation_summary = result.get("investigation_summary", {})
        logger.info(f"Investigation summary: {investigation_summary}")
        
        context = {
            "investigation_id": result.get("investigation_id"),
            "risk_level": investigation_summary.get("risk_level"),
            "risk_score": investigation_summary.get("risk_score"),
            "key_findings": investigation_summary.get("key_findings", []),
            "recommendations": investigation_summary.get("recommendations", [])
        }
        
        logger.info(f"Context: {context}")
        
        response = ChatResponse(
            prompt=message.prompt,
            response=response_text,
            thread_id=result.get("thread_id", message.thread_id),
            investigation_id=result.get("investigation_id"),
            context=context
        )
        
        logger.info(f"=== CHAT MESSAGE RESPONSE ===")
        logger.info(f"Response length: {len(response.response)}")
        logger.info(f"Thread ID: {response.thread_id}")
        logger.info(f"Investigation ID: {response.investigation_id}")
        logger.info(f"Chat response generated for thread {response.thread_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"=== CHAT MESSAGE ERROR ===")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/investigate", response_model=InvestigationResponse)
async def start_investigation(
    request: InvestigationRequest,
    background_tasks: BackgroundTasks
) -> InvestigationResponse:
    """
    Start a new AML investigation for a transaction.
    
    This endpoint initiates a comprehensive AML investigation using the
    production workflow with all analysis agents.
    """
    try:
        logger.info(f"Starting investigation for transaction {request.transaction_id}")
        
        # Generate thread_id if not provided
        thread_id = request.thread_id or f"thread_{request.transaction_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Run investigation
        # Note: This is a simplified implementation - in production you'd need
        # to fetch transaction and customer data from the database
        transaction_data = {
            "transaction_id": request.transaction_id,
            "amount": 0,  # Would be fetched from database
            "currency": "USD",
            "transaction_type": "unknown",
            "transaction_date": datetime.utcnow().isoformat(),
            "status": "completed"
        }
        customer_data = {
            "name": f"Customer_{request.transaction_id}",
            "account_age_days": 30,
            "transaction_history": []
        }
        
        result = analyze_transaction(
            transaction=transaction_data,
            customer=customer_data,
            thread_id=thread_id
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=500,
                detail=f"Investigation error: {result['error']}"
            )
        
        # Check if investigation is complete
        investigation_summary = result.get("investigation_summary", {})
        chat_ready = bool(investigation_summary and not investigation_summary.get("error"))
        
        response = InvestigationResponse(
            investigation_id=result.get("investigation_id", "unknown"),
            thread_id=thread_id,
            status="completed" if chat_ready else "failed",
            results=result,
            chat_ready=chat_ready
        )
        
        logger.info(f"Investigation completed for transaction {request.transaction_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Investigation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/threads", response_model=ThreadInfo)
async def create_thread(
    request: ThreadCreateRequest
) -> ThreadInfo:
    """
    Create a new chat thread.
    
    This endpoint creates a new chat thread and optionally loads
    specific investigations into the thread context.
    """
    try:
        logger.info(f"=== CREATE THREAD REQUEST ===")
        logger.info(f"Investigation IDs: {request.investigation_ids}")
        
        # Create thread using the production workflow
        from app.agents.production_workflow_simple import create_chat_thread, INVESTIGATION_RESULTS
        
        logger.info(f"Available investigations: {list(INVESTIGATION_RESULTS.keys())}")
        
        # Load investigations if specified
        investigations = []
        if request.investigation_ids:
            logger.info(f"Loading specific investigations: {request.investigation_ids}")
            for case_id in request.investigation_ids:
                if case_id in INVESTIGATION_RESULTS:
                    investigations.append(INVESTIGATION_RESULTS[case_id])
                    logger.info(f"Loaded investigation: {case_id}")
                else:
                    logger.warning(f"Investigation not found: {case_id}")
        else:
            # Load all investigations
            logger.info("Loading all investigations")
            investigations = list(INVESTIGATION_RESULTS.values())
            logger.info(f"Loaded {len(investigations)} investigations")
        
        logger.info(f"Total investigations to load: {len(investigations)}")
        
        # Create thread
        logger.info("Calling create_chat_thread...")
        thread_id = create_chat_thread(investigations)
        logger.info(f"Created thread: {thread_id}")
        
        thread_info = ThreadInfo(
            thread_id=thread_id,
            investigation_id=None,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            message_count=0,
            status="active"
        )
        
        logger.info(f"=== CREATE THREAD RESPONSE ===")
        logger.info(f"Thread ID: {thread_info.thread_id}")
        logger.info(f"Status: {thread_info.status}")
        
        return thread_info
        
    except Exception as e:
        logger.error(f"=== CREATE THREAD ERROR ===")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/threads", response_model=List[ThreadInfo])
async def list_threads() -> List[ThreadInfo]:
    """
    List all active chat threads.
    
    This endpoint returns information about all active chat threads
    and their associated investigations.
    """
    try:
        logger.info("=== LIST THREADS REQUEST ===")
        
        # Get threads from the production workflow
        from app.agents.production_workflow_simple import CHAT_THREADS
        
        logger.info(f"CHAT_THREADS type: {type(CHAT_THREADS)}")
        logger.info(f"CHAT_THREADS keys: {list(CHAT_THREADS.keys())}")
        logger.info(f"Total threads: {len(CHAT_THREADS)}")
        
        threads = []
        for thread_id, thread_data in CHAT_THREADS.items():
            logger.info(f"Processing thread: {thread_id}")
            logger.info(f"Thread data keys: {list(thread_data.keys())}")
            
            # Ensure all required fields are present with defaults
            created_at = thread_data.get("created_at")
            if created_at is None:
                created_at = datetime.utcnow()
                logger.info(f"Set default created_at for thread {thread_id}")
            
            last_updated = thread_data.get("last_updated")
            if last_updated is None:
                last_updated = datetime.utcnow()
                logger.info(f"Set default last_updated for thread {thread_id}")
            
            chat_history = thread_data.get("chat_history", [])
            message_count = len(chat_history) if chat_history else 0
            logger.info(f"Thread {thread_id} has {message_count} messages")
            
            thread_info = ThreadInfo(
                thread_id=thread_id,
                investigation_id=None,
                created_at=created_at,
                last_activity=last_updated,
                message_count=message_count,
                status="active"
            )
            
            logger.info(f"Created ThreadInfo for {thread_id}: {thread_info}")
            threads.append(thread_info)
        
        logger.info(f"=== LIST THREADS RESPONSE ===")
        logger.info(f"Returning {len(threads)} threads")
        return threads
        
    except Exception as e:
        logger.error(f"=== LIST THREADS ERROR ===")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/thread/{thread_id}", response_model=ThreadInfo)
async def get_thread_info(thread_id: str) -> ThreadInfo:
    """
    Get information about a specific chat thread.
    
    This endpoint returns detailed information about a specific
    chat thread and its associated investigation.
    """
    try:
        logger.info(f"Getting thread info for {thread_id}")
        
        # This would typically query a database for thread information
        # For now, return basic info
        thread_info = ThreadInfo(
            thread_id=thread_id,
            investigation_id=None,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            message_count=0,
            status="active"
        )
        
        return thread_info
        
    except Exception as e:
        logger.error(f"Get thread info error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.delete("/thread/{thread_id}")
async def delete_thread(thread_id: str) -> Dict[str, str]:
    """
    Delete a chat thread and its associated data.
    
    This endpoint removes a chat thread and all associated
    investigation data.
    """
    try:
        logger.info(f"Deleting thread {thread_id}")
        
        # This would typically delete from database
        # For now, just return success
        
        return {"message": f"Thread {thread_id} deleted successfully"}
        
    except Exception as e:
        logger.error(f"Delete thread error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

# ============================================================================
# STREAMING CHAT ENDPOINTS
# ============================================================================

@router.post("/stream")
async def stream_chat(message: ChatMessage):
    """
    Stream chat responses for real-time interaction.
    
    This endpoint provides streaming chat responses for real-time
    interaction with the AML investigation system.
    """
    try:
        logger.info(f"Starting stream chat for thread {message.thread_id}")
        
        async def generate_response():
            try:
                # Get chat response
                result = query_investigations(
                    prompt=message.prompt,
                    thread_id=message.thread_id
                )
                
                if "error" in result:
                    yield f"data: {json.dumps({'error': result['error']})}\n\n"
                    return
                
                # Stream the response
                chat_history = result.get("chat_history", [])
                if chat_history:
                    last_message = chat_history[-1]
                    if hasattr(last_message, 'content'):
                        response_text = last_message.content
                    else:
                        response_text = str(last_message)
                    
                    # Stream response in chunks
                    chunk_size = 50
                    for i in range(0, len(response_text), chunk_size):
                        chunk = response_text[i:i+chunk_size]
                        yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                        await asyncio.sleep(0.1)  # Small delay for streaming effect
                    
                    # Send completion signal
                    yield f"data: {json.dumps({'complete': True})}\n\n"
                else:
                    yield f"data: {json.dumps({'error': 'No response generated'})}\n\n"
                    
            except Exception as e:
                logger.error(f"Stream chat error: {str(e)}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate_response(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
        
    except Exception as e:
        logger.error(f"Stream chat error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

# ============================================================================
# INVESTIGATION STATUS ENDPOINTS
# ============================================================================

@router.get("/investigation/{investigation_id}/status")
async def get_investigation_status(investigation_id: str) -> Dict[str, Any]:
    """
    Get the status of a specific investigation.
    
    This endpoint returns the current status and progress
    of an AML investigation.
    """
    try:
        logger.info(f"Getting investigation status for {investigation_id}")
        
        # This would typically query the investigation status from database
        # For now, return basic status
        status = {
            "investigation_id": investigation_id,
            "status": "completed",
            "progress": 100,
            "current_agent": "chat_agent",
            "workflow_complete": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return status
        
    except Exception as e:
        logger.error(f"Get investigation status error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/investigation/{investigation_id}/results")
async def get_investigation_results(investigation_id: str) -> Dict[str, Any]:
    """
    Get the complete results of a specific investigation.
    
    This endpoint returns the full investigation results including
    all analysis results and recommendations.
    """
    try:
        logger.info(f"Getting investigation results for {investigation_id}")
        
        # This would typically query the investigation results from database
        # For now, return basic results structure
        results = {
            "investigation_id": investigation_id,
            "status": "completed",
            "results": {
                "pattern_analysis": {},
                "behavioral_analysis": {},
                "geographic_risks": {},
                "network_analysis": {},
                "risk_assessment": {},
                "investigation_summary": {}
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return results
        
    except Exception as e:
        logger.error(f"Get investigation results error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@router.get("/health")
async def chat_health_check() -> Dict[str, str]:
    """
    Health check endpoint for chat functionality.
    
    This endpoint verifies that the chat system is working properly.
    """
    try:
        logger.info("Chat health check requested")
        
        return {
            "status": "healthy",
            "service": "chat",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Chat health check error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/threads/{thread_id}")
async def get_thread_history(thread_id: str) -> Dict[str, Any]:
    """
    Get chat conversation history for a specific thread.
    
    This endpoint returns the complete conversation history
    for a specific chat thread.
    """
    try:
        logger.info(f"Getting thread history for {thread_id}")
        
        # Get thread from the production workflow
        from app.agents.production_workflow_simple import CHAT_THREADS, get_chat_thread
        
        thread = get_chat_thread(thread_id)
        if not thread:
            raise HTTPException(
                status_code=404,
                detail=f"Thread {thread_id} not found"
            )
        
        # Format chat history
        messages = []
        for msg in thread.get("chat_history", []):
            messages.append({
                "role": "user" if msg.__class__.__name__ == "HumanMessage" else "assistant",
                "content": msg.content,
                "timestamp": thread.get("last_updated", datetime.utcnow()).isoformat()
            })
        
        return {
            "thread_id": thread_id,
            "messages": messages,
            "investigation_count": len(thread.get("investigation_results", [])),
            "created_at": thread.get("created_at", datetime.utcnow()).isoformat(),
            "last_updated": thread.get("last_updated", datetime.utcnow()).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get thread history error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/statistics")
async def get_statistics() -> Dict[str, Any]:
    """
    Get global statistics across all investigations.
    
    This endpoint returns statistics about investigations, risk levels,
    and system activity.
    """
    try:
        logger.info("=== GET STATISTICS REQUEST ===")
        
        # Get statistics from the production workflow
        from app.agents.production_workflow_simple import INVESTIGATION_RESULTS, _calculate_investigation_statistics, CHAT_THREADS
        
        logger.info(f"INVESTIGATION_RESULTS type: {type(INVESTIGATION_RESULTS)}")
        logger.info(f"INVESTIGATION_RESULTS keys: {list(INVESTIGATION_RESULTS.keys())}")
        logger.info(f"Total investigations: {len(INVESTIGATION_RESULTS)}")
        
        all_investigations = list(INVESTIGATION_RESULTS.values())
        logger.info(f"All investigations count: {len(all_investigations)}")
        
        logger.info("Calling _calculate_investigation_statistics...")
        stats = _calculate_investigation_statistics(all_investigations)
        logger.info(f"Statistics calculated: {stats}")
        
        result = {
            "total_investigations": stats["total"],
            "high_risk_cases": stats["high_risk"],
            "medium_risk_cases": stats["medium_risk"],
            "low_risk_cases": stats["low_risk"],
            "sar_filed": stats["sar_filed"],
            "human_review_required": stats["human_review"],
            "active_threads": len(CHAT_THREADS)
        }
        
        logger.info(f"=== GET STATISTICS RESPONSE ===")
        logger.info(f"Result: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"=== GET STATISTICS ERROR ===")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
