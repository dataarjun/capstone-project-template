"""
Database Models

This module contains SQLAlchemy models for the Multi-Agent
AML Investigation System database schema.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Investigation(Base):
    """Investigation model"""
    __tablename__ = "investigations"
    
    id = Column(Integer, primary_key=True, index=True)
    investigation_id = Column(String(50), unique=True, index=True, nullable=False)
    alert_id = Column(String(50), nullable=False, index=True)
    transaction_id = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="running")
    priority = Column(String(20), nullable=False, default="medium")
    risk_level = Column(String(20), nullable=True)
    user_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    findings = Column(JSON, nullable=True)
    final_report = Column(JSON, nullable=True)
    audit_trail = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)


class AgentExecution(Base):
    """Agent execution model"""
    __tablename__ = "agent_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(String(50), unique=True, index=True, nullable=False)
    investigation_id = Column(String(50), nullable=False, index=True)
    agent_name = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="running")
    started_at = Column(DateTime, default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    execution_time = Column(Float, nullable=True)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    token_usage = Column(JSON, nullable=True)
    execution_metadata = Column(JSON, nullable=True)


class Transaction(Base):
    """Transaction model"""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(50), unique=True, index=True, nullable=False)
    customer_id = Column(String(50), nullable=False, index=True)
    counterparty_id = Column(String(50), nullable=True, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    transaction_type = Column(String(50), nullable=False)
    transaction_date = Column(DateTime, nullable=False, index=True)
    location = Column(String(100), nullable=True)
    country = Column(String(2), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="completed")
    created_at = Column(DateTime, default=func.now(), nullable=False)


class Customer(Base):
    """Customer model"""
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String(50), unique=True, index=True, nullable=False)
    customer_name = Column(String(100), nullable=False)
    customer_type = Column(String(50), nullable=False)
    risk_level = Column(String(20), nullable=False, default="low")
    kyc_status = Column(String(20), nullable=False, default="pending")
    location = Column(String(100), nullable=True)
    country = Column(String(2), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class Alert(Base):
    """Alert model"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(50), unique=True, index=True, nullable=False)
    transaction_id = Column(String(50), nullable=False, index=True)
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False, default="medium")
    status = Column(String(20), nullable=False, default="open")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(50), nullable=True)


class SystemMetrics(Base):
    """System metrics model"""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_type = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)
    execution_metadata = Column(JSON, nullable=True)


class AgentTrace(Base):
    """Agent trace model"""
    __tablename__ = "agent_traces"
    
    id = Column(Integer, primary_key=True, index=True)
    trace_id = Column(String(50), unique=True, index=True, nullable=False)
    investigation_id = Column(String(50), nullable=False, index=True)
    agent_name = Column(String(50), nullable=False, index=True)
    execution_id = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False)
    started_at = Column(DateTime, default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    execution_time = Column(Float, nullable=True)
    token_usage = Column(JSON, nullable=True)
    execution_metadata = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)


class FinancialTransaction(Base):
    """Financial transaction model for HI-Small_Trans.csv data"""
    __tablename__ = "financial_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    from_bank = Column(String(20), nullable=False, index=True)
    from_account = Column(String(50), nullable=False, index=True)
    to_bank = Column(String(20), nullable=False, index=True)
    to_account = Column(String(50), nullable=False, index=True)
    amount_received = Column(Float, nullable=False)
    receiving_currency = Column(String(10), nullable=False)
    amount_paid = Column(Float, nullable=False)
    payment_currency = Column(String(10), nullable=False)
    payment_format = Column(String(50), nullable=False)
    is_laundering = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
