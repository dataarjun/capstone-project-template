"""
Demo: Using AML Agents with SQLite Transaction Data

This script demonstrates how to:
1. Retrieve transactions from SQLite database
2. Process transactions through the AML agents
3. Show results and statistics
"""

import asyncio
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from app.services.sqlite_transaction_service import SQLiteTransactionService
from app.agents.simple_workflow import run_simple_investigation
from app.core.logger import get_logger

logger = get_logger(__name__)

async def demo_agents_with_sqlite_data():
    """
    Demonstrate using AML agents with SQLite transaction data
    """
    print("🚀 AML Agents with SQLite Data Demo")
    print("=" * 60)
    
    # Initialize transaction service
    transaction_service = SQLiteTransactionService()
    
    try:
        # Connect to database
        transaction_service.connect()
        
        # Get transaction statistics
        print("📊 Database Statistics:")
        stats = transaction_service.get_transaction_statistics()
        if stats:
            print(f"   Total Transactions: {stats.get('total_transactions', 0):,}")
            print(f"   Unique Senders: {stats.get('unique_senders', 0):,}")
            print(f"   Unique Receivers: {stats.get('unique_receivers', 0):,}")
            print(f"   Amount Range: ${stats.get('min_amount', 0):.2f} - ${stats.get('max_amount', 0):.2f}")
            print(f"   Average Amount: ${stats.get('avg_amount', 0):.2f}")
            print(f"   Fraud Transactions: {stats.get('fraud_count', 0):,}")
        else:
            print("   No statistics available - database may be empty")
            return
        
        # Demo 1: Process a batch of regular transactions
        print("\n🧪 Demo 1: Processing Regular Transactions")
        print("-" * 50)
        
        regular_transactions = transaction_service.get_transactions_for_batch_processing(
            batch_size=10, offset=0
        )
        
        if not regular_transactions:
            print("❌ No transactions found in database")
            return
        
        print(f"📥 Retrieved {len(regular_transactions)} regular transactions")
        
        # Process first 5 transactions through agents
        results = []
        for i, transaction_data in enumerate(regular_transactions[:5]):
            try:
                print(f"🔄 Processing transaction {transaction_data['transaction_id']}...")
                
                result = await run_simple_investigation(
                    transaction_data,
                    config={"configurable": {"thread_id": f"demo-regular-{i}"}}
                )
                
                results.append(result)
                print(f"✅ Transaction {transaction_data['transaction_id']}: {result['risk_level']} risk")
                
            except Exception as e:
                print(f"❌ Transaction {transaction_data['transaction_id']} failed: {str(e)}")
                results.append({
                    "transaction_id": transaction_data['transaction_id'],
                    "error": str(e),
                    "risk_level": "Unknown",
                    "risk_score": 0.0,
                    "escalated": False,
                    "severity": "Low"
                })
        
        # Show results summary
        print(f"\n📊 Regular Transactions Results:")
        print(f"   Processed: {len(results)}")
        successful = len([r for r in results if 'error' not in r])
        print(f"   Successful: {successful}")
        print(f"   Failed: {len(results) - successful}")
        
        if results:
            risk_levels = [r.get('risk_level', 'Unknown') for r in results if 'error' not in r]
            risk_dist = pd.Series(risk_levels).value_counts()
            print(f"   Risk Distribution:")
            for level, count in risk_dist.items():
                print(f"     {level}: {count}")
        
        # Demo 2: Process fraud transactions
        print("\n🚨 Demo 2: Processing Fraud Transactions")
        print("-" * 50)
        
        fraud_transactions = transaction_service.get_fraud_transactions(limit=5)
        
        if fraud_transactions:
            print(f"📥 Retrieved {len(fraud_transactions)} fraud transactions")
            
            fraud_results = []
            for i, transaction_data in enumerate(fraud_transactions[:3]):  # Process first 3
                try:
                    print(f"🔄 Processing fraud transaction {transaction_data['transaction_id']}...")
                    
                    result = await run_simple_investigation(
                        transaction_data,
                        config={"configurable": {"thread_id": f"demo-fraud-{i}"}}
                    )
                    
                    fraud_results.append(result)
                    print(f"✅ Fraud transaction {transaction_data['transaction_id']}: {result['risk_level']} risk")
                    
                except Exception as e:
                    print(f"❌ Fraud transaction {transaction_data['transaction_id']} failed: {str(e)}")
                    fraud_results.append({
                        "transaction_id": transaction_data['transaction_id'],
                        "error": str(e),
                        "risk_level": "Unknown",
                        "risk_score": 0.0,
                        "escalated": False,
                        "severity": "Low"
                    })
            
            # Show fraud results
            print(f"\n📊 Fraud Transactions Results:")
            print(f"   Processed: {len(fraud_results)}")
            successful_fraud = len([r for r in fraud_results if 'error' not in r])
            print(f"   Successful: {successful_fraud}")
            print(f"   Failed: {len(fraud_results) - successful_fraud}")
            
            if fraud_results:
                fraud_risk_levels = [r.get('risk_level', 'Unknown') for r in fraud_results if 'error' not in r]
                fraud_risk_dist = pd.Series(fraud_risk_levels).value_counts()
                print(f"   Risk Distribution:")
                for level, count in fraud_risk_dist.items():
                    print(f"     {level}: {count}")
        else:
            print("❌ No fraud transactions found")
        
        # Demo 3: Process high-value transactions
        print("\n💰 Demo 3: Processing High-Value Transactions")
        print("-" * 50)
        
        high_value_transactions = transaction_service.get_high_value_transactions(
            min_amount=5000.0, limit=5
        )
        
        if high_value_transactions:
            print(f"📥 Retrieved {len(high_value_transactions)} high-value transactions")
            
            hv_results = []
            for i, transaction_data in enumerate(high_value_transactions[:3]):  # Process first 3
                try:
                    print(f"🔄 Processing high-value transaction {transaction_data['transaction_id']}...")
                    
                    result = await run_simple_investigation(
                        transaction_data,
                        config={"configurable": {"thread_id": f"demo-hv-{i}"}}
                    )
                    
                    hv_results.append(result)
                    print(f"✅ High-value transaction {transaction_data['transaction_id']}: {result['risk_level']} risk")
                    
                except Exception as e:
                    print(f"❌ High-value transaction {transaction_data['transaction_id']} failed: {str(e)}")
                    hv_results.append({
                        "transaction_id": transaction_data['transaction_id'],
                        "error": str(e),
                        "risk_level": "Unknown",
                        "risk_score": 0.0,
                        "escalated": False,
                        "severity": "Low"
                    })
            
            # Show high-value results
            print(f"\n📊 High-Value Transactions Results:")
            print(f"   Processed: {len(hv_results)}")
            successful_hv = len([r for r in hv_results if 'error' not in r])
            print(f"   Successful: {successful_hv}")
            print(f"   Failed: {len(hv_results) - successful_hv}")
            
            if hv_results:
                hv_risk_levels = [r.get('risk_level', 'Unknown') for r in hv_results if 'error' not in r]
                hv_risk_dist = pd.Series(hv_risk_levels).value_counts()
                print(f"   Risk Distribution:")
                for level, count in hv_risk_dist.items():
                    print(f"     {level}: {count}")
        else:
            print("❌ No high-value transactions found")
        
        # Overall summary
        print(f"\n🎉 Demo Completed Successfully!")
        print(f"   Regular transactions processed: {len(results)}")
        print(f"   Fraud transactions processed: {len(fraud_results) if 'fraud_results' in locals() else 0}")
        print(f"   High-value transactions processed: {len(hv_results) if 'hv_results' in locals() else 0}")
        
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        import traceback
        print(traceback.format_exc())
    
    finally:
        transaction_service.disconnect()

