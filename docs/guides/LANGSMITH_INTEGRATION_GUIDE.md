# 🔧 **LangSmith Integration Guide**

## 🚀 **Complete LangSmith Integration for Prompt Management**

This guide provides comprehensive documentation for the LangSmith integration in the Multi-Agent AML Investigation System, including prompt management, version control, A/B testing, and performance monitoring.

## 📋 **Overview**

The system integrates with **LangSmith** for:
- **Prompt Version Control**: Track and manage prompt changes
- **A/B Testing**: Compare prompt performance
- **Performance Monitoring**: Track usage and effectiveness
- **Collaboration**: Team-based prompt management
- **Automated Deployment**: Deploy prompts to production

## 🤖 **Agent Prompts in LangSmith**

### **Available Agents & Their Prompts**

#### **1. Risk Assessor Agent**
- **Prompt File**: `prompts/risk_assessment.yaml`
- **LangSmith Project**: `aml-risk-assessor`
- **Purpose**: Transaction risk classification and scoring
- **Variables**: `txn_json`, `rule_summary`
- **Output**: Risk level, confidence score, reasoning

#### **2. Pattern Analyst Agent**
- **Prompt File**: `prompts/behavior_analysis.yaml`
- **LangSmith Project**: `aml-pattern-analyst`
- **Purpose**: Behavioral pattern detection and analysis
- **Variables**: `transaction_history`, `behavioral_data`
- **Output**: Pattern analysis, suspicious indicators

#### **3. Data Enrichment Agent**
- **Prompt File**: `prompts/document_analysis.yaml`
- **LangSmith Project**: `aml-data-enrichment`
- **Purpose**: KYC document processing and verification
- **Variables**: `customer_data`, `document_content`
- **Output**: Enriched profiles, verification results

#### **4. Report Synthesizer Agent**
- **Prompt File**: `prompts/sar_generation.yaml`, `prompts/edd_report.yaml`
- **LangSmith Project**: `aml-report-synthesizer`
- **Purpose**: SAR and compliance report generation
- **Variables**: `investigation_results`, `evidence`
- **Output**: SAR documents, compliance reports

#### **5. Coordinator Agent**
- **Prompt File**: `prompts/coordinator.yaml`
- **LangSmith Project**: `aml-coordinator`
- **Purpose**: Workflow orchestration and decision routing
- **Variables**: `transaction_data`, `investigation_context`
- **Output**: Investigation plan, agent assignments

## 🔧 **LangSmith API Integration**

### **Core Components**

#### **1. LangSmith Client (`app/core/langsmith_client.py`)**
```python
class LangSmithManager:
    """LangSmith integration manager"""
    
    def __init__(self):
        self.api_key = settings.LANGSMITH_API_KEY
        self.project_name = settings.LANGSMITH_PROJECT_NAME
        self.client = Client(api_key=self.api_key)
    
    async def deploy_prompt(self, agent_name: str, prompt_data: dict) -> str:
        """Deploy prompt to LangSmith"""
        
    async def get_prompt_versions(self, agent_name: str) -> List[dict]:
        """Get all versions of a prompt"""
        
    async def compare_prompts(self, agent_name: str, version_a: str, version_b: str) -> dict:
        """Compare two prompt versions"""
        
    async def get_performance_metrics(self, agent_name: str, period: str) -> dict:
        """Get performance metrics for an agent"""
```

#### **2. Prompt Manager (`app/core/prompt_manager.py`)**
```python
class PromptManager:
    """Prompt management system with LangSmith integration"""
    
    def __init__(self):
        self.langsmith = LangSmithManager()
        self.local_prompts = self.load_local_prompts()
    
    def load_local_prompts(self) -> dict:
        """Load prompts from local YAML files"""
        
    async def deploy_to_langsmith(self, agent_name: str, force_update: bool = False) -> str:
        """Deploy local prompt to LangSmith"""
        
    async def sync_from_langsmith(self, agent_name: str) -> dict:
        """Sync prompt from LangSmith to local"""
        
    async def get_prompt_performance(self, agent_name: str) -> dict:
        """Get performance metrics from LangSmith"""
```

## 📊 **Prompt Management API Endpoints**

### **1. List All Prompts**
```http
GET /api/prompts/
```
**Description**: Get list of all available prompts with LangSmith integration status.

**Response**:
```json
{
  "prompts": [
    {
      "agent_name": "risk_assessor",
      "local_version": "1.0.0",
      "langsmith_version": "1.0.0",
      "status": "synced",
      "last_updated": "2024-01-15T10:30:00",
      "performance_score": 0.85
    },
    {
      "agent_name": "pattern_analyst",
      "local_version": "1.1.0",
      "langsmith_version": "1.0.0",
      "status": "local_ahead",
      "last_updated": "2024-01-15T11:00:00",
      "performance_score": 0.78
    }
  ]
}
```

### **2. Get Agent Prompts**
```http
GET /api/prompts/{agent_name}
```
**Description**: Get detailed information about prompts for a specific agent.

