# 🔧 **Complete API Documentation**

## 🚀 **Multi-Agent AML System API Reference**

This document provides comprehensive documentation for all API endpoints in the Multi-Agent AML Investigation System.

## 📋 **Base URL**
```
http://localhost:8000/api
```

## 🔍 **Authentication**
Currently, the system runs without authentication for development. For production, implement JWT or API key authentication.

---

## 📊 **Transaction Management API**

### **Health & Statistics**

#### **Database Health Check**
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

#### **Transaction Statistics**
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

### **CRUD Operations**

#### **Get Transactions**
```http
GET /api/transactions/
```
**Description**: Get transactions with optional filtering.

**Query Parameters**:
- `limit` (int, default=100): Number of transactions (1-10000)
- `offset` (int, default=0): Number to skip
- `min_amount` (float, optional): Minimum amount filter
- `max_amount` (float, optional): Maximum amount filter
- `fraud_only` (bool, default=false): Only fraud transactions
- `tx_type` (string, optional): Transaction type filter
- `sender_account_id` (int, optional): Sender account filter
- `receiver_account_id` (int, optional): Receiver account filter

**Example**:
```bash
curl -X GET "http://localhost:8000/api/transactions/?limit=10&fraud_only=true"
```

#### **Get Transaction by ID**
```http
GET /api/transactions/{transaction_id}
```
**Description**: Get a specific transaction by ID.

**Example**:
```bash
curl -X GET "http://localhost:8000/api/transactions/12345"
```

#### **Insert Single Transaction**
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