async def demo_batch_processing():
    """
    Demo batch processing with SQLite data
    """
    print("\n🔄 Batch Processing Demo with SQLite Data")
    print("=" * 60)
    
    transaction_service = SQLiteTransactionService()
    
    try:
        transaction_service.connect()
        
        # Get a larger batch for processing
        batch_transactions = transaction_service.get_transactions_for_batch_processing(
            batch_size=20, offset=0
        )
        
        if not batch_transactions:
            print("❌ No transactions found for batch processing")
            return
        
        print(f"📥 Retrieved {len(batch_transactions)} transactions for batch processing")
        
        # Process batch
        batch_results = []
        for i, transaction_data in enumerate(batch_transactions):
            try:
                result = await run_simple_investigation(
                    transaction_data,
                    config={"configurable": {"thread_id": f"batch-{i}"}}
                )
                batch_results.append(result)
                
                if (i + 1) % 5 == 0:  # Progress update every 5 transactions
                    print(f"📈 Processed {i + 1}/{len(batch_transactions)} transactions")
                
            except Exception as e:
                print(f"❌ Transaction {transaction_data['transaction_id']} failed: {str(e)}")
                batch_results.append({
                    "transaction_id": transaction_data['transaction_id'],
                    "error": str(e),
                    "risk_level": "Unknown",
                    "risk_score": 0.0,
                    "escalated": False,
                    "severity": "Low"
                })
        
        # Batch results summary
        print(f"\n📊 Batch Processing Results:")
        print(f"   Total Processed: {len(batch_results)}")
        successful = len([r for r in batch_results if 'error' not in r])
        print(f"   Successful: {successful}")
        print(f"   Failed: {len(batch_results) - successful}")
        print(f"   Escalated: {sum(1 for r in batch_results if r.get('escalated', False))}")
        
        # Risk distribution
        risk_levels = [r.get('risk_level', 'Unknown') for r in batch_results if 'error' not in r]
        if risk_levels:
            risk_dist = pd.Series(risk_levels).value_counts()
            print(f"\n📈 Risk Level Distribution:")
            for level, count in risk_dist.items():
                print(f"   {level}: {count} ({count/len(risk_levels)*100:.1f}%)")
        
    except Exception as e:
        print(f"❌ Batch processing demo failed: {str(e)}")
        import traceback
        print(traceback.format_exc())
    
    finally:
        transaction_service.disconnect()

if __name__ == "__main__":
    print("🔧 AML Agents with SQLite Data Demo")
    print("=" * 60)
    
    # Run main demo
    asyncio.run(demo_agents_with_sqlite_data())
    
    # Run batch processing demo
    asyncio.run(demo_batch_processing())
    
    print("\n🎉 All demos completed!")
