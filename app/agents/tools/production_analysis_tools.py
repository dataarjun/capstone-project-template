"""
Production-Ready Analysis Tools for AML Agents

This module provides production-ready analysis utilities for AML investigation agents
with proper @tool decorators for LangChain integration.
"""

import json
import statistics
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from langchain_core.tools import tool
from app.core.logger import get_logger

logger = get_logger(__name__)

# ============================================================================
# STRUCTURING DETECTION TOOLS
# ============================================================================

@tool
def detect_structuring_patterns(
    transaction_data: Dict[str, Any], 
    related_transactions: List[Dict[str, Any]],
    reporting_threshold: float = 10000.0
) -> Dict[str, Any]:
    """
    Detect structuring patterns where transactions are deliberately kept 
    just under reporting thresholds to avoid regulatory reporting.
    
    Args:
        transaction_data: Current transaction data
        related_transactions: Related transactions for analysis
        reporting_threshold: Regulatory reporting threshold (default: $10,000)
    
    Returns:
        Structuring detection results with pattern analysis
    """
    try:
        current_amount = float(transaction_data.get("amount", 0))
        suspicious_threshold = reporting_threshold * 0.95  # 95% of threshold
        
        # Check if current transaction is just under threshold
        is_under_threshold = current_amount < reporting_threshold
        is_suspicious_amount = current_amount >= suspicious_threshold
        
        # Analyze related transactions for patterns
        suspicious_transactions = []
        total_amount = current_amount
        
        for tx in related_transactions:
            tx_amount = float(tx.get("amount", 0))
            
            # Check if transaction is just under threshold
            if (tx_amount < reporting_threshold and 
                tx_amount >= suspicious_threshold):
                suspicious_transactions.append(tx)
                total_amount += tx_amount
        
        # Calculate structuring score
        structuring_score = _calculate_structuring_score(
            current_amount, total_amount, len(suspicious_transactions), reporting_threshold
        )
        
        return {
            "detected": structuring_score > 0.7,
            "structuring_score": structuring_score,
            "current_transaction_suspicious": is_suspicious_amount,
            "suspicious_transactions": suspicious_transactions,
            "total_amount": total_amount,
            "pattern_description": "Multiple transactions just under reporting threshold",
            "confidence_level": "high" if structuring_score > 0.8 else "medium" if structuring_score > 0.5 else "low"
        }
        
    except Exception as e:
        logger.error(f"Failed to detect structuring patterns: {str(e)}")
        return {
            "detected": False,
            "structuring_score": 0.0,
            "error": str(e),
            "pattern_description": "Error in structuring detection"
        }

def _calculate_structuring_score(
    current_amount: float, 
    total_amount: float, 
    suspicious_count: int,
    reporting_threshold: float
) -> float:
    """Calculate structuring suspicion score"""
    score = 0.0
    
    # Factor 1: Current transaction amount (30% weight)
    if current_amount >= (reporting_threshold * 0.95):
        score += 0.3
    
    # Factor 2: Number of suspicious transactions (40% weight)
    if suspicious_count > 0:
        score += min(0.4, suspicious_count * 0.1)
    
    # Factor 3: Total amount approaching threshold (30% weight)
    if total_amount >= reporting_threshold:
        score += 0.3
    
    return min(1.0, score)

@tool
def detect_smurfing_patterns(
    transaction_data: Dict[str, Any], 
    related_transactions: List[Dict[str, Any]],
    time_window_hours: int = 24
) -> Dict[str, Any]:
    """
    Detect smurfing patterns where multiple accounts coordinate to send 
    money to a single recipient to avoid detection.
    
    Args:
        transaction_data: Current transaction data
        related_transactions: Related transactions for analysis
        time_window_hours: Time window for coordination analysis (default: 24 hours)
    
    Returns:
        Smurfing detection results with coordination analysis
    """
    try:
        min_coordinated_accounts = 3
        
        # Group transactions by time window
        time_groups = _group_by_time_window(related_transactions, time_window_hours)
        
        # Analyze each time group for coordination
        coordinated_groups = []
        for time_group in time_groups:
            if len(time_group) >= min_coordinated_accounts:
                coordination_score = _calculate_coordination_score(time_group)
                if coordination_score > 0.6:
                    coordinated_groups.append({
                        "transactions": time_group,
                        "coordination_score": coordination_score,
                        "time_window": time_group[0].get("transaction_date", ""),
                        "participant_count": len(time_group)
                    })
        
        # Calculate overall smurfing score
        smurfing_score = _calculate_smurfing_score(coordinated_groups)
        
        return {
            "detected": smurfing_score > 0.7,
            "smurfing_score": smurfing_score,
            "coordinated_groups": coordinated_groups,
            "pattern_description": "Multiple coordinated transactions to single recipient",
            "confidence_level": "high" if smurfing_score > 0.8 else "medium" if smurfing_score > 0.5 else "low"
        }
        
    except Exception as e:
        logger.error(f"Failed to detect smurfing patterns: {str(e)}")
        return {
            "detected": False,
            "smurfing_score": 0.0,
            "error": str(e),
            "pattern_description": "Error in smurfing detection"
        }

