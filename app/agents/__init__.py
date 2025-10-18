"""
Production-Ready AML Agents

This module contains the production-ready agents for the Multi-Agent AML Investigation System.
All agents are designed with proper @tool decorators, memory, and chat functionality.
"""

from .production_workflow_simple import (
    production_workflow,
    analyze_transaction,
    query_investigations
)

__all__ = [
    "production_workflow",
    "analyze_transaction", 
    "query_investigations"
]