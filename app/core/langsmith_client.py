"""
LangSmith Integration for AML System

This module provides centralized LangSmith client configuration,
prompt management, and tracing for all AML agents.
"""

import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from app.core.logger import get_logger

logger = get_logger(__name__)


class LangSmithManager:
    """
    Centralized LangSmith client for prompt management and tracing
    """
    
    def __init__(self):
        # Initialize LangSmith client
        self.client = Client()
        self.project_name = "aml-multi-agent-system"
        self.workspace_name = os.getenv("LANGSMITH_WORKSPACE", "default")
        
        # Agent prompt configurations
        self.agent_prompts = {
            "risk_assessor": {
                "name": "aml-risk-assessor-prompt",
                "description": "Risk assessment prompt for AML transactions",
                "tags": ["production", "risk-assessment", "aml"]
            },
            "pattern_analyst": {
                "name": "aml-pattern-analyst-prompt", 
                "description": "Pattern analysis prompt for suspicious activity detection",
                "tags": ["production", "pattern-analysis", "aml"]
            },
            "report_synthesizer": {
                "name": "aml-report-synthesizer-prompt",
                "description": "Report synthesis prompt for SAR generation",
                "tags": ["production", "report-generation", "aml"]
            },
            "data_enrichment": {
                "name": "aml-data-enrichment-prompt",
                "description": "Data enrichment prompt for customer information",
                "tags": ["production", "data-enrichment", "aml"]
            },
            "coordinator": {
                "name": "aml-coordinator-prompt",
                "description": "Workflow coordination prompt for AML investigations",
                "tags": ["production", "coordination", "aml"]
            }
        }
        
        # Initialize tracing
        self._setup_tracing()
    
    def _setup_tracing(self):
        """Setup LangSmith tracing configuration"""
        try:
            # Set environment variables for tracing
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_PROJECT"] = self.project_name
            os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
            
            if os.getenv("LANGSMITH_API_KEY"):
                os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGSMITH_API_KEY")
            
            logger.info(f"LangSmith tracing configured for project: {self.project_name}")
        except Exception as e:
            logger.warning(f"LangSmith tracing setup failed: {e}")
    
    def create_or_update_prompt(self, agent_name: str, template: str, 
                               description: Optional[str] = None,
                               tags: Optional[List[str]] = None) -> str:
        """
        Create or update a prompt for a specific agent
        
        Args:
            agent_name: Name of the agent (risk_assessor, pattern_analyst, etc.)
            template: Prompt template string
            description: Optional description
            tags: Optional tags
            
        Returns:
            URL of the created/updated prompt
        """
        try:
            if agent_name not in self.agent_prompts:
                raise ValueError(f"Unknown agent: {agent_name}")
            
            # Create prompt template
            prompt = ChatPromptTemplate.from_template(template)
            
            # Get agent configuration
            agent_config = self.agent_prompts[agent_name]
            
            # Use provided description or default
            prompt_description = description or agent_config["description"]
            prompt_tags = tags or agent_config["tags"]
            
            # Push prompt to LangSmith
            try:
                url = self.client.push_prompt(
                    agent_config["name"],
                    object=prompt,
                    description=prompt_description,
                    tags=prompt_tags
                )
                
                logger.info(f"Prompt updated for {agent_name}: {url}")
                return url
            except Exception as push_error:
                # Handle "nothing to commit" error gracefully
                if "Nothing to commit" in str(push_error):
                    logger.info(f"Prompt for {agent_name} unchanged, using existing version")
                    # Try to get the existing prompt URL
                    try:
                        existing_prompt = self.client.pull_prompt(agent_config["name"])
                        return f"Existing prompt (unchanged): {agent_config['name']}"
                    except:
                        return f"Prompt unchanged: {agent_config['name']}"
                else:
                    raise push_error
            
        except Exception as e:
            logger.error(f"Failed to create/update prompt for {agent_name}: {e}")
            raise
    
    def get_prompt(self, agent_name: str, version: Optional[str] = None) -> ChatPromptTemplate:
        """
        Get a prompt for a specific agent
        
        Args:
            agent_name: Name of the agent
            version: Optional version (commit hash, tag, or 'latest')
            
        Returns:
            ChatPromptTemplate instance
        """
        try:
            if agent_name not in self.agent_prompts:
                raise ValueError(f"Unknown agent: {agent_name}")
            
            agent_config = self.agent_prompts[agent_name]
            prompt_name = agent_config["name"]
            
            if version:
                prompt_name = f"{prompt_name}:{version}"
            
            # Pull prompt from LangSmith
            prompt = self.client.pull_prompt(prompt_name)
            
            logger.info(f"Retrieved prompt for {agent_name} (version: {version or 'latest'})")
            return prompt
            
        except Exception as e:
            logger.error(f"Failed to get prompt for {agent_name}: {e}")
            raise
    
    def create_agent_chain(self, agent_name: str, model_config: Dict[str, Any] = None,
                         version: Optional[str] = None) -> Any:
        """
        Create a complete agent chain with prompt and model
        
        Args:
            agent_name: Name of the agent
            model_config: Model configuration
            version: Prompt version
            
        Returns:
            LangChain chain
        """
        try:
            # Get prompt
            prompt = self.get_prompt(agent_name, version)
            
            # Create model with configuration
            model_config = model_config or {
                "model": "gpt-4o",
                "temperature": 0.2,
                "max_tokens": 1000
            }
            
            model = ChatOpenAI(**model_config)
            
            # Create chain
            chain = prompt | model
            
            logger.info(f"Created chain for {agent_name}")
            return chain
            
        except Exception as e:
            logger.error(f"Failed to create chain for {agent_name}: {e}")
            raise
    
    def list_agent_prompts(self, agent_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List prompts for agents
        
        Args:
            agent_name: Optional specific agent name
            
        Returns:
            List of prompt information
        """
        try:
            if agent_name:
                if agent_name not in self.agent_prompts:
                    raise ValueError(f"Unknown agent: {agent_name}")
                
                agent_config = self.agent_prompts[agent_name]
                prompts = self.client.list_prompts(
                    query=agent_config["name"],
                    limit=10
                )
            else:
                prompts = self.client.list_prompts(limit=50)
            
            return list(prompts)
            
        except Exception as e:
            logger.error(f"Failed to list prompts: {e}")
            return []
    
    def delete_prompt(self, agent_name: str, version: Optional[str] = None) -> bool:
        """
        Delete a prompt version
        
        Args:
            agent_name: Name of the agent
            version: Optional version to delete
            
        Returns:
            Success status
        """
        try:
            if agent_name not in self.agent_prompts:
                raise ValueError(f"Unknown agent: {agent_name}")
            
            agent_config = self.agent_prompts[agent_name]
            prompt_name = agent_config["name"]
            
            if version:
                prompt_name = f"{prompt_name}:{version}"
            
            self.client.delete_prompt(prompt_name)
            logger.info(f"Deleted prompt for {agent_name} (version: {version or 'all'})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete prompt for {agent_name}: {e}")
            return False
    
    def get_prompt_versions(self, agent_name: str) -> List[Dict[str, Any]]:
        """
        Get all versions of a prompt
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            List of prompt versions
        """
        try:
            if agent_name not in self.agent_prompts:
                raise ValueError(f"Unknown agent: {agent_name}")
            
            agent_config = self.agent_prompts[agent_name]
            prompts = self.client.list_prompts(
                query=agent_config["name"],
                limit=100
            )
            
            versions = []
            for prompt in prompts:
                # Handle different response formats
                if hasattr(prompt, 'name'):
                    versions.append({
                        "name": prompt.name,
                        "description": getattr(prompt, 'description', ''),
                        "tags": getattr(prompt, 'tags', []),
                        "created_at": getattr(prompt, 'created_at', None),
                        "commit_hash": getattr(prompt, 'commit_hash', None)
                    })
                elif isinstance(prompt, dict):
                    versions.append({
                        "name": prompt.get('name', ''),
                        "description": prompt.get('description', ''),
                        "tags": prompt.get('tags', []),
                        "created_at": prompt.get('created_at', None),
                        "commit_hash": prompt.get('commit_hash', None)
                    })
            
            return versions
            
        except Exception as e:
            logger.error(f"Failed to get prompt versions for {agent_name}: {e}")
            return []


# Global instance
langsmith_manager = LangSmithManager()
