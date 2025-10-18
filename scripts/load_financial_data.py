#!/usr/bin/env python3
"""
Financial Data Loader Script

This script loads 20% of the HI-Small_Trans.csv data into PostgreSQL.
It uses chunked reading for memory efficiency and batch inserts for performance.
"""

import sys
import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Tuple
import random

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.db.postgres_session import get_postgres_db, create_postgres_tables
from app.db.models import FinancialTransaction
from app.core.logger import get_logger

logger = get_logger(__name__)

# Configuration
CSV_FILE_PATH = project_root / "data" / "sampledata" / "HI-Small_Trans.csv"
CHUNK_SIZE = 10000  # Process 10k rows at a time
SAMPLE_RATIO = 0.20  # Load 20% of data
BATCH_SIZE = 1000   # Insert 1k records per batch

def get_csv_info() -> Tuple[int, int]:
    """Get total row count and estimate sample size"""
    print("📊 Analyzing CSV file...")
    
    # Count total lines (subtract 1 for header)
    with open(CSV_FILE_PATH, 'r') as f:
        total_lines = sum(1 for _ in f) - 1
    
    sample_size = int(total_lines * SAMPLE_RATIO)
    
    print(f"📁 File: {CSV_FILE_PATH}")
    print(f"📈 Total rows: {total_lines:,}")
    print(f"🎯 Target sample: {sample_size:,} rows ({SAMPLE_RATIO*100:.1f}%)")
    
    return total_lines, sample_size

def parse_timestamp(timestamp_str: str) -> datetime:
    """Parse timestamp string to datetime object"""
    try:
        return datetime.strptime(timestamp_str, "%Y/%m/%d %H:%M")
    except ValueError:
        # Try alternative format if needed
        return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

def process_chunk(chunk: pd.DataFrame, sample_ratio: float) -> List[FinancialTransaction]:
    """Process a chunk of data and return FinancialTransaction objects"""
    transactions = []
    
    # Sample the chunk
    if sample_ratio < 1.0:
        chunk = chunk.sample(frac=sample_ratio, random_state=42)
    
    for _, row in chunk.iterrows():
        try:
            transaction = FinancialTransaction(
                timestamp=parse_timestamp(row['Timestamp']),
                from_bank=str(row['From Bank']),
                from_account=str(row['Account']),
                to_bank=str(row['To Bank']),
                to_account=str(row['Account']),  # Note: CSV has 'Account' for both from and to
                amount_received=float(row['Amount Received']),
                receiving_currency=str(row['Receiving Currency']),
                amount_paid=float(row['Amount Paid']),
                payment_currency=str(row['Payment Currency']),
                payment_format=str(row['Payment Format']),
                is_laundering=int(row['Is Laundering'])
            )
            transactions.append(transaction)
        except Exception as e:
            logger.warning(f"Failed to process row: {str(e)}")
            continue
    
    return transactions

