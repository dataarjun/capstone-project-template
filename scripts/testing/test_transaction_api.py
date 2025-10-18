"""
Test Transaction API Endpoints

Comprehensive test script for the transaction API endpoints.
Tests all CRUD operations, filtering, and bulk operations.
"""

import asyncio
import aiohttp
import json
from datetime import datetime
import random

# API base URL
BASE_URL = "http://localhost:8000/api/transactions"

async def test_api_endpoint(session, method, url, data=None, params=None):
    """Test a single API endpoint"""
    try:
        async with session.request(method, url, json=data, params=params) as response:
            result = await response.json()
            print(f"✅ {method} {url} - Status: {response.status}")
            return result
    except Exception as e:
        print(f"❌ {method} {url} - Error: {e}")
        return None

async def test_health_check(session):
    """Test database health check"""
    print("\n🔍 Testing Health Check...")
    result = await test_api_endpoint(session, "GET", f"{BASE_URL}/health")
    if result:
        print(f"   Database Status: {result.get('status')}")
        print(f"   Total Transactions: {result.get('total_transactions', 0):,}")

async def test_get_statistics(session):
    """Test transaction statistics"""
    print("\n📊 Testing Transaction Statistics...")
    result = await test_api_endpoint(session, "GET", f"{BASE_URL}/stats")
    if result:
        print(f"   Total Transactions: {result.get('total_transactions', 0):,}")
        print(f"   Unique Senders: {result.get('unique_senders', 0):,}")
        print(f"   Unique Receivers: {result.get('unique_receivers', 0):,}")
        print(f"   Amount Range: ${result.get('min_amount', 0):.2f} - ${result.get('max_amount', 0):.2f}")
        print(f"   Average Amount: ${result.get('avg_amount', 0):.2f}")
        print(f"   Fraud Count: {result.get('fraud_count', 0):,}")

async def test_get_transactions(session):
    """Test getting transactions with filters"""
    print("\n📋 Testing Get Transactions...")
    
    # Test basic get
    result = await test_api_endpoint(session, "GET", f"{BASE_URL}/", params={"limit": 5})
    if result:
        print(f"   Retrieved {len(result)} transactions")
        if result:
            first_txn = result[0]
            print(f"   Sample Transaction: {first_txn.get('transaction_id')} - ${first_txn.get('amount'):.2f}")
    
    # Test fraud filter
    result = await test_api_endpoint(session, "GET", f"{BASE_URL}/", params={"fraud_only": "true", "limit": 3})
    if result:
        print(f"   Fraud Transactions: {len(result)}")
    
    # Test amount filter
    result = await test_api_endpoint(session, "GET", f"{BASE_URL}/", params={"min_amount": 50000, "limit": 3})
    if result:
        print(f"   High-Value Transactions: {len(result)}")

async def test_get_specific_transaction(session):
    """Test getting a specific transaction"""
    print("\n🔍 Testing Get Specific Transaction...")
    
    # First get a list to find a valid transaction ID
    result = await test_api_endpoint(session, "GET", f"{BASE_URL}/", params={"limit": 1})
    if result and result[0]:
        transaction_id = result[0]['transaction_id']
        result = await test_api_endpoint(session, "GET", f"{BASE_URL}/{transaction_id}")
        if result:
            print(f"   Retrieved Transaction: {result.get('transaction_id')} - ${result.get('amount'):.2f}")

async def test_get_fraud_transactions(session):
    """Test getting fraud transactions"""
    print("\n🚨 Testing Fraud Transactions...")
    result = await test_api_endpoint(session, "GET", f"{BASE_URL}/fraud/list", params={"limit": 5})
    if result:
        print(f"   Fraud Transactions: {len(result)}")
        for txn in result[:2]:
            print(f"   - {txn.get('transaction_id')}: ${txn.get('amount'):.2f} (Fraud: {txn.get('is_fraud')})")

async def test_get_high_value_transactions(session):
    """Test getting high-value transactions"""
    print("\n💰 Testing High-Value Transactions...")
    result = await test_api_endpoint(session, "GET", f"{BASE_URL}/high-value/list", 
                                   params={"min_amount": 10000, "limit": 5})
    if result:
        print(f"   High-Value Transactions: {len(result)}")
        for txn in result[:2]:
            print(f"   - {txn.get('transaction_id')}: ${txn.get('amount'):.2f}")

