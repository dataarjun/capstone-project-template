"""
Prompt Management for AML Agents

This module handles loading prompts from YAML files and managing them
through LangSmith for version control and deployment.
"""

import yaml
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
from app.core.langsmith_client import langsmith_manager
from app.core.logger import get_logger

logger = get_logger(__name__)


class PromptManager:
    """
    Manages prompts for all AML agents with LangSmith integration
    """
    
    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = Path(prompts_dir)
        self.langsmith = langsmith_manager
        
        # Agent prompt mappings
        self.agent_prompt_files = {
            "risk_assessor": "risk_assessment.yaml",
            "pattern_analyst": "behavior_analysis.yaml", 
            "report_synthesizer": "sar_generation.yaml",
            "data_enrichment": "document_analysis.yaml",
            "coordinator": "behavior_analysis.yaml"  # Using behavior analysis for coordination
        }
    
    def load_prompt_from_yaml(self, agent_name: str) -> Dict[str, Any]:
        """
        Load prompt configuration from YAML file
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Prompt configuration dictionary
        """
        try:
            if agent_name not in self.agent_prompt_files:
                raise ValueError(f"No prompt file defined for agent: {agent_name}")
            
            prompt_file = self.prompts_dir / self.agent_prompt_files[agent_name]
            
            if not prompt_file.exists():
                raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
            
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_config = yaml.safe_load(f)
            
            logger.info(f"Loaded prompt configuration for {agent_name}")
            return prompt_config
            
        except Exception as e:
            logger.error(f"Failed to load prompt for {agent_name}: {e}")
            raise
    
    def deploy_prompt_to_langsmith(self, agent_name: str, 
                                  description: Optional[str] = None,
                                  tags: Optional[List[str]] = None) -> str:
        """
        Deploy a prompt to LangSmith from YAML configuration
        
        Args:
            agent_name: Name of the agent
            description: Optional description override
            tags: Optional tags override
            
        Returns:
            LangSmith prompt URL
        """
        try:
            # Load prompt configuration
            prompt_config = self.load_prompt_from_yaml(agent_name)
            
            # Extract template and metadata
            template = prompt_config.get('prompt_template', prompt_config.get('template', ''))
            yaml_description = prompt_config.get('description', '')
            yaml_tags = prompt_config.get('tags', [])
            
            # Use provided values or fall back to YAML
            final_description = description or yaml_description
            final_tags = tags or yaml_tags
            
            # Deploy to LangSmith
            url = self.langsmith.create_or_update_prompt(
                agent_name=agent_name,
                template=template,
                description=final_description,
                tags=final_tags
            )
            
            logger.info(f"Deployed prompt for {agent_name} to LangSmith: {url}")
            return url
            
        except Exception as e:
            logger.error(f"Failed to deploy prompt for {agent_name}: {e}")
            raise
    
    def deploy_all_prompts(self, force_update: bool = False) -> Dict[str, str]:
        """
        Deploy all agent prompts to LangSmith
        
        Args:
            force_update: Whether to force update existing prompts
            
        Returns:
            Dictionary mapping agent names to LangSmith URLs
        """
        results = {}
        
        for agent_name in self.agent_prompt_files.keys():
            try:
                url = self.deploy_prompt_to_langsmith(agent_name)
                results[agent_name] = url
                logger.info(f"Successfully deployed prompt for {agent_name}")
            except Exception as e:
                logger.error(f"Failed to deploy prompt for {agent_name}: {e}")
                results[agent_name] = f"Error: {str(e)}"
        
        return results
    
    def get_agent_chain(self, agent_name: str, model_config: Dict[str, Any] = None,
                       version: Optional[str] = None) -> Any:
        """
        Get a complete agent chain with prompt and model
        
        Args:
            agent_name: Name of the agent
            model_config: Model configuration
            version: Prompt version
            
        Returns:
            LangChain chain
        """
        try:
            return self.langsmith.create_agent_chain(
                agent_name=agent_name,
                model_config=model_config,
                version=version
            )
        except Exception as e:
            logger.error(f"Failed to get chain for {agent_name}: {e}")
            raise
    
    def get_prompt_versions(self, agent_name: str) -> List[Dict[str, Any]]:
        """
        Get all versions of a prompt for an agent
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            List of prompt versions
        """
        try:
            return self.langsmith.get_prompt_versions(agent_name)
        except Exception as e:
            logger.error(f"Failed to get prompt versions for {agent_name}: {e}")
            return []
    
    def rollback_prompt(self, agent_name: str, version: str) -> bool:
        """
        Rollback to a specific prompt version
        
        Args:
            agent_name: Name of the agent
            version: Version to rollback to
            
        Returns:
            Success status
        """
        try:
            # Get the specific version
            prompt = self.langsmith.get_prompt(agent_name, version)
            
            # Deploy it as the latest version
            url = self.langsmith.create_or_update_prompt(
                agent_name=agent_name,
                template=str(prompt.template),
                description=f"Rollback to version {version}",
                tags=["rollback", "aml"]
            )
            
            logger.info(f"Rolled back {agent_name} to version {version}: {url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rollback {agent_name} to {version}: {e}")
            return False
    
    def compare_prompt_versions(self, agent_name: str, version1: str, version2: str) -> Dict[str, Any]:
        """
        Compare two prompt versions
        
        Args:
            agent_name: Name of the agent
            version1: First version
            version2: Second version
            
        Returns:
            Comparison results
        """
        try:
            prompt1 = self.langsmith.get_prompt(agent_name, version1)
            prompt2 = self.langsmith.get_prompt(agent_name, version2)
            
            return {
                "agent_name": agent_name,
                "version1": {
                    "version": version1,
                    "template": str(prompt1)
                },
                "version2": {
                    "version": version2,
                    "template": str(prompt2)
                },
                "templates_different": str(prompt1) != str(prompt2)
            }
            
        except Exception as e:
            logger.error(f"Failed to compare prompt versions: {e}")
            return {"error": str(e)}


# Global instance
prompt_manager = PromptManager()
