#!/usr/bin/env python3
"""
Deploy AML Agent Prompts to LangSmith

This script deploys all agent prompts from YAML files to LangSmith
for version control and centralized management.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.core.prompt_manager import prompt_manager
from app.core.logger import get_logger

logger = get_logger(__name__)


async def deploy_all_prompts():
    """Deploy all agent prompts to LangSmith"""
    try:
        logger.info("Starting prompt deployment to LangSmith...")
        
        # Deploy all prompts
        results = prompt_manager.deploy_all_prompts(force_update=True)
        
        logger.info("Prompt deployment results:")
        for agent_name, url in results.items():
            if url.startswith("http"):
                logger.info(f"✅ {agent_name}: {url}")
            else:
                logger.error(f"❌ {agent_name}: {url}")
        
        # Get deployment summary
        successful_deployments = sum(1 for url in results.values() if url.startswith("http"))
        total_agents = len(results)
        
        logger.info(f"Deployment complete: {successful_deployments}/{total_agents} agents deployed successfully")
        
        return results
        
    except Exception as e:
        logger.error(f"Failed to deploy prompts: {e}")
        raise


async def verify_deployments():
    """Verify that all prompts were deployed successfully"""
    try:
        logger.info("Verifying prompt deployments...")
        
        for agent_name in prompt_manager.agent_prompt_files.keys():
            try:
                # Try to get the latest version
                prompt = prompt_manager.get_agent_chain(agent_name)
                logger.info(f"✅ {agent_name}: Prompt verified")
            except Exception as e:
                logger.error(f"❌ {agent_name}: Verification failed - {e}")
        
    except Exception as e:
        logger.error(f"Failed to verify deployments: {e}")


async def main():
    """Main deployment function"""
    try:
        # Check environment variables
        if not os.getenv("LANGSMITH_API_KEY"):
            logger.warning("LANGSMITH_API_KEY not set. Some features may not work.")
        
        # Deploy all prompts
        results = await deploy_all_prompts()
        
        # Verify deployments
        await verify_deployments()
        
        logger.info("Prompt deployment completed successfully!")
        
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

