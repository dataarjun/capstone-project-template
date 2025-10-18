"""
Simple AML System Test

Test the core AML functionality without complex dependencies
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_data_loading():
    """Test basic data loading"""
    print("🧪 Testing Data Loading...")
    
    try:
        from scripts.load_aml_data import AMLDataManager
        
        data_manager = AMLDataManager()
        operational_summary = data_manager.get_operational_summary()
        hi_trans_summary = data_manager.get_hi_trans_summary()
        
        print(f"✅ Data loading successful:")
        print(f"  - Operational datasets: {len(operational_summary)}")
        print(f"  - HI-Small_Trans records: {hi_trans_summary.get('total_records', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Data loading failed: {str(e)}")
        return False


def test_rule_engine():
    """Test rule-based scoring"""
    print("\n🧪 Testing Rule Engine...")
    
    try:
        from app.models.aml_models import TxnEvent
        from app.agents.tools.rule_engine import score_rules
        
        # Create test transaction
        test_txn = TxnEvent(
            transaction_id="TEST_001",
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            customer_id="CUST_001",
            amount=15000.0,
            currency="USD",
            transaction_type="WIRE_TRANSFER",
            location="New York",
            country="US",
            description="Transfer to offshore account",
            amount_z=2.5,
            c_txn_7d=15,
            kw_flag=1,
            payment_format="WIRE_TRANSFER"
        )
        
        # Test rule scoring
        rule_result = score_rules(test_txn)
        
        print(f"✅ Rule engine test passed:")
        print(f"  - Risk points: {rule_result['points']}")
        print(f"  - Risk level: {rule_result['base_level']}")
        print(f"  - Reasons: {len(rule_result['reasons'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Rule engine test failed: {str(e)}")
        return False


def test_models():
    """Test Pydantic models"""
    print("\n🧪 Testing Pydantic Models...")
    
    try:
        from app.models.aml_models import TxnEvent, RiskLabel, Enrichment, EscalationDecision, ReportDoc
        
        # Test TxnEvent
        txn = TxnEvent(
            transaction_id="TEST_001",
            timestamp=datetime.now(),
            customer_id="CUST_001",
            amount=1000.0,
            currency="USD",
            transaction_type="TRANSFER",
            location="New York",
            country="US",
            description="Test transaction"
        )
        
        # Test RiskLabel
        risk = RiskLabel(risk_level="High", score=0.8, reason="Test risk")
        
        # Test Enrichment
        enrichment = Enrichment(customer_id="CUST_001", pep_flag=True)
        
        # Test EscalationDecision
        escalation = EscalationDecision(create_case=True, severity="High", reason="Test escalation")
        
        # Test ReportDoc
        report = ReportDoc(
            title="Test Report",
            summary="Test summary",
            indicators=["Indicator 1", "Indicator 2"],
            counterparty_context="Test counterparty",
            timeline=["Event 1", "Event 2"],
            recommendation="Test recommendation"
        )
        
        print(f"✅ All models created successfully:")
        print(f"  - TxnEvent: {txn.transaction_id}")
        print(f"  - RiskLabel: {risk.risk_level}")
        print(f"  - Enrichment: PEP={enrichment.pep_flag}")
        print(f"  - EscalationDecision: {escalation.create_case}")
        print(f"  - ReportDoc: {report.title}")
        
        return True
        
    except Exception as e:
        print(f"❌ Models test failed: {str(e)}")
        return False


def test_data_loader():
    """Test AML data loader"""
    print("\n🧪 Testing AML Data Loader...")
    
    try:
        from app.utils.aml_data_loader import AMLDataLoader
        
        loader = AMLDataLoader()
        
        # Test loading different datasets
        alerts_df = loader.load_alerts(limit=5)
        customers_df = loader.load_customers()
        hi_trans_df = loader.load_hi_trans_batch(batch_size=5)
        
        print(f"✅ AML Data Loader test passed:")
        print(f"  - Alerts: {len(alerts_df)} records")
        print(f"  - Customers: {len(customers_df)} records")
        print(f"  - HI-Small_Trans: {len(hi_trans_df)} records")
        
        return True
        
    except Exception as e:
        print(f"❌ AML Data Loader test failed: {str(e)}")
        return False


def test_report_exporter():
    """Test report export functionality"""
    print("\n🧪 Testing Report Exporter...")
    
    try:
        from app.services.report_exporter import ReportExporter
        
        exporter = ReportExporter()
        print("✅ Report exporter initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Report exporter test failed: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("🚀 Simple AML System Test Suite")
    print("=" * 50)
    
    tests = [
        ("Data Loading", test_data_loading),
        ("Rule Engine", test_rule_engine),
        ("Pydantic Models", test_models),
        ("AML Data Loader", test_data_loader),
        ("Report Exporter", test_report_exporter)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 Test Results Summary:")
    print("=" * 30)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Core AML system is working.")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
