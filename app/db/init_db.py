"""
Database Initialization

This module handles database initialization, table creation,
and initial data seeding for the Multi-Agent AML Investigation System.
"""

from sqlalchemy.orm import Session
from app.db.session import SessionLocal, create_tables
from app.db.models import (
    Investigation, AgentExecution, Transaction, Customer, 
    Alert, SystemMetrics, AgentTrace
)
from app.core.logger import get_logger
from datetime import datetime, timedelta
import random

logger = get_logger(__name__)


def init_database():
    """Initialize database with tables and sample data"""
    try:
        # Create tables
        create_tables()
        logger.info("Database tables created successfully")
        
        # Seed sample data
        seed_sample_data()
        logger.info("Sample data seeded successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise


def seed_sample_data():
    """Seed database with sample data"""
    try:
        db = SessionLocal()
        
        # Create sample customers
        customers = [
            Customer(
                customer_id="C001",
                customer_name="John Smith",
                customer_type="individual",
                risk_level="low",
                kyc_status="completed",
                location="New York, NY",
                country="US"
            ),
            Customer(
                customer_id="C002",
                customer_name="Jane Doe",
                customer_type="individual",
                risk_level="medium",
                kyc_status="completed",
                location="Los Angeles, CA",
                country="US"
            ),
            Customer(
                customer_id="C003",
                customer_name="ABC Corporation",
                customer_type="corporate",
                risk_level="low",
                kyc_status="completed",
                location="Chicago, IL",
                country="US"
            )
        ]
        
        for customer in customers:
            db.add(customer)
        
        # Create sample transactions
        transactions = []
        for i in range(100):
            customer_id = f"C{random.randint(1, 3):03d}"
            amount = random.uniform(100, 50000)
            
            transaction = Transaction(
                transaction_id=f"T{i+1:05d}",
                customer_id=customer_id,
                counterparty_id=f"CP{random.randint(1, 10):03d}",
                amount=amount,
                currency="USD",
                transaction_type=random.choice(["deposit", "withdrawal", "transfer"]),
                transaction_date=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                location=random.choice(["New York, NY", "Los Angeles, CA", "Chicago, IL"]),
                country="US",
                description=f"Transaction {i+1}",
                status="completed"
            )
            transactions.append(transaction)
        
        for transaction in transactions:
            db.add(transaction)
        
        # Create sample alerts
        alerts = [
            Alert(
                alert_id="ALT001",
                transaction_id="T00001",
                alert_type="structuring",
                severity="high",
                status="open",
                description="Multiple transactions just under reporting threshold"
            ),
            Alert(
                alert_id="ALT002",
                transaction_id="T00002",
                alert_type="smurfing",
                severity="critical",
                status="open",
                description="Coordinated multi-account transactions"
            ),
            Alert(
                alert_id="ALT003",
                transaction_id="T00003",
                alert_type="behavioral",
                severity="medium",
                status="open",
                description="Unusual transaction pattern detected"
            )
        ]
        
        for alert in alerts:
            db.add(alert)
        
        # Create sample investigations
        investigations = [
            Investigation(
                investigation_id="INV001",
                alert_id="ALT001",
                transaction_id="T00001",
                status="completed",
                priority="high",
                risk_level="HIGH",
                user_id="system",
                created_at=datetime.utcnow() - timedelta(hours=2),
                completed_at=datetime.utcnow() - timedelta(hours=1),
                findings={"pattern_detected": "structuring", "risk_score": 0.85},
                final_report={"summary": "High risk structuring pattern detected"},
                audit_trail=["Investigation started", "Data enrichment completed", "Pattern analysis completed"]
            ),
            Investigation(
                investigation_id="INV002",
                alert_id="ALT002",
                transaction_id="T00002",
                status="running",
                priority="critical",
                user_id="system",
                created_at=datetime.utcnow() - timedelta(minutes=30),
                audit_trail=["Investigation started", "Data enrichment in progress"]
            )
        ]
        
        for investigation in investigations:
            db.add(investigation)
        
        # Commit all changes
        db.commit()
        logger.info("Sample data seeded successfully")
        
    except Exception as e:
        logger.error(f"Failed to seed sample data: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


def reset_database():
    """Reset database by dropping and recreating tables"""
    try:
        from app.db.session import drop_tables
        drop_tables()
        init_database()
        logger.info("Database reset successfully")
    except Exception as e:
        logger.error(f"Failed to reset database: {str(e)}")
        raise


if __name__ == "__main__":
    init_database()
