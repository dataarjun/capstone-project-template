# LangSmith Integration for AML Multi-Agent System

This document describes the comprehensive LangSmith integration for prompt management, tracing, and version control in the AML multi-agent system.

## Overview

The LangSmith integration provides:
- **Prompt Version Control**: Centralized management of all agent prompts
- **Tracing & Monitoring**: Real-time tracking of agent performance
- **API Management**: RESTful endpoints for prompt operations
- **Deployment Automation**: Scripts for prompt deployment and management

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   AML Agents    │    │  LangSmith API   │    │  FastAPI App    │
│                 │    │                  │    │                 │
│ • Risk Assessor │◄──►│ • Prompt Storage │◄──►│ • /api/prompts  │
│ • Pattern Anal. │    │ • Version Control│    │ • /api/tracing  │
│ • Report Synth. │    │ • Tracing        │    │ • Management    │
│ • Data Enrich.  │    │ • Monitoring     │    │                 │
│ • Coordinator   │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Setup

### 1. Environment Configuration

Add to your `.env` file:

```bash
# LangSmith Configuration
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=aml-multi-agent-system
LANGSMITH_WORKSPACE=default
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

### 2. Install Dependencies

```bash
pip install langsmith langchain-openai
```

### 3. Deploy Prompts

```bash
# Deploy all prompts to LangSmith
python scripts/deploy_prompts.py

# Or deploy individual prompts via API
curl -X POST "http://localhost:8000/api/prompts/deploy" \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "risk_assessor"}'
```

## Usage

### Prompt Management

#### Deploy a Prompt

```python
from app.core.prompt_manager import prompt_manager

# Deploy a specific agent prompt
url = prompt_manager.deploy_prompt_to_langsmith(
    agent_name="risk_assessor",
    description="Updated risk assessment prompt",
    tags=["production", "aml"]
)
```

#### Get Agent Chain

```python
# Get a complete agent chain with prompt and model
chain = prompt_manager.get_agent_chain(
    agent_name="risk_assessor",
    model_config={"model": "gpt-4o", "temperature": 0.2}
)

# Use the chain
result = chain.invoke({"transaction_data": {...}})
```

#### Version Management

```python
# Get all versions of a prompt
versions = prompt_manager.get_prompt_versions("risk_assessor")

# Rollback to a specific version
success = prompt_manager.rollback_prompt("risk_assessor", "abc123")

# Compare two versions
comparison = prompt_manager.compare_prompt_versions(
    "risk_assessor", "v1", "v2"
)
```

### Tracing & Monitoring

#### Agent Tracing

```python
from app.core.tracing import trace_risk_assessor, aml_tracer

@trace_risk_assessor("assess_risk")
async def assess_transaction_risk(transaction_data):
    # Your risk assessment logic
    return {"risk_score": 85, "risk_level": "High"}

# Get agent metrics
metrics = aml_tracer.get_agent_metrics("risk_assessor")
print(f"Calls: {metrics['calls']}, Avg Time: {metrics['avg_time']}s")
```

#### Investigation Tracing

```python
# Create a trace for an entire investigation
trace_data = aml_tracer.create_investigation_trace(
    case_id="CASE-2024-001",
    investigation_data={
        "transaction_amount": 50000,
        "risk_score": 85,
        "agents_involved": ["risk_assessor", "pattern_analyst"]
    }
)
```

## API Endpoints

### Prompt Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/prompts/deploy` | POST | Deploy a prompt for an agent |
| `/api/prompts/deploy-all` | POST | Deploy all agent prompts |
| `/api/prompts/agents` | GET | List all available agents |
| `/api/prompts/{agent_name}/versions` | GET | Get prompt versions |
| `/api/prompts/rollback` | POST | Rollback to a version |
| `/api/prompts/compare` | POST | Compare two versions |
| `/api/prompts/{agent_name}/chain` | GET | Get agent chain |
| `/api/prompts/health` | GET | Health check |

### Example API Usage

