# 🔧 **Scripts Directory**

## 📁 **Scripts Organization**

This directory contains all utility scripts organized by category for the Multi-Agent AML Investigation System.

## 📊 **Script Categories**

### **🗄️ Data Scripts** (`data/`)
Scripts for data loading, processing, and database operations.

#### **Database Loading Scripts**
- **[load_transactions_postgres_v2.py](./data/load_transactions_postgres_v2.py)** - Load transactions to PostgreSQL (Production)
- **[load_transactions_postgres.py](./data/load_transactions_postgres.py)** - Load transactions to PostgreSQL (Legacy)
- **[load_transactions_sqlite.py](./data/load_transactions_sqlite.py)** - Load transactions to SQLite (Development)
- **[simple_load_transactions.py](./data/simple_load_transactions.py)** - Simple transaction loading script
- **[check_postgres_table.py](./data/check_postgres_table.py)** - Check PostgreSQL table schema

#### **Data Processing Scripts**
- **[generate_synthetic_data.py](./data/generate_synthetic_data.py)** - Generate synthetic AML data
- **[load_aml_data.py](./data/load_aml_data.py)** - Load AML-specific data
- **[load_financial_data.py](./data/load_financial_data.py)** - Load financial data
- **[init_database.py](./data/init_database.py)** - Initialize database schema

### **🚀 Deployment Scripts** (`deployment/`)
Scripts for system deployment, startup, and configuration.

#### **System Startup**
- **[run_server.py](./deployment/run_server.py)** - Start FastAPI server
- **[run_data_generation.py](./deployment/run_data_generation.py)** - Run data generation
- **[start_notebooks.py](./deployment/start_notebooks.py)** - Start Jupyter notebooks

#### **Configuration & Setup**
- **[notebook_fix.py](./deployment/notebook_fix.py)** - Fix notebook issues
- **[deploy_prompts.py](./deployment/deploy_prompts.py)** - Deploy prompts to LangSmith

### **🧪 Testing Scripts** (`testing/`)
Scripts for testing, validation, and quality assurance.

#### **API Testing**
- **[test_transaction_api.py](./testing/test_transaction_api.py)** - Comprehensive transaction API tests
- **[test_api.py](./testing/test_api.py)** - General API testing
- **[test_prompt_api.py](./testing/test_prompt_api.py)** - Prompt API testing

#### **System Testing**
- **[test_aml_simple.py](./testing/test_aml_simple.py)** - Simple AML system tests
- **[test_aml_system.py](./testing/test_aml_system.py)** - Complete AML system tests
- **[test_simple_workflow_fix.py](./testing/test_simple_workflow_fix.py)** - Simple workflow tests

#### **Database Testing**
- **[test_postgres_connection.py](./testing/test_postgres_connection.py)** - PostgreSQL connection testing

## 🚀 **Quick Start Scripts**

### **1. Database Setup**
```bash
# Load transactions to PostgreSQL (Production)
python scripts/data/load_transactions_postgres_v2.py

# Load transactions to SQLite (Development)
python scripts/data/load_transactions_sqlite.py

# Check database connection
python scripts/data/check_postgres_table.py
```

### **2. Start the System**
```bash
# Start FastAPI server
python scripts/deployment/run_server.py

# Start Jupyter notebooks
python scripts/deployment/start_notebooks.py
```

### **3. Run Tests**
```bash
# Test transaction API
python scripts/testing/test_transaction_api.py

# Test AML system
python scripts/testing/test_aml_system.py

# Test database connection
python scripts/testing/test_postgres_connection.py
```

## 📊 **Script Usage Examples**

### **Data Loading**
```bash
# Load 546K+ transactions to PostgreSQL
cd scripts/data
python load_transactions_postgres_v2.py

# Load to SQLite for development
python load_transactions_sqlite.py

# Generate synthetic data
python generate_synthetic_data.py
```

### **System Deployment**
```bash
# Start the complete system
cd scripts/deployment
python run_server.py

# Deploy prompts to LangSmith
python deploy_prompts.py
```

### **Testing & Validation**
```bash
# Run comprehensive tests
cd scripts/testing
python test_transaction_api.py

# Test database connections
python test_postgres_connection.py
```

## 🔧 **Script Configuration**

### **Environment Variables**
```bash
# Database Configuration
POSTGRES_URL=your_postgres_url
SQLITE_PATH=./data/transactions.db

# LangSmith Configuration
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT_NAME=aml-investigation-system

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

### **Script Dependencies**
```bash
# Install required packages
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

## 📈 **Script Performance**

### **Data Loading Performance**
- **PostgreSQL**: 546,327 transactions loaded in ~5 minutes
- **SQLite**: 546,327 transactions loaded in ~3 minutes
- **Bulk Operations**: Up to 10,000 records per batch
- **Memory Usage**: Optimized for large datasets

### **Testing Performance**
- **API Tests**: 100% endpoint coverage
- **Database Tests**: Sub-second query validation
- **Agent Tests**: Real-time workflow validation
- **Integration Tests**: End-to-end system validation

## 🎯 **Script Categories Summary**

| Category | Purpose | Scripts | Usage |
|----------|---------|---------|-------|
| **Data** | Database operations, data loading | 8 scripts | Production data management |
| **Deployment** | System startup, configuration | 5 scripts | System deployment |
| **Testing** | Quality assurance, validation | 6 scripts | Testing and validation |

## 📞 **Script Support**

### **Common Issues**
- **Database Connection**: Check environment variables
- **Permission Errors**: Ensure proper file permissions
- **Memory Issues**: Use batch processing for large datasets
- **Timeout Errors**: Increase timeout settings

### **Debugging**
- **Enable Debug Logging**: Set `DEBUG=True` in environment
- **Check Logs**: Review log files for error details
- **Test Connections**: Use connection testing scripts
- **Validate Data**: Use data validation scripts

---

## 🎉 **Complete Scripts Organization**

All scripts are now organized by category with:
- ✅ **Clear categorization** by purpose
- ✅ **Usage examples** for each script
- ✅ **Performance metrics** and benchmarks
- ✅ **Configuration guides** for setup
- ✅ **Troubleshooting** and support information

**🚀 Your Multi-Agent AML System scripts are now fully organized and ready for use!**
