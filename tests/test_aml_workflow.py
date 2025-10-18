"""
Test Suite for AML Multi-Agent Workflow

This module contains comprehensive tests for the AML investigation system,
including workflow execution, Human-in-the-Loop approval, batch processing,
and accuracy metrics evaluation.
"""

import pytest
import asyncio
import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Import AML system components
from app.models.aml_models import TxnEvent, Enrichment, AMLState
from app.agents.aml_workflow import run_aml_investigation, aml_workflow
from app.agents.tools.rule_engine import score_rules, normalize_rule_score
from app.agents.tools.hitl_tools_simple import approval_workflow_manager
from app.utils.aml_data_loader import AMLDataLoader
from app.services.batch_processor import batch_processor, run_hi_trans_demo
from app.services.report_exporter import report_exporter
from app.utils.accuracy_metrics import calculate_aml_accuracy, metrics_calculator


class TestRuleEngine:
    """Test rule-based scoring engine"""
    
    def test_score_rules_basic(self):
        """Test basic rule scoring functionality"""
        txn = TxnEvent(
            transaction_id="TEST_001",
            timestamp=datetime.now(),
            customer_id="CUST_001",
            amount=9500.0,
            currency="USD",
            transaction_type="wire",
            location="Unknown",
            country="US",
            description="Test transaction",
            c_txn_7d=5,
            kw_flag=1
        )
        
        result = score_rules(txn)
        
        assert "points" in result
        assert "base_level" in result
        assert "reasons" in result
        assert result["base_level"] in ["Low", "Medium", "High", "Critical"]
        assert result["points"] >= 0
    
    def test_score_rules_high_amount(self):
        """Test scoring for high amount transactions"""
        txn = TxnEvent(
            transaction_id="TEST_002",
            timestamp=datetime.now(),
            customer_id="CUST_002",
            amount=250000.0,  # High amount
            currency="USD",
            transaction_type="wire",
            location="Unknown",
            country="US",
            description="High value transaction"
        )
        
        result = score_rules(txn)
        
        assert result["points"] > 0
        assert any("Critical value" in reason for reason in result["reasons"])
    
    def test_score_rules_high_risk_country(self):
        """Test scoring for high-risk country transactions"""
        txn = TxnEvent(
            transaction_id="TEST_003",
            timestamp=datetime.now(),
            customer_id="CUST_003",
            amount=5000.0,
            currency="USD",
            transaction_type="wire",
            location="Unknown",
            country="IR",  # High-risk country
            description="Iran transaction"
        )
        
        result = score_rules(txn)
        
        assert result["points"] > 0
        assert any("HIGH_RISK_JURISDICTION_IR" in reason for reason in result["reasons"])
    
    def test_score_rules_with_enrichment(self):
        """Test scoring with customer enrichment data"""
        txn = TxnEvent(
            transaction_id="TEST_004",
            timestamp=datetime.now(),
            customer_id="CUST_004",
            amount=15000.0,
            currency="USD",
            transaction_type="wire",
            location="Unknown",
            country="US",
            description="Test transaction"
        )
        
        enrichment = Enrichment(
            customer_id="CUST_004",
            customer_type="CRIM",  # Criminal entity
            pep_flag=True,
            country_risk="High",
            prior_alerts_90d=3
        )
        
        result = score_rules(txn, enrichment)
        
        assert result["points"] > 0
        assert any("Known criminal entity" in reason for reason in result["reasons"])
        assert any("PEP" in reason for reason in result["reasons"])
    
    def test_normalize_rule_score(self):
        """Test rule score normalization"""
        rule_result = {
            "points": 8,
            "max_possible_points": 20
        }
        
        normalized = normalize_rule_score(rule_result)
        
        assert 0.0 <= normalized <= 1.0
        assert normalized == 0.4  # 8/20