```bash
# Deploy all prompts
curl -X POST "http://localhost:8000/api/prompts/deploy-all"

# Get prompt versions
curl "http://localhost:8000/api/prompts/risk_assessor/versions"

# Rollback to a version
curl -X POST "http://localhost:8000/api/prompts/rollback" \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "risk_assessor", "version": "abc123"}'
```

## Agent Integration

### Risk Assessor

```python
from app.core.tracing import trace_risk_assessor
from app.core.prompt_manager import prompt_manager

@trace_risk_assessor("assess_risk")
async def assess_risk(transaction_data):
    # Get the latest prompt and model
    chain = prompt_manager.get_agent_chain("risk_assessor")
    
    # Process with tracing
    result = await chain.ainvoke({
        "transaction": transaction_data,
        "context": "AML risk assessment"
    })
    
    return result
```

### Pattern Analyst

```python
from app.core.tracing import trace_pattern_analyst

@trace_pattern_analyst("analyze_patterns")
async def analyze_patterns(transaction_history):
    chain = prompt_manager.get_agent_chain("pattern_analyst")
    return await chain.ainvoke({"history": transaction_history})
```

## Deployment Workflow

### 1. Development

```bash
# Test prompts locally
python examples/langsmith_integration_demo.py

# Deploy to development environment
LANGSMITH_PROJECT=aml-dev python scripts/deploy_prompts.py
```

### 2. Production

```bash
# Deploy to production
LANGSMITH_PROJECT=aml-production python scripts/deploy_prompts.py

# Verify deployment
curl "http://localhost:8000/api/prompts/health"
```

### 3. Monitoring

```bash
# Check agent performance
curl "http://localhost:8000/api/monitoring/agents"

# View traces in LangSmith dashboard
# https://smith.langchain.com
```

## Best Practices

### 1. Prompt Versioning

- Always tag production prompts with `["production", "aml"]`
- Use descriptive commit messages for prompt updates
- Test prompts in development before production deployment

### 2. Tracing

- Use tracing decorators on all agent functions
- Monitor agent performance metrics regularly
- Set up alerts for high error rates

### 3. Deployment

- Deploy prompts during maintenance windows
- Always verify deployments with health checks
- Keep rollback versions available

### 4. Monitoring

- Monitor agent execution times
- Track error rates and success rates
- Use LangSmith dashboard for detailed analysis

## Troubleshooting

### Common Issues

1. **LangSmith API Key Not Set**
   ```bash
   export LANGSMITH_API_KEY=your_key_here
   ```

2. **Prompt Deployment Fails**
   ```bash
   # Check LangSmith connection
   curl "http://localhost:8000/api/prompts/health"
   ```

3. **Tracing Not Working**
   ```bash
   # Verify environment variables
   echo $LANGSMITH_TRACING
   echo $LANGSMITH_PROJECT
   ```

### Debug Mode

```python
import logging
logging.getLogger("langsmith").setLevel(logging.DEBUG)
```

## Advanced Features

### Custom Model Configurations

```python
# Custom model configuration for specific agents
chain = prompt_manager.get_agent_chain(
    agent_name="risk_assessor",
    model_config={
        "model": "gpt-4o",
        "temperature": 0.1,
        "max_tokens": 2000
    }
)
```

### Batch Processing with Tracing

```python
# Process multiple transactions with tracing
async def process_batch(transactions):
    results = []
    for txn in transactions:
        with aml_tracer.trace_agent_call("risk_assessor", "batch_process"):
            result = await assess_risk(txn)
            results.append(result)
    return results
```

## Integration with Existing Agents

To integrate LangSmith with existing agents, simply add the tracing decorators:

```python
# Before
async def assess_risk(transaction_data):
    # existing logic
    return result

# After
@trace_risk_assessor("assess_risk")
async def assess_risk(transaction_data):
    # existing logic
    return result
```

This provides immediate tracing and monitoring without changing the core logic.

## Support

For issues or questions:
1. Check the LangSmith dashboard: https://smith.langchain.com
2. Review agent metrics: `/api/monitoring/agents`
3. Check logs for detailed error information
4. Use the health check endpoint: `/api/prompts/health`





