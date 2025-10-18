# Test LangGraph workflow with simple invocation
print("🚀 Testing LangGraph Workflow Invocation")
print("=" * 60)

try:
    # Get the compiled workflow
    graph = aml_workflow
    
    print("✅ Workflow compiled successfully")
    print(f"   Graph type: {type(graph)}")
    
    # Test 1: Basic invocation with sample data
    print("\n1️⃣ Testing Basic Invocation...")
    
    # Create initial state for the workflow
    initial_state = {
        "transaction": sample_transaction,
        "customer": sample_customer,
        "risk_score": 0,
        "alerts": [],
        "investigation": {},
        "llm_analysis": {},
        "risk_factors": [],
        "decision_path": [],
        "reporting_status": None,
        "case_id": None,
        "requires_approval": False,
        "approval_status": None,
        "approval_metadata": {},
        "documents": sample_customer.get("kyc_documents", []),
        "pep_status": None,
        "sanction_hits": [],
        "transaction_count": 1,
        "batch_mode": False,
        "alert_id": sample_alert["alert_id"]
    }
    
    print(f"📥 Initial state created with {len(initial_state)} fields")
    
    # Invoke the workflow
    result = await graph.ainvoke(initial_state)
    
    print(f"✅ Workflow invocation completed!")
    print(f"   Result type: {type(result)}")
    print(f"   Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
    
    # Show key results
    if isinstance(result, dict):
        print(f"\n📊 Workflow Results:")
        print(f"   Case ID: {result.get('case_id', 'N/A')}")
        print(f"   Risk Score: {result.get('risk_score', 'N/A')}")
        print(f"   Risk Level: {result.get('risk_level', 'N/A')}")
        print(f"   Decision Path: {result.get('decision_path', [])}")
        print(f"   Alerts: {result.get('alerts', [])}")
        print(f"   Risk Factors: {result.get('risk_factors', [])}")
        print(f"   Reporting Status: {result.get('reporting_status', 'N/A')}")
    
    # Test 2: Different transaction scenario
    print("\n2️⃣ Testing Different Scenario...")
    
    # Create a high-risk transaction
    high_risk_transaction = {
        **sample_transaction,
        "amount": 500000,
        "country": "IR",  # High-risk country
        "transaction_type": "wire"
    }
    
    high_risk_state = {
        **initial_state,
        "transaction": high_risk_transaction
    }
    
    result2 = await graph.ainvoke(high_risk_state)
    
    print(f"✅ High-risk scenario completed!")
    if isinstance(result2, dict):
        print(f"   Risk Score: {result2.get('risk_score', 'N/A')}")
        print(f"   Risk Level: {result2.get('risk_level', 'N/A')}")
        print(f"   Decision Path: {result2.get('decision_path', [])}")
    
except Exception as e:
    print(f"❌ Workflow invocation failed: {str(e)}")
    import traceback
    print(f"   Full traceback:\n{traceback.format_exc()}")
