# Jupyter Notebooks Summary

## 📚 Created Notebooks

### 1. Database Setup (`01_database_setup.ipynb`)
**Purpose**: Database connection testing, table creation, and sample data insertion

**Features**:
- Database connection testing
- Table creation and schema setup
- Sample data insertion (customers, transactions, alerts)
- Data verification and querying
- Performance testing
- Complex query examples

**Sample Data Included**:
- 3 customers with different risk levels
- Multiple transaction types
- Sample alerts and investigations

### 2. Document Chunking (`02_document_chunking.ipynb`)
**Purpose**: Document processing and vector database setup for RAG pipeline

**Features**:
- Sample KYC document creation
- Text chunking strategies
- Embedding generation
- ChromaDB vector database setup
- Document similarity search
- RAG pipeline testing

**Sample Documents**:
- Passport information
- Address verification
- Source of wealth declarations
- Business licenses

### 3. Agent Testing (`03_agent_testing.ipynb`)
**Purpose**: Individual agent testing and workflow simulation

**Features**:
- Individual agent testing
- Agent tool functionality
- Workflow simulation
- Performance monitoring
- Error handling and debugging
- Multi-agent orchestration testing

**Agents Tested**:
- Coordinator Agent
- Data Enrichment Agent
- Pattern Analyst Agent
- Risk Assessor Agent
- Report Synthesizer Agent

### 4. API Testing (`04_api_testing.ipynb`)
**Purpose**: FastAPI endpoint testing and integration

**Features**:
- API endpoint testing
- Request/response validation
- Error handling
- Performance testing
- Integration testing
- Load testing scenarios

**Endpoints Tested**:
- Health endpoints
- Agent management
- Investigation workflows
- RAG operations
- Monitoring and metrics

## 🚀 Getting Started

### Quick Start
```bash
# Start Jupyter Notebooks
python start_notebooks.py

# Or manually
cd notebooks
jupyter notebook
```

### Prerequisites
- All main application dependencies installed
- Virtual environment activated
- Database and vector store paths configured

### Execution Order
1. **Database Setup** - Set up database first
2. **Document Chunking** - Process documents and vector store
3. **Agent Testing** - Test individual agents
4. **API Testing** - Test API endpoints

## 🔧 Features

### Interactive Development
- **Real-time feedback**: See results immediately
- **Data visualization**: Charts and graphs for analysis
- **Error debugging**: Step-by-step error resolution
- **Performance metrics**: Timing and resource usage

### Comprehensive Testing
- **Happy path testing**: Normal operation scenarios
- **Edge cases**: Boundary conditions and error handling
- **Performance testing**: Load and stress testing
- **Integration testing**: End-to-end workflow testing

### Sample Data
- **Customers**: 3 sample customers with different risk levels
- **Transactions**: Various transaction types and amounts
- **KYC Documents**: Passport, address proof, source of wealth, business license
- **Alerts**: Sample AML alerts for testing

## 📊 Notebook Capabilities

### Database Operations
- Connection testing and validation
- Table creation and schema management
- Sample data insertion and verification
- Complex query execution
- Performance benchmarking

### Document Processing
- Text chunking and preprocessing
- Embedding generation
- Vector database operations
- Similarity search and retrieval
- RAG pipeline testing

### Agent Testing
- Individual agent functionality
- Tool integration testing
- Workflow simulation
- Performance monitoring
- Error handling and recovery

### API Testing
- Endpoint validation
- Request/response testing
- Error scenario testing
- Performance benchmarking
- Integration testing

## 🐛 Troubleshooting

### Common Issues
1. **Import Errors**: Ensure app directory is in Python path
2. **Database Issues**: Check file permissions and paths
3. **ChromaDB Issues**: Verify vector database setup
4. **API Issues**: Ensure FastAPI server is running

### Debug Tips
- Use debug mode for detailed logging
- Check environment variables
- Verify file paths and permissions
- Monitor resource usage

## 📈 Performance Tips

### Memory Management
- Clear variables when not needed
- Use garbage collection
- Monitor memory usage

### Database Optimization
- Use batch operations
- Create appropriate indexes
- Use connection pooling

### Vector Database Optimization
- Batch document processing
- Use appropriate chunk sizes
- Monitor embedding dimensions

## 🔄 Integration

### CI/CD Integration
```bash
# Run notebooks programmatically
jupyter nbconvert --to notebook --execute notebooks/*.ipynb
```

### Development Workflow
1. Use notebooks for development and testing
2. Convert successful code to production modules
3. Maintain notebook documentation
4. Update notebooks as system evolves

## 📝 Best Practices

### Notebook Development
1. **Follow naming convention**: `XX_description.ipynb`
2. **Include comprehensive documentation** in markdown cells
3. **Add error handling** and validation
4. **Test thoroughly** before committing
5. **Update documentation** with changes

### Code Organization
1. **Keep cells focused** on single tasks
2. **Use clear variable names**
3. **Add comments** for complex logic
4. **Test edge cases** and error conditions
5. **Document assumptions** and limitations

## 🎯 Use Cases

### Development
- **Feature development**: Test new features in isolation
- **Debugging**: Step-by-step problem resolution
- **Performance analysis**: Identify bottlenecks and optimizations
- **Integration testing**: Verify component interactions

### Testing
- **Unit testing**: Individual component validation
- **Integration testing**: End-to-end workflow validation
- **Performance testing**: Load and stress testing
- **Regression testing**: Ensure changes don't break existing functionality

### Documentation
- **Tutorial creation**: Step-by-step guides
- **Example demonstrations**: Show system capabilities
- **Best practices**: Document recommended approaches
- **Troubleshooting guides**: Common issues and solutions

---

**Ready for Development!** 🚀✨

The notebooks provide a comprehensive testing and development environment for the Multi-Agent AML Investigation System, enabling interactive development, thorough testing, and detailed analysis of all system components.
