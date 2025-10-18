"""
Prompt Management API Routes

This module provides FastAPI endpoints for managing AML agent prompts
through LangSmith integration.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.prompt_manager import prompt_manager
from app.core.langsmith_client import langsmith_manager
from app.core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/prompts", tags=["prompts"])


# Request/Response Models
class PromptDeployRequest(BaseModel):
    agent_name: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    force_update: bool = False
    
    def __init__(self, **data):
        super().__init__(**data)
        # Validate agent name at model level
        valid_agents = ['risk_assessor', 'pattern_analyst', 'report_synthesizer', 'data_enrichment', 'coordinator']
        if self.agent_name not in valid_agents:
            raise ValueError(f"Invalid agent name: {self.agent_name}. Valid agents: {valid_agents}")


class PromptVersionRequest(BaseModel):
    agent_name: str
    version: str
    
    def __init__(self, **data):
        super().__init__(**data)
        # Validate agent name at model level
        valid_agents = ['risk_assessor', 'pattern_analyst', 'report_synthesizer', 'data_enrichment', 'coordinator']
        if self.agent_name not in valid_agents:
            raise ValueError(f"Invalid agent name: {self.agent_name}. Valid agents: {valid_agents}")


class PromptCompareRequest(BaseModel):
    agent_name: str
    version1: str
    version2: str


class PromptResponse(BaseModel):
    agent_name: str
    url: str
    description: str
    tags: List[str]
    created_at: datetime


class PromptVersionResponse(BaseModel):
    name: str
    description: str
    tags: List[str]
    created_at: datetime
    commit_hash: Optional[str]


class PromptCompareResponse(BaseModel):
    agent_name: str
    version1: Dict[str, Any]
    version2: Dict[str, Any]
    templates_different: bool


@router.post("/deploy", response_model=PromptResponse)
async def deploy_prompt(request: PromptDeployRequest):
    """
    Deploy a prompt for a specific agent to LangSmith
    """
    # Validate agent name first
    valid_agents = list(prompt_manager.agent_prompt_files.keys())
    if request.agent_name not in valid_agents:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid agent name: {request.agent_name}. Valid agents: {valid_agents}"
        )
    
    try:
        url = prompt_manager.deploy_prompt_to_langsmith(
            agent_name=request.agent_name,
            description=request.description,
            tags=request.tags
        )
        
        # Get prompt details
        prompt_versions = prompt_manager.get_prompt_versions(request.agent_name)
        latest_version = prompt_versions[0] if prompt_versions else {}
        
        return PromptResponse(
            agent_name=request.agent_name,
            url=url,
            description=latest_version.get("description", ""),
            tags=latest_version.get("tags", []),
            created_at=latest_version.get("created_at", datetime.utcnow())
        )
        
    except Exception as e:
        logger.error(f"Failed to deploy prompt for {request.agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deploy-all")
async def deploy_all_prompts(background_tasks: BackgroundTasks, force_update: bool = False):
    """
    Deploy all agent prompts to LangSmith
    """
    try:
        def deploy_task():
            results = prompt_manager.deploy_all_prompts(force_update=force_update)
            logger.info(f"Deployed all prompts: {results}")
        
        background_tasks.add_task(deploy_task)
        
        return {
            "message": "Deployment started in background",
            "agents": list(prompt_manager.agent_prompt_files.keys())
        }
        
    except Exception as e:
        logger.error(f"Failed to deploy all prompts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents")
async def list_agents():
    """
    List all available agents and their prompt files
    """
    try:
        return {
            "agents": prompt_manager.agent_prompt_files,
            "total_agents": len(prompt_manager.agent_prompt_files)
        }
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_name}/versions", response_model=List[PromptVersionResponse])
async def get_prompt_versions(agent_name: str):
    """
    Get all versions of a prompt for a specific agent
    """
    # Validate agent name first
    valid_agents = list(prompt_manager.agent_prompt_files.keys())
    if agent_name not in valid_agents:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid agent name: {agent_name}. Valid agents: {valid_agents}"
        )
    
    try:
        versions = prompt_manager.get_prompt_versions(agent_name)
        
        return [
            PromptVersionResponse(
                name=version.get("name", ""),
                description=version.get("description", ""),
                tags=version.get("tags", []),
                created_at=version.get("created_at", datetime.utcnow()),
                commit_hash=version.get("commit_hash")
            )
            for version in versions
        ]
        
    except Exception as e:
        logger.error(f"Failed to get prompt versions for {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rollback", response_model=Dict[str, Any])
async def rollback_prompt(request: PromptVersionRequest):
    """
    Rollback a prompt to a specific version
    """
    # Validate agent name first
    valid_agents = list(prompt_manager.agent_prompt_files.keys())
    if request.agent_name not in valid_agents:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid agent name: {request.agent_name}. Valid agents: {valid_agents}"
        )
    
    try:
        success = prompt_manager.rollback_prompt(
            agent_name=request.agent_name,
            version=request.version
        )
        
        if success:
            return {
                "message": f"Successfully rolled back {request.agent_name} to version {request.version}",
                "agent_name": request.agent_name,
                "version": request.version
            }
        else:
            raise HTTPException(status_code=400, detail="Rollback failed")
            
    except Exception as e:
        logger.error(f"Failed to rollback {request.agent_name} to {request.version}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare", response_model=PromptCompareResponse)
async def compare_prompt_versions(request: PromptCompareRequest):
    """
    Compare two prompt versions
    """
    try:
        comparison = prompt_manager.compare_prompt_versions(
            agent_name=request.agent_name,
            version1=request.version1,
            version2=request.version2
        )
        
        return PromptCompareResponse(**comparison)
        
    except Exception as e:
        logger.error(f"Failed to compare prompt versions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_name}/chain")
async def get_agent_chain(agent_name: str, version: Optional[str] = None):
    """
    Get a complete agent chain (prompt + model) for testing
    """
    try:
        chain = prompt_manager.get_agent_chain(
            agent_name=agent_name,
            version=version
        )
        
        return {
            "agent_name": agent_name,
            "version": version or "latest",
            "chain_available": True,
            "message": "Chain created successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to get chain for {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{agent_name}/version/{version}")
async def delete_prompt_version(agent_name: str, version: str):
    """
    Delete a specific prompt version
    """
    try:
        success = langsmith_manager.delete_prompt(agent_name, version)
        
        if success:
            return {
                "message": f"Successfully deleted version {version} for {agent_name}",
                "agent_name": agent_name,
                "version": version
            }
        else:
            raise HTTPException(status_code=400, detail="Delete failed")
            
    except Exception as e:
        logger.error(f"Failed to delete version {version} for {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Health check for prompt management system
    """
    try:
        # Test LangSmith connection
        prompts = langsmith_manager.list_agent_prompts()
        
        return {
            "status": "healthy",
            "langsmith_connected": True,
            "total_prompts": len(prompts),
            "agents_configured": len(prompt_manager.agent_prompt_files)
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