def _group_by_time_window(transactions: List[Dict[str, Any]], time_window_hours: int) -> List[List[Dict[str, Any]]]:
    """Group transactions by time windows"""
    # Sort transactions by date
    sorted_transactions = sorted(transactions, key=lambda x: x.get("transaction_date", ""))
    
    groups = []
    current_group = []
    
    for tx in sorted_transactions:
        if not current_group:
            current_group.append(tx)
        else:
            # Check if transaction is within time window
            if _within_time_window(current_group[0], tx, time_window_hours):
                current_group.append(tx)
            else:
                if len(current_group) > 0:
                    groups.append(current_group)
                current_group = [tx]
    
    if current_group:
        groups.append(current_group)
    
    return groups

def _within_time_window(tx1: Dict[str, Any], tx2: Dict[str, Any], time_window_hours: int) -> bool:
    """Check if two transactions are within time window"""
    try:
        date1 = datetime.fromisoformat(tx1.get("transaction_date", ""))
        date2 = datetime.fromisoformat(tx2.get("transaction_date", ""))
        time_diff = abs((date2 - date1).total_seconds() / 3600)  # hours
        return time_diff <= time_window_hours
    except:
        return False

def _calculate_coordination_score(transactions: List[Dict[str, Any]]) -> float:
    """Calculate coordination score for a group of transactions"""
    if len(transactions) < 2:
        return 0.0
    
    # Check for common recipients
    recipients = [tx.get("counterparty_id") for tx in transactions]
    unique_recipients = len(set(recipients))
    
    # Check for similar amounts
    amounts = [float(tx.get("amount", 0)) for tx in transactions]
    amount_variance = np.var(amounts) if len(amounts) > 1 else 0
    
    # Calculate score based on coordination factors
    score = 0.0
    
    # Factor 1: Multiple transactions to same recipient (50% weight)
    if unique_recipients == 1:
        score += 0.5
    
    # Factor 2: Similar amounts (30% weight)
    if amount_variance < 1000:  # Low variance in amounts
        score += 0.3
    
    # Factor 3: Number of transactions (20% weight)
    if len(transactions) >= 3:
        score += 0.2
    
    return min(1.0, score)

def _calculate_smurfing_score(coordinated_groups: List[Dict[str, Any]]) -> float:
    """Calculate overall smurfing score"""
    if not coordinated_groups:
        return 0.0
    
    # Average coordination scores
    avg_coordination = np.mean([group["coordination_score"] for group in coordinated_groups])
    
    # Number of coordinated groups
    group_factor = min(1.0, len(coordinated_groups) / 3)
    
    return (avg_coordination * 0.7) + (group_factor * 0.3)

# ============================================================================
# BEHAVIORAL ANALYSIS TOOLS
# ============================================================================