#### **Bulk Insert Transactions**
```http
POST /api/transactions/bulk
```
**Description**: Insert multiple transactions (max 10,000 per request).

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
    }
  ]
}
```

#### **Delete Transaction**
```http
DELETE /api/transactions/{transaction_id}
```
**Description**: Delete a specific transaction.

### **Advanced Queries**

#### **Get Fraud Transactions**
```http
GET /api/transactions/fraud/list
```
**Query Parameters**:
- `limit` (int, default=100): Number of fraud transactions (1-1000)

#### **Get High-Value Transactions**
```http
GET /api/transactions/high-value/list
```
**Query Parameters**:
- `min_amount` (float, default=10000.0): Minimum amount
- `limit` (int, default=100): Number of transactions (1-1000)

#### **Search by Amount Range**
```http
GET /api/transactions/search/amount
```
**Query Parameters**:
- `min_amount` (float, required): Minimum amount
- `max_amount` (float, required): Maximum amount
- `limit` (int, default=100): Number of results (1-1000)

#### **Export to CSV**
```http
GET /api/transactions/export/csv
```
**Query Parameters**:
- `limit` (int, default=1000): Number of transactions (1-10000)
- `fraud_only` (bool, default=false): Export only fraud transactions
- `min_amount` (float, optional): Minimum amount filter

---

## 🤖 **Agent Management API**

### **List All Agents**
```http
GET /api/agents/
```
**Description**: Get list of all available agents.

**Response**:
```json
{
  "agents": [
    {
      "name": "coordinator",
      "description": "Workflow orchestration and decision routing",
      "status": "active",
      "capabilities": ["orchestration", "workflow_management"]
    },
    {
      "name": "risk_assessor",
      "description": "Risk classification and scoring",
      "status": "active",
      "capabilities": ["risk_analysis", "scoring"]
    }
  ]
}
```

### **Get Agent Details**
```http
GET /api/agents/{agent_name}
```
**Description**: Get detailed information about a specific agent.

**Path Parameters**:
- `agent_name` (string): Name of the agent (coordinator, risk_assessor, pattern_analyst, data_enrichment, report_synthesizer)

### **Invoke Agent**
```http
POST /api/agents/{agent_name}/invoke
```
**Description**: Invoke a specific agent with input data.

**Request Body**:
```json
{
  "input_data": {
    "transaction_id": "12345",
    "amount": 5000.0,
    "customer_id": "CUST001"
  },
  "context": {
    "investigation_id": "INV001",
    "priority": "high"
  }
}
```

### **Get Agent Status**
```http
GET /api/agents/{agent_name}/status
```
**Description**: Get current status and performance metrics of an agent.

---

## 🔍 **Investigation Workflows API**

### **Start Investigation**
```http
POST /api/investigations/start
```
**Description**: Start a new AML investigation.

**Request Body**:
```json
{
  "transaction_ids": ["12345", "12346"],
  "customer_id": "CUST001",
  "priority": "high",
  "investigation_type": "suspicious_activity"
}
```

**Response**:
```json
{
  "investigation_id": "INV001",
  "status": "started",
  "assigned_agents": ["risk_assessor", "pattern_analyst"],
  "estimated_completion": "2024-01-15T12:00:00"
}
```

### **Get Investigation Status**
```http
GET /api/investigations/{investigation_id}
```
**Description**: Get current status of an investigation.

### **Human Approval**
```http
POST /api/investigations/{investigation_id}/approve
```
**Description**: Submit human approval for investigation decisions.

**Request Body**:
```json
{
  "approval_status": "approved",
  "comments": "Investigation approved for SAR filing",
  "reviewer_id": "REV001"
}
```

### **Get Investigation Report**
```http
GET /api/investigations/{investigation_id}/report
```
**Description**: Get the final investigation report.

---

## 📝 **Prompt Management API (LangSmith Integration)**

### **List All Prompts**
```http
GET /api/prompts/
```
**Description**: Get list of all available prompts.

**Response**:
```json
{
  "prompts": [
    {
      "agent_name": "risk_assessor",
      "version": "1.0.0",
      "description": "Risk assessment prompt for AML transaction analysis",
      "category": "compliance",
      "last_updated": "2024-01-15T10:30:00"
    }
  ]
}
```

### **Get Agent Prompts**
```http
GET /api/prompts/{agent_name}
```
**Description**: Get prompts for a specific agent.

**Path Parameters**:
- `agent_name` (string): Name of the agent

**Response**:
```json
{
  "agent_name": "risk_assessor",
  "current_version": "1.0.0",
  "prompts": [
    {
      "version": "1.0.0",
      "description": "Risk assessment prompt",
      "template": "You are a compliance risk analyst...",
      "variables": ["txn_json", "rule_summary"],
      "last_updated": "2024-01-15T10:30:00"
    }
  ]
}
```

### **Deploy Prompt to LangSmith**
```http
POST /api/prompts/deploy
```
**Description**: Deploy a prompt to LangSmith for version control and A/B testing.

**Request Body**:
```json
{
  "agent_name": "risk_assessor",
  "description": "Updated risk assessment prompt",
  "tags": ["production", "v1.1"],
  "force_update": false
}
```

**Response**:
```json
{
  "status": "success",
  "prompt_id": "prompt_12345",
  "version": "1.1.0",
  "langsmith_url": "https://smith.langchain.com/prompts/prompt_12345"
}
```

### **Update Agent Prompt**
```http
PUT /api/prompts/{agent_name}
```
**Description**: Update the prompt for a specific agent.

**Request Body**:
```json
{
  "prompt_template": "Updated prompt template...",
  "variables": [
    {
      "name": "txn_json",
      "description": "Transaction data",
      "type": "string",
      "required": true
    }
  ],
  "expected_output": {
    "type": "json",
    "schema": {
      "risk_level": "string",
      "score": "number",
      "reason": "string"
    }
  }
}
```

### **Get Prompt Versions**
```http
GET /api/prompts/{agent_name}/versions
```
**Description**: Get all versions of prompts for an agent.

**Response**:
```json
{
  "agent_name": "risk_assessor",
  "versions": [
    {
      "version": "1.1.0",
      "status": "active",
      "created_at": "2024-01-15T10:30:00",
      "performance_score": 0.85
    },
    {
      "version": "1.0.0",
      "status": "archived",
      "created_at": "2024-01-10T10:30:00",
      "performance_score": 0.78
    }
  ]
}
```

### **Compare Prompt Versions**
```http
POST /api/prompts/compare
```
**Description**: Compare performance of different prompt versions.

**Request Body**:
```json
{
  "agent_name": "risk_assessor",
  "version_a": "1.0.0",
  "version_b": "1.1.0",
  "test_period": "7d"
}
```

**Response**:
```json
{
  "comparison": {
    "version_a": {
      "version": "1.0.0",
      "accuracy": 0.78,
      "response_time": 1.2,
      "usage_count": 150
    },
    "version_b": {
      "version": "1.1.0",
      "accuracy": 0.85,
      "response_time": 1.1,
      "usage_count": 200
    },
    "improvement": {
      "accuracy": "+9.0%",
      "response_time": "-8.3%",
      "usage": "+33.3%"
    }
  }
}
```

### **Get Performance Metrics**
```http
GET /api/prompts/{agent_name}/performance
```
**Description**: Get performance metrics for an agent's prompts.

**Query Parameters**:
- `period` (string, optional): Time period (1d, 7d, 30d, 90d)
- `metric` (string, optional): Specific metric (accuracy, response_time, usage)

**Response**:
```json
{
  "agent_name": "risk_assessor",
  "period": "7d",
  "metrics": {
    "accuracy": 0.85,
    "response_time": 1.1,
    "usage_count": 200,
    "error_rate": 0.02,
    "user_satisfaction": 4.2
  },
  "trends": {
    "accuracy": "+5%",
    "response_time": "-10%",
    "usage": "+25%"
  }
}
```

---

## 🔧 **RAG (Retrieval-Augmented Generation) API**

### **Document Search**
```http
GET /api/rag/search
```
**Description**: Search documents using semantic similarity.

**Query Parameters**:
- `query` (string, required): Search query
- `limit` (int, default=10): Number of results
- `threshold` (float, default=0.7): Similarity threshold

### **Document Upload**
```http
POST /api/rag/upload
```
**Description**: Upload and process documents for RAG.

**Request Body** (multipart/form-data):
- `file`: Document file
- `metadata`: JSON metadata

### **Get Document**
```http
GET /api/rag/documents/{document_id}
```
**Description**: Get a specific document by ID.

---

## 📊 **Monitoring API**

### **System Health**
```http
GET /api/monitoring/health
```
**Description**: Get overall system health status.

### **Performance Metrics**
```http
GET /api/monitoring/metrics
```
**Description**: Get system performance metrics.

### **Agent Performance**
```http
GET /api/monitoring/agents
```
**Description**: Get performance metrics for all agents.

---

## 🧪 **Testing Examples**

### **Python Client Example**
```python
import requests

