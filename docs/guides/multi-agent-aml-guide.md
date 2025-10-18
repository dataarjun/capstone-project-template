# Multi-Agent AML Investigation System - Full Stack Capstone Project | Capstone2025-Oct

## 1. Overview

This capstone project extends the multi-agent financial crime detection system into a full-stack production application. The system uses 5 specialized AI agents orchestrated through LangGraph to investigate suspicious transactions, reducing false positives by 45% and transforming hours-long investigations into minutes.

**Tech Stack:**

- **Backend:** FastAPI with async endpoints
- **Agents:** LangGraph + LangChain with OpenAI GPT-4
- **Frontend:** React with modern UI components
- **Databases:** SQLite/PostgreSQL + ChromaDB for vectors
- Longeterm Memory: PostgreSQL 
- Shorterm Memory: Mem0
- **Monitoring:** LangSmith for agent traces and token tracking
- **Deployment:** Docker + optional AWS ECS

## 2. System Architecture

### Architecture Layers

```
┌─────────────────────────────────────────────────────┐
│                 React Frontend                      │
│         (Investigation Dashboard + Reports)         │
└─────────────────┬───────────────────────────────────┘
                  │ REST API
┌─────────────────┴───────────────────────────────────┐
│              FastAPI Backend Layer                  │
│  ┌──────────────────────────────────────────────┐   │
│  │     API Routes (Agent, RAG, Monitoring)      │   │
│  └──────────────┬───────────────────────────────┘   │
│  ┌──────────────┴───────────────────────────────┐   │
│  │      LangGraph Multi-Agent Orchestrator      │   │
│  │  ┌────────┐  ┌────────┐  ┌────────┐          │   │
│  │  │Coord.  │  │Data    │  │Pattern │  ...     │   │
│  │  │Agent   │→ │Enrich. │→ │Analyst │          │   │
│  │  └────────┘  └────────┘  └────────┘          │   │
│  └──────────────┬───────────────────────────────┘   │
└─────────────────┼───────────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────────────┐
│         Data Layer & External Services              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │SQLite/   │  │ChromaDB  │  │LangSmith │           │
│  │Postgres  │  │Vector DB │  │Monitoring│           │
│  └──────────┘  └──────────┘  └──────────┘           │
└─────────────────────────────────────────────────────┘
```

### Key Integrations

- **LLM:** OpenAI GPT-4 for agent reasoning
- **Vector DB:** ChromaDB or pgvector for KYC document embeddings
- **SQL DB:** SQLite (dev) / PostgreSQL (prod) for transactions
- Memory: Mem0, Supabase PostgreSQL
- **Monitoring:** LangSmith for traces, logs, and token usage
- **Web Search:** DuckDuckGo for adverse media screening

## 3. Project Folder Structure

