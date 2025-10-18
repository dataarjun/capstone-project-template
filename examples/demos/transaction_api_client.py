"""
Transaction API Client

Simple client for interacting with the Transaction API endpoints.
Provides easy-to-use methods for common operations.
"""

import requests
import json
from typing import List, Dict, Optional, Any
from datetime import datetime

class TransactionAPIClient:
    """Client for Transaction API"""
    
    def __init__(self, base_url: str = "http://localhost:8000/api/transactions"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """Check database health"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get transaction statistics"""
        response = self.session.get(f"{self.base_url}/stats")
        response.raise_for_status()
        return response.json()
    
    def get_transactions(self, 
                        limit: int = 100, 
                        offset: int = 0,
                        min_amount: Optional[float] = None,
                        max_amount: Optional[float] = None,
                        fraud_only: bool = False,
                        tx_type: Optional[str] = None,
                        sender_account_id: Optional[int] = None,
                        receiver_account_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get transactions with optional filtering"""
        params = {
            "limit": limit,
            "offset": offset,
            "fraud_only": fraud_only
        }
        
        if min_amount is not None:
            params["min_amount"] = min_amount
        if max_amount is not None:
            params["max_amount"] = max_amount
        if tx_type:
            params["tx_type"] = tx_type
        if sender_account_id:
            params["sender_account_id"] = sender_account_id
        if receiver_account_id:
            params["receiver_account_id"] = receiver_account_id
        
        response = self.session.get(f"{self.base_url}/", params=params)
        response.raise_for_status()
        return response.json()
    
    def get_transaction_by_id(self, transaction_id: str) -> Dict[str, Any]:
        """Get a specific transaction by ID"""
        response = self.session.get(f"{self.base_url}/{transaction_id}")
        response.raise_for_status()
        return response.json()
    
    def get_fraud_transactions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get fraud transactions"""
        response = self.session.get(f"{self.base_url}/fraud/list", params={"limit": limit})
        response.raise_for_status()
        return response.json()
    
    def get_high_value_transactions(self, min_amount: float = 10000.0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get high-value transactions"""
        response = self.session.get(f"{self.base_url}/high-value/list", 
                                  params={"min_amount": min_amount, "limit": limit})
        response.raise_for_status()
        return response.json()
    
    def search_by_amount(self, min_amount: float, max_amount: float, limit: int = 100) -> List[Dict[str, Any]]:
        """Search transactions by amount range"""
        response = self.session.get(f"{self.base_url}/search/amount", 
                                  params={"min_amount": min_amount, "max_amount": max_amount, "limit": limit})
        response.raise_for_status()
        return response.json()
    
    def insert_transaction(self, 
                          transaction_id: int,
                          sender_account_id: int,
                          receiver_account_id: int,
                          tx_type: str,
                          amount: float,
                          timestamp: int,
                          is_fraud: bool = False,
                          alert_id: int = -1) -> Dict[str, Any]:
        """Insert a single transaction"""
        data = {
            "transaction_id": transaction_id,
            "sender_account_id": sender_account_id,
            "receiver_account_id": receiver_account_id,
            "tx_type": tx_type,
            "amount": amount,
            "timestamp": timestamp,
            "is_fraud": is_fraud,
            "alert_id": alert_id
        }
        
        response = self.session.post(f"{self.base_url}/", json=data)
        response.raise_for_status()
        return response.json()
    
    def insert_bulk_transactions(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Insert multiple transactions"""
        data = {"transactions": transactions}
        response = self.session.post(f"{self.base_url}/bulk", json=data)
        response.raise_for_status()
        return response.json()
    
    def delete_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """Delete a transaction"""
        response = self.session.delete(f"{self.base_url}/{transaction_id}")
        response.raise_for_status()
        return response.json()
    
    def export_csv(self, limit: int = 1000, fraud_only: bool = False, min_amount: Optional[float] = None) -> Dict[str, Any]:
        """Export transactions to CSV"""
        params = {"limit": limit, "fraud_only": fraud_only}
        if min_amount is not None:
            params["min_amount"] = min_amount
        
        response = self.session.get(f"{self.base_url}/export/csv", params=params)
        response.raise_for_status()
        return response.json()

def demo_api_client():
    """Demonstrate the API client usage"""
    print("🔧 Transaction API Client Demo")
    print("=" * 50)
    
    client = TransactionAPIClient()
    
    try:
        # Health check
        print("\n1. Health Check:")
        health = client.health_check()
        print(f"   Status: {health.get('status')}")
        print(f"   Total Transactions: {health.get('total_transactions', 0):,}")
        
        # Statistics
        print("\n2. Statistics:")
        stats = client.get_statistics()
        print(f"   Total: {stats.get('total_transactions', 0):,}")
        print(f"   Fraud: {stats.get('fraud_count', 0):,}")
        print(f"   Avg Amount: ${stats.get('avg_amount', 0):.2f}")
        
        # Get some transactions
        print("\n3. Sample Transactions:")
        transactions = client.get_transactions(limit=3)
        for txn in transactions:
            print(f"   {txn.get('transaction_id')}: ${txn.get('amount'):.2f}")
        
        # Get fraud transactions
        print("\n4. Fraud Transactions:")
        fraud_txns = client.get_fraud_transactions(limit=3)
        print(f"   Found {len(fraud_txns)} fraud transactions")
        
        # Get high-value transactions
        print("\n5. High-Value Transactions:")
        high_value = client.get_high_value_transactions(min_amount=50000, limit=3)
        print(f"   Found {len(high_value)} high-value transactions")
        
        # Search by amount range
        print("\n6. Amount Range Search:")
        range_results = client.search_by_amount(1000, 5000, limit=3)
        print(f"   Found {len(range_results)} transactions in range $1,000-$5,000")
        
        # Test insert (single)
        print("\n7. Insert Single Transaction:")
        timestamp = int(datetime.now().timestamp())
        insert_result = client.insert_transaction(
            transaction_id=timestamp,
            sender_account_id=99999,
            receiver_account_id=88888,
            tx_type="api_test",
            amount=1234.56,
            timestamp=timestamp,
            is_fraud=False
        )
        print(f"   Inserted: {insert_result.get('transaction_id')}")
        
        # Test bulk insert
        print("\n8. Bulk Insert:")
        bulk_transactions = []
        for i in range(3):
            bulk_transactions.append({
                "transaction_id": timestamp + 1000 + i,
                "sender_account_id": 90000 + i,
                "receiver_account_id": 80000 + i,
                "tx_type": "bulk_test",
                "amount": 1000.0 + i * 100,
                "timestamp": timestamp + 1000 + i,
                "is_fraud": i == 1,
                "alert_id": -1
            })
        
        bulk_result = client.insert_bulk_transactions(bulk_transactions)
        print(f"   Bulk inserted: {bulk_result.get('count')} transactions")
        
        # Test CSV export
        print("\n9. CSV Export:")
        csv_result = client.export_csv(limit=10)
        print(f"   Exported: {csv_result.get('count')} transactions")
        
        # Clean up test data
        print("\n10. Cleanup:")
        client.delete_transaction(str(timestamp))
        for i in range(3):
            client.delete_transaction(str(timestamp + 1000 + i))
        print("   Test data cleaned up")
        
        print("\n✅ API Client Demo Completed Successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure the FastAPI server is running on http://localhost:8000")

if __name__ == "__main__":
    demo_api_client()