**Path Parameters**:
- `agent_name` (string): Name of the agent

**Response**:
```json
{
  "agent_name": "risk_assessor",
  "local_prompt": {
    "version": "1.0.0",
    "description": "Risk assessment prompt for AML transaction analysis",
    "template": "You are a compliance risk analyst...",
    "variables": [
      {
        "name": "txn_json",
        "description": "JSON representation of transaction data",
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
  },
  "langsmith_prompt": {
    "prompt_id": "prompt_12345",
    "version": "1.0.0",
    "status": "active",
    "performance_metrics": {
      "accuracy": 0.85,
      "response_time": 1.2,
      "usage_count": 150
    }
  }
}
```

### **3. Deploy Prompt to LangSmith**
```http
POST /api/prompts/deploy
```
**Description**: Deploy a local prompt to LangSmith for version control and A/B testing.

**Request Body**:
```json
{
  "agent_name": "risk_assessor",
  "description": "Updated risk assessment prompt with improved accuracy",
  "tags": ["production", "v1.1", "improved"],
  "force_update": false
}
```

**Response**:
```json
{
  "status": "success",
  "prompt_id": "prompt_12345",
  "version": "1.1.0",
  "langsmith_url": "https://smith.langchain.com/prompts/prompt_12345",
  "deployment_status": "active",
  "performance_baseline": {
    "accuracy": 0.85,
    "response_time": 1.2
  }
}
```

### **4. Update Agent Prompt**
```http
PUT /api/prompts/{agent_name}
```
**Description**: Update the prompt for a specific agent both locally and in LangSmith.

**Request Body**:
```json
{
  "prompt_template": "Updated prompt template with improved instructions...",
  "description": "Enhanced risk assessment prompt",
  "variables": [
    {
      "name": "txn_json",
      "description": "Transaction data in JSON format",
      "type": "string",
      "required": true
    },
    {
      "name": "rule_summary",
      "description": "Summary of rule-based analysis",
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
  },
  "examples": [
    {
      "input": {
        "txn_json": "{\"amount\": 9500, \"currency\": \"USD\"}",
        "rule_summary": "{\"points\": 3, \"base_level\": \"Medium\"}"
      },
      "output": {
        "risk_level": "Medium",
        "score": 0.65,
        "reason": "Transaction amount near CTR threshold suggests potential structuring."
      }
    }
  ]
}
```

### **5. Get Prompt Versions**
```http
GET /api/prompts/{agent_name}/versions
```
**Description**: Get all versions of prompts for an agent from LangSmith.

**Response**:
```json
{
  "agent_name": "risk_assessor",
  "versions": [
    {
      "version": "1.1.0",
      "status": "active",
      "created_at": "2024-01-15T10:30:00",
      "performance_score": 0.85,
      "usage_count": 200,
      "tags": ["production", "v1.1"]
    },
    {
      "version": "1.0.0",
      "status": "archived",
      "created_at": "2024-01-10T10:30:00",
      "performance_score": 0.78,
      "usage_count": 150,
      "tags": ["production", "v1.0"]
    }
  ]
}
```

### **6. Compare Prompt Versions**
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
  "test_period": "7d",
  "metrics": ["accuracy", "response_time", "usage"]
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
      "usage_count": 150,
      "error_rate": 0.05
    },
    "version_b": {
      "version": "1.1.0",
      "accuracy": 0.85,
      "response_time": 1.1,
      "usage_count": 200,
      "error_rate": 0.02
    },
    "improvement": {
      "accuracy": "+9.0%",
      "response_time": "-8.3%",
      "usage": "+33.3%",
      "error_rate": "-60.0%"
    },
    "statistical_significance": {
      "accuracy": true,
      "response_time": true,
      "confidence_level": 0.95
    }
  }
}
```

### **7. Get Performance Metrics**
```http
GET /api/prompts/{agent_name}/performance
```
**Description**: Get performance metrics for an agent's prompts from LangSmith.

**Query Parameters**:
- `period` (string, optional): Time period (1d, 7d, 30d, 90d)
- `metric` (string, optional): Specific metric (accuracy, response_time, usage, error_rate)

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
    "user_satisfaction": 4.2,
    "cost_per_request": 0.05
  },
  "trends": {
    "accuracy": "+5%",
    "response_time": "-10%",
    "usage": "+25%",
    "error_rate": "-50%"
  },
  "benchmarks": {
    "industry_average_accuracy": 0.75,
    "industry_average_response_time": 1.5,
    "our_performance_vs_industry": "+13.3%"
  }
}
```

## 🔄 **Prompt Deployment Workflow**

### **1. Local Development**
```bash
# Edit prompt file
vim prompts/risk_assessment.yaml

# Test locally
python test_prompt_locally.py --agent risk_assessor
```

### **2. Deploy to LangSmith**
```bash
# Deploy to LangSmith
curl -X POST "http://localhost:8000/api/prompts/deploy" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "risk_assessor",
    "description": "Updated risk assessment prompt",
    "tags": ["staging", "v1.1"]
  }'
```

