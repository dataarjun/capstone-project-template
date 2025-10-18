"""
Test AML System

Simple test script to verify the AML system components work correctly
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from app.core.logger import get_logger
from scripts.load_aml_data import AMLDataManager
from app.utils.aml_data_loader import AMLDataLoader
from app.agents.tools.rule_engine import score_rules
from app.models.aml_models import TxnEvent

logger = get_logger(__name__)


def test_data_loading():
    """Test data loading functionality"""
    print("🧪 Testing Data Loading...")
    
    try:
        # Test AMLDataManager
        data_manager = AMLDataManager()
        operational_summary = data_manager.get_operational_summary()
        hi_trans_summary = data_manager.get_hi_trans_summary()
        
        print(f"✅ AMLDataManager loaded:")
        print(f"  - Operational data: {len(operational_summary)} datasets")
        print(f"  - HI-Small_Trans: {hi_trans_summary.get('total_records', 0)} records")
        
        # Test AMLDataLoader
        data_loader = AMLDataLoader()
        alerts_df = data_loader.load_alerts(limit=5)
        customers_df = data_loader.load_customers()
        transactions_df = data_loader.load_transactions()
        hi_trans_df = data_loader.load_hi_small_trans(limit=5)
        
        print(f"✅ AMLDataLoader loaded:")
        print(f"  - Alerts: {len(alerts_df)} records")
        print(f"  - Customers: {len(customers_df)} records")
        print(f"  - Transactions: {len(transactions_df)} records")
        print(f"  - HI-Small_Trans: {len(hi_trans_df)} records")
        
        return True
        
    except Exception as e:
        print(f"❌ Data loading test failed: {str(e)}")
        return False


def test_rule_engine():
    """Test rule-based scoring engine"""
    print("\n🧪 Testing Rule Engine...")
    
    try:
        # Create test transaction
        test_txn = TxnEvent(
            transaction_id="TEST_001",
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            customer_id="CUST_001",
            amount=15000.0,  # High amount
            currency="USD",
            transaction_type="WIRE_TRANSFER",
            location="New York",
            country="US",
            description="Transfer to offshore account",
            amount_z=2.5,
            c_txn_7d=15,  # High velocity
            kw_flag=1,  # Suspicious keywords
            payment_format="WIRE_TRANSFER"
        )
        
        # Test rule scoring
        rule_result = score_rules(test_txn)
        
        print(f"✅ Rule engine test passed:")
        print(f"  - Transaction: ${test_txn.amount} {test_txn.type}")
        print(f"  - Risk points: {rule_result['points']}")
        print(f"  - Base level: {rule_result['base_level']}")
        print(f"  - Reasons: {rule_result['reasons'][:2]}...")  # Show first 2 reasons
        
        return True
        
    except Exception as e:
        print(f"❌ Rule engine test failed: {str(e)}")
        return False


async def test_aml_workflow():
    """Test AML workflow components"""
    print("\n🧪 Testing AML Workflow...")
    
    try:
        # Test imports
        from app.agents.aml_workflow import build_aml_workflow
        
        # Build workflow
        workflow = build_aml_workflow()
        print("✅ AML workflow built successfully")
        
        # Test individual nodes
        from app.agents.aml_workflow import initial_screening_node, geographic_risk_node
        
        # Create test state
        test_state = {
            "transaction": {
                "transaction_id": "TEST_002",
                "amount": 25000,
                "type": "CRYPTO",
                "origin_country": "US",
                "destination_country": "RU",  # High-risk country
                "parties": ["Exchange A", "Wallet B"]
            },
            "customer": {
                "customer_id": "CUST_002",
                "customer_name": "Test Customer",
                "customer_type": "Individual",
                "risk_level": "medium"
            },
            "risk_score": 0,
            "alerts": [],
            "investigation": {},
            "llm_analysis": {},
            "risk_factors": [],
            "decision_path": [],
            "documents": [],
            "pep_status": None,
            "sanction_hits": [],
            "transaction_count": 1,
            "requires_approval": False,
            "approval_status": None,
            "approval_metadata": {},
            "batch_mode": False
        }
        
        # Test initial screening
        updated_state = await initial_screening_node(test_state)
        print(f"✅ Initial screening completed:")
        print(f"  - Risk score: {updated_state.get('risk_score', 0)}")
        print(f"  - Risk level: {updated_state.get('risk_level', 'Unknown')}")
        print(f"  - Risk factors: {len(updated_state.get('risk_factors', []))}")
        
        # Test geographic risk
        geo_state = await geographic_risk_node(updated_state)
        print(f"✅ Geographic risk analysis completed:")
        print(f"  - Updated risk score: {geo_state.get('risk_score', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ AML workflow test failed: {str(e)}")
        logger.error(f"Workflow test error: {str(e)}")
        return False


def test_report_exporter():
    """Test report export functionality"""
    print("\n🧪 Testing Report Exporter...")
    
    try:
        from app.services.report_exporter import ReportExporter
        
        # Create test report
        test_reports = [
            {
                "case_id": "CASE_001",
                "transaction": {"amount": 15000, "type": "WIRE_TRANSFER"},
                "customer": {"customer_name": "Test Customer"},
                "risk_score": 75,
                "risk_level": "High",
                "investigation": {
                    "sar_report": {
                        "title": "Test SAR Report",
                        "summary": "Test summary",
                        "indicators": ["High amount", "Offshore transfer"],
                        "counterparty_context": "Test counterparty",
                        "timeline": ["2024-01-15: Transaction initiated"],
                        "recommendation": "File SAR"
                    }
                },
                "approval_status": "APPROVED",
                "approval_metadata": {"reviewer": "Test Reviewer"}
            }
        ]
        
        # Test exporter
        exporter = ReportExporter()
        print("✅ Report exporter initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Report exporter test failed: {str(e)}")
        return False


async def main():
    """Run all tests"""
    print("🚀 AML System Test Suite")
    print("=" * 50)
    
    tests = [
        ("Data Loading", test_data_loading),
        ("Rule Engine", test_rule_engine),
        ("AML Workflow", test_aml_workflow),
        ("Report Exporter", test_report_exporter)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
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
        print("🎉 All tests passed! AML system is ready.")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
