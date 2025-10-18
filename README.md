# Multi-Agent AML Investigation System

A sophisticated Anti-Money Laundering (AML) investigation system built with multi-agent AI architecture, featuring LangGraph workflows, FastAPI backend, and comprehensive chat capabilities.

## 🚀 Features

- **Multi-Agent Architecture**: Specialized AI agents for risk assessment, pattern analysis, and investigation coordination
- **LangGraph Workflows**: Complex AML investigation workflows with state management
- **FastAPI Backend**: RESTful API with comprehensive chat functionality
- **Real-time Chat**: Interactive chat system for AML case investigation
- **Risk Assessment**: Automated risk scoring and analysis
- **Document Analysis**: KYC document processing and analysis
- **Investigation Management**: Thread-based investigation tracking

## 🏗️ Architecture

```
├── app/
│   ├── agents/           # AI agents and workflows
│   ├── api/             # FastAPI routes and endpoints
│   ├── core/            # Core configuration and utilities
│   ├── db/              # Database models and connections
│   ├── models/          # Pydantic models
│   ├── services/        # Business logic services
│   └── utils/           # Utility functions
├── notebooks/           # Jupyter notebooks for testing
├── prompts/             # Prompt templates
├── scripts/             # Setup and utility scripts
└── tests/               # Test suites
```

## 🛠️ Installation

### Prerequisites

- Python 3.10+
- PostgreSQL (or use Docker)
- OpenAI API key

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd multi-agent-aml-system
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment configuration**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Database setup**
   ```bash
   python scripts/init_database.py
   ```

## 🚀 Quick Start

### Start the Server

```bash
python run_server.py
```

The API will be available at `http://localhost:8002`

### API Documentation

Visit `http://localhost:8002/docs` for interactive API documentation.

### Chat API Usage

```python
import requests

# Send a chat message
response = requests.post("http://localhost:8002/api/chat/message", json={
    "prompt": "What is the risk distribution across investigations?",
    "thread_id": None  # Auto-creates thread
})

print(response.json())
```

## 📊 API Endpoints

### Chat Endpoints
- `POST /api/chat/message` - Send chat message
- `POST /api/chat/threads` - Create new thread
- `GET /api/chat/threads` - List all threads
- `GET /api/chat/threads/{thread_id}` - Get thread history
- `GET /api/chat/statistics` - Get global statistics

### Investigation Endpoints
- `POST /api/investigate` - Start new investigation
- `GET /api/investigations` - List investigations
- `GET /api/investigations/{investigation_id}` - Get investigation details

## 🧪 Testing

### Run Tests
```bash
python -m pytest tests/
```

### Interactive Testing
```bash
# Start Jupyter notebooks
jupyter notebook notebooks/

# Run API tests
python test_api.py
```

## 🔧 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/aml_db

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# LangSmith (optional)
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_PROJECT=aml-multi-agent-system

# Server
HOST=0.0.0.0
PORT=8002
```

### Agent Configuration

The system uses specialized agents for different AML tasks:

- **Risk Assessor**: Evaluates transaction risk levels
- **Pattern Analyst**: Identifies suspicious patterns
- **Data Enrichment**: Gathers additional context
- **Report Synthesizer**: Generates investigation reports
- **Coordinator**: Manages workflow orchestration

## 📈 Usage Examples

### 1. Basic Chat Interaction

```python
# Create a new conversation
response = requests.post("http://localhost:8002/api/chat/message", json={
    "prompt": "Analyze the risk factors in case #12345",
    "thread_id": None
})

thread_id = response.json()["thread_id"]

# Continue the conversation
response = requests.post("http://localhost:8002/api/chat/message", json={
    "prompt": "What are the key findings?",
    "thread_id": thread_id
})
```

### 2. Investigation Workflow

```python
# Start new investigation
response = requests.post("http://localhost:8002/api/investigate", json={
    "transaction_id": "TXN-12345",
    "user_query": "Investigate this high-value transaction"
})

investigation_id = response.json()["investigation_id"]
```

### 3. Get Statistics

```python
# Get global statistics
response = requests.get("http://localhost:8002/api/chat/statistics")
stats = response.json()

print(f"Total investigations: {stats['total_investigations']}")
print(f"High risk cases: {stats['high_risk_cases']}")
```

## 🐳 Docker Support

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build individual container
docker build -t aml-system .
docker run -p 8002:8002 aml-system
```

## 📚 Documentation

- [API Documentation](http://localhost:8002/docs) - Interactive API docs
- [Notebooks](notebooks/) - Jupyter notebooks for testing and examples
- [Prompts](prompts/) - AI prompt templates
- [Architecture Guide](docs/) - Detailed system architecture

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the [documentation](docs/)
- Review the [notebooks](notebooks/) for examples

## 🔮 Roadmap

- [ ] Enhanced pattern recognition
- [ ] Real-time monitoring dashboard
- [ ] Advanced reporting features
- [ ] Integration with external AML systems
- [ ] Machine learning model improvements

---

**Note**: This system is designed for educational and research purposes. For production use, ensure proper security measures and compliance with relevant regulations.