class TestAMLWorkflow:
    """Test AML workflow execution"""
    
    @pytest.fixture
    def sample_transaction(self):
        """Sample transaction data for testing"""
        return {
            "transaction_id": "TXN_TEST_001",
            "timestamp": datetime.now(),
            "customer_id": "CUST_TEST_001",
            "amount": 50000.0,
            "currency": "USD",
            "transaction_type": "wire",
            "location": "New York",
            "country": "US",
            "description": "Test transaction for workflow",
            "amount_z": 1.5,
            "c_txn_7d": 3,
            "kw_flag": 0
        }
    
    @pytest.fixture
    def sample_customer(self):
        """Sample customer data for testing"""
        return {
            "customer_id": "CUST_TEST_001",
            "customer_name": "Test Customer",
            "customer_type": "LEG",
            "risk_level": "medium",
            "kyc_status": "verified",
            "location": "New York",
            "country": "US",
            "kyc_documents": ["passport.pdf", "utility_bill.pdf"]
        }
    
    @pytest.mark.asyncio
    async def test_aml_investigation_basic(self, sample_transaction, sample_customer):
        """Test basic AML investigation workflow"""
        # Enable mock approval
        approval_workflow_manager.enable_mock_mode(auto_approve_threshold=70)
        
        result = await run_aml_investigation(
            transaction_data=sample_transaction,
            customer_data=sample_customer
        )
        
        # Verify basic structure
        assert "case_id" in result
        assert "risk_level" in result
        assert "risk_score" in result
        assert "decision_path" in result
        assert "approval_status" in result
        
        # Verify risk level is valid
        assert result["risk_level"] in ["Low", "Medium", "High", "Critical"]
        
        # Verify decision path contains expected steps
        decision_path = result["decision_path"]
        assert "initial_screening" in decision_path
    
    @pytest.mark.asyncio
    async def test_aml_investigation_high_risk(self):
        """Test AML investigation for high-risk transaction"""
        high_risk_transaction = {
            "transaction_id": "TXN_HIGH_RISK",
            "timestamp": datetime.now(),
            "customer_id": "CUST_HIGH_RISK",
            "amount": 200000.0,
            "currency": "USD",
            "transaction_type": "wire",
            "location": "Tehran",
            "country": "IR",  # High-risk country
            "description": "High-risk transaction"
        }
        
        high_risk_customer = {
            "customer_id": "CUST_HIGH_RISK",
            "customer_name": "Minister Test",
            "customer_type": "gov",
            "risk_level": "high",
            "kyc_status": "verified",
            "location": "Tehran",
            "country": "IR"
        }
        
        # Enable mock approval
        approval_workflow_manager.enable_mock_mode(auto_approve_threshold=70)
        
        result = await run_aml_investigation(
            transaction_data=high_risk_transaction,
            customer_data=high_risk_customer
        )
        
        # Should result in high risk
        assert result["risk_level"] in ["High", "Critical"]
        assert result["risk_score"] >= 65
        
        # Should trigger approval or SAR
        assert result["approval_status"] in ["approved", "pending", "not_required"]
    
    @pytest.mark.asyncio
    async def test_aml_investigation_workflow_nodes(self, sample_transaction, sample_customer):
        """Test that all workflow nodes are executed"""
        approval_workflow_manager.enable_mock_mode(auto_approve_threshold=70)
        
        result = await run_aml_investigation(
            transaction_data=sample_transaction,
            customer_data=sample_customer
        )
        
        decision_path = result["decision_path"]
        
        # Verify key nodes are present
        assert "initial_screening" in decision_path
        assert any(node in decision_path for node in ["geo_analysis", "document_check"])
        assert "score_risk" in decision_path


class TestHumanInTheLoop:
    """Test Human-in-the-Loop approval functionality"""
    
    def test_mock_approval_node(self):
        """Test mock approval node functionality"""
        mock_node = MockHumanApprovalNode(auto_approve_threshold=70, approval_delay=0.01)
        
        # Test should_require_approval
        high_risk_state = {
            "risk_score": 80,
            "sanction_hits": [],
            "pep_status": False
        }
        
        assert mock_node.should_require_approval(high_risk_state)
        
        low_risk_state = {
            "risk_score": 30,
            "sanction_hits": [],
            "pep_status": False
        }
        
        assert not mock_node.should_require_approval(low_risk_state)
    
    @pytest.mark.asyncio
    async def test_mock_approval_workflow(self):
        """Test mock approval workflow"""
        mock_node = MockHumanApprovalNode(auto_approve_threshold=70)
        
        # High risk state should be auto-approved
        high_risk_state = {
            "case_id": "CASE_001",
            "risk_score": 80,
            "risk_level": "High",
            "transaction": {"amount": 100000},
            "risk_factors": ["Large amount"],
            "approval_status": None
        }
        
        result = await mock_node.request_approval(high_risk_state)
        
        assert result["approval_status"] == "approved"
        assert result["approval_metadata"]["decision"] == "approved"
    
    def test_approval_workflow_manager(self):
        """Test approval workflow manager"""
        manager = approval_workflow_manager
        
        # Enable mock mode
        manager.enable_mock_mode(auto_approve_threshold=70)
        
        # Get dashboard data
        dashboard = manager.get_approval_dashboard_data()
        
        assert "pending_approvals" in dashboard
        assert "stats" in dashboard
        assert "mock_mode" in dashboard
        assert dashboard["mock_mode"] is True


