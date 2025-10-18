"""
Accuracy Metrics Utilities

This module provides comprehensive accuracy calculation utilities for comparing
AML system predictions against ground truth labels, including precision, recall,
F1 score, confusion matrix, and advanced metrics for financial crime detection.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score, roc_curve
)
import matplotlib.pyplot as plt
import seaborn as sns
from app.core.logger import get_logger

logger = get_logger(__name__)


class AMLMetricsCalculator:
    """
    Comprehensive metrics calculator for AML system performance evaluation
    """
    
    def __init__(self):
        self.metrics_history = []
    
    def calculate_basic_metrics(self, 
                              ground_truth: List[int], 
                              predictions: List[int],
                              labels: Optional[List[str]] = None) -> Dict[str, float]:
        """
        Calculate basic classification metrics
        
        Args:
            ground_truth: Ground truth labels (0/1)
            predictions: Predicted labels (0/1)
            labels: Optional class labels
            
        Returns:
            Dictionary with basic metrics
        """
        if labels is None:
            labels = ["Legitimate", "Laundering"]
        
        # Convert to numpy arrays
        y_true = np.array(ground_truth)
        y_pred = np.array(predictions)
        
        # Calculate basic metrics
        accuracy = accuracy_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred, zero_division=0)
        recall = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        
        # Calculate confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        
        # Extract confusion matrix elements
        tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)
        
        # Calculate additional metrics
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
        sensitivity = recall  # Same as recall
        precision_neg = tn / (tn + fn) if (tn + fn) > 0 else 0
        f1_neg = 2 * (precision_neg * specificity) / (precision_neg + specificity) if (precision_neg + specificity) > 0 else 0
        
        metrics = {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "specificity": specificity,
            "sensitivity": sensitivity,
            "precision_negative": precision_neg,
            "f1_score_negative": f1_neg,
            "true_positives": int(tp),
            "false_positives": int(fp),
            "true_negatives": int(tn),
            "false_negatives": int(fn),
            "total_samples": len(y_true)
        }
        
        logger.info(f"Basic metrics calculated: F1={f1:.3f}, Precision={precision:.3f}, Recall={recall:.3f}")
        return metrics
    
    def calculate_financial_metrics(self, 
                                  ground_truth: List[int], 
                                  predictions: List[int],
                                  amounts: Optional[List[float]] = None) -> Dict[str, Any]:
        """
        Calculate financial crime detection specific metrics
        
        Args:
            ground_truth: Ground truth labels (0/1)
            predictions: Predicted labels (0/1)
            amounts: Optional transaction amounts for weighted metrics
            
        Returns:
            Dictionary with financial metrics
        """
        y_true = np.array(ground_truth)
        y_pred = np.array(predictions)
        
        # Basic metrics
        basic_metrics = self.calculate_basic_metrics(ground_truth, predictions)
        
        # Financial impact metrics
        if amounts is not None:
            amounts = np.array(amounts)
            
            # True positive amounts (correctly detected laundering)
            tp_mask = (y_true == 1) & (y_pred == 1)
            tp_amounts = amounts[tp_mask] if np.any(tp_mask) else np.array([0])
            
            # False negative amounts (missed laundering)
            fn_mask = (y_true == 1) & (y_pred == 0)
            fn_amounts = amounts[fn_mask] if np.any(fn_mask) else np.array([0])
            
            # False positive amounts (false alarms)
            fp_mask = (y_true == 0) & (y_pred == 1)
            fp_amounts = amounts[fp_mask] if np.any(fp_mask) else np.array([0])
            
            financial_metrics = {
                "total_laundering_amount": np.sum(amounts[y_true == 1]),
                "detected_laundering_amount": np.sum(tp_amounts),
                "missed_laundering_amount": np.sum(fn_amounts),
                "false_alarm_amount": np.sum(fp_amounts),
                "detection_rate_by_amount": np.sum(tp_amounts) / np.sum(amounts[y_true == 1]) if np.sum(amounts[y_true == 1]) > 0 else 0,
                "average_laundering_amount_detected": np.mean(tp_amounts) if len(tp_amounts) > 0 else 0,
                "average_laundering_amount_missed": np.mean(fn_amounts) if len(fn_amounts) > 0 else 0
            }
        else:
            financial_metrics = {}
        
        # Combine metrics
        all_metrics = {**basic_metrics, **financial_metrics}
        
        return all_metrics
    
    def calculate_risk_score_metrics(self, 
                                   ground_truth: List[int],
                                   risk_scores: List[float],
                                   thresholds: Optional[List[float]] = None) -> Dict[str, Any]:
        """
        Calculate metrics for risk score based predictions
        
        Args:
            ground_truth: Ground truth labels (0/1)
            risk_scores: Risk scores (0-100)
            thresholds: Optional thresholds to evaluate
            
        Returns:
            Dictionary with threshold-based metrics
        """
        if thresholds is None:
            thresholds = [30, 50, 70, 80, 90]
        
        y_true = np.array(ground_truth)
        scores = np.array(risk_scores)
        
        threshold_metrics = {}
        
        for threshold in thresholds:
            # Convert scores to binary predictions
            y_pred = (scores >= threshold).astype(int)
            
            # Calculate metrics for this threshold
            metrics = self.calculate_basic_metrics(y_true, y_pred)
            threshold_metrics[f"threshold_{threshold}"] = metrics
        
        # Calculate ROC AUC if we have enough positive samples
        if len(np.unique(y_true)) > 1:
            try:
                roc_auc = roc_auc_score(y_true, scores)
                threshold_metrics["roc_auc"] = roc_auc
            except ValueError:
                threshold_metrics["roc_auc"] = 0.5
        
        return threshold_metrics
    
    def calculate_business_metrics(self, 
                                 ground_truth: List[int],
                                 predictions: List[int],
                                 investigation_costs: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate business impact metrics
        
        Args:
            ground_truth: Ground truth labels (0/1)
            predictions: Predicted labels (0/1)
            investigation_costs: Cost dictionary with keys like 'investigation_cost', 'sar_filing_cost'
            
        Returns:
            Dictionary with business metrics
        """
        y_true = np.array(ground_truth)
        y_pred = np.array(predictions)
        
        # Extract confusion matrix elements
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
        
        # Business costs
        investigation_cost = investigation_costs.get('investigation_cost', 100)
        sar_filing_cost = investigation_costs.get('sar_filing_cost', 500)
        missed_laundering_penalty = investigation_costs.get('missed_laundering_penalty', 10000)
        
        # Calculate costs
        total_investigation_cost = (tp + fp) * investigation_cost
        total_sar_cost = tp * sar_filing_cost
        total_penalty_cost = fn * missed_laundering_penalty
        
        total_cost = total_investigation_cost + total_sar_cost + total_penalty_cost
        
        # Calculate cost per detection
        cost_per_detection = total_cost / tp if tp > 0 else float('inf')
        
        # Calculate savings (avoided penalties)
        avoided_penalties = tp * missed_laundering_penalty
        
        business_metrics = {
            "total_investigation_cost": total_investigation_cost,
            "total_sar_filing_cost": total_sar_cost,
            "total_penalty_cost": total_penalty_cost,
            "total_cost": total_cost,
            "cost_per_detection": cost_per_detection,
            "avoided_penalties": avoided_penalties,
            "net_savings": avoided_penalties - total_cost,
            "investigation_efficiency": tp / (tp + fp) if (tp + fp) > 0 else 0
        }
        
        return business_metrics
    
    def generate_confusion_matrix_plot(self, 
                                     ground_truth: List[int],
                                     predictions: List[int],
                                     labels: Optional[List[str]] = None,
                                     title: str = "Confusion Matrix") -> plt.Figure:
        """
        Generate confusion matrix visualization
        
        Args:
            ground_truth: Ground truth labels
            predictions: Predicted labels
            labels: Class labels
            title: Plot title
            
        Returns:
            Matplotlib figure
        """
        if labels is None:
            labels = ["Legitimate", "Laundering"]
        
        cm = confusion_matrix(ground_truth, predictions)
        
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                   xticklabels=labels, yticklabels=labels, ax=ax)
        
        ax.set_title(title)
        ax.set_xlabel('Predicted')
        ax.set_ylabel('Actual')
        
        plt.tight_layout()
        return fig
    
    def generate_roc_curve(self, 
                          ground_truth: List[int],
                          risk_scores: List[float],
                          title: str = "ROC Curve") -> plt.Figure:
        """
        Generate ROC curve visualization
        
        Args:
            ground_truth: Ground truth labels
            risk_scores: Risk scores
            title: Plot title
            
        Returns:
            Matplotlib figure
        """
        y_true = np.array(ground_truth)
        scores = np.array(risk_scores)
        
        if len(np.unique(y_true)) <= 1:
            logger.warning("Cannot generate ROC curve: insufficient class diversity")
            return None
        
        fpr, tpr, thresholds = roc_curve(y_true, scores)
        roc_auc = roc_auc_score(y_true, scores)
        
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot(fpr, tpr, color='darkorange', lw=2, 
               label=f'ROC curve (AUC = {roc_auc:.2f})')
        ax.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
        
        ax.set_xlim([0.0, 1.0])
        ax.set_ylim([0.0, 1.05])
        ax.set_xlabel('False Positive Rate')
        ax.set_ylabel('True Positive Rate')
        ax.set_title(title)
        ax.legend(loc="lower right")
        
        plt.tight_layout()
        return fig
    
    def calculate_comprehensive_metrics(self, 
                                      ground_truth: List[int],
                                      predictions: List[int],
                                      risk_scores: Optional[List[float]] = None,
                                      amounts: Optional[List[float]] = None,
                                      investigation_costs: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Calculate comprehensive metrics for AML system evaluation
        
        Args:
            ground_truth: Ground truth labels
            predictions: Predicted labels
            risk_scores: Optional risk scores
            amounts: Optional transaction amounts
            investigation_costs: Optional cost parameters
            
        Returns:
            Comprehensive metrics dictionary
        """
        logger.info("Calculating comprehensive AML metrics")
        
        # Basic metrics
        basic_metrics = self.calculate_basic_metrics(ground_truth, predictions)
        
        # Financial metrics
        financial_metrics = self.calculate_financial_metrics(ground_truth, predictions, amounts)
        
        # Risk score metrics
        risk_metrics = {}
        if risk_scores is not None:
            risk_metrics = self.calculate_risk_score_metrics(ground_truth, risk_scores)
        
        # Business metrics
        business_metrics = {}
        if investigation_costs is not None:
            business_metrics = self.calculate_business_metrics(ground_truth, predictions, investigation_costs)
        
        # Combine all metrics
        comprehensive_metrics = {
            "basic_metrics": basic_metrics,
            "financial_metrics": financial_metrics,
            "risk_score_metrics": risk_metrics,
            "business_metrics": business_metrics,
            "evaluation_timestamp": pd.Timestamp.now().isoformat()
        }
        
        # Store in history
        self.metrics_history.append(comprehensive_metrics)
        
        logger.info(f"Comprehensive metrics calculated for {len(ground_truth)} samples")
        return comprehensive_metrics
    
    def get_metrics_summary(self, metrics: Dict[str, Any]) -> str:
        """
        Generate human-readable metrics summary
        
        Args:
            metrics: Comprehensive metrics dictionary
            
        Returns:
            Formatted summary string
        """
        basic = metrics.get("basic_metrics", {})
        financial = metrics.get("financial_metrics", {})
        business = metrics.get("business_metrics", {})
        
        summary = f"""
AML System Performance Summary
==============================

Basic Performance:
- Accuracy: {basic.get('accuracy', 0):.1%}
- Precision: {basic.get('precision', 0):.1%}
- Recall: {basic.get('recall', 0):.1%}
- F1 Score: {basic.get('f1_score', 0):.1%}
- Specificity: {basic.get('specificity', 0):.1%}

Detection Results:
- True Positives: {basic.get('true_positives', 0)}
- False Positives: {basic.get('false_positives', 0)}
- True Negatives: {basic.get('true_negatives', 0)}
- False Negatives: {basic.get('false_negatives', 0)}
- Total Samples: {basic.get('total_samples', 0)}

Financial Impact:
- Detection Rate by Amount: {financial.get('detection_rate_by_amount', 0):.1%}
- Detected Laundering Amount: ${financial.get('detected_laundering_amount', 0):,.2f}
- Missed Laundering Amount: ${financial.get('missed_laundering_amount', 0):,.2f}

Business Impact:
- Total Investigation Cost: ${business.get('total_cost', 0):,.2f}
- Cost per Detection: ${business.get('cost_per_detection', 0):,.2f}
- Net Savings: ${business.get('net_savings', 0):,.2f}
- Investigation Efficiency: {business.get('investigation_efficiency', 0):.1%}
"""
        
        return summary


# Global metrics calculator instance
metrics_calculator = AMLMetricsCalculator()


def calculate_aml_accuracy(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate accuracy metrics for AML investigation results
    
    Args:
        results: List of investigation results with ground_truth and prediction fields
        
    Returns:
        Comprehensive metrics dictionary
    """
    # Extract data
    ground_truth = [r.get("ground_truth", 0) for r in results]
    predictions = [r.get("prediction", 0) for r in results]
    risk_scores = [r.get("risk_score", 0) for r in results]
    
    # Extract amounts if available
    amounts = []
    for r in results:
        transaction = r.get("transaction", {})
        amount = transaction.get("amount", 0)
        amounts.append(amount)
    
    # Define investigation costs (example values)
    investigation_costs = {
        "investigation_cost": 100,
        "sar_filing_cost": 500,
        "missed_laundering_penalty": 10000
    }
    
    # Calculate comprehensive metrics
    metrics = metrics_calculator.calculate_comprehensive_metrics(
        ground_truth=ground_truth,
        predictions=predictions,
        risk_scores=risk_scores,
        amounts=amounts,
        investigation_costs=investigation_costs
    )
    
    return metrics