def load_data():
    """Load financial data into PostgreSQL"""
    print("🚀 Starting financial data loading...")
    print(f"⏰ Started at: {datetime.now()}")
    
    # Get CSV info
    total_rows, target_sample = get_csv_info()
    
    # Ensure tables exist
    print("\n📋 Creating database tables...")
    create_postgres_tables()
    print("✅ Tables created/verified")
    
    # Initialize counters
    total_loaded = 0
    laundering_count = 0
    non_laundering_count = 0
    chunk_count = 0
    
    print(f"\n📥 Loading data in chunks of {CHUNK_SIZE:,} rows...")
    print("=" * 60)
    
    try:
        # Read CSV in chunks
        chunk_iterator = pd.read_csv(
            CSV_FILE_PATH, 
            chunksize=CHUNK_SIZE,
            dtype={'Is Laundering': 'int64'}  # Ensure consistent data type
        )
        
        for chunk in chunk_iterator:
            chunk_count += 1
            
            # Process chunk
            transactions = process_chunk(chunk, SAMPLE_RATIO)
            
            if not transactions:
                continue
            
            # Batch insert
            db_gen = get_postgres_db()
            db = next(db_gen)
            
            try:
                # Insert in batches
                for i in range(0, len(transactions), BATCH_SIZE):
                    batch = transactions[i:i + BATCH_SIZE]
                    db.bulk_save_objects(batch)
                    db.commit()
                    
                    # Update counters
                    batch_laundering = sum(1 for t in batch if t.is_laundering == 1)
                    laundering_count += batch_laundering
                    non_laundering_count += len(batch) - batch_laundering
                    total_loaded += len(batch)
                
                # Progress update
                progress = (total_loaded / target_sample) * 100
                print(f"📊 Chunk {chunk_count}: Loaded {total_loaded:,}/{target_sample:,} rows ({progress:.1f}%)")
                
            except Exception as e:
                logger.error(f"Failed to insert chunk {chunk_count}: {str(e)}")
                db.rollback()
                raise
            finally:
                db.close()
            
            # Stop if we've loaded enough
            if total_loaded >= target_sample:
                break
        
        # Final statistics
        print("\n" + "=" * 60)
        print("📊 LOADING COMPLETE!")
        print("=" * 60)
        print(f"✅ Total records loaded: {total_loaded:,}")
        print(f"🔴 Laundering transactions: {laundering_count:,} ({laundering_count/total_loaded*100:.2f}%)")
        print(f"🟢 Non-laundering transactions: {non_laundering_count:,} ({non_laundering_count/total_loaded*100:.2f}%)")
        print(f"📁 Chunks processed: {chunk_count}")
        print(f"⏰ Completed at: {datetime.now()}")
        
        return True
        
    except Exception as e:
        logger.error(f"Data loading failed: {str(e)}")
        print(f"❌ Error: {str(e)}")
        return False

def verify_data():
    """Verify the loaded data"""
    print("\n🔍 Verifying loaded data...")
    
    try:
        db_gen = get_postgres_db()
        db = next(db_gen)
        
        # Get total count
        total_count = db.query(FinancialTransaction).count()
        print(f"📊 Total records in database: {total_count:,}")
        
        # Get laundering statistics
        laundering_count = db.query(FinancialTransaction).filter(
            FinancialTransaction.is_laundering == 1
        ).count()
        
        non_laundering_count = total_count - laundering_count
        
        print(f"🔴 Laundering transactions: {laundering_count:,}")
        print(f"🟢 Non-laundering transactions: {non_laundering_count:,}")
        
        # Get date range
        min_date = db.query(FinancialTransaction).order_by(FinancialTransaction.timestamp.asc()).first()
        max_date = db.query(FinancialTransaction).order_by(FinancialTransaction.timestamp.desc()).first()
        
        if min_date and max_date:
            print(f"📅 Date range: {min_date.timestamp} to {max_date.timestamp}")
        
        # Get amount statistics
        result = db.query(
            FinancialTransaction.amount_received
        ).all()
        
        if result:
            amounts = [r[0] for r in result]
            print(f"💰 Amount range: ${min(amounts):,.2f} to ${max(amounts):,.2f}")
            print(f"💰 Average amount: ${sum(amounts)/len(amounts):,.2f}")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"Data verification failed: {str(e)}")
        print(f"❌ Verification error: {str(e)}")
        return False

def main():
    """Main function"""
    print("🏦 Financial Data Loader for PostgreSQL")
    print("=" * 60)
    
    # Check if CSV file exists
    if not CSV_FILE_PATH.exists():
        print(f"❌ CSV file not found: {CSV_FILE_PATH}")
        print("Please ensure the HI-Small_Trans.csv file exists in the data/sampledata directory.")
        return 1
    
    # Load data
    success = load_data()
    
    if not success:
        print("❌ Data loading failed!")
        return 1
    
    # Verify data
    verify_success = verify_data()
    
    if not verify_success:
        print("⚠️  Data verification failed, but loading may have succeeded.")
        return 1
    
    print("\n🎉 Data loading completed successfully!")
    print("You can now run: python scripts/test_postgres_connection.py")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
