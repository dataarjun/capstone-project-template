"""
PostgreSQL Transaction Service for AML Agents

This service provides methods for AML agents to retrieve transaction data
from the PostgreSQL database.
"""

import asyncio
import asyncpg
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd

from app.core.config_simple import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

class PostgreSQLTransactionService:
    """Service for retrieving transaction data for AML agents from PostgreSQL"""
    
    def __init__(self, table_name: str = "csv_transactions"):
        self.postgres_url = settings.POSTGRES_URL
        self.connection = None
        self.table_name = table_name
    
    async def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.connection = await asyncpg.connect(self.postgres_url)
            logger.info("Connected to PostgreSQL database for transaction service")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from PostgreSQL database"""
        if self.connection:
            await self.connection.close()
            logger.info("Disconnected from PostgreSQL database")
    
    async def get_transactions_for_batch_processing(self, batch_size: int = 50, 
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
            query = f"""
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
                FROM {self.table_name} 
                ORDER BY transaction_id
                LIMIT $1 OFFSET $2
            """
            
            rows = await self.connection.fetch(query, batch_size, offset)
            
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
    
    async def get_transaction_by_id(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific transaction by ID"""
        try:
            row = await self.connection.fetchrow(f"""
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
                FROM {self.table_name} 
                WHERE transaction_id = $1
            """, int(transaction_id))
            
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
    
    async def get_fraud_transactions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get transactions marked as fraud"""
        try:
            query = f"""
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
                FROM {self.table_name} 
                WHERE is_fraud = true
                ORDER BY amount DESC
                LIMIT $1
            """
            
            rows = await self.connection.fetch(query, limit)
            
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
    
    async def get_high_value_transactions(self, min_amount: float = 10000.0, 
                                       limit: int = 100) -> List[Dict[str, Any]]:
        """Get high-value transactions"""
        try:
            query = f"""
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
                FROM {self.table_name} 
                WHERE amount >= $1
                ORDER BY amount DESC
                LIMIT $2
            """
            
            rows = await self.connection.fetch(query, min_amount, limit)
            
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
    
    async def get_transaction_statistics(self) -> Dict[str, Any]:
        """Get transaction statistics"""
        try:
            stats = await self.connection.fetchrow(f"""
                SELECT 
                    COUNT(*) as total_transactions,
                    COUNT(DISTINCT sender_account_id) as unique_senders,
                    COUNT(DISTINCT receiver_account_id) as unique_receivers,
                    MIN(amount) as min_amount,
                    MAX(amount) as max_amount,
                    AVG(amount) as avg_amount,
                    COUNT(CASE WHEN is_fraud = true THEN 1 END) as fraud_count,
                    MIN(created_at) as earliest_transaction,
                    MAX(created_at) as latest_transaction
                FROM {self.table_name}
            """)
            
            return dict(stats)
            
        except Exception as e:
            logger.error(f"Error getting transaction statistics: {e}")
            return {}

# Global instance for easy access
postgres_transaction_service = PostgreSQLTransactionService()