### **3. A/B Testing**
```bash
# Start A/B test
curl -X POST "http://localhost:8000/api/prompts/compare" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "risk_assessor",
    "version_a": "1.0.0",
    "version_b": "1.1.0",
    "test_period": "7d"
  }'
```

### **4. Production Deployment**
```bash
# Deploy to production
curl -X POST "http://localhost:8000/api/prompts/deploy" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "risk_assessor",
    "description": "Production-ready risk assessment prompt",
    "tags": ["production", "v1.1"],
    "force_update": true
  }'
```

## 📊 **Performance Monitoring**

### **Key Metrics Tracked**

#### **1. Accuracy Metrics**
- **Classification Accuracy**: Correct risk level predictions
- **Confidence Calibration**: How well confidence scores match actual performance
- **False Positive Rate**: Incorrect high-risk classifications
- **False Negative Rate**: Missed high-risk transactions

#### **2. Performance Metrics**
- **Response Time**: Average time to process requests
- **Throughput**: Requests processed per minute
- **Error Rate**: Percentage of failed requests
- **Resource Usage**: CPU, memory, and API costs

#### **3. Business Metrics**
- **Usage Patterns**: Which prompts are used most frequently
- **User Satisfaction**: Feedback on prompt quality
- **Cost Efficiency**: Cost per accurate prediction
- **ROI**: Return on investment for prompt improvements

### **Monitoring Dashboard**

#### **Real-time Metrics**
```json
{
  "system_status": "healthy",
  "active_prompts": 5,
  "total_requests": 15420,
  "average_response_time": 1.1,
  "error_rate": 0.02,
  "cost_today": 45.50
}
```

#### **Agent Performance**
```json
{
  "risk_assessor": {
    "accuracy": 0.85,
    "response_time": 1.1,
    "usage": 200,
    "status": "excellent"
  },
  "pattern_analyst": {
    "accuracy": 0.78,
    "response_time": 1.3,
    "usage": 150,
    "status": "good"
  }
}
```

## 🔧 **Configuration & Setup**

### **Environment Variables**
```bash
# LangSmith Configuration
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT_NAME=aml-investigation-system
LANGSMITH_ENDPOINT=https://api.smith.langchain.com

# Prompt Management
PROMPT_CACHE_TTL=3600
PROMPT_SYNC_INTERVAL=300
AUTO_DEPLOY_ENABLED=false
```

### **LangSmith Project Setup**
```python
# Initialize LangSmith projects for each agent
langsmith_projects = {
    "risk_assessor": "aml-risk-assessor",
    "pattern_analyst": "aml-pattern-analyst", 
    "data_enrichment": "aml-data-enrichment",
    "report_synthesizer": "aml-report-synthesizer",
    "coordinator": "aml-coordinator"
}
```

## 🧪 **Testing & Validation**

### **Prompt Testing**
```python
# Test prompt locally
def test_prompt_locally(agent_name: str, test_data: dict):
    """Test prompt with sample data"""
    prompt = load_prompt(agent_name)
    result = run_prompt(prompt, test_data)
    return validate_output(result)

# A/B test prompts
def run_ab_test(agent_name: str, version_a: str, version_b: str):
    """Run A/B test between two prompt versions"""
    results_a = test_prompt_version(agent_name, version_a)
    results_b = test_prompt_version(agent_name, version_b)
    return compare_results(results_a, results_b)
```

### **Performance Validation**
```python
# Validate performance metrics
def validate_performance(agent_name: str, metrics: dict):
    """Validate that performance meets requirements"""
    requirements = {
        "accuracy": 0.80,
        "response_time": 2.0,
        "error_rate": 0.05
    }
    
    for metric, threshold in requirements.items():
        if metrics[metric] < threshold:
            raise ValidationError(f"{metric} below threshold")
```

## 🚀 **Best Practices**

### **1. Prompt Development**
- **Version Control**: Always version your prompts
- **Testing**: Test prompts with diverse data
- **Documentation**: Document prompt changes and rationale
- **Rollback Plan**: Always have a rollback strategy

### **2. Deployment**
- **Staging First**: Deploy to staging before production
- **Gradual Rollout**: Use A/B testing for major changes
- **Monitoring**: Monitor performance after deployment
- **Feedback Loop**: Collect and act on user feedback

### **3. Performance Optimization**
- **Regular Monitoring**: Monitor performance continuously
- **Benchmarking**: Compare against industry standards
- **Cost Optimization**: Balance performance with cost
- **Continuous Improvement**: Iterate based on metrics

---

## 📞 **Support & Resources**

- **LangSmith Documentation**: https://docs.smith.langchain.com/
- **API Reference**: `http://localhost:8000/docs`
- **Interactive Testing**: Built-in API explorer
- **Performance Dashboard**: Real-time metrics and monitoring

**🎉 Complete LangSmith integration for advanced prompt management in your Multi-Agent AML System!**