```
aml-investigation-system/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app entry point
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py                # Dependency injection
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       ├── agents.py          # /api/agents/* endpoints
│   │   │       ├── investigations.py  # /api/investigations/* endpoints
│   │   │       ├── rag.py             # /api/rag/* RAG endpoints
│   │   │       ├── monitoring.py      # /api/monitoring/* metrics
│   │   │       └── health.py          # /api/health endpoint
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py              # Settings and env vars
│   │   │   ├── logger.py              # Structured logging
│   │   │   ├── security.py            # API key validation (optional)
│   │   │   └── exceptions.py          # Custom exception handlers
│   │   │
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── coordinator.py         # Coordinator Agent
│   │   │   ├── data_enrichment.py     # Data Enrichment Agent
│   │   │   ├── pattern_analyst.py     # Pattern Analyst Agent
│   │   │   ├── risk_assessor.py       # Risk Assessor Agent
│   │   │   ├── report_synthesizer.py  # Report Synthesizer Agent
│   │   │   ├── orchestrator.py        # LangGraph workflow
│   │   │   └── tools/
│   │   │       ├── __init__.py
│   │   │       ├── sql_tools.py       # SQL query tools
│   │   │       ├── vector_tools.py    # Vector retrieval tools
│   │   │       ├── search_tools.py    # Web search tools
│   │   │       └── analysis_tools.py  # Pattern analysis tools
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── investigation_service.py  # Business logic
│   │   │   ├── rag_service.py            # RAG pipeline
│   │   │   ├── monitoring_service.py     # LangSmith integration
│   │   │   └── database_service.py       # DB connection pool
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── request_models.py      # Pydantic request models
│   │   │   ├── response_models.py     # Pydantic response models
│   │   │   └── state_models.py        # Agent state models
│   │   │
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── session.py             # DB session management
│   │   │   ├── init_db.py             # Database initialization
│   │   │   └── models.py              # SQLAlchemy models (if using ORM)
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── audit_logger.py        # Compliance audit trails
│   │       └── validators.py          # Input validation
│   │
│   ├── data/
│   │   ├── raw/
│   │   │   ├── amlsim_transactions.csv
│   │   │   └── amlsim_customers.csv
│   │   ├── processed/
│   │   │   └── aml_database.db
│   │   ├── kyc_documents/
│   │   │   ├── customer_C001.txt
│   │   │   ├── customer_C002.txt
│   │   │   └── ...
│   │   └── kyc_vectordb/              # ChromaDB storage
│   │
│   ├── scripts/
│   │   ├── init_sqlite.py             # Initialize SQLite DB
│   │   ├── init_postgres.py           # Initialize PostgreSQL
│   │   ├── init_vectordb.py           # Setup ChromaDB
│   │   ├── generate_synthetic_data.py # Create test data
│   │   └── seed_test_cases.py         # Seed known patterns
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py                # Pytest fixtures
│   │   ├── test_api/
│   │   │   ├── test_agents.py
│   │   │   ├── test_investigations.py
│   │   │   └── test_rag.py
│   │   ├── test_agents/
│   │   │   ├── test_coordinator.py
│   │   │   ├── test_data_enrichment.py
│   │   │   └── test_pattern_analyst.py
│   │   └── test_services/
│   │       ├── test_investigation_service.py
│   │       └── test_rag_service.py
│   │
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── Dockerfile
│   ├── .env.example
│   └── README.md
│
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/
│   │   │   ├── AlertDashboard.jsx    # Main dashboard
│   │   │   ├── InvestigationView.jsx # Investigation results
│   │   │   ├── AgentStatus.jsx       # Agent execution status
│   │   │   ├── RiskIndicator.jsx     # Risk level display
│   │   │   └── AuditTrail.jsx        # Audit trail viewer
│   │   │
│   │   ├── services/
│   │   │   └── api.js                # API client
│   │   │
│   │   ├── utils/
│   │   │   └── formatters.js         # Data formatting utilities
│   │   │
│   │   ├── App.jsx
│   │   ├── index.js
│   │   └── App.css
│   │
│   ├── package.json
│   ├── Dockerfile
│   └── README.md
│
├── deployment/
│   ├── docker-compose.yml            # Local development
│   ├── docker-compose.prod.yml       # Production with Postgres
│   ├── nginx.conf                    # Nginx reverse proxy
│   ├── aws/
│   │   ├── ecs-task-definition.json  # AWS ECS config
│   │   ├── cloudformation.yaml       # AWS infrastructure
│   │   └── deploy.sh                 # Deployment script
│   └── k8s/                          # Kubernetes manifests (optional)
│       ├── backend-deployment.yaml
│       └── frontend-deployment.yaml
│
├── docs/
│   ├── API.md                        # API documentation
│   ├── ARCHITECTURE.md               # System architecture
│   ├── DEPLOYMENT.md                 # Deployment guide
│   └── DEMO_SCENARIOS.md             # Demo walkthrough
│
├── .gitignore
├── README.md
└── Makefile                          # Common commands
```

## 4. API Design

### Core Endpoints

#### Investigation Endpoints

**POST /api/investigations/start**

- Start new investigation for an alert
- Request:
```json
{
  "alert_id": "ALT001",
  "transaction_id": "T12345",
  "priority": "high"
}
```

- Response:
```json
{
  "investigation_id": "INV001",
  "status": "running",
  "created_at": "2024-01-15T10:00:00Z"
}
```


**GET /api/investigations/{investigation_id}**

- Get investigation status and results
- Response:
```json
{
  "investigation_id": "INV001",
  "status": "completed",
  "alert_id": "ALT001",
  "risk_level": "HIGH",
  "findings": {
    "enriched_data": {...},
    "pattern_analysis": {...},
    "risk_assessment": {...}
  },
  "final_report": "Full investigation narrative...",
  "audit_trail": ["Step 1...", "Step 2..."],
  "completion_time": "2024-01-15T10:05:30Z"
}
```


**GET /api/investigations/list**

- List all investigations with filtering
- Query params: `?status=completed&priority=high&limit=50`

#### Agent Endpoints

**POST /api/agents/{agent_name}/execute**

- Execute specific agent task (for testing)
- Supported agents: `coordinator`, `data_enrichment`, `pattern_analyst`, `risk_assessor`, `report_synthesizer`
- Request:
```json
{
  "input_data": {
    "transaction_id": "T12345",
    "customer_id": "C001"
  }
}
```


**GET /api/agents/status**

