# Transaction API Documentation

## 🚀 **Complete FastAPI Transaction API**

This document provides comprehensive documentation for the Transaction API endpoints that allow querying, checking, and inserting records into the PostgreSQL database.

## 📋 **API Overview**

- **Base URL**: `http://localhost:8000/api/transactions`
- **Database**: PostgreSQL (Supabase)
- **Table**: `csv_transactions`
- **Authentication**: None (for development)
- **Content-Type**: `application/json`

## 🔧 **Available Endpoints**

### 1. **Health Check**
```http
GET /api/transactions/health
```
**Description**: Check database health and connection status.

**Response**:
```json
{
  "status": "healthy",
  "database": "postgresql",
  "table": "csv_transactions",
  "total_transactions": 546327,
  "timestamp": "2024-01-15T10:30:00"
}
```

### 2. **Get Statistics**
```http
GET /api/transactions/stats
```
**Description**: Get comprehensive transaction statistics.

**Response**:
```json
{
  "total_transactions": 546327,
  "unique_senders": 9999,
  "unique_receivers": 9854,
  "min_amount": 0.0,
  "max_amount": 1109807.87,
  "avg_amount": 1250.45,
  "fraud_count": 727,
  "earliest_transaction": "2024-01-01T00:00:00",
  "latest_transaction": "2024-01-15T23:59:59"
}
```

### 3. **Get Transactions**
```http
GET /api/transactions/
```
**Description**: Get transactions with optional filtering.

**Query Parameters**:
- `limit` (int, default=100): Number of transactions to retrieve (1-10000)
- `offset` (int, default=0): Number of transactions to skip
- `min_amount` (float, optional): Minimum transaction amount
- `max_amount` (float, optional): Maximum transaction amount
- `fraud_only` (bool, default=false): Only return fraud transactions
- `tx_type` (string, optional): Filter by transaction type
- `sender_account_id` (int, optional): Filter by sender account ID
- `receiver_account_id` (int, optional): Filter by receiver account ID

**Example**:
```http
GET /api/transactions/?limit=10&fraud_only=true&min_amount=1000
```

**Response**:
```json
[
  {
    "transaction_id": "12345",
    "sender_account_id": "1001",
    "receiver_account_id": "2001",
    "tx_type": "wire",
    "amount": 5000.0,
    "timestamp": 1705123456,
    "is_fraud": true,
    "alert_id": 1,
    "created_at": "2024-01-15T10:30:00"
  }
]
```

### 4. **Get Transaction by ID**
```http
GET /api/transactions/{transaction_id}
```
**Description**: Get a specific transaction by ID.

**Example**:
```http
GET /api/transactions/12345
```

### 5. **Get Fraud Transactions**
```http
GET /api/transactions/fraud/list
```
**Description**: Get transactions marked as fraud.

**Query Parameters**:
- `limit` (int, default=100): Number of fraud transactions to retrieve (1-1000)

### 6. **Get High-Value Transactions**
```http
GET /api/transactions/high-value/list
```
**Description**: Get high-value transactions.

**Query Parameters**:
- `min_amount` (float, default=10000.0): Minimum transaction amount
- `limit` (int, default=100): Number of transactions to retrieve (1-1000)

### 7. **Search by Amount Range**
```http
GET /api/transactions/search/amount
```
**Description**: Search transactions by amount range.

**Query Parameters**:
- `min_amount` (float, required): Minimum amount
- `max_amount` (float, required): Maximum amount
- `limit` (int, default=100): Number of results to return (1-1000)

### 8. **Insert Single Transaction**
```http
POST /api/transactions/
```
**Description**: Insert a single transaction.

**Request Body**:
```json
{
  "transaction_id": 12345,
  "sender_account_id": 1001,
  "receiver_account_id": 2001,
  "tx_type": "wire",
  "amount": 5000.0,
  "timestamp": 1705123456,
  "is_fraud": false,
  "alert_id": -1
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Transaction 12345 inserted successfully",
  "transaction_id": "12345",
  "timestamp": "2024-01-15T10:30:00"
}
```

### 9. **Bulk Insert Transactions**
```http
POST /api/transactions/bulk
```
**Description**: Insert multiple transactions in bulk (max 10,000 per request).

**Request Body**:
```json
{
  "transactions": [
    {
      "transaction_id": 12345,
      "sender_account_id": 1001,
      "receiver_account_id": 2001,
      "tx_type": "wire",
      "amount": 5000.0,
      "timestamp": 1705123456,
      "is_fraud": false,
      "alert_id": -1
    },
    {
      "transaction_id": 12346,
      "sender_account_id": 1002,
      "receiver_account_id": 2002,
      "tx_type": "ach",
      "amount": 2500.0,
      "timestamp": 1705123457,
      "is_fraud": true,
      "alert_id": 1
    }
  ]
}
```

**Response**:
```json
{
  "status": "success",
  "message": "2 transactions inserted successfully",
  "count": 2,
  "timestamp": "2024-01-15T10:30:00"
}
```