class TestBatchProcessing:
    """Test batch processing functionality"""
    
    @pytest.mark.asyncio
    async def test_hi_trans_demo(self):
        """Test HI-Small_Trans demo processing"""
        # Mock the data loader to avoid file dependencies
        with patch('app.services.batch_processor.data_loader') as mock_loader:
            # Create mock data
            mock_data = {
                'Timestamp': [datetime.now()] * 10,
                'Account': [f'ACC_{i}' for i in range(10)],
                'Amount Received': [5000 + i * 1000 for i in range(10)],
                'Receiving Currency': ['USD'] * 10,
                'Payment Format': ['Wire'] * 10,
                'Is Laundering': [0, 1, 0, 1, 0, 0, 1, 0, 0, 1]
            }
            mock_df = Mock()
            mock_df.__len__ = Mock(return_value=10)
            mock_df.iloc = Mock()
            mock_df.iterrows = Mock(return_value=enumerate([
                Mock(**{k: v[i] for k, v in mock_data.items()}) 
                for i in range(10)
            ]))
            
            mock_loader.load_hi_trans_batch.return_value = mock_df
            mock_loader.engineer_features.return_value = mock_df
            mock_loader.make_txn_event.return_value = TxnEvent(
                transaction_id="TEST",
                timestamp=datetime.now(),
                customer_id="TEST",
                amount=5000,
                currency="USD",
                transaction_type="wire",
                location="Unknown",
                country="US",
                description="Test"
            )
            
            # Enable mock approval
            approval_workflow_manager.enable_mock_mode(auto_approve_threshold=70)
            
            # Run demo
            results = await run_hi_trans_demo(batch_size=10, max_batches=1)
            
            # Verify results structure
            assert "results" in results
            assert "summary" in results
            assert "stats" in results
            
            # Verify summary structure
            summary = results["summary"]
            assert "total_transactions" in summary
            assert "escalated_cases" in summary
            assert "processing_time" in summary


