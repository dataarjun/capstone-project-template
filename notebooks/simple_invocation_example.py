# Simple workflow invocation example
print("🚀 Testing Simple Workflow Invocation")

# Create initial state
initial_state = {
    "transaction": sample_transaction,
    "customer": sample_customer,
    "risk_score": 0,
    "alerts": [],
    "decision_path": [],
    "alert_id": sample_alert["alert_id"]
}

# Invoke workflow
result = await aml_workflow.ainvoke(
    initial_state, 
    config={"configurable": {"thread_id": "test-simple-1"}}
)

# Display key results
print(f"✅ Invocation completed")
print(f"   Case ID: {result.get('case_id', 'N/A')}")
print(f"   Risk Score: {result.get('risk_score', 'N/A')}")
print(f"   Decision Path: {result.get('decision_path', [])}")




