"""
Load Transactions Data into PostgreSQL Database (Version 2)

This script loads the transactions.csv file into a new PostgreSQL table
to avoid conflicts with existing tables.
"""

import pandas as pd
import asyncio
import asyncpg
from datetime import datetime
import os
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Import the existing database configuration
from app.core.config_simple import settings

class PostgreSQLTransactionLoaderV2:
    """Load and manage transaction data in PostgreSQL with new table"""
    
    def __init__(self):
        self.postgres_url = settings.POSTGRES_URL
        self.connection = None
        self.table_name = "csv_transactions"  # Use different table name
    
    async def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.connection = await asyncpg.connect(self.postgres_url)
            print("✅ Connected to PostgreSQL database")
        except Exception as e:
            print(f"❌ Failed to connect to PostgreSQL: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from PostgreSQL database"""
        if self.connection:
            await self.connection.close()
            print("✅ Disconnected from PostgreSQL database")
    
    async def create_transactions_table(self):
        """Create transactions table if it doesn't exist"""
        try:
            # First, check if table exists
            table_exists = await self.connection.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = $1
                );
            """, self.table_name)
            
            if not table_exists:
                print(f"📋 Creating {self.table_name} table...")
                create_table_sql = f"""
                CREATE TABLE {self.table_name} (
                    transaction_id INTEGER PRIMARY KEY,
                    sender_account_id INTEGER NOT NULL,
                    receiver_account_id INTEGER NOT NULL,
                    tx_type VARCHAR(50) NOT NULL,
                    amount DECIMAL(15,2) NOT NULL,
                    timestamp BIGINT NOT NULL,
                    is_fraud BOOLEAN NOT NULL DEFAULT FALSE,
                    alert_id INTEGER DEFAULT -1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
                await self.connection.execute(create_table_sql)
                print(f"✅ {self.table_name} table created")
            else:
                print(f"✅ {self.table_name} table already exists")
            
            # Create indexes separately
            print("📋 Creating indexes...")
            index_statements = [
                f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_sender ON {self.table_name}(sender_account_id)",
                f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_receiver ON {self.table_name}(receiver_account_id)",
                f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_amount ON {self.table_name}(amount)",
                f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_timestamp ON {self.table_name}(timestamp)",
                f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_fraud ON {self.table_name}(is_fraud)"
            ]
            
            for index_sql in index_statements:
                try:
                    await self.connection.execute(index_sql)
                except Exception as e:
                    print(f"⚠️ Index creation warning: {e}")
            
            print("✅ Indexes created/verified")
            
        except Exception as e:
            print(f"❌ Failed to create transactions table: {e}")
            raise
    
    async def load_transactions_from_csv(self, csv_path: str, batch_size: int = 10000):
        """Load transactions from CSV file into PostgreSQL"""
        print(f"📥 Loading transactions from {csv_path}")
        
        # Check if file exists
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        # Get file size for progress tracking
        file_size = os.path.getsize(csv_path)
        print(f"📊 File size: {file_size / (1024*1024):.1f} MB")
        
        # Read CSV in chunks
        total_rows = 0
        chunk_count = 0
        
        try:
            for chunk in pd.read_csv(csv_path, chunksize=batch_size):
                chunk_count += 1
                
                # Prepare data for insertion
                records = []
                for _, row in chunk.iterrows():
                    records.append((
                        int(row['transaction_id']),
                        int(row['SENDER_ACCOUNT_ID']),
                        int(row['RECEIVER_ACCOUNT_ID']),
                        str(row['TX_TYPE']),
                        float(row['amount']),
                        int(row['TIMESTAMP']),
                        bool(row['IS_FRAUD']),
                        int(row['ALERT_ID'])
                    ))
                
                # Insert batch into database
                insert_sql = f"""
                INSERT INTO {self.table_name} 
                (transaction_id, sender_account_id, receiver_account_id, tx_type, amount, timestamp, is_fraud, alert_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (transaction_id) DO UPDATE SET
                    sender_account_id = EXCLUDED.sender_account_id,
                    receiver_account_id = EXCLUDED.receiver_account_id,
                    tx_type = EXCLUDED.tx_type,
                    amount = EXCLUDED.amount,
                    timestamp = EXCLUDED.timestamp,
                    is_fraud = EXCLUDED.is_fraud,
                    alert_id = EXCLUDED.alert_id,
                    updated_at = CURRENT_TIMESTAMP
                """
                
                await self.connection.executemany(insert_sql, records)
                total_rows += len(records)
                
                if chunk_count % 50 == 0:  # Progress update every 50 chunks
                    print(f"📈 Processed {chunk_count} chunks, {total_rows:,} transactions loaded")
            
            print(f"✅ Successfully loaded {total_rows:,} transactions")
            return total_rows
            
        except Exception as e:
            print(f"❌ Error loading transactions: {e}")
            raise
    
    async def get_transaction_stats(self):
        """Get statistics about loaded transactions"""
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
            
            print("📊 Transaction Statistics:")
            print(f"   Total Transactions: {stats['total_transactions']:,}")
            print(f"   Unique Senders: {stats['unique_senders']:,}")
            print(f"   Unique Receivers: {stats['unique_receivers']:,}")
            print(f"   Amount Range: ${stats['min_amount']:.2f} - ${stats['max_amount']:.2f}")
            print(f"   Average Amount: ${stats['avg_amount']:.2f}")
            print(f"   Fraud Transactions: {stats['fraud_count']:,}")
            print(f"   Date Range: {stats['earliest_transaction']} to {stats['latest_transaction']}")
            
            return dict(stats)
            
        except Exception as e:
            print(f"❌ Error getting transaction stats: {e}")
            return None

class PostgreSQLTransactionRetrieverV2:
    """Retrieve transaction data for AML agents from PostgreSQL"""
    
    def __init__(self):
        self.postgres_url = settings.POSTGRES_URL
        self.connection = None
        self.table_name = "csv_transactions"
    
    async def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.connection = await asyncpg.connect(self.postgres_url)
            print("✅ Connected to PostgreSQL database for retrieval")
        except Exception as e:
            print(f"❌ Failed to connect to PostgreSQL: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from PostgreSQL database"""
        if self.connection:
            await self.connection.close()
    
    async def get_transactions_for_agents(self, limit: int = 100, offset: int = 0, 
                                        min_amount: float = None, max_amount: float = None,
                                        fraud_only: bool = False):
        """
        Retrieve transactions formatted for AML agents
        
        Args:
            limit: Maximum number of transactions to retrieve
            offset: Number of transactions to skip
            min_amount: Minimum transaction amount filter
            max_amount: Maximum transaction amount filter
            fraud_only: If True, only return fraud transactions
        
        Returns:
            List of transaction dictionaries formatted for agents
        """
        try:
            # Build query
            where_conditions = []
            params = []
            param_count = 0
            
            if min_amount is not None:
                param_count += 1
                where_conditions.append(f"amount >= ${param_count}")
                params.append(min_amount)
            
            if max_amount is not None:
                param_count += 1
                where_conditions.append(f"amount <= ${param_count}")
                params.append(max_amount)
            
            if fraud_only:
                where_conditions.append("is_fraud = true")
            
            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            param_count += 1
            params.append(limit)
            param_count += 1
            params.append(offset)
            
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
                {where_clause}
                ORDER BY transaction_id
                LIMIT ${param_count - 1} OFFSET ${param_count}
            """
            
            rows = await self.connection.fetch(query, *params)
            
            # Convert to agent-friendly format
            transactions = []
            for row in rows:
                transaction = {
                    "transaction_id": str(row['transaction_id']),  # Convert to string for agents
                    "sender_account_id": str(row['sender_account_id']),
                    "receiver_account_id": str(row['receiver_account_id']),
                    "tx_type": str(row['tx_type']),
                    "amount": float(row['amount']),
                    "timestamp": int(row['timestamp']),
                    "is_fraud": bool(row['is_fraud']),
                    "alert_id": int(row['alert_id']),
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None
                }
                transactions.append(transaction)
            
            print(f"📥 Retrieved {len(transactions)} transactions for agents")
            return transactions
            
        except Exception as e:
            print(f"❌ Error retrieving transactions: {e}")
            return []
    
    async def get_transaction_by_id(self, transaction_id: str):
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
                return {
                    "transaction_id": str(row['transaction_id']),
                    "sender_account_id": str(row['sender_account_id']),
                    "receiver_account_id": str(row['receiver_account_id']),
                    "tx_type": str(row['tx_type']),
                    "amount": float(row['amount']),
                    "timestamp": int(row['timestamp']),
                    "is_fraud": bool(row['is_fraud']),
                    "alert_id": int(row['alert_id']),
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None
                }
            return None
            
        except Exception as e:
            print(f"❌ Error retrieving transaction {transaction_id}: {e}")
            return None

async def main():
    """Main function to load transactions and test retrieval"""
    print("🚀 Loading Transactions into PostgreSQL Database (V2)")
    print("=" * 60)
    
    # Initialize loader
    loader = PostgreSQLTransactionLoaderV2()
    
    try:
        # Connect to database
        await loader.connect()
        
        # Create table
        await loader.create_transactions_table()
        
        # Load transactions from CSV
        csv_path = "/Users/indrajitsingh/Course_Materials/AgenticAI/Capstone2025/data/transactions.csv"
        total_loaded = await loader.load_transactions_from_csv(csv_path, batch_size=5000)
        
        # Get statistics
        await loader.get_transaction_stats()
        
        # Test retrieval
        print("\n🧪 Testing Transaction Retrieval")
        print("=" * 40)
        
        retriever = PostgreSQLTransactionRetrieverV2()
        await retriever.connect()
        
        # Test getting sample transactions
        sample_transactions = await retriever.get_transactions_for_agents(limit=10)
        print(f"📥 Retrieved {len(sample_transactions)} sample transactions")
        
        if sample_transactions:
            print("📋 Sample transaction:")
            sample = sample_transactions[0]
            for key, value in sample.items():
                print(f"   {key}: {value} (type: {type(value).__name__})")
        
        # Test getting fraud transactions
        fraud_transactions = await retriever.get_transactions_for_agents(limit=5, fraud_only=True)
        print(f"🚨 Retrieved {len(fraud_transactions)} fraud transactions")
        
        # Test getting high-value transactions
        high_value_transactions = await retriever.get_transactions_for_agents(
            limit=5, min_amount=10000.0
        )
        print(f"💰 Retrieved {len(high_value_transactions)} high-value transactions")
        
        await retriever.disconnect()
        
        print("\n✅ Transaction loading and retrieval completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in main process: {e}")
        import traceback
        print(traceback.format_exc())
    
    finally:
        await loader.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
