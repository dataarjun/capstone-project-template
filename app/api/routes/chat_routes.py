"""
Chat API Routes for AML Investigation System
Provides conversational interface to query investigation results
"""

from fastapi import APIRouter, HTTPException, Body
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime

from app.agents.production_workflow import (
    create_chat_thread,
    get_chat_thread,
    query_investigations,
    CHAT_THREADS,
    INVESTIGATION_RESULTS,
    _calculate_investigation_statistics
)
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


# Request/Response Models
class ChatThreadCreate(BaseModel):
    """Request to create a new chat thread"""
    investigation_ids: Optional[List[str]] = Field(
        None, 
        description="Optional list of case IDs to load into thread context"
    )

class ChatThreadResponse(BaseModel):
    """Response with thread information"""
    thread_id: str
    created_at: str
    investigation_count: int
    statistics: Dict[str, int]
    message: str

class ChatMessageRequest(BaseModel):
    """Request to send a chat message"""
    prompt: str = Field(..., description="User's prompt/query (first message starts new conversation)")
    thread_id: Optional[str] = Field(
        None, 
        description="Thread ID for conversation continuity (optional for first message)"
    )

class ChatMessageResponse(BaseModel):
    """Response from chat agent"""
    thread_id: str
    prompt: str
    response: str
    statistics: Dict[str, int]
    timestamp: str

class ChatHistoryResponse(BaseModel):
    """Chat conversation history"""
    thread_id: str
    messages: List[Dict[str, str]]
    investigation_count: int
    created_at: str
    last_updated: str


# API Endpoints
@router.post("/threads", response_model=ChatThreadResponse)
def create_thread(
    request: ChatThreadCreate = Body(...)
) -> ChatThreadResponse:
    """
    Create a new chat thread
    
    Automatically loads specified investigations or all available investigations
    into the thread context for querying.
    """
    try:
        # Load specified investigations
        investigations = []
        if request.investigation_ids:
            for case_id in request.investigation_ids:
                if case_id in INVESTIGATION_RESULTS:
                    investigations.append(INVESTIGATION_RESULTS[case_id])
        else:
            # Load all investigations
            investigations = list(INVESTIGATION_RESULTS.values())
        
        # Create thread
        thread_id = create_chat_thread(investigations)
        thread = get_chat_thread(thread_id)
        
        # Calculate statistics
        stats = _calculate_investigation_statistics(investigations)
        
        return ChatThreadResponse(
            thread_id=thread_id,
            created_at=thread["created_at"].isoformat(),
            investigation_count=len(investigations),
            statistics=stats,
            message=f"Chat thread created with {len(investigations)} investigations loaded"
        )
        
    except Exception as e:
        logger.error(f"Failed to create chat thread: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create chat thread: {str(e)}")


@router.post("/message", response_model=ChatMessageResponse)
def send_message(
    request: ChatMessageRequest = Body(...)
) -> ChatMessageResponse:
    """
    Send a message to the chat agent
    
    Examples of queries:
    - "How many accounts have AML cases?"
    - "Why are they flagged as fraudulent?"
    - "Show me all high-risk cases"
    - "What are the most common risk factors?"
    """
    try:
        # Query investigations
        result = query_investigations(
            query=request.prompt,
            thread_id=request.thread_id
        )
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return ChatMessageResponse(
            thread_id=result["thread_id"],
            prompt=request.prompt,
            response=result["response"],
            statistics=result["statistics"],
            timestamp=result["timestamp"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send chat message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")


@router.get("/threads/{thread_id}", response_model=ChatHistoryResponse)
def get_thread_history(thread_id: str) -> ChatHistoryResponse:
    """
    Get chat conversation history for a thread
    """
    try:
        thread = get_chat_thread(thread_id)
        
        if not thread:
            raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
        
        # Format chat history
        messages = []
        for msg in thread["chat_history"]:
            messages.append({
                "role": "user" if msg.__class__.__name__ == "HumanMessage" else "assistant",
                "content": msg.content,
                "timestamp": thread["last_updated"].isoformat()
            })
        
        return ChatHistoryResponse(
            thread_id=thread_id,
            messages=messages,
            investigation_count=len(thread["investigation_results"]),
            created_at=thread["created_at"].isoformat(),
            last_updated=thread["last_updated"].isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get thread history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve thread: {str(e)}")


@router.get("/threads", response_model=List[Dict[str, Any]])
def list_threads() -> List[Dict[str, Any]]:
    """
    List all available chat threads
    """
    try:
        threads_list = []
        for thread_id, thread in CHAT_THREADS.items():
            threads_list.append({
                "thread_id": thread_id,
                "investigation_count": len(thread["investigation_results"]),
                "message_count": len(thread["chat_history"]),
                "created_at": thread["created_at"].isoformat(),
                "last_updated": thread["last_updated"].isoformat()
            })
        
        return threads_list
        
    except Exception as e:
        logger.error(f"Failed to list threads: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list threads: {str(e)}")


@router.delete("/threads/{thread_id}")
def delete_thread(thread_id: str) -> Dict[str, str]:
    """
    Delete a chat thread
    """
    try:
        if thread_id not in CHAT_THREADS:
            raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
        
        del CHAT_THREADS[thread_id]
        
        return {
            "message": f"Thread {thread_id} deleted successfully",
            "thread_id": thread_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete thread: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete thread: {str(e)}")


@router.get("/statistics")
def get_global_statistics() -> Dict[str, Any]:
    """
    Get global statistics across all investigations
    """
    try:
        all_investigations = list(INVESTIGATION_RESULTS.values())
        stats = _calculate_investigation_statistics(all_investigations)
        
        return {
            "total_investigations": stats["total"],
            "high_risk_cases": stats["high_risk"],
            "medium_risk_cases": stats["medium_risk"],
            "low_risk_cases": stats["low_risk"],
            "sar_filed": stats["sar_filed"],
            "human_review_required": stats["human_review"],
            "active_threads": len(CHAT_THREADS)
        }
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


# WebSocket Support for Real-time Chat
from fastapi import WebSocket, WebSocketDisconnect
import json

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, thread_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[thread_id] = websocket
    
    def disconnect(self, thread_id: str):
        if thread_id in self.active_connections:
            del self.active_connections[thread_id]
    
    async def send_message(self, thread_id: str, message: dict):
        if thread_id in self.active_connections:
            await self.active_connections[thread_id].send_json(message)

manager = ConnectionManager()


@router.websocket("/ws/{thread_id}")
async def websocket_chat(websocket: WebSocket, thread_id: str):
    """
    WebSocket endpoint for real-time chat
    """
    await manager.connect(thread_id, websocket)
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            message_data = json.loads(data)
            query = message_data.get("query", "")
            
            # Process query
            result = query_investigations(query=query, thread_id=thread_id)
            
            # Send response
            await manager.send_message(thread_id, {
                "type": "response",
                "prompt": query,
                "response": result["response"],
                "statistics": result["statistics"],
                "timestamp": result["timestamp"]
            })
            
    except WebSocketDisconnect:
        manager.disconnect(thread_id)
        logger.info(f"WebSocket disconnected for thread {thread_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await manager.send_message(thread_id, {
            "type": "error",
            "message": str(e)
        })
        manager.disconnect(thread_id)