- Get status of all agents
- Response:
```json
{
  "agents": [
    {"name": "coordinator", "status": "idle", "last_execution": "..."},
    {"name": "data_enrichment", "status": "running", "current_task": "..."}
  ]
}
```


#### RAG Endpoints

**POST /api/rag/retrieve**

- Retrieve relevant KYC documents
- Request:
```json
{
  "query": "customer C001 profile",
  "customer_id": "C001",
  "top_k": 3
}
```

- Response:
```json
{
  "documents": [
    {
      "content": "KYC document content...",
      "metadata": {"customer_id": "C001", "document_type": "profile"},
      "similarity_score": 0.95
    }
  ]
}
```


**POST /api/rag/query**

- Full RAG query with LLM synthesis
- Request:
```json
{
  "question": "What is the typical transaction pattern for customer C001?",
  "context": {"customer_id": "C001"}
}
```


#### Monitoring Endpoints

**GET /api/monitoring/traces**

- Get LangSmith traces for investigations
- Query params: `?investigation_id=INV001`

**GET /api/monitoring/metrics**

- System performance metrics
- Response:
```json
{
  "total_investigations": 150,
  "avg_investigation_time_seconds": 45.2,
  "false_positive_rate": 0.12,
  "token_usage": {
    "total_tokens": 125000,
    "cost_usd": 2.50
  }
}
```


**GET /api/health**

- Health check endpoint
- Response: `{"status": "healthy", "timestamp": "..."}`

## 5. Agent Descriptions

### 1. Coordinator Agent (Team Lead)

- **Role:** Workflow orchestration and task delegation
- **Implementation:** LangGraph state machine with conditional routing
- **Tools:** None (pure orchestration)
- **Communication:** Sends Commands to delegate tasks to specialist agents
- **Key Logic:**
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Validates alert input
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Determines investigation sequence
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Monitors completion of each stage
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Ensures audit trail completeness

### 2. Data Enrichment Agent (Researcher)

- **Role:** Comprehensive data gathering from multiple sources
- **Tools:**
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - `sql_query_tool`: Query transaction database
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - `vector_retrieval_tool`: Retrieve KYC documents from ChromaDB
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - `customer_profile_tool`: Get customer history
- **Output:** Enriched state with transaction details, customer profile, KYC documents
- **Communication:** Handoff to Pattern Analyst via Command

### 3. Pattern Analyst Agent (Detective)

- **Role:** Identify suspicious transaction patterns
- **Tools:**
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - `structuring_detector`: Detect transactions under thresholds
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - `smurfing_detector`: Identify distributed transaction patterns
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - `network_analyzer`: Build transaction graphs
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - `behavioral_scorer`: Calculate anomaly scores
- **Patterns Detected:**
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Structuring (amounts just under $10k threshold)
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Smurfing (coordinated multi-account transactions)
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Circular flows (round-trip money movements)
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Behavioral anomalies (deviation from baselines)
- **Communication:** Handoff to Risk Assessor with pattern findings

### 4. Risk Assessor Agent (Profiler)

- **Role:** External risk evaluation and scoring
- **Tools:**
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - `adverse_media_search`: Web search for negative news
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - `sanctions_checker`: Check against OFAC/UN lists
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - `geographic_risk_scorer`: Assess location-based risks
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - `risk_calculator`: Combine factors into final score
- **Output:** Risk level (LOW/MEDIUM/HIGH/CRITICAL) with justification
- **Communication:** Handoff to Report Synthesizer

### 5. Report Synthesizer Agent (Scribe)

- **Role:** Generate comprehensive investigation reports
- **Tools:**
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - `report_generator`: Create structured narrative
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - `compliance_formatter`: Ensure regulatory compliance
- **Output:** Final report with:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Executive summary
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Key findings
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Risk assessment
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Recommendations
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Complete audit trail
- **Communication:** Returns to END state with final report

## 6. RAG Workflow

### Query Routing

1. **User Query** → FastAPI endpoint `/api/rag/query`
2. **Router:** Determines if query needs retrieval or direct LLM
3. **Retrieval Step:**

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Embed query using OpenAI embeddings
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Search ChromaDB for top-k similar KYC documents
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Retrieve relevant transaction data from SQL

4. **Synthesis Step:**

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Combine retrieved context
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Send to LLM with prompt template
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Generate contextualized answer

5. **Response:** Return answer with source citations

### RAG Pipeline Implementation