class TestReportGeneration:
    """Test report generation functionality"""
    
    @pytest.fixture
    def sample_investigation_results(self):
        """Sample investigation results for testing"""
        return [
            {
                "case_id": "CASE_001",
                "risk_level": "High",
                "risk_score": 75,
                "reporting_status": "SAR_FILED",
                "transaction": {
                    "amount": 100000,
                    "currency": "USD",
                    "type": "wire"
                },
                "customer": {
                    "customer_id": "CUST_001",
                    "customer_name": "Test Customer"
                }
            },
            {
                "case_id": "CASE_002",
                "risk_level": "Medium",
                "risk_score": 45,
                "reporting_status": "REVIEW_COMPLETED",
                "transaction": {
                    "amount": 25000,
                    "currency": "USD",
                    "type": "ach"
                },
                "customer": {
                    "customer_id": "CUST_002",
                    "customer_name": "Test Customer 2"
                }
            }
        ]
    
    @pytest.mark.asyncio
    async def test_json_report_export(self, sample_investigation_results):
        """Test JSON report export"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set custom output directory
            original_output_dir = report_exporter.output_dir
            report_exporter.output_dir = Path(temp_dir)
            
            try:
                filepath = await report_exporter.export_json(
                    sample_investigation_results, 
                    "test_report.json"
                )
                
                assert Path(filepath).exists()
                
                # Verify file content
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                assert len(data) == 2
                assert data[0]["case_id"] == "CASE_001"
                
            finally:
                report_exporter.output_dir = original_output_dir
    
    @pytest.mark.asyncio
    async def test_csv_report_export(self, sample_investigation_results):
        """Test CSV report export"""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_output_dir = report_exporter.output_dir
            report_exporter.output_dir = Path(temp_dir)
            
            try:
                filepath = await report_exporter.export_csv(
                    sample_investigation_results, 
                    "test_report.csv"
                )
                
                assert Path(filepath).exists()
                
                # Verify CSV can be read
                import pandas as pd
                df = pd.read_csv(filepath)
                assert len(df) == 2
                assert "case_id" in df.columns
                
            finally:
                report_exporter.output_dir = original_output_dir
    
    @pytest.mark.asyncio
    async def test_markdown_report_export(self, sample_investigation_results):
        """Test Markdown report export"""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_output_dir = report_exporter.output_dir
            report_exporter.output_dir = Path(temp_dir)
            
            try:
                filepath = await report_exporter.export_markdown(
                    sample_investigation_results, 
                    "test_report.md"
                )
                
                assert Path(filepath).exists()
                
                # Verify markdown content
                with open(filepath, 'r') as f:
                    content = f.read()
                
                assert "# AML Investigation Report" in content
                assert "CASE_001" in content
                
            finally:
                report_exporter.output_dir = original_output_dir


class TestAccuracyMetrics:
    """Test accuracy metrics calculation"""
    
    def test_basic_metrics_calculation(self):
        """Test basic accuracy metrics calculation"""
        ground_truth = [0, 1, 0, 1, 1, 0, 0, 1]
        predictions = [0, 1, 1, 1, 0, 0, 0, 1]
        
        metrics = metrics_calculator.calculate_basic_metrics(ground_truth, predictions)
        
        assert "accuracy" in metrics
        assert "precision" in metrics
        assert "recall" in metrics
        assert "f1_score" in metrics
        
        # Verify metrics are valid
        assert 0.0 <= metrics["accuracy"] <= 1.0
        assert 0.0 <= metrics["precision"] <= 1.0
        assert 0.0 <= metrics["recall"] <= 1.0
        assert 0.0 <= metrics["f1_score"] <= 1.0
    
    def test_financial_metrics_calculation(self):
        """Test financial metrics calculation"""
        ground_truth = [0, 1, 0, 1, 1, 0]
        predictions = [0, 1, 1, 1, 0, 0]
        amounts = [1000, 50000, 2000, 75000, 30000, 1500]
        
        metrics = metrics_calculator.calculate_financial_metrics(
            ground_truth, predictions, amounts
        )
        
        assert "detected_laundering_amount" in metrics
        assert "missed_laundering_amount" in metrics
        assert "detection_rate_by_amount" in metrics
        
        # Verify financial metrics make sense
        assert metrics["detected_laundering_amount"] >= 0
        assert metrics["missed_laundering_amount"] >= 0
        assert 0.0 <= metrics["detection_rate_by_amount"] <= 1.0
    
    def test_risk_score_metrics(self):
        """Test risk score based metrics"""
        ground_truth = [0, 1, 0, 1, 1, 0]
        risk_scores = [20, 85, 45, 75, 90, 25]
        
        metrics = metrics_calculator.calculate_risk_score_metrics(
            ground_truth, risk_scores
        )
        
        assert "threshold_70" in metrics
        assert "threshold_80" in metrics
        assert "roc_auc" in metrics
        
        # Verify threshold metrics structure
        threshold_70 = metrics["threshold_70"]
        assert "accuracy" in threshold_70
        assert "precision" in threshold_70
    
    def test_comprehensive_metrics(self):
        """Test comprehensive metrics calculation"""
        ground_truth = [0, 1, 0, 1, 1, 0]
        predictions = [0, 1, 1, 1, 0, 0]
        risk_scores = [20, 85, 45, 75, 90, 25]
        amounts = [1000, 50000, 2000, 75000, 30000, 1500]
        
        investigation_costs = {
            "investigation_cost": 100,
            "sar_filing_cost": 500,
            "missed_laundering_penalty": 10000
        }
        
        metrics = metrics_calculator.calculate_comprehensive_metrics(
            ground_truth=ground_truth,
            predictions=predictions,
            risk_scores=risk_scores,
            amounts=amounts,
            investigation_costs=investigation_costs
        )
        
        assert "basic_metrics" in metrics
        assert "financial_metrics" in metrics
        assert "risk_score_metrics" in metrics
        assert "business_metrics" in metrics
        
        # Verify all metric categories have data
        assert len(metrics["basic_metrics"]) > 0
        assert len(metrics["financial_metrics"]) > 0
        assert len(metrics["risk_score_metrics"]) > 0
        assert len(metrics["business_metrics"]) > 0


class TestDataLoader:
    """Test data loading functionality"""
    
    def test_make_txn_event_operational(self):
        """Test TxnEvent creation from operational data"""
        # Mock operational transaction data
        row_data = {
            'transaction_id': 'TXN_001',
            'transaction_date': '2024-01-01',
            'customer_id': 'CUST_001',
            'amount': 10000.0,
            'currency': 'USD',
            'transaction_type': 'wire',
            'location': 'New York',
            'country': 'US',
            'description': 'Test transaction'
        }
        
        row = Mock()
        for key, value in row_data.items():
            setattr(row, key, value)
        
        loader = AMLDataLoader()
        txn_event = loader.make_txn_event(row)
        
        assert txn_event.transaction_id == 'TXN_001'
        assert txn_event.amount == 10000.0
        assert txn_event.currency == 'USD'
    
    def test_make_txn_event_hi_trans(self):
        """Test TxnEvent creation from HI-Small_Trans data"""
        # Mock HI-Small_Trans data
        row_data = {
            'name': 0,  # Row index
            'Timestamp': '2024-01-01 10:00:00',
            'Account': 'ACC_001',
            'Amount Received': 15000.0,
            'Receiving Currency': 'USD',
            'Payment Format': 'Wire',
            'Is Laundering': 1,
            'amount_z': 1.2,
            'c_txn_7d': 3,
            'kw_flag': 0
        }
        
        row = Mock()
        for key, value in row_data.items():
            setattr(row, key, value)
        
        loader = AMLDataLoader()
        txn_event = loader.make_txn_event(row)
        
        assert txn_event.transaction_id == 'HI_0'
        assert txn_event.amount == 15000.0
        assert txn_event.is_laundering == 1
        assert txn_event.payment_format == 'Wire'


# Integration Tests
class TestAMLIntegration:
    """Integration tests for the complete AML system"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test complete end-to-end AML workflow"""
        # Sample high-risk transaction
        transaction_data = {
            "transaction_id": "TXN_E2E_TEST",
            "timestamp": datetime.now(),
            "customer_id": "CUST_E2E",
            "amount": 150000.0,
            "currency": "USD",
            "transaction_type": "wire",
            "location": "Dubai",
            "country": "AE",  # Tax haven
            "description": "End-to-end test transaction",
            "amount_z": 2.5,
            "c_txn_7d": 8,
            "kw_flag": 1
        }
        
        customer_data = {
            "customer_id": "CUST_E2E",
            "customer_name": "Test Minister",
            "customer_type": "gov",
            "risk_level": "high",
            "kyc_status": "verified",
            "location": "Dubai",
            "country": "AE",
            "kyc_documents": ["passport.pdf"]
        }
        
        # Enable mock approval
        approval_workflow_manager.enable_mock_mode(auto_approve_threshold=70)
        
        # Run investigation
        result = await run_aml_investigation(
            transaction_data=transaction_data,
            customer_data=customer_data
        )
        
        # Verify complete workflow execution
        assert result["case_id"] is not None
        assert result["risk_level"] in ["High", "Critical"]
        assert result["risk_score"] >= 65
        assert len(result["decision_path"]) > 3
        
        # Verify risk factors were identified
        assert len(result["risk_factors"]) > 0
        
        # Verify approval workflow
        assert result["approval_status"] in ["approved", "pending", "not_required"]
    
    def test_accuracy_calculation_integration(self):
        """Test accuracy calculation with real-like data"""
        # Simulate investigation results with ground truth
        results = [
            {
                "ground_truth": 1,
                "prediction": 1,
                "risk_score": 85,
                "transaction": {"amount": 100000}
            },
            {
                "ground_truth": 0,
                "prediction": 1,
                "risk_score": 75,
                "transaction": {"amount": 50000}
            },
            {
                "ground_truth": 1,
                "prediction": 0,
                "risk_score": 45,
                "transaction": {"amount": 75000}
            },
            {
                "ground_truth": 0,
                "prediction": 0,
                "risk_score": 25,
                "transaction": {"amount": 25000}
            }
        ]
        
        # Calculate accuracy metrics
        metrics = calculate_aml_accuracy(results)
        
        # Verify metrics structure
        assert "basic_metrics" in metrics
        assert "financial_metrics" in metrics
        assert "risk_score_metrics" in metrics
        assert "business_metrics" in metrics
        
        # Verify basic metrics
        basic = metrics["basic_metrics"]
        assert basic["accuracy"] == 0.5  # 2 out of 4 correct
        assert basic["precision"] == 0.5  # 1 out of 2 positive predictions correct
        assert basic["recall"] == 0.5  # 1 out of 2 actual positives detected


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
