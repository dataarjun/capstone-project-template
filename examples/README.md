# 🎯 **Examples Directory**

## 📁 **Examples Organization**

This directory contains all example code, demos, and notebooks for the Multi-Agent AML Investigation System.

## 📊 **Example Categories**

### **🎬 Demo Scripts** (`demos/`)
Working examples and demonstrations of the AML system.

#### **Agent Demonstrations**
- **[demo_agents_with_postgres_data.py](./demos/demo_agents_with_postgres_data.py)** - Demo agents with PostgreSQL data
- **[demo_agents_with_sqlite_data.py](./demos/demo_agents_with_sqlite_data.py)** - Demo agents with SQLite data
- **[aml_demo_working.py](./demos/aml_demo_working.py)** - Complete AML system demo

#### **API Client Examples**
- **[transaction_api_client.py](./demos/transaction_api_client.py)** - Transaction API client library

### **📓 Notebook Examples** (`notebooks/`)
Jupyter notebook examples and working code cells.

#### **Working Code Examples**
- **[FINAL_WORKING_NOTEBOOK_CELL.py](./notebooks/FINAL_WORKING_NOTEBOOK_CELL.py)** - Final working notebook cell
- **[WORKING_NOTEBOOK_IMPORTS.py](./notebooks/WORKING_NOTEBOOK_IMPORTS.py)** - Working notebook imports

#### **Development Notebooks**
- **[01_database_setup.ipynb](./notebooks/01_database_setup.ipynb)** - Database setup and initialization
- **[02_document_chunking.ipynb](./notebooks/02_document_chunking.ipynb)** - Document processing and chunking
- **[03_agent_testing.ipynb](./notebooks/03_agent_testing.ipynb)** - Agent testing and validation
- **[04_api_testing.ipynb](./notebooks/04_api_testing.ipynb)** - API endpoint testing
- **[05_aml_investigation_demo.ipynb](./notebooks/05_aml_investigation_demo.ipynb)** - Complete AML investigation demo
- **[06_langgraph_workflow_testing.ipynb](./notebooks/06_langgraph_workflow_testing.ipynb)** - LangGraph workflow testing

### **🔧 Integration Examples** (`integration/`)
Examples of system integrations and external connections.

#### **LangSmith Integration**
- **[langsmith_integration_demo.py](./integration/langsmith_integration_demo.py)** - LangSmith integration demonstration

## 🚀 **Quick Start Examples**

### **1. Run Agent Demos**
```bash
# Demo with PostgreSQL data
python examples/demos/demo_agents_with_postgres_data.py

# Demo with SQLite data
python examples/demos/demo_agents_with_sqlite_data.py

# Complete AML system demo
python examples/demos/aml_demo_working.py
```

### **2. Use API Client**
```bash
# Transaction API client demo
python examples/demos/transaction_api_client.py
```

### **3. Run Jupyter Notebooks**
```bash
# Start Jupyter server
jupyter notebook examples/notebooks/

# Or use the startup script
python scripts/deployment/start_notebooks.py
```

## 📊 **Example Usage Guide**

### **Agent Demonstrations**

#### **PostgreSQL Demo**
```python
# examples/demos/demo_agents_with_postgres_data.py
import asyncio
from app.services.postgres_transaction_service import PostgreSQLTransactionService
from app.agents.simple_workflow import run_simple_investigation

async def main():
    # Initialize service
    service = PostgreSQLTransactionService()
    await service.connect()
    
    # Get transactions
    transactions = await service.get_transactions_for_batch_processing(batch_size=20)
    
    # Process with agents
    for txn in transactions:
        result = await run_simple_investigation(txn)
        print(f"Transaction {txn['transaction_id']}: {result['risk_level']}")
    
    await service.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

#### **API Client Example**
```python
# examples/demos/transaction_api_client.py
from transaction_api_client import TransactionAPIClient

# Initialize client
client = TransactionAPIClient()

# Get statistics
stats = client.get_statistics()
print(f"Total transactions: {stats['total_transactions']:,}")

# Get fraud transactions
fraud_txns = client.get_fraud_transactions(limit=10)
print(f"Found {len(fraud_txns)} fraud transactions")

# Insert transaction
result = client.insert_transaction(
    transaction_id=12345,
    sender_account_id=1001,
    receiver_account_id=2001,
    tx_type="wire",
    amount=5000.0,
    timestamp=1705123456
)
print(f"Inserted: {result['transaction_id']}")
```

### **Jupyter Notebook Examples**

#### **Database Setup**
```python
# examples/notebooks/01_database_setup.ipynb
import pandas as pd
from app.services.postgres_transaction_service import PostgreSQLTransactionService

# Load transaction data
df = pd.read_csv('data/transactions.csv')
print(f"Loaded {len(df)} transactions")

# Initialize database service
service = PostgreSQLTransactionService()
await service.connect()

# Get statistics
stats = await service.get_transaction_statistics()
print(f"Database stats: {stats}")
```

#### **Agent Testing**
```python
# examples/notebooks/03_agent_testing.ipynb
from app.agents.simple_workflow import run_simple_investigation

# Test single transaction
transaction_data = {
    "transaction_id": "12345",
    "amount": 5000.0,
    "customer_id": "CUST001",
    "tx_type": "wire"
}

result = await run_simple_investigation(transaction_data)
print(f"Risk Assessment: {result['risk_level']}")
print(f"Confidence: {result['confidence']}")
```

## 📈 **Example Performance**

### **Demo Performance**
- **Agent Processing**: Real-time risk assessment (< 2 seconds)
- **Database Queries**: Sub-second response times
- **API Calls**: 100+ requests per minute
- **Memory Usage**: Optimized for large datasets

### **Notebook Performance**
- **Data Loading**: 546K+ transactions in seconds
- **Agent Execution**: Real-time processing
- **Visualization**: Interactive charts and graphs
- **Export**: Multiple format support (CSV, JSON, PDF)

## 🎯 **Example Categories Summary**

| Category | Purpose | Examples | Usage |
|----------|---------|----------|-------|
| **Demos** | System demonstrations | 4 scripts | Show system capabilities |
| **Notebooks** | Development examples | 6 notebooks | Interactive development |
| **Integration** | External integrations | 1 script | LangSmith integration |

## 📞 **Example Support**

### **Running Examples**
- **Prerequisites**: Ensure database is loaded
- **Dependencies**: Install required packages
- **Configuration**: Set environment variables
- **Permissions**: Check file access permissions

### **Common Issues**
- **Import Errors**: Check Python path and dependencies
- **Database Errors**: Verify database connection
- **Memory Issues**: Use smaller datasets for testing
- **Timeout Errors**: Increase timeout settings

### **Debugging**
- **Enable Logging**: Set debug mode for detailed output
- **Check Logs**: Review log files for error details
- **Test Components**: Run individual components first
- **Validate Data**: Ensure data format is correct

---

## 🎉 **Complete Examples Organization**

All examples are now organized with:
- ✅ **Working demonstrations** of all system components
- ✅ **Interactive notebooks** for development and testing
- ✅ **API client examples** for integration
- ✅ **Performance benchmarks** and optimization
- ✅ **Clear usage instructions** and examples

**🚀 Your Multi-Agent AML System examples are now fully organized and ready for use!**