async def test_search_by_amount(session):
    """Test searching by amount range"""
    print("\n🔍 Testing Amount Range Search...")
    result = await test_api_endpoint(session, "GET", f"{BASE_URL}/search/amount", 
                                   params={"min_amount": 1000, "max_amount": 5000, "limit": 3})
    if result:
        print(f"   Amount Range Results: {len(result)}")
        for txn in result:
            print(f"   - {txn.get('transaction_id')}: ${txn.get('amount'):.2f}")

async def test_insert_single_transaction(session):
    """Test inserting a single transaction"""
    print("\n➕ Testing Single Transaction Insert...")
    
    # Generate a unique transaction ID
    timestamp = int(datetime.now().timestamp())
    transaction_id = f"TEST_{timestamp}"
    
    transaction_data = {
        "transaction_id": timestamp,
        "sender_account_id": 99999,
        "receiver_account_id": 88888,
        "tx_type": "test_transfer",
        "amount": 1000.50,
        "timestamp": timestamp,
        "is_fraud": False,
        "alert_id": -1
    }
    
    result = await test_api_endpoint(session, "POST", f"{BASE_URL}/", data=transaction_data)
    if result:
        print(f"   Inserted Transaction: {result.get('transaction_id')}")
        return result.get('transaction_id')
    return None

async def test_insert_bulk_transactions(session):
    """Test bulk transaction insert"""
    print("\n📦 Testing Bulk Transaction Insert...")
    
    # Generate test transactions
    transactions = []
    base_timestamp = int(datetime.now().timestamp())
    
    for i in range(5):
        transactions.append({
            "transaction_id": base_timestamp + i,
            "sender_account_id": 90000 + i,
            "receiver_account_id": 80000 + i,
            "tx_type": "bulk_test",
            "amount": round(random.uniform(100, 5000), 2),
            "timestamp": base_timestamp + i,
            "is_fraud": i % 3 == 0,  # Every 3rd transaction is fraud
            "alert_id": -1
        })
    
    bulk_data = {"transactions": transactions}
    result = await test_api_endpoint(session, "POST", f"{BASE_URL}/bulk", data=bulk_data)
    if result:
        print(f"   Bulk Insert: {result.get('count')} transactions")
        return [str(base_timestamp + i) for i in range(5)]
    return []

async def test_export_csv(session):
    """Test CSV export"""
    print("\n📄 Testing CSV Export...")
    result = await test_api_endpoint(session, "GET", f"{BASE_URL}/export/csv", 
                                   params={"limit": 10, "fraud_only": "false"})
    if result:
        print(f"   CSV Export: {result.get('count')} transactions")
        print(f"   Status: {result.get('status')}")

async def test_delete_transaction(session, transaction_id):
    """Test deleting a transaction"""
    if not transaction_id:
        return
    
    print(f"\n🗑️ Testing Delete Transaction: {transaction_id}...")
    result = await test_api_endpoint(session, "DELETE", f"{BASE_URL}/{transaction_id}")
    if result:
        print(f"   Deleted Transaction: {result.get('transaction_id')}")

async def run_comprehensive_tests():
    """Run all API tests"""
    print("🚀 Starting Comprehensive Transaction API Tests")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # Health and Statistics
        await test_health_check(session)
        await test_get_statistics(session)
        
        # Query Operations
        await test_get_transactions(session)
        await test_get_specific_transaction(session)
        await test_get_fraud_transactions(session)
        await test_get_high_value_transactions(session)
        await test_search_by_amount(session)
        
        # Insert Operations
        single_txn_id = await test_insert_single_transaction(session)
        bulk_txn_ids = await test_insert_bulk_transactions(session)
        
        # Export Operations
        await test_export_csv(session)
        
        # Delete Operations
        if single_txn_id:
            await test_delete_transaction(session, single_txn_id)
        
        # Clean up bulk transactions
        for txn_id in bulk_txn_ids:
            await test_delete_transaction(session, txn_id)
    
    print("\n" + "=" * 60)
    print("✅ All Transaction API Tests Completed!")

if __name__ == "__main__":
    print("🔧 Transaction API Test Suite")
    print("Make sure the FastAPI server is running on http://localhost:8000")
    print("Start the server with: python -m uvicorn app.main:app --reload")
    print()
    
    asyncio.run(run_comprehensive_tests())
