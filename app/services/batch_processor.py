"""
AML Batch Processor

This service handles batch processing of both operational alerts and HI-Small_Trans
dataset for large-scale AML investigation with progress tracking and accuracy metrics.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
from app.core.logger import get_logger
from app.models.aml_models import BatchProcessingResult, InvestigationSummary
from app.agents.aml_workflow import aml_workflow, run_aml_investigation
from app.utils.aml_data_loader import AMLDataLoader
from app.agents.tools.hitl_tools_simple import approval_workflow_manager

logger = get_logger(__name__)


class AMLBatchProcessor:
    """
    Batch processor for AML investigations across multiple datasets
    """
    
    def __init__(self):
        self.data_loader = AMLDataLoader()
        self.workflow = aml_workflow
        self.results = []
        self.processing_stats = {
            "total_processed": 0,
            "escalated_cases": 0,
            "sar_cases": 0,
            "pending_approvals": 0,
            "errors": 0
        }
    
    async def process_operational_alerts(self, 
                                       limit: Optional[int] = None,
                                       enable_mock_approval: bool = True) -> List[Dict[str, Any]]:
        """
        Process alerts from operational system (data/raw/)
        
        Args:
            limit: Optional limit on number of alerts to process
            enable_mock_approval: Enable mock approval for testing
            
        Returns:
            List of investigation results
        """
        logger.info(f"Starting operational alerts processing (limit: {limit})")
        
        if enable_mock_approval:
            approval_workflow_manager.enable_mock_mode(auto_approve_threshold=70)
        
        # Load alerts
        alerts_df = self.data_loader.load_alerts(limit=limit)
        
        if alerts_df.empty:
            logger.warning("No alerts found to process")
            return []
        
        results = []
        start_time = time.time()
        
        for idx, alert_row in alerts_df.iterrows():
            try:
                alert_id = alert_row['alert_id']
                
                # Load related data
                alert, transaction, customer = self.data_loader.load_operational_alert(alert_id)
                
                if not all([alert, transaction, customer]):
                    logger.error(f"Missing data for alert {alert_id}")
                    self.processing_stats["errors"] += 1
                    continue
                
                # Run investigation
                result = await run_aml_investigation(
                    transaction_data=transaction,
                    customer_data=customer,
                    alert_id=alert_id
                )
                
                # Track statistics
                self._update_stats(result)
                
                # Create investigation summary
                summary = InvestigationSummary(
                    investigation_id=f"INV_{alert_id}",
                    alert_id=alert_id,
                    transaction_id=transaction.get('transaction_id', 'unknown'),
                    customer_id=customer.get('customer_id', 'unknown'),
                    risk_level=result.get('risk_level', 'Unknown'),
                    risk_score=result.get('risk_score', 0),
                    escalation_required=result.get('reporting_status') == 'SAR_FILED',
                    sar_filed=result.get('reporting_status') == 'SAR_FILED',
                    approval_status=result.get('approval_status'),
                    created_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                    execution_time=time.time() - start_time
                )
                
                result['summary'] = summary.model_dump()
                results.append(result)
                
                logger.info(f"Processed alert {alert_id} - Risk: {result.get('risk_level')}")
                
            except Exception as e:
                logger.error(f"Error processing alert {alert_row.get('alert_id', 'unknown')}: {str(e)}")
                self.processing_stats["errors"] += 1
        
        processing_time = time.time() - start_time
        
        logger.info(f"Operational alerts processing completed: {len(results)} results in {processing_time:.2f}s")
        return results
    
    async def process_hi_trans_batch(self, 
                                   batch_size: int = 1000,
                                   offset: int = 0,
                                   max_batches: Optional[int] = None,
                                   enable_mock_approval: bool = True) -> List[Dict[str, Any]]:
        """
        Process HI-Small_Trans.csv in batches
        
        Args:
            batch_size: Number of transactions per batch
            offset: Starting offset
            max_batches: Maximum number of batches to process
            enable_mock_approval: Enable mock approval for testing
            
        Returns:
            List of investigation results
        """
        logger.info(f"Starting HI-Small_Trans batch processing (batch_size: {batch_size}, offset: {offset})")
        
        if enable_mock_approval:
            approval_workflow_manager.enable_mock_mode(auto_approve_threshold=70)
        
        all_results = []
        batch_count = 0
        total_processed = 0
        
        start_time = time.time()
        
        while True:
            if max_batches and batch_count >= max_batches:
                break
            
            # Load batch
            df = self.data_loader.load_hi_trans_batch(batch_size, offset + (batch_count * batch_size))
            
            if df.empty:
                logger.info("No more data to process")
                break
            
            # Engineer features
            df = self.data_loader.engineer_features(df)
            
            # Process batch
            batch_results = await self._process_hi_trans_batch(df, batch_count)
            all_results.extend(batch_results)
            
            batch_count += 1
            total_processed += len(df)
            
            logger.info(f"Completed batch {batch_count}: {len(df)} transactions")
            
            # Break if we got less than batch_size (end of data)
            if len(df) < batch_size:
                break
        
        processing_time = time.time() - start_time
        
        logger.info(f"HI-Small_Trans batch processing completed: {total_processed} transactions in {processing_time:.2f}s")
        return all_results
    
    async def _process_hi_trans_batch(self, df: pd.DataFrame, batch_num: int) -> List[Dict[str, Any]]:
        """
        Process a single batch of HI-Small_Trans data
        
        Args:
            df: DataFrame with batch data
            batch_num: Batch number for logging
            
        Returns:
            List of investigation results
        """
        results = []
        
        for idx, row in df.iterrows():
            try:
                # Convert to TxnEvent
                txn_event = self.data_loader.make_txn_event(row)
                
                # Create mock customer data
                customer_data = {
                    "customer_id": txn_event.customer_id,
                    "customer_name": f"Account_{txn_event.customer_id}",
                    "customer_type": "LEG",  # Default to legitimate
                    "risk_level": "low",
                    "kyc_status": "verified",
                    "location": "Unknown",
                    "country": "US",
                    "kyc_documents": []
                }
                
                # Run investigation
                result = await run_aml_investigation(
                    transaction_data=txn_event.model_dump(),
                    customer_data=customer_data,
                    config={"configurable": {"thread_id": f"batch_{batch_num}_{idx}"}}
                )
                
                # Add ground truth for accuracy calculation
                result["ground_truth"] = row.get("Is Laundering", 0)
                result["prediction"] = 1 if result.get('risk_level') in ['High', 'Critical'] else 0
                
                # Track statistics
                self._update_stats(result)
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error processing HI-Small_Trans row {idx}: {str(e)}")
                self.processing_stats["errors"] += 1
        
        return results
    
    def _update_stats(self, result: Dict[str, Any]):
        """Update processing statistics"""
        self.processing_stats["total_processed"] += 1
        
        risk_level = result.get("risk_level", "Low")
        reporting_status = result.get("reporting_status", "")
        
        if risk_level in ["High", "Critical"]:
            self.processing_stats["escalated_cases"] += 1
        
        if reporting_status == "SAR_FILED":
            self.processing_stats["sar_cases"] += 1
        
        if result.get("approval_status") == "pending":
            self.processing_stats["pending_approvals"] += 1
    
    def calculate_accuracy_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate accuracy metrics for batch processing results
        
        Args:
            results: List of investigation results with ground truth
            
        Returns:
            Dictionary with accuracy metrics
        """
        if not results:
            return {}
        
        # Filter results with ground truth
        valid_results = [r for r in results if "ground_truth" in r and "prediction" in r]
        
        if not valid_results:
            logger.warning("No results with ground truth found for accuracy calculation")
            return {}
        
        # Extract predictions and ground truth
        predictions = [r["prediction"] for r in valid_results]
        ground_truth = [r["ground_truth"] for r in valid_results]
        
        # Calculate metrics
        true_positives = sum(1 for p, gt in zip(predictions, ground_truth) if p == 1 and gt == 1)
        false_positives = sum(1 for p, gt in zip(predictions, ground_truth) if p == 1 and gt == 0)
        true_negatives = sum(1 for p, gt in zip(predictions, ground_truth) if p == 0 and gt == 0)
        false_negatives = sum(1 for p, gt in zip(predictions, ground_truth) if p == 0 and gt == 1)
        
        # Calculate rates
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        accuracy = (true_positives + true_negatives) / len(valid_results) if valid_results else 0
        
        metrics = {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "true_positives": true_positives,
            "false_positives": false_positives,
            "true_negatives": true_negatives,
            "false_negatives": false_negatives,
            "total_samples": len(valid_results)
        }
        
        logger.info(f"Accuracy metrics calculated: F1={f1_score:.3f}, Precision={precision:.3f}, Recall={recall:.3f}")
        return metrics
    
    def create_batch_summary(self, results: List[Dict[str, Any]], 
                           processing_time: float) -> BatchProcessingResult:
        """
        Create batch processing summary
        
        Args:
            results: List of investigation results
            processing_time: Total processing time in seconds
            
        Returns:
            BatchProcessingResult object
        """
        # Calculate accuracy metrics
        accuracy_metrics = self.calculate_accuracy_metrics(results)
        
        # Count escalated cases
        escalated_cases = sum(1 for r in results if r.get('risk_level') in ['High', 'Critical'])
        sar_cases = sum(1 for r in results if r.get('reporting_status') == 'SAR_FILED')
        pending_approvals = len(approval_workflow_manager.pending_approvals)
        
        return BatchProcessingResult(
            batch_id=f"BATCH_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            total_transactions=len(results),
            processed_transactions=self.processing_stats["total_processed"],
            escalated_cases=escalated_cases,
            sar_cases=sar_cases,
            pending_approvals=pending_approvals,
            accuracy_metrics=accuracy_metrics,
            processing_time=processing_time,
            created_at=datetime.utcnow()
        )
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get current processing statistics"""
        return self.processing_stats.copy()
    
    def reset_stats(self):
        """Reset processing statistics"""
        self.processing_stats = {
            "total_processed": 0,
            "escalated_cases": 0,
            "sar_cases": 0,
            "pending_approvals": 0,
            "errors": 0
        }
        logger.info("Processing statistics reset")
    
    async def process_with_progress_tracking(self, 
                                           dataset: str,
                                           **kwargs) -> Tuple[List[Dict[str, Any]], BatchProcessingResult]:
        """
        Process dataset with progress tracking
        
        Args:
            dataset: Dataset to process ("operational" or "hi_trans")
            **kwargs: Additional arguments for processing
            
        Returns:
            Tuple of (results, summary)
        """
        start_time = time.time()
        
        try:
            if dataset == "operational":
                results = await self.process_operational_alerts(**kwargs)
            elif dataset == "hi_trans":
                results = await self.process_hi_trans_batch(**kwargs)
            else:
                raise ValueError(f"Unknown dataset: {dataset}")
            
            processing_time = time.time() - start_time
            summary = self.create_batch_summary(results, processing_time)
            
            return results, summary
            
        except Exception as e:
            logger.error(f"Batch processing failed: {str(e)}")
            raise


# Global batch processor instance
batch_processor = AMLBatchProcessor()


async def run_operational_demo(limit: int = 5) -> Dict[str, Any]:
    """
    Run operational alerts demo
    
    Args:
        limit: Number of alerts to process
        
    Returns:
        Demo results
    """
    logger.info(f"Running operational demo with {limit} alerts")
    
    results, summary = await batch_processor.process_with_progress_tracking(
        dataset="operational",
        limit=limit,
        enable_mock_approval=True
    )
    
    return {
        "results": results,
        "summary": summary.model_dump(),
        "stats": batch_processor.get_processing_stats()
    }


async def run_hi_trans_demo(batch_size: int = 100, max_batches: int = 2) -> Dict[str, Any]:
    """
    Run HI-Small_Trans demo
    
    Args:
        batch_size: Transactions per batch
        max_batches: Maximum batches to process
        
    Returns:
        Demo results
    """
    logger.info(f"Running HI-Small_Trans demo: {batch_size} per batch, max {max_batches} batches")
    
    results, summary = await batch_processor.process_with_progress_tracking(
        dataset="hi_trans",
        batch_size=batch_size,
        max_batches=max_batches,
        enable_mock_approval=True
    )
    
    return {
        "results": results,
        "summary": summary.model_dump(),
        "stats": batch_processor.get_processing_stats()
    }
