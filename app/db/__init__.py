"""
Database Layer

This module contains database configuration, models, and session management
for the Multi-Agent AML Investigation System.
"""

from .session import get_db, create_tables, drop_tables
from .postgres_session import (
    get_postgres_db, create_postgres_tables, drop_postgres_tables,
    test_postgres_connection, get_postgres_table_count
)
from .models import (
    Investigation, AgentExecution, Transaction, Customer, 
    Alert, SystemMetrics, AgentTrace, FinancialTransaction
)

__all__ = [
    # SQLite session functions
    "get_db", "create_tables", "drop_tables",
    # PostgreSQL session functions
    "get_postgres_db", "create_postgres_tables", "drop_postgres_tables",
    "test_postgres_connection", "get_postgres_table_count",
    # Models
    "Investigation", "AgentExecution", "Transaction", "Customer",
    "Alert", "SystemMetrics", "AgentTrace", "FinancialTransaction"
]
