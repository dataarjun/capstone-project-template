"""
SQLite Transaction Service for AML Agents

This service provides methods for AML agents to retrieve transaction data
from the SQLite database.
"""

import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
from pathlib import Path

from app.core.logger import get_logger

logger = get_logger(__name__)

class SQLiteTransactionService:
    """Service for retrieving transaction data for AML agents from SQLite"""
    
    def __init__(self, db_path: str = "data/transactions.db"):
        self.db_path = db_path
        self.connection = None
    
    def connect(self):
        """Connect to SQLite database"""
        try:
            # Ensure the database file exists
            if not Path(self.db_path).exists():
                raise FileNotFoundError(f"Database file not found: {self.db_path}")
            
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # Enable column access by name
            logger.info(f"Connected to SQLite database: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to SQLite: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from SQLite database"""
        if self.connection:
            self.connection.close()
            logger.info("Disconnected from SQLite database")
    
    def get_transactions_for_batch_processing(self, batch_size: int = 50, 
                                            offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get transactions formatted for batch processing with agents
        
        Args:
            batch_size: Number of transactions to retrieve
            offset: Number of transactions to skip
            
        Returns:
            List of transaction dictionaries formatted for agents
        """
        try:
            query = """
                SELECT 
                    transaction_id,
                    sender_account_id,
                    receiver_account_id,
                    tx_type,
                    amount,
                    timestamp,
                    is_fraud,
                    alert_id,
                    created_at
                FROM transactions 
                ORDER BY transaction_id
                LIMIT ? OFFSET ?
            """
            
            cursor = self.connection.execute(query, (batch_size, offset))
            rows = cursor.fetchall()
            
            # Convert to agent-friendly format
            transactions = []
            for row in rows:
                # Convert timestamp to datetime for agents
                transaction_date = datetime.fromtimestamp(row['timestamp']) if row['timestamp'] > 0 else datetime.now()
                
                transaction = {
                    "transaction_id": str(row['transaction_id']),  # String for Pydantic
                    "date": transaction_date,
                    "customer_id": str(row['sender_account_id']),  # Use sender as customer
                    "amount": float(row['amount']),
                    "type": str(row['tx_type']).lower(),  # Convert to lowercase
                    "description": f"Transaction {row['transaction_id']} - {row['tx_type']}",
                    "amount_z": 0.0,  # Will be calculated by agents if needed
                    "c_txn_7d": 1,  # Will be calculated by agents if needed
                    "kw_flag": bool(row['is_fraud']),  # Use fraud flag as keyword flag
                    # Additional fields for agents
                    "sender_account_id": str(row['sender_account_id']),
                    "receiver_account_id": str(row['receiver_account_id']),
                    "is_fraud": bool(row['is_fraud']),
                    "alert_id": int(row['alert_id']),
                    "original_timestamp": int(row['timestamp'])
                }
                transactions.append(transaction)
            
            logger.info(f"Retrieved {len(transactions)} transactions for batch processing")
            return transactions
            
        except Exception as e:
            logger.error(f"Error retrieving transactions for batch processing: {e}")
            return []
    
    def get_transaction_by_id(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific transaction by ID"""
        try:
            cursor = self.connection.execute("""
                SELECT 
                    transaction_id,
                    sender_account_id,
                    receiver_account_id,
                    tx_type,
                    amount,
                    timestamp,
                    is_fraud,
                    alert_id,
                    created_at
                FROM transactions 
                WHERE transaction_id = ?
            """, (int(transaction_id),))
            
            row = cursor.fetchone()
            
            if row:
                transaction_date = datetime.fromtimestamp(row['timestamp']) if row['timestamp'] > 0 else datetime.now()
                
                return {
                    "transaction_id": str(row['transaction_id']),
                    "date": transaction_date,
                    "customer_id": str(row['sender_account_id']),
                    "amount": float(row['amount']),
                    "type": str(row['tx_type']).lower(),
                    "description": f"Transaction {row['transaction_id']} - {row['tx_type']}",
                    "amount_z": 0.0,
                    "c_txn_7d": 1,
                    "kw_flag": bool(row['is_fraud']),
                    "sender_account_id": str(row['sender_account_id']),
                    "receiver_account_id": str(row['receiver_account_id']),
                    "is_fraud": bool(row['is_fraud']),
                    "alert_id": int(row['alert_id']),
                    "original_timestamp": int(row['timestamp'])
                }
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving transaction {transaction_id}: {e}")
            return None
    
    def get_fraud_transactions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get transactions marked as fraud"""
        try:
            query = """
                SELECT 
                    transaction_id,
                    sender_account_id,
                    receiver_account_id,
                    tx_type,
                    amount,
                    timestamp,
                    is_fraud,
                    alert_id,
                    created_at
                FROM transactions 
                WHERE is_fraud = 1
                ORDER BY amount DESC
                LIMIT ?
            """
            
            cursor = self.connection.execute(query, (limit,))
            rows = cursor.fetchall()
            
            transactions = []
            for row in rows:
                transaction_date = datetime.fromtimestamp(row['timestamp']) if row['timestamp'] > 0 else datetime.now()
                
                transaction = {
                    "transaction_id": str(row['transaction_id']),
                    "date": transaction_date,
                    "customer_id": str(row['sender_account_id']),
                    "amount": float(row['amount']),
                    "type": str(row['tx_type']).lower(),
                    "description": f"FRAUD - Transaction {row['transaction_id']} - {row['tx_type']}",
                    "amount_z": 0.0,
                    "c_txn_7d": 1,
                    "kw_flag": True,  # Always true for fraud
                    "sender_account_id": str(row['sender_account_id']),
                    "receiver_account_id": str(row['receiver_account_id']),
                    "is_fraud": True,
                    "alert_id": int(row['alert_id']),
                    "original_timestamp": int(row['timestamp'])
                }
                transactions.append(transaction)
            
            logger.info(f"Retrieved {len(transactions)} fraud transactions")
            return transactions
            
        except Exception as e:
            logger.error(f"Error retrieving fraud transactions: {e}")
            return []
    
    def get_high_value_transactions(self, min_amount: float = 10000.0, 
                                   limit: int = 100) -> List[Dict[str, Any]]:
        """Get high-value transactions"""
        try:
            query = """
                SELECT 
                    transaction_id,
                    sender_account_id,
                    receiver_account_id,
                    tx_type,
                    amount,
                    timestamp,
                    is_fraud,
                    alert_id,
                    created_at
                FROM transactions 
                WHERE amount >= ?
                ORDER BY amount DESC
                LIMIT ?
            """
            
            cursor = self.connection.execute(query, (min_amount, limit))
            rows = cursor.fetchall()
            
            transactions = []
            for row in rows:
                transaction_date = datetime.fromtimestamp(row['timestamp']) if row['timestamp'] > 0 else datetime.now()
                
                transaction = {
                    "transaction_id": str(row['transaction_id']),
                    "date": transaction_date,
                    "customer_id": str(row['sender_account_id']),
                    "amount": float(row['amount']),
                    "type": str(row['tx_type']).lower(),
                    "description": f"HIGH VALUE - Transaction {row['transaction_id']} - {row['tx_type']}",
                    "amount_z": 0.0,
                    "c_txn_7d": 1,
                    "kw_flag": bool(row['is_fraud']),
                    "sender_account_id": str(row['sender_account_id']),
                    "receiver_account_id": str(row['receiver_account_id']),
                    "is_fraud": bool(row['is_fraud']),
                    "alert_id": int(row['alert_id']),
                    "original_timestamp": int(row['timestamp'])
                }
                transactions.append(transaction)
            
            logger.info(f"Retrieved {len(transactions)} high-value transactions (>= ${min_amount})")
            return transactions
            
        except Exception as e:
            logger.error(f"Error retrieving high-value transactions: {e}")
            return []
    
    def get_transaction_statistics(self) -> Dict[str, Any]:
        """Get transaction statistics"""
        try:
            cursor = self.connection.execute("""
                SELECT 
                    COUNT(*) as total_transactions,
                    COUNT(DISTINCT sender_account_id) as unique_senders,
                    COUNT(DISTINCT receiver_account_id) as unique_receivers,
                    MIN(amount) as min_amount,
                    MAX(amount) as max_amount,
                    AVG(amount) as avg_amount,
                    COUNT(CASE WHEN is_fraud = 1 THEN 1 END) as fraud_count,
                    MIN(created_at) as earliest_transaction,
                    MAX(created_at) as latest_transaction
                FROM transactions
            """)
            
            stats = cursor.fetchone()
            return dict(stats) if stats else {}
            
        except Exception as e:
            logger.error(f"Error getting transaction statistics: {e}")
            return {}

# Global instance for easy access
sqlite_transaction_service = SQLiteTransactionService()