### 10. **Delete Transaction**
```http
DELETE /api/transactions/{transaction_id}
```
**Description**: Delete a specific transaction.

**Example**:
```http
DELETE /api/transactions/12345
```

**Response**:
```json
{
  "status": "success",
  "message": "Transaction 12345 deleted successfully",
  "transaction_id": "12345",
  "timestamp": "2024-01-15T10:30:00"
}
```

### 11. **Export to CSV**
```http
GET /api/transactions/export/csv
```
**Description**: Export transactions to CSV format.

**Query Parameters**:
- `limit` (int, default=1000): Number of transactions to export (1-10000)
- `fraud_only` (bool, default=false): Export only fraud transactions
- `min_amount` (float, optional): Minimum amount filter

**Response**:
```json
{
  "status": "success",
  "message": "Exported 1000 transactions",
  "count": 1000,
  "csv_data": "transaction_id,sender_account_id,receiver_account_id,...",
  "timestamp": "2024-01-15T10:30:00"
}
```

## 🧪 **Testing the API**

### 1. **Start the FastAPI Server**
```bash
cd /Users/indrajitsingh/Course_Materials/AgenticAI/Capstone2025
python -m uvicorn app.main:app --reload
```

### 2. **Interactive API Documentation**
Visit: `http://localhost:8000/docs`

### 3. **Run Test Scripts**

**Comprehensive Test Suite**:
```bash
python test_transaction_api.py
```

**API Client Demo**:
```bash
python transaction_api_client.py
```

## 📊 **Data Models**

### TransactionResponse
```python
{
  "transaction_id": "string",
  "sender_account_id": "string", 
  "receiver_account_id": "string",
  "tx_type": "string",
  "amount": "float",
  "timestamp": "integer",
  "is_fraud": "boolean",
  "alert_id": "integer",
  "created_at": "string"
}
```

### TransactionInsertRequest
```python
{
  "transaction_id": "integer",
  "sender_account_id": "integer",
  "receiver_account_id": "integer", 
  "tx_type": "string",
  "amount": "float",
  "timestamp": "integer",
  "is_fraud": "boolean (default: false)",
  "alert_id": "integer (default: -1)"
}
```

## 🔍 **Example Usage**

### Python Client Example
```python
import requests

# Get statistics
response = requests.get("http://localhost:8000/api/transactions/stats")
stats = response.json()
print(f"Total transactions: {stats['total_transactions']:,}")

# Get fraud transactions
response = requests.get("http://localhost:8000/api/transactions/fraud/list?limit=10")
fraud_txns = response.json()
print(f"Found {len(fraud_txns)} fraud transactions")

# Insert a transaction
new_txn = {
    "transaction_id": 99999,
    "sender_account_id": 1001,
    "receiver_account_id": 2001,
    "tx_type": "test",
    "amount": 1000.0,
    "timestamp": 1705123456,
    "is_fraud": False,
    "alert_id": -1
}
response = requests.post("http://localhost:8000/api/transactions/", json=new_txn)
result = response.json()
print(f"Inserted: {result['transaction_id']}")
```

### cURL Examples
```bash
# Health check
curl -X GET "http://localhost:8000/api/transactions/health"

# Get statistics
curl -X GET "http://localhost:8000/api/transactions/stats"

# Get fraud transactions
curl -X GET "http://localhost:8000/api/transactions/fraud/list?limit=5"

# Search by amount
curl -X GET "http://localhost:8000/api/transactions/search/amount?min_amount=1000&max_amount=5000&limit=10"
```

## 🚀 **Performance Features**

- **Indexed Queries**: All queries use database indexes for optimal performance
- **Batch Processing**: Bulk insert supports up to 10,000 transactions
- **Pagination**: Efficient offset/limit pagination for large datasets
- **Filtering**: Multiple filter options for precise data retrieval
- **Async Operations**: All database operations are asynchronous

## 🔒 **Security Considerations**

- **Input Validation**: All inputs are validated using Pydantic models
- **SQL Injection Protection**: Uses parameterized queries
- **Rate Limiting**: Consider implementing rate limiting for production
- **Authentication**: Add authentication for production use

## 📈 **Monitoring & Logging**

- **Health Checks**: Built-in database health monitoring
- **Error Handling**: Comprehensive error responses
- **Logging**: All operations are logged for debugging
- **Statistics**: Real-time database statistics

## 🎯 **Next Steps**

1. **Authentication**: Add JWT or API key authentication
2. **Rate Limiting**: Implement rate limiting for production
3. **Caching**: Add Redis caching for frequently accessed data
4. **Monitoring**: Add Prometheus metrics and Grafana dashboards
5. **Documentation**: Add OpenAPI/Swagger documentation
6. **Testing**: Add comprehensive unit and integration tests

---

**🎉 Your Transaction API is now fully functional with comprehensive CRUD operations, filtering, bulk operations, and export capabilities!**