```python
# In backend/app/services/rag_service.py

class RAGService:
    async def query(self, question: str, context: dict):
        # 1. Retrieve relevant documents
        docs = await self.retrieve_documents(question, context)
        
        # 2. Format context for LLM
        context_text = self.format_context(docs)
        
        # 3. Generate response with LLM
        response = await self.generate_answer(question, context_text)
        
        # 4. Track with LangSmith
        self.monitor.log_rag_query(question, docs, response)
        
        return response
```

## 7. Demo Scenarios

### Scenario 1: Structuring Detection

**Story:** Customer C103 makes multiple $9,900 deposits (just under $10k reporting threshold)

**Demo Flow:**

1. Load alert ALT001 in dashboard
2. Click "Start Investigation"
3. Watch agents execute in sequence:

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Coordinator: Initializes workflow
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Data Enrichment: Retrieves 4 transactions totaling $39,600
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Pattern Analyst: Flags "STRUCTURING" pattern
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Risk Assessor: Calculates HIGH risk score
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Report Synthesizer: Generates SAR recommendation

4. View final report with evidence
5. Show audit trail with agent decisions

**Expected Result:** HIGH risk, recommend filing SAR

### Scenario 2: Smurfing Network

**Story:** Multiple accounts (C104-C107) send coordinated payments to C999 within 15 minutes

**Demo Flow:**

1. Load alert ALT002
2. Start investigation
3. Pattern Analyst builds transaction network graph
4. Identifies 4 coordinated senders
5. Risk Assessor searches adverse media on all entities
6. Report shows network visualization

**Expected Result:** CRITICAL risk, immediate escalation

### Scenario 3: False Positive - Legitimate Business

**Story:** Cash-intensive restaurant (C102) has high deposit volume

**Demo Flow:**

1. Load alert ALT003
2. Data Enrichment retrieves KYC noting "cash-intensive business"
3. Pattern Analyst compares against industry benchmarks
4. Risk Assessor finds no adverse media
5. Report recommends closure as false positive

**Expected Result:** LOW risk, close alert

## 8. Deployment & Scaling

### Local Development (Docker)

**docker-compose.yml:**

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
   - "8000:8000"
    environment:
   - OPENAI_API_KEY=${OPENAI_API_KEY}
   - DATABASE_URL=sqlite:///data/aml_database.db
   - VECTOR_DB_PATH=/app/data/kyc_vectordb
   - LANGSMITH_API_KEY=${LANGSMITH_API_KEY}
   - LANGSMITH_PROJECT=aml-investigation
    volumes:
   - ./backend/data:/app/data
   - ./backend/app:/app/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build: ./frontend
    ports:
   - "3000:3000"
    environment:
   - REACT_APP_API_URL=http://localhost:8000
    volumes:
   - ./frontend/src:/app/src
    command: npm start

  postgres:
    image: postgres:15
    environment:
   - POSTGRES_DB=aml_db
   - POSTGRES_USER=aml_user
   - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    ports:
   - "5432:5432"
    volumes:
   - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

**Commands:**

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Run database initialization
docker-compose exec backend python scripts/init_sqlite.py

# Stop services
docker-compose down
```

### Production Deployment (AWS ECS)

**Architecture:**

- ECS Fargate for backend containers
- S3 + CloudFront for React frontend
- RDS PostgreSQL for database
- EFS for vector database persistence
- Application Load Balancer for routing

**Deployment Steps:**

1. Build and push Docker images to ECR
2. Deploy RDS PostgreSQL instance
3. Create EFS file system for ChromaDB
4. Deploy ECS task definition
5. Configure ALB with health checks
6. Deploy React frontend to S3
7. Set up CloudFront distribution

**Cost Estimate (monthly):**

- ECS Fargate (2 vCPU, 4GB): ~$50
- RDS PostgreSQL (db.t3.medium): ~$60
- EFS storage (50GB): ~$15
- ALB: ~$20
- Total: ~$145/month

### Scaling Considerations

**Horizontal Scaling:**

- Run multiple FastAPI instances behind ALB
- Use Redis for shared session state
- Database connection pooling

**Performance Optimization:**

- Cache frequent queries in Redis
- Async database operations
- Batch vector searches
- Stream large responses

## 9. Evaluation & Monitoring

### LangSmith Integration

**Setup:**

```python
# In backend/app/core/config.py
import os
from langchain.callbacks import LangChainTracer

os.environ["LANGSMITH_API_KEY"] = settings.LANGSMITH_API_KEY
os.environ["LANGSMITH_PROJECT"] = "aml-investigation"
os.environ["LANGSMITH_TRACING"] = "true"

