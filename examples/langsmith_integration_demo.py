#!/usr/bin/env python3
"""
LangSmith Integration Demo

This script demonstrates how to use LangSmith for prompt management,
tracing, and version control in the AML multi-agent system.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.core.prompt_manager import prompt_manager
from app.core.langsmith_client import langsmith_manager
from app.core.tracing import aml_tracer, trace_risk_assessor
from app.core.logger import get_logger

logger = get_logger(__name__)


async def demo_prompt_management():
    """Demonstrate prompt management capabilities"""
    print("\n🔧 LangSmith Prompt Management Demo")
    print("=" * 50)
    
    # 1. Deploy a single prompt
    print("\n1. Deploying risk assessor prompt...")
    try:
        url = prompt_manager.deploy_prompt_to_langsmith(
            agent_name="risk_assessor",
            description="Updated risk assessment prompt with improved accuracy",
            tags=["production", "updated", "aml"]
        )
        print(f"✅ Prompt deployed: {url}")
    except Exception as e:
        print(f"❌ Failed to deploy prompt: {e}")
    
    # 2. Get prompt versions
    print("\n2. Getting prompt versions...")
    try:
        versions = prompt_manager.get_prompt_versions("risk_assessor")
        print(f"✅ Found {len(versions)} versions:")
        for i, version in enumerate(versions[:3]):  # Show first 3
            print(f"   Version {i+1}: {version.get('description', 'No description')}")
    except Exception as e:
        print(f"❌ Failed to get versions: {e}")
    
    # 3. Create agent chain
    print("\n3. Creating agent chain...")
    try:
        chain = prompt_manager.get_agent_chain(
            agent_name="risk_assessor",
            model_config={"model": "gpt-4o", "temperature": 0.2}
        )
        print("✅ Agent chain created successfully")
    except Exception as e:
        print(f"❌ Failed to create chain: {e}")


async def demo_tracing():
    """Demonstrate tracing capabilities"""
    print("\n📊 LangSmith Tracing Demo")
    print("=" * 50)
    
    # 1. Get agent metrics
    print("\n1. Getting agent performance metrics...")
    try:
        metrics = aml_tracer.get_agent_metrics()
        print("✅ Agent metrics:")
        for agent, stats in metrics.items():
            print(f"   {agent}: {stats['calls']} calls, {stats['avg_time']:.2f}s avg, {stats['errors']} errors")
    except Exception as e:
        print(f"❌ Failed to get metrics: {e}")
    
    # 2. Create investigation trace
    print("\n2. Creating investigation trace...")
    try:
        trace_data = aml_tracer.create_investigation_trace(
            case_id="CASE-2024-001",
            investigation_data={
                "transaction_amount": 50000,
                "risk_score": 85,
                "customer_type": "high_risk"
            }
        )
        print(f"✅ Investigation trace created: {trace_data['case_id']}")
    except Exception as e:
        print(f"❌ Failed to create trace: {e}")


async def demo_agent_with_tracing():
    """Demonstrate agent execution with tracing"""
    print("\n🤖 Agent Execution with Tracing Demo")
    print("=" * 50)
    
    # Example traced agent function
    @trace_risk_assessor("assess_transaction_risk")
    async def assess_risk_example(transaction_data):
        """Example risk assessment with tracing"""
        # Simulate processing time
        await asyncio.sleep(0.1)
        
        # Simulate risk assessment logic
        amount = transaction_data.get("amount", 0)
        risk_score = min(100, amount / 1000)  # Simple risk calculation
        
        return {
            "risk_score": risk_score,
            "risk_level": "High" if risk_score > 70 else "Medium" if risk_score > 30 else "Low",
            "recommendation": "Escalate" if risk_score > 70 else "Monitor"
        }
    
    # Execute traced agent
    print("\n1. Executing traced risk assessment...")
    try:
        result = await assess_risk_example({"amount": 75000})
        print(f"✅ Risk assessment result: {result}")
    except Exception as e:
        print(f"❌ Risk assessment failed: {e}")
    
    # Show updated metrics
    print("\n2. Updated agent metrics:")
    try:
        metrics = aml_tracer.get_agent_metrics("risk_assessor")
        print(f"✅ Risk assessor metrics: {metrics}")
    except Exception as e:
        print(f"❌ Failed to get updated metrics: {e}")


async def demo_prompt_versioning():
    """Demonstrate prompt versioning capabilities"""
    print("\n📝 Prompt Versioning Demo")
    print("=" * 50)
    
    # 1. Compare prompt versions
    print("\n1. Comparing prompt versions...")
    try:
        # This would work if we had multiple versions
        comparison = prompt_manager.compare_prompt_versions(
            agent_name="risk_assessor",
            version1="latest",
            version2="latest"
        )
        print(f"✅ Comparison result: {comparison.get('templates_different', 'N/A')}")
    except Exception as e:
        print(f"❌ Failed to compare versions: {e}")
    
    # 2. List all agent prompts
    print("\n2. Listing all agent prompts...")
    try:
        prompts = langsmith_manager.list_agent_prompts()
        print(f"✅ Found {len(prompts)} prompts in LangSmith")
        for prompt in prompts[:3]:  # Show first 3
            print(f"   - {prompt.name}: {prompt.description}")
    except Exception as e:
        print(f"❌ Failed to list prompts: {e}")


async def main():
    """Main demo function"""
    print("🚀 LangSmith Integration Demo")
    print("=" * 60)
    
    # Check environment
    if not os.getenv("LANGSMITH_API_KEY"):
        print("⚠️  LANGSMITH_API_KEY not set. Some features may not work.")
        print("   Set your LangSmith API key to enable full functionality.")
    
    try:
        # Run all demos
        await demo_prompt_management()
        await demo_tracing()
        await demo_agent_with_tracing()
        await demo_prompt_versioning()
        
        print("\n✅ LangSmith integration demo completed successfully!")
        print("\nNext steps:")
        print("1. Set LANGSMITH_API_KEY environment variable")
        print("2. Deploy prompts: python scripts/deploy_prompts.py")
        print("3. Access LangSmith dashboard to view traces and prompts")
        print("4. Use API endpoints at /api/prompts for prompt management")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())





