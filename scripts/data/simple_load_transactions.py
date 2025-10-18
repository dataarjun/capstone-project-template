"""
Simple Transaction Loader for PostgreSQL

This script loads transactions.csv into PostgreSQL without complex config dependencies.
"""

import pandas as pd
import asyncio
import asyncpg
from datetime import datetime
import os
from pathlib import Path

# Simple configuration
POSTGRES_URL = "postgresql://postgres.rddonqnsfmnwwvrbgsmi:supabase%007B@aws-1-us-east-2.pooler.supabase.com:5432/postgres"

async def load_transactions_simple():
    """Load transactions into PostgreSQL with simple approach"""
    print("🚀 Simple Transaction Loader")
    print("=" * 40)
    
    connection = None
    
    try:
        # Connect to database
        print("📡 Connecting to PostgreSQL...")
        connection = await asyncpg.connect(POSTGRES_URL)
        print("✅ Connected to PostgreSQL database")
        
        # Create transactions table
        print("📋 Creating transactions table...")
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS transactions (
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
        
        CREATE INDEX IF NOT EXISTS idx_transactions_sender ON transactions(sender_account_id);
        CREATE INDEX IF NOT EXISTS idx_transactions_receiver ON transactions(receiver_account_id);
        CREATE INDEX IF NOT EXISTS idx_transactions_amount ON transactions(amount);
        CREATE INDEX IF NOT EXISTS idx_transactions_timestamp ON transactions(timestamp);
        CREATE INDEX IF NOT EXISTS idx_transactions_fraud ON transactions(is_fraud);
        """
        
        await connection.execute(create_table_sql)
        print("✅ Transactions table created/verified")
        
        # Load transactions from CSV
        csv_path = "/Users/indrajitsingh/Course_Materials/AgenticAI/Capstone2025/data/transactions.csv"
        
        if not os.path.exists(csv_path):
            print(f"❌ CSV file not found: {csv_path}")
            return
        
        print(f"📥 Loading transactions from {csv_path}")
        
        # Get file size for progress tracking
        file_size = os.path.getsize(csv_path)
        print(f"📊 File size: {file_size / (1024*1024):.1f} MB")
        
        # Read CSV in chunks
        total_rows = 0
        chunk_count = 0
        batch_size = 5000  # Smaller batch size for stability
        
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
            insert_sql = """
            INSERT INTO transactions 
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
            
            await connection.executemany(insert_sql, records)
            total_rows += len(records)
            
            if chunk_count % 20 == 0:  # Progress update every 20 chunks
                print(f"📈 Processed {chunk_count} chunks, {total_rows:,} transactions loaded")
        
        print(f"✅ Successfully loaded {total_rows:,} transactions")
        
        # Get statistics
        print("\n📊 Getting transaction statistics...")
        stats = await connection.fetchrow("""
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
            FROM transactions
        """)
        
        print("📊 Transaction Statistics:")
        print(f"   Total Transactions: {stats['total_transactions']:,}")
        print(f"   Unique Senders: {stats['unique_senders']:,}")
        print(f"   Unique Receivers: {stats['unique_receivers']:,}")
        print(f"   Amount Range: ${stats['min_amount']:.2f} - ${stats['max_amount']:.2f}")
        print(f"   Average Amount: ${stats['avg_amount']:.2f}")
        print(f"   Fraud Transactions: {stats['fraud_count']:,}")
        print(f"   Date Range: {stats['earliest_transaction']} to {stats['latest_transaction']}")
        
        # Test retrieval
        print("\n🧪 Testing transaction retrieval...")
        test_transactions = await connection.fetch("""
            SELECT transaction_id, sender_account_id, receiver_account_id, tx_type, amount, is_fraud
            FROM transactions 
            ORDER BY transaction_id
            LIMIT 5
        """)
        
        print(f"📥 Retrieved {len(test_transactions)} test transactions:")
        for row in test_transactions:
            print(f"   ID: {row['transaction_id']}, Sender: {row['sender_account_id']}, "
                  f"Receiver: {row['receiver_account_id']}, Amount: ${row['amount']:.2f}, "
                  f"Type: {row['tx_type']}, Fraud: {row['is_fraud']}")
        
        print("\n✅ Transaction loading completed successfully!")
        
    except Exception as e:
        print(f"❌ Error loading transactions: {e}")
        import traceback
        print(traceback.format_exc())
    
    finally:
        if connection:
            await connection.close()
            print("✅ Disconnected from PostgreSQL database")

if __name__ == "__main__":
    asyncio.run(load_transactions_simple())