tracer = LangChainTracer(project_name="aml-investigation")
```

**Tracked Metrics:**

- **Agent Traces:** Full execution path for each investigation
- **Token Usage:** Input/output tokens per agent call
- **Latency:** Time spent in each agent
- **Errors:** Failed agent executions with stack traces
- **Cost:** Estimated OpenAI API costs per investigation

**LangSmith Dashboard Views:**

1. **Investigation Timeline:** Visualize agent handoffs
2. **Performance Analytics:** P50/P95/P99 latencies
3. **Token Economics:** Cost breakdown by agent
4. **Error Rate:** Failed investigations and causes
5. **Evaluation Sets:** Compare agent outputs on test cases

### Performance Metrics

**System KPIs:**

- Average investigation time: Target < 60 seconds
- False positive reduction: Target 45%
- Agent success rate: Target > 95%
- API response time (p95): Target < 5 seconds

**Monitoring Dashboard:**

```python
# GET /api/monitoring/metrics response
{
  "period": "last_24h",
  "investigations": {
    "total": 150,
    "completed": 145,
    "failed": 5,
    "avg_duration_seconds": 48.5
  },
  "agents": {
    "coordinator": {"calls": 150, "avg_latency_ms": 1200},
    "data_enrichment": {"calls": 145, "avg_latency_ms": 3500},
    "pattern_analyst": {"calls": 145, "avg_latency_ms": 5200},
    "risk_assessor": {"calls": 145, "avg_latency_ms": 8500},
    "report_synthesizer": {"calls": 145, "avg_latency_ms": 6800}
  },
  "llm_usage": {
    "total_tokens": 2850000,
    "total_cost_usd": 57.00,
    "avg_tokens_per_investigation": 19655
  },
  "patterns_detected": {
    "structuring": 12,
    "smurfing": 8,
    "circular_flow": 3,
    "behavioral_anomaly": 25
  }
}
```

### Evaluation Strategy

**Automated Testing:**

- Unit tests for each agent (pytest)
- Integration tests for full workflow
- Load testing with locust (100 concurrent investigations)
- Regression tests on known patterns

**Quality Metrics:**

- Pattern detection accuracy (precision/recall)
- Risk scoring consistency
- Report quality (human evaluation)
- Audit trail completeness

**Continuous Improvement:**

- A/B test prompt variations
- Track false positive rate over time
- Compare agent performance across models
- Collect analyst feedback on report quality

## Implementation Checklist

### Phase 1: Backend Foundation (Day 1-2)

- [ ] Setup project structure and virtual environment
- [ ] Implement FastAPI app with core routes
- [ ] Configure settings and environment variables
- [ ] Setup database connections (SQLite + ChromaDB)
- [ ] Create Pydantic models for requests/responses
- [ ] Implement health check and basic monitoring endpoints

### Phase 2: Agent Implementation (Day 2-4)

- [ ] Implement Coordinator Agent with LangGraph
- [ ] Build Data Enrichment Agent with SQL/vector tools
- [ ] Create Pattern Analyst Agent with detection logic
- [ ] Develop Risk Assessor Agent with search tools
- [ ] Implement Report Synthesizer Agent
- [ ] Setup LangGraph workflow with agent handoffs
- [ ] Integrate LangSmith tracing

### Phase 3: RAG Pipeline (Day 4-5)

- [ ] Initialize ChromaDB with KYC documents
- [ ] Implement vector embedding service
- [ ] Build RAG query endpoint
- [ ] Add document retrieval endpoint
- [ ] Test retrieval accuracy

### Phase 4: Frontend Development (Day 5-6)

- [ ] Setup React project with create-react-app
- [ ] Build Alert Dashboard component
- [ ] Create Investigation View component
- [ ] Implement Agent Status display
- [ ] Add Audit Trail viewer
- [ ] Connect to backend API
- [ ] Style with modern UI library (Material-UI/Tailwind)

### Phase 5: Data & Testing (Day 6-7)

- [ ] Generate synthetic AML dataset
- [ ] Seed test cases (structuring, smurfing, false positives)
- [ ] Write unit tests for agents
- [ ] Create integration tests for API endpoints
- [ ] Test full investigation workflows
- [ ] Validate LangSmith logging

### Phase 6: Deployment (Day 7)

- [ ] Create Dockerfiles for backend and frontend
- [ ] Setup docker-compose for local development
- [ ] Write deployment documentation
- [ ] Test Docker deployment locally
- [ ] (Optional) Deploy to AWS ECS
- [ ] Create demo scenarios documentation

### Phase 7: Polish & Demo Prep

- [ ] Optimize API performance
- [ ] Add error handling and validation
- [ ] Create demo walkthrough script
- [ ] Prepare presentation slides
- [ ] Record demo videos for each scenario
- [ ] Write comprehensive README