# Get transaction statistics
response = requests.get("http://localhost:8000/api/transactions/stats")
stats = response.json()
print(f"Total transactions: {stats['total_transactions']:,}")

# Get fraud transactions
response = requests.get("http://localhost:8000/api/transactions/fraud/list?limit=10")
fraud_txns = response.json()
print(f"Found {len(fraud_txns)} fraud transactions")

# Invoke risk assessor agent
response = requests.post("http://localhost:8000/api/agents/risk_assessor/invoke", 
                        json={
                            "input_data": {
                                "transaction_id": "12345",
                                "amount": 5000.0,
                                "customer_id": "CUST001"
                            }
                        })
result = response.json()
print(f"Risk assessment: {result['risk_level']}")
```

### **cURL Examples**
```bash
# Health check
curl -X GET "http://localhost:8000/api/transactions/health"

# Get statistics
curl -X GET "http://localhost:8000/api/transactions/stats"

# Search fraud transactions
curl -X GET "http://localhost:8000/api/transactions/fraud/list?limit=5"

# Deploy prompt to LangSmith
curl -X POST "http://localhost:8000/api/prompts/deploy" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "risk_assessor",
    "description": "Updated risk assessment prompt",
    "tags": ["production", "v1.1"]
  }'
```

---

## 📈 **Error Handling**

### **Standard Error Response**
```json
{
  "error": "Validation Error",
  "message": "Invalid transaction ID format",
  "status_code": 400,
  "timestamp": "2024-01-15T10:30:00"
}
```

### **Common HTTP Status Codes**
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `404`: Not Found
- `422`: Validation Error
- `500`: Internal Server Error

---

## 🔒 **Security Considerations**

### **Input Validation**
- All inputs are validated using Pydantic models
- SQL injection protection with parameterized queries
- XSS protection with input sanitization

### **Rate Limiting**
- Consider implementing rate limiting for production
- API key authentication for external access
- CORS configuration for web applications

---

## 📞 **Support & Documentation**

- **Interactive API Documentation**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

**🎉 Complete API documentation for your Multi-Agent AML Investigation System!**