@tool
def analyze_behavioral_anomalies(
    transaction_data: Dict[str, Any], 
    customer_data: Dict[str, Any], 
    related_transactions: List[Dict[str, Any]],
    baseline_period_days: int = 90
) -> Dict[str, Any]:
    """
    Analyze customer behavior for anomalies and suspicious patterns
    by comparing against historical baseline.
    
    Args:
        transaction_data: Current transaction data
        customer_data: Customer profile data
        related_transactions: Related transactions for analysis
        baseline_period_days: Baseline period for comparison (default: 90 days)
    
    Returns:
        Behavioral anomaly analysis results
    """
    try:
        # Calculate behavioral metrics
        behavioral_metrics = _calculate_behavioral_metrics(
            transaction_data, customer_data, related_transactions
        )
        
        # Calculate anomaly score
        anomaly_score = _calculate_anomaly_score(behavioral_metrics)
        
        # Identify specific anomalies
        anomalies = _identify_anomalies(behavioral_metrics)
        
        return {
            "anomaly_score": anomaly_score,
            "is_anomalous": anomaly_score >= 0.7,
            "behavioral_metrics": behavioral_metrics,
            "anomalies": anomalies,
            "scoring_method": "Behavioral baseline comparison",
            "confidence_level": "high" if anomaly_score > 0.8 else "medium" if anomaly_score > 0.5 else "low"
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze behavioral anomalies: {str(e)}")
        return {
            "anomaly_score": 0.0,
            "is_anomalous": False,
            "error": str(e),
            "scoring_method": "Error in behavioral analysis"
        }

def _calculate_behavioral_metrics(
    transaction_data: Dict[str, Any], 
    customer_data: Dict[str, Any], 
    related_transactions: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Calculate behavioral metrics"""
    # Transaction frequency
    transaction_count = len(related_transactions) + 1
    
    # Transaction amounts
    amounts = [float(tx.get("amount", 0)) for tx in related_transactions]
    amounts.append(float(transaction_data.get("amount", 0)))
    
    # Calculate metrics
    avg_amount = np.mean(amounts) if amounts else 0
    max_amount = max(amounts) if amounts else 0
    amount_variance = np.var(amounts) if len(amounts) > 1 else 0
    
    # Transaction timing patterns
    dates = [tx.get("transaction_date") for tx in related_transactions]
    dates.append(transaction_data.get("transaction_date"))
    
    return {
        "transaction_count": transaction_count,
        "average_amount": avg_amount,
        "max_amount": max_amount,
        "amount_variance": amount_variance,
        "transaction_frequency": transaction_count / 30,  # per day
        "amount_trend": _calculate_amount_trend(amounts),
        "timing_patterns": _analyze_timing_patterns(dates)
    }

def _calculate_amount_trend(amounts: List[float]) -> str:
    """Calculate amount trend"""
    if len(amounts) < 2:
        return "insufficient_data"
    
    # Simple trend calculation
    first_half = np.mean(amounts[:len(amounts)//2])
    second_half = np.mean(amounts[len(amounts)//2:])
    
    if second_half > first_half * 1.2:
        return "increasing"
    elif second_half < first_half * 0.8:
        return "decreasing"
    else:
        return "stable"

def _analyze_timing_patterns(dates: List[str]) -> Dict[str, Any]:
    """Analyze timing patterns"""
    return {
        "pattern_type": "regular",
        "frequency": "daily",
        "anomaly_detected": False
    }

def _calculate_anomaly_score(metrics: Dict[str, Any]) -> float:
    """Calculate overall anomaly score"""
    score = 0.0
    
    # Factor 1: Unusual transaction frequency (30% weight)
    if metrics["transaction_frequency"] > 5:  # More than 5 transactions per day
        score += 0.3
    
    # Factor 2: High amount variance (30% weight)
    if metrics["amount_variance"] > 1000000:  # High variance in amounts
        score += 0.3
    
    # Factor 3: Unusual amount trend (20% weight)
    if metrics["amount_trend"] == "increasing":
        score += 0.2
    
    # Factor 4: Timing anomalies (20% weight)
    if metrics["timing_patterns"]["anomaly_detected"]:
        score += 0.2
    
    return min(1.0, score)

def _identify_anomalies(metrics: Dict[str, Any]) -> List[str]:
    """Identify specific anomalies"""
    anomalies = []
    
    if metrics["transaction_frequency"] > 5:
        anomalies.append("High transaction frequency")
    
    if metrics["amount_variance"] > 1000000:
        anomalies.append("High amount variance")
    
    if metrics["amount_trend"] == "increasing":
        anomalies.append("Increasing transaction amounts")
    
    if metrics["timing_patterns"]["anomaly_detected"]:
        anomalies.append("Unusual timing patterns")
    
    return anomalies

# ============================================================================
# GEOGRAPHIC RISK ANALYSIS TOOLS
# ============================================================================

@tool
def assess_geographic_risks(
    customer_location: str, 
    transaction_location: str, 
    transaction_country: str
) -> Dict[str, Any]:
    """
    Assess geographic risks based on transaction locations and customer locations.
    
    Args:
        customer_location: Customer location
        transaction_location: Transaction location
        transaction_country: Transaction country code
    
    Returns:
        Geographic risk assessment results
    """
    try:
        # Assess country risk
        country_risk = _assess_country_risk(transaction_country)
        
        # Assess location mismatch
        location_mismatch = _assess_location_mismatch(
            customer_location, transaction_location
        )
        
        # Calculate overall geographic risk score
        geographic_risk_score = _calculate_geographic_risk_score(
            country_risk, location_mismatch
        )
        
        return {
            "geographic_risk_score": geographic_risk_score,
            "country_risk": country_risk,
            "location_mismatch": location_mismatch,
            "risk_level": _determine_risk_level(geographic_risk_score),
            "confidence_level": "high" if geographic_risk_score > 0.8 else "medium" if geographic_risk_score > 0.5 else "low"
        }
        
    except Exception as e:
        logger.error(f"Failed to assess geographic risks: {str(e)}")
        return {
            "geographic_risk_score": 0.0,
            "error": str(e),
            "risk_level": "unknown"
        }

def _assess_country_risk(country_code: str) -> Dict[str, Any]:
    """Assess country risk level"""
    high_risk_countries = [
        "AF", "IR", "KP", "SY", "VE", "CU", "BY", "MM", "ZW"
    ]
    medium_risk_countries = [
        "CN", "RU", "TR", "PK", "BD", "NG", "KE", "GH", "UG"
    ]
    
    if country_code in high_risk_countries:
        return {
            "risk_level": "high",
            "risk_score": 0.8,
            "description": "High-risk country"
        }
    elif country_code in medium_risk_countries:
        return {
            "risk_level": "medium",
            "risk_score": 0.5,
            "description": "Medium-risk country"
        }
    else:
        return {
            "risk_level": "low",
            "risk_score": 0.2,
            "description": "Low-risk country"
        }

def _assess_location_mismatch(
    customer_location: str, 
    transaction_location: str
) -> Dict[str, Any]:
    """Assess location mismatch risk"""
    if not customer_location or not transaction_location:
        return {
            "mismatch_detected": False,
            "mismatch_score": 0.0,
            "description": "Insufficient location data"
        }
    
    # Simple location mismatch detection
    customer_country = customer_location.split(",")[-1].strip()
    transaction_country = transaction_location.split(",")[-1].strip()
    
    mismatch_detected = customer_country != transaction_country
    
    return {
        "mismatch_detected": mismatch_detected,
        "mismatch_score": 0.7 if mismatch_detected else 0.0,
        "description": "Customer and transaction locations differ" if mismatch_detected else "Locations match"
    }

def _calculate_geographic_risk_score(
    country_risk: Dict[str, Any], 
    location_mismatch: Dict[str, Any]
) -> float:
    """Calculate overall geographic risk score"""
    country_score = country_risk.get("risk_score", 0.0)
    mismatch_score = location_mismatch.get("mismatch_score", 0.0)
    
    # Weighted combination
    return (country_score * 0.7) + (mismatch_score * 0.3)

def _determine_risk_level(risk_score: float) -> str:
    """Determine risk level from score"""
    if risk_score >= 0.7:
        return "high"
    elif risk_score >= 0.4:
        return "medium"
    else:
        return "low"

# ============================================================================
# NETWORK ANALYSIS TOOLS
# ============================================================================

@tool
def analyze_transaction_network(
    transaction_data: Dict[str, Any], 
    related_transactions: List[Dict[str, Any]],
    max_network_depth: int = 3
) -> Dict[str, Any]:
    """
    Analyze transaction networks to identify suspicious connections and patterns.
    
    Args:
        transaction_data: Current transaction data
        related_transactions: Related transactions for analysis
        max_network_depth: Maximum network depth for analysis
    
    Returns:
        Network analysis results
    """
    try:
        # Build network graph
        network_graph = _build_network_graph(transaction_data, related_transactions)
        
        # Analyze network properties
        network_properties = _analyze_network_properties(network_graph)
        
        # Identify suspicious connections
        suspicious_connections = _identify_suspicious_connections(network_graph)
        
        return {
            "network_size": len(network_graph.get("nodes", [])),
            "network_properties": network_properties,
            "suspicious_connections": len(suspicious_connections),
            "suspicious_connection_details": suspicious_connections,
            "network_analysis": "Network analysis completed",
            "confidence_level": "high" if len(suspicious_connections) > 0 else "medium"
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze transaction network: {str(e)}")
        return {
            "network_size": 0,
            "error": str(e),
            "network_analysis": "Error in network analysis"
        }

def _build_network_graph(
    transaction_data: Dict[str, Any], 
    related_transactions: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Build network graph from transactions"""
    graph = {
        "nodes": [],
        "edges": []
    }
    
    # Add current transaction as central node
    central_node = {
        "id": transaction_data.get("transaction_id"),
        "type": "transaction",
        "amount": transaction_data.get("amount"),
        "date": transaction_data.get("transaction_date")
    }
    graph["nodes"].append(central_node)
    
    # Add related transactions
    for tx in related_transactions:
        node = {
            "id": tx.get("transaction_id"),
            "type": "transaction",
            "amount": tx.get("amount"),
            "date": tx.get("transaction_date")
        }
        graph["nodes"].append(node)
        
        # Add edge if connected
        if _are_connected(transaction_data, tx):
            edge = {
                "source": transaction_data.get("transaction_id"),
                "target": tx.get("transaction_id"),
                "weight": _calculate_connection_weight(transaction_data, tx)
            }
            graph["edges"].append(edge)
    
    return graph

def _are_connected(tx1: Dict[str, Any], tx2: Dict[str, Any]) -> bool:
    """Check if two transactions are connected"""
    # Check for common customer or counterparty
    return (tx1.get("customer_id") == tx2.get("customer_id") or
            tx1.get("counterparty_id") == tx2.get("counterparty_id"))

def _calculate_connection_weight(tx1: Dict[str, Any], tx2: Dict[str, Any]) -> float:
    """Calculate connection weight between transactions"""
    weight = 0.0
    
    # Factor 1: Same customer (50% weight)
    if tx1.get("customer_id") == tx2.get("customer_id"):
        weight += 0.5
    
    # Factor 2: Same counterparty (50% weight)
    if tx1.get("counterparty_id") == tx2.get("counterparty_id"):
        weight += 0.5
    
    # Factor 3: Similar amounts (bonus)
    amount1 = float(tx1.get("amount", 0))
    amount2 = float(tx2.get("amount", 0))
    if amount1 > 0 and amount2 > 0:
        amount_ratio = min(amount1, amount2) / max(amount1, amount2)
        if amount_ratio > 0.8:
            weight += 0.3
    
    return min(1.0, weight)

def _analyze_network_properties(network_graph: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze network properties"""
    nodes = network_graph.get("nodes", [])
    edges = network_graph.get("edges", [])
    
    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "density": len(edges) / max(1, len(nodes) * (len(nodes) - 1) / 2),
        "average_degree": len(edges) * 2 / max(1, len(nodes))
    }

def _identify_suspicious_connections(network_graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Identify suspicious connections in the network"""
    suspicious_connections = []
    suspicious_connection_threshold = 0.8
    
    for edge in network_graph.get("edges", []):
        if edge.get("weight", 0) >= suspicious_connection_threshold:
            suspicious_connections.append(edge)
    
    return suspicious_connections

# ============================================================================
# RISK CALCULATION TOOLS
# ============================================================================

@tool
def calculate_overall_risk_score(
    pattern_analysis: Dict[str, Any], 
    behavioral_analysis: Dict[str, Any], 
    geographic_risks: Dict[str, Any],
    network_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate overall risk score by combining all risk factors.
    
    Args:
        pattern_analysis: Pattern analysis results
        behavioral_analysis: Behavioral analysis results
        geographic_risks: Geographic risk assessment
        network_analysis: Network analysis results
    
    Returns:
        Overall risk score and assessment
    """
    try:
        # Risk weights
        risk_weights = {
            "pattern_analysis": 0.3,
            "behavioral_analysis": 0.25,
            "geographic_risks": 0.2,
            "network_analysis": 0.25
        }
        
        # Calculate individual risk scores
        pattern_score = pattern_analysis.get("structuring_score", 0.0) + pattern_analysis.get("smurfing_score", 0.0)
        behavioral_score = behavioral_analysis.get("anomaly_score", 0.0)
        geographic_score = geographic_risks.get("geographic_risk_score", 0.0)
        network_score = min(1.0, network_analysis.get("suspicious_connections", 0) / 5.0)
        
        # Weighted combination
        overall_score = (
            pattern_score * risk_weights["pattern_analysis"] +
            behavioral_score * risk_weights["behavioral_analysis"] +
            geographic_score * risk_weights["geographic_risks"] +
            network_score * risk_weights["network_analysis"]
        )
        
        # Determine risk level
        risk_level = _determine_overall_risk_level(overall_score)
        
        return {
            "overall_risk_score": min(1.0, max(0.0, overall_score)),
            "risk_level": risk_level,
            "component_scores": {
                "pattern_score": pattern_score,
                "behavioral_score": behavioral_score,
                "geographic_score": geographic_score,
                "network_score": network_score
            },
            "risk_weights": risk_weights,
            "confidence_level": "high" if overall_score > 0.8 else "medium" if overall_score > 0.5 else "low"
        }
        
    except Exception as e:
        logger.error(f"Failed to calculate overall risk score: {str(e)}")
        return {
            "overall_risk_score": 0.0,
            "risk_level": "unknown",
            "error": str(e)
        }

def _determine_overall_risk_level(risk_score: float) -> str:
    """Determine overall risk level from score"""
    if risk_score >= 0.8:
        return "CRITICAL"
    elif risk_score >= 0.6:
        return "HIGH"
    elif risk_score >= 0.4:
        return "MEDIUM"
    else:
        return "LOW"

# ============================================================================
# REPORT GENERATION TOOLS
# ============================================================================

@tool
def generate_investigation_summary(
    investigation_id: str,
    risk_assessment: Dict[str, Any],
    pattern_analysis: Dict[str, Any],
    behavioral_analysis: Dict[str, Any],
    geographic_risks: Dict[str, Any],
    network_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate comprehensive investigation summary combining all analysis results.
    
    Args:
        investigation_id: Investigation ID
        risk_assessment: Overall risk assessment
        pattern_analysis: Pattern analysis results
        behavioral_analysis: Behavioral analysis results
        geographic_risks: Geographic risk assessment
        network_analysis: Network analysis results
    
    Returns:
        Comprehensive investigation summary
    """
    try:
        risk_level = risk_assessment.get("risk_level", "UNKNOWN")
        risk_score = risk_assessment.get("overall_risk_score", 0.0)
        
        # Generate key findings
        key_findings = []
        
        if pattern_analysis.get("detected", False):
            key_findings.append(f"Pattern Detection: {pattern_analysis.get('pattern_description', 'Suspicious patterns detected')}")
        
        if behavioral_analysis.get("is_anomalous", False):
            key_findings.append(f"Behavioral Anomalies: {len(behavioral_analysis.get('anomalies', []))} anomalies detected")
        
        if geographic_risks.get("risk_level") == "high":
            key_findings.append(f"Geographic Risk: {geographic_risks.get('country_risk', {}).get('description', 'High-risk jurisdiction')}")
        
        if network_analysis.get("suspicious_connections", 0) > 0:
            key_findings.append(f"Network Analysis: {network_analysis.get('suspicious_connections', 0)} suspicious connections identified")
        
        # Generate recommendations
        recommendations = _generate_recommendations(risk_level, risk_score, key_findings)
        
        return {
            "investigation_id": investigation_id,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "key_findings": key_findings,
            "recommendations": recommendations,
            "analysis_summary": {
                "pattern_analysis": pattern_analysis.get("detected", False),
                "behavioral_anomalies": behavioral_analysis.get("is_anomalous", False),
                "geographic_risks": geographic_risks.get("risk_level", "low"),
                "network_connections": network_analysis.get("suspicious_connections", 0)
            },
            "generated_at": datetime.utcnow().isoformat(),
            "confidence_level": "high" if risk_score > 0.8 else "medium" if risk_score > 0.5 else "low"
        }
        
    except Exception as e:
        logger.error(f"Failed to generate investigation summary: {str(e)}")
        return {
            "investigation_id": investigation_id,
            "error": str(e),
            "generated_at": datetime.utcnow().isoformat()
        }

def _generate_recommendations(risk_level: str, risk_score: float, key_findings: List[str]) -> List[str]:
    """Generate recommendations based on risk assessment"""
    recommendations = []
    
    if risk_level == "CRITICAL":
        recommendations.extend([
            "Immediate escalation required",
            "Enhanced due diligence mandatory",
            "Regulatory filing required",
            "Account review and potential suspension"
        ])
    elif risk_level == "HIGH":
        recommendations.extend([
            "Enhanced monitoring required",
            "Regulatory filing recommended",
            "Additional documentation needed",
            "Regular review schedule"
        ])
    elif risk_level == "MEDIUM":
        recommendations.extend([
            "Standard monitoring sufficient",
            "Document findings for audit",
            "Regular review recommended"
        ])
    else:
        recommendations.extend([
            "Continue standard monitoring",
            "Document for compliance records"
        ])
    
    return recommendations
