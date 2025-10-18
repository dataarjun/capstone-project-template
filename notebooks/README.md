# Jupyter Notebooks for Multi-Agent AML Investigation System

This directory contains Jupyter notebooks for testing and development of the Multi-Agent AML Investigation System.

## 📚 Available Notebooks

### 1. Database Setup (`01_database_setup.ipynb`)
- **Purpose**: Database connection testing, table creation, and sample data insertion
- **What it covers**:
  - Database connection testing
  - Table creation and schema setup
  - Sample data insertion (customers, transactions, alerts)
  - Data verification and querying
  - Performance testing

### 2. Document Chunking (`02_document_chunking.ipynb`)
- **Purpose**: Document processing and vector database setup for RAG pipeline
- **What it covers**:
  - Sample KYC document creation
  - Text chunking strategies
  - Embedding generation
  - ChromaDB vector database setup
  - Document similarity search

### 3. Agent Testing (`03_agent_testing.ipynb`)
- **Purpose**: Individual agent testing and workflow simulation
- **What it covers**:
  - Individual agent testing
  - Agent tool functionality
  - Workflow simulation
  - Performance monitoring
  - Error handling and debugging

### 4. API Testing (`04_api_testing.ipynb`)
- **Purpose**: FastAPI endpoint testing and integration
- **What it covers**:
  - API endpoint testing
  - Request/response validation
  - Error handling
  - Performance testing
  - Integration testing

## 🚀 Getting Started

### Prerequisites
1. Ensure the main application dependencies are installed
2. Install notebook-specific dependencies:
   ```bash
   pip install -r notebooks/requirements.txt
   ```

### Running the Notebooks

1. **Start Jupyter Notebook**:
   ```bash
   cd /Users/indrajitsingh/Course_Materials/AgenticAI/Capstone2025
   jupyter notebook
   ```

2. **Or start JupyterLab**:
   ```bash
   jupyter lab
   ```

3. **Navigate to the notebooks directory** and open any notebook

### Notebook Execution Order

For best results, run the notebooks in this order:

1. **01_database_setup.ipynb** - Set up the database first
2. **02_document_chunking.ipynb** - Process documents and set up vector store
3. **03_agent_testing.ipynb** - Test individual agents
4. **04_api_testing.ipynb** - Test the API endpoints

## 🔧 Configuration

### Environment Setup
Make sure you have the following environment variables set:
```bash
# In your .env file
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///./data/aml_database.db
VECTOR_DB_PATH=./data/kyc_vectordb
OPENAI_API_KEY=your_openai_api_key
```

### Database Setup
The notebooks will automatically create the necessary database tables and sample data. Make sure the `data/` directory exists:
```bash
mkdir -p data/{raw,processed,kyc_documents,kyc_vectordb}
```

## 📊 Notebook Features

### Interactive Testing
- **Real-time feedback**: See results immediately as you run cells
- **Data visualization**: Charts and graphs for analysis
- **Error debugging**: Step-by-step error resolution
- **Performance metrics**: Timing and resource usage

### Sample Data
Each notebook includes comprehensive sample data:
- **Customers**: 3 sample customers with different risk levels
- **Transactions**: Various transaction types and amounts
- **KYC Documents**: Passport, address proof, source of wealth, business license
- **Alerts**: Sample AML alerts for testing

### Testing Scenarios
- **Happy path testing**: Normal operation scenarios
- **Edge cases**: Boundary conditions and error handling
- **Performance testing**: Load and stress testing
- **Integration testing**: End-to-end workflow testing

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**:
   - Make sure you're running from the project root directory
   - Check that all dependencies are installed
   - Verify the Python path includes the app directory

2. **Database Connection Issues**:
   - Ensure the database file path is correct
   - Check file permissions
   - Verify SQLite is working

3. **ChromaDB Issues**:
   - Check that the vector database path exists
   - Verify ChromaDB installation
   - Clear the vector database if corrupted

4. **API Connection Issues**:
   - Make sure the FastAPI server is running
   - Check the server URL and port
   - Verify network connectivity

### Debug Mode
Enable debug mode for more detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📈 Performance Tips

1. **Memory Management**:
   - Clear variables when not needed: `del variable_name`
   - Use `gc.collect()` to force garbage collection
   - Monitor memory usage with `%memit` magic command

2. **Database Optimization**:
   - Use batch operations for large data inserts
   - Create indexes for frequently queried columns
   - Use connection pooling for concurrent operations

3. **Vector Database Optimization**:
   - Batch document processing
   - Use appropriate chunk sizes
   - Monitor embedding dimensions

## 🔄 Continuous Integration

These notebooks can be integrated into CI/CD pipelines:

```bash
# Run all notebooks programmatically
jupyter nbconvert --to notebook --execute notebooks/*.ipynb
```

## 📝 Contributing

When adding new notebooks:

1. **Follow the naming convention**: `XX_description.ipynb`
2. **Include comprehensive documentation** in markdown cells
3. **Add error handling** and validation
4. **Test thoroughly** before committing
5. **Update this README** with new notebook descriptions

## 📚 Additional Resources

- [Jupyter Notebook Documentation](https://jupyter-notebook.readthedocs.io/)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [ChromaDB Documentation](https://docs.trychroma.com/)

---

**Happy Testing!** 🧪✨
