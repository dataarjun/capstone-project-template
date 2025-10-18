# Poetry Setup Guide

This guide will help you set up the Multi-Agent AML Investigation System using Poetry for dependency management.

## 🚀 Quick Setup

### Step 1: Install Poetry

If you don't have Poetry installed:

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to your PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.local/bin:$PATH"

# Verify installation
poetry --version
```

### Step 2: Clone and Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd Capstone2025

# Run the automatic setup script
python setup.py
```

### Step 3: Manual Setup (Alternative)

If you prefer manual setup:

```bash
# Install dependencies
poetry install

# Set up environment variables
cp env.example .env
# Edit .env with your API keys

# Create data directories
mkdir -p data/{raw,processed,kyc_documents,kyc_vectordb}

# Initialize database
poetry run python -m app.db.init_db
```

## 🏃‍♂️ Running the Application

### Development Mode

```bash
# Using Poetry directly
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Using Makefile
make run

# Using Poetry scripts
poetry run start
```

### Production Mode

```bash
# Using Poetry
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Using Makefile
make run-prod
```

## 🧪 Development Commands

### Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app --cov-report=html

# Using Makefile
make test
make test-cov
```

### Code Quality

```bash
# Format code
poetry run black app tests
poetry run isort app tests

# Run linting
poetry run flake8 app tests
poetry run mypy app

# Using Makefile
make format
make lint
```

### Database Operations

```bash
# Initialize database
poetry run python -m app.db.init_db

# Using Makefile
make init-db
```

## 🔧 Environment Configuration

### Required Environment Variables

Create a `.env` file with the following variables:

```bash
# OpenAI Configuration (Required)
OPENAI_API_KEY=your_openai_api_key_here

# LangSmith Configuration (Optional)
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=aml-investigation
LANGSMITH_TRACING=true

# Memory Configuration (Optional)
MEM0_API_KEY=your_mem0_api_key_here
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_key_here

# Database Configuration
DATABASE_URL=sqlite:///./data/aml_database.db

# Vector Database Configuration
VECTOR_DB_PATH=./data/kyc_vectordb

# Application Configuration
DEBUG=false
LOG_LEVEL=INFO
SECRET_KEY=your_secret_key_here
```

### Getting API Keys

1. **OpenAI API Key:**
   - Go to https://platform.openai.com/api-keys
   - Create a new API key
   - Add it to your `.env` file

2. **LangSmith API Key (Optional):**
   - Go to https://smith.langchain.com/
   - Sign up and get your API key
   - Add it to your `.env` file

## 📁 Project Structure

```
Capstone2025/
├── app/                    # FastAPI application
├── data/                   # Data storage
├── tests/                  # Test suite
├── pyproject.toml         # Poetry configuration
├── Makefile               # Development commands
├── setup.py               # Setup script
└── README.md              # Main documentation
```

## 🐳 Docker Alternative

If you prefer Docker over Poetry:

```bash
# Start with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

## 🚨 Troubleshooting

### Common Issues

1. **Poetry not found:**
   ```bash
   # Add Poetry to PATH
   export PATH="$HOME/.local/bin:$PATH"
   # Add to ~/.bashrc or ~/.zshrc for persistence
   ```

2. **Python version issues:**
   ```bash
   # Ensure Python 3.11+ is installed
   python --version
   
   # Use Poetry to manage Python version
   poetry env use python3.11
   ```

3. **Database initialization fails:**
   ```bash
   # Create data directory first
   mkdir -p data
   
   # Then initialize database
   poetry run python -m app.db.init_db
   ```

4. **Port already in use:**
   ```bash
   # Kill process using port 8000
   lsof -ti:8000 | xargs kill -9
   
   # Or use a different port
   poetry run uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
   ```

### Getting Help

- Check the main README.md for detailed documentation
- View API documentation at http://localhost:8000/docs
- Check logs for error messages
- Ensure all environment variables are set correctly

## 🎯 Next Steps

1. **Start the application:**
   ```bash
   make run
   ```

2. **Access the API:**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/api/health

3. **Test the system:**
   ```bash
   # Start an investigation
   curl -X POST "http://localhost:8000/api/investigations/start" \
     -H "Content-Type: application/json" \
     -d '{
       "alert_id": "ALT001",
       "transaction_id": "T12345",
       "priority": "high"
     }'
   ```

4. **Explore the API:**
   - Visit http://localhost:8000/docs for interactive API documentation
   - Try the different endpoints
   - Check the monitoring endpoints for system metrics

## 📚 Additional Resources

- [Poetry Documentation](https://python-poetry.org/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [ChromaDB Documentation](https://docs.trychroma.com/)

---

**Happy coding! 🚀**
