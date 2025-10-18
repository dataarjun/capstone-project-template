"""
Simplified Production AML Workflow for testing
"""

import asyncio
import hashlib
import re
import statistics
import datetime
import uuid
from typing import Dict, List, Any, Optional, TypedDict
from pathlib import Path

import yaml
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.core.logger import get_logger
from app.core.config_simple import settings

logger = get_logger(__name__)

# Configuration
HIGH_RISK_COUNTRIES = ["AF", "IR", "KP", "SY", "VE", "CU", "BY", "MM", "ZW", "RU"]
TAX_HAVENS = ["KY", "VG", "BM", "PA", "MT", "AE", "LI", "MC", "AN"]
SANCTIONED_ENTITIES = [
    "narcotics_cartel_xyz",
    "terror_group_abc", 
    "sanctioned_russian_bank",
    "hezbollah_front_company",
    "isis_financial_network"
]
DARKNET_MARKETS = [
    "AlphaMarket",
    "Dark0d3",
    "Hydra",
    "Silk_Road_Reborn",
    "Dream_Market"
]
HIGH_RISK_BANKS = ["03208", "03209", "0211050", "0245335"]
CTR_THRESHOLD = 10000.0

# State definitions
class AMLState(TypedDict):
    transaction: Dict[str, Any]
    customer: Dict[str, Any]
    risk_score: int
    alerts: List[str]
    investigation: Dict[str, Any]
    llm_analysis: Dict[str, Any]
    risk_factors: List[str]
    decision_path: List[str]
    pep_status: Optional[bool]
    sanction_hits: List[str]
    documents: List[str]
    document_risks: List[str]
    asset_type: Optional[str]
    crypto_details: Optional[Dict[str, Any]]
    origin_country: Optional[str]
    destination_country: Optional[str]
    intermediate_countries: List[str]
    structuring_detected: bool
    smurfing_detected: bool
    layering_detected: bool
    reporting_status: Optional[str]
    case_id: Optional[str]
    sar_timestamp: Optional[datetime.datetime]
    review_status: Optional[str]
    review_deadline: Optional[datetime.datetime]
    transaction_count: int
    workflow_complete: bool

class ChatState(TypedDict):
    thread_id: str
    investigation_results: List[Dict[str, Any]]
    chat_history: List[BaseMessage]
    created_at: datetime.datetime
    last_updated: datetime.datetime

# Global storage
CHAT_THREADS: Dict[str, ChatState] = {}
INVESTIGATION_RESULTS: Dict[str, Dict[str, Any]] = {}

# Utility functions
def generate_case_id() -> str:
    """Generate unique case ID using timestamp hash"""
    timestamp = str(datetime.datetime.now())
    return hashlib.sha256(timestamp.encode()).hexdigest()[:12]

def check_pep_database(name: str) -> bool:
    """Check if customer is a Politically Exposed Person"""
    if not name:
        return False
    pep_keywords = ["gov", "minister", "official", "senator", 
                    "president", "director", "ambassador"]
    return any(keyword in name.lower() for keyword in pep_keywords)

def check_sanctions_list(entities: List[str]) -> List[str]:
    """Check entities against sanctions list"""
    hits = []
    for entity in entities:
        if not entity:  # Skip None or empty entities
            continue
        for sanctioned in SANCTIONED_ENTITIES:
            if sanctioned.lower() in entity.lower():
                hits.append(entity)
    return hits

def update_path(state: AMLState, step: str) -> AMLState:
    """Update decision path tracking"""
    return {**state, "decision_path": state["decision_path"] + [step]}

def unify_transaction_data(transaction: Dict[str, Any]) -> Dict[str, Any]:
    """Unify transaction data from both datasets into common format"""
    unified = {}
    
    # Handle HI-Small_Trans format
    if "From Bank" in transaction:
        unified.update({
            "transaction_id": f"HI_{transaction.get('Account', 'unknown')}",
            "customer_id": transaction.get("Account", "unknown"),
            "counterparty_id": transaction.get("To Bank", "unknown"),
            "amount": float(transaction.get("Amount Received", 0)),
            "currency": transaction.get("Receiving Currency", "USD"),
            "transaction_type": transaction.get("Payment Format", "unknown"),
            "transaction_date": transaction.get("Timestamp", ""),
            "location": "Unknown",
            "country": "Unknown",
            "description": "HI-Small_Trans transaction",
            "status": "completed",
            "from_bank": transaction.get("From Bank"),
            "to_bank": transaction.get("To Bank"),
            "payment_format": transaction.get("Payment Format"),
            "ground_truth_label": int(transaction.get("Is Laundering", 0))
        })
    
    # Handle operational format
    elif "transaction_id" in transaction:
        unified.update({
            "transaction_id": transaction.get("transaction_id"),
            "customer_id": transaction.get("customer_id", "unknown"),
            "counterparty_id": transaction.get("counterparty_id"),
            "amount": float(transaction.get("amount", 0)),
            "currency": transaction.get("currency", "USD"),
            "transaction_type": transaction.get("transaction_type", "unknown"),
            "transaction_date": transaction.get("transaction_date", ""),
            "location": transaction.get("location", "Unknown"),
            "country": transaction.get("country", "Unknown"),
            "description": transaction.get("description", ""),
            "status": transaction.get("status", "completed"),
            "asset_type": transaction.get("asset_type", "FIAT"),
            "crypto_details": transaction.get("crypto_details"),
            "origin_country": transaction.get("origin_country"),
            "destination_country": transaction.get("destination_country"),
            "intermediate_countries": transaction.get("intermediate_countries", []),
            "documents": transaction.get("documents", [])
        })
    
    # Handle fraud detection format
    elif "SENDER_ACCOUNT_ID" in transaction:
        unified.update({
            "transaction_id": str(transaction.get("transaction_id", "unknown")),
            "customer_id": transaction.get("SENDER_ACCOUNT_ID", "unknown"),
            "counterparty_id": transaction.get("RECEIVER_ACCOUNT_ID", "unknown"),
            "amount": float(transaction.get("amount", 0)),
            "currency": "USD",
            "transaction_type": transaction.get("TX_TYPE", "unknown"),
            "transaction_date": str(transaction.get("TIMESTAMP", "")),
            "location": "Unknown",
            "country": "Unknown",
            "description": "Fraud detection transaction",
            "status": "completed",
            "ground_truth_label": int(transaction.get("IS_FRAUD", 0))
        })
    
    return unified

# Chat thread management
def create_chat_thread(investigation_results: Optional[List[Dict[str, Any]]] = None) -> str:
    """Create a new chat thread with UUID"""
    thread_id = str(uuid.uuid4())
    
    CHAT_THREADS[thread_id] = ChatState(
        thread_id=thread_id,
        investigation_results=investigation_results or [],
        chat_history=[],
        created_at=datetime.datetime.now(),
        last_updated=datetime.datetime.now()
    )
    
    return thread_id

def get_chat_thread(thread_id: str) -> Optional[ChatState]:
    """Get chat thread by ID"""
    return CHAT_THREADS.get(thread_id)

def update_chat_thread(thread_id: str, chat_state: ChatState):
    """Update chat thread state"""
    chat_state["last_updated"] = datetime.datetime.now()
    CHAT_THREADS[thread_id] = chat_state

def add_investigation_to_thread(thread_id: str, investigation_result: Dict[str, Any]):
    """Add investigation result to chat thread context"""
    thread = get_chat_thread(thread_id)
    if thread:
        thread["investigation_results"].append(investigation_result)
        update_chat_thread(thread_id, thread)

# Analysis nodes
def geographic_risk_assessment(state: AMLState) -> AMLState:
    """Comprehensive geographic risk assessment"""
    state = update_path(state, "geo_analysis")
    tx = state["transaction"]
    risk_factors = []
    
    # Collect all locations in transaction path
    locations = [
        tx.get("origin_country", ""),
        tx.get("destination_country", ""),
        tx.get("country", "")
    ]
    locations.extend(tx.get("intermediate_countries", []))
    
    # Remove empty strings
    locations = [loc for loc in locations if loc]
    
    # Check each location
    for country in locations:
        if country in HIGH_RISK_COUNTRIES:
            risk_factors.append(f"HIGH_RISK_{country}")
        if country in TAX_HAVENS:
            risk_factors.append(f"TAX_HAVEN_{country}")
    
    return {
        **state,
        "risk_factors": state["risk_factors"] + risk_factors,
        "origin_country": tx.get("origin_country"),
        "destination_country": tx.get("destination_country"),
        "intermediate_countries": tx.get("intermediate_countries", [])
    }

def sanctions_screening(state: AMLState) -> AMLState:
    """Screen transaction parties against sanctions lists"""
    state = update_path(state, "sanctions_check")
    parties = state["transaction"].get("parties", [])
    
    # Add customer and counterparty to parties list
    parties.append(state["customer"].get("name", ""))
    parties.append(state["transaction"].get("counterparty_id", ""))
    
    hits = check_sanctions_list(parties)
    
    return {
        **state,
        "sanction_hits": hits,
        "risk_factors": state["risk_factors"] + [f"SANCTION_HIT_{hit}" for hit in hits]
    }

def pep_screening(state: AMLState) -> AMLState:
    """Check for Politically Exposed Person status"""
    state = update_path(state, "pep_check")
    customer_name = state["customer"].get("name", "")
    is_pep = check_pep_database(customer_name)
    
    risk_factors = state["risk_factors"]
    if is_pep:
        risk_factors.append("PEP_CUSTOMER")
    
    return {
        **state,
        "pep_status": is_pep,
        "risk_factors": risk_factors
    }

def risk_scoring(state: AMLState) -> AMLState:
    """Comprehensive weighted risk scoring"""
    state = update_path(state, "risk_scoring")
    score = 0
    
    # Critical factors (highest weight)
    sanction_hits = len(state.get("sanction_hits", []))
    score += 40 * sanction_hits  # 40 points per sanction hit
    
    if state.get("pep_status"):
        score += 35  # 35 points for PEP
    
    # Crypto risks (25 points per crypto risk)
    crypto_risks = len([rf for rf in state["risk_factors"] if "CRYPTO" in rf])
    score += 25 * crypto_risks
    
    # Geographic risks (20 points per jurisdiction risk)
    jurisdiction_risks = len([rf for rf in state["risk_factors"] 
                             if "HIGH_RISK" in rf or "TAX_HAVEN" in rf])
    score += 20 * jurisdiction_risks
    
    # Document risks (15 points per document risk)
    document_risks = len(state.get("document_risks", []))
    score += 15 * document_risks
    
    # Behavioral alerts (10 points per alert)
    score += 10 * len(state.get("alerts", []))
    
    # Structuring/Smurfing detection (30 points each)
    if state.get("structuring_detected"):
        score += 30
    if state.get("smurfing_detected"):
        score += 30
    
    # Cap score at 100
    final_score = min(score, 100)
    
    return {
        **state,
        "risk_score": final_score
    }

def human_review(state: AMLState) -> AMLState:
    """Route to human review for medium-risk cases"""
    state = update_path(state, "human_review")
    
    return {
        **state,
        "reporting_status": "HUMAN_REVIEW",
        "review_status": "PENDING",
        "review_deadline": datetime.datetime.now() + datetime.timedelta(hours=24)
    }

# Routing functions
def route_initial_screening(state: AMLState) -> str:
    """Route based on transaction characteristics"""
    tx = state["transaction"]
    customer = state["customer"]
    
    # Crypto transactions go to geographic analysis (simplified)
    if tx.get("asset_type") == "CRYPTO":
        return "LARGE_TRANSACTION"
    
    # Large transactions (>$100k) go to geographic analysis
    if float(tx.get("amount", 0)) > 100000:
        return "LARGE_TRANSACTION"
    
    # New accounts (<7 days) go to sanctions check
    if customer.get("account_age_days", 365) < 7:
        return "STANDARD_FLOW"
    
    # High-risk bank in HI-Small_Trans dataset
    if tx.get("from_bank") in HIGH_RISK_BANKS or tx.get("to_bank") in HIGH_RISK_BANKS:
        return "LARGE_TRANSACTION"
    
    # Standard flow
    return "STANDARD_FLOW"

def route_sanctions_check(state: AMLState) -> str:
    """Route based on sanctions screening results"""
    if state.get("sanction_hits"):
        return "SANCTION_HIT"
    return "NO_HIT"

def route_pep_check(state: AMLState) -> str:
    """Route based on PEP status"""
    if state.get("pep_status"):
        return "PEP_FOUND"
    return "NO_PEP"

def route_risk_score(state: AMLState) -> str:
    """Final routing based on risk score"""
    risk_score = state.get("risk_score", 0)
    
    # Critical/High risk (>=65) -> SAR
    if risk_score >= 65:
        return "HIGH_RISK"
    
    # Medium risk (40-64) -> Human review
    if risk_score >= 40:
        return "MEDIUM_RISK"
    
    # Low risk (<40) -> Close case
    return "LOW_RISK"

# Workflow class
class ProductionAMLWorkflow:
    """Complete LLM-driven AML workflow implementation"""
    
    def __init__(self):
        """Initialize workflow with LLM and memory"""
        self.llm = self._initialize_llm()
        self.memory = MemorySaver()
        self.workflow = self._build_workflow()
    
    def _initialize_llm(self) -> ChatOpenAI:
        """Initialize OpenAI LLM"""
        return ChatOpenAI(
            model="gpt-4o",
            temperature=0.1,
            api_key=settings.OPENAI_API_KEY
        )
    
    def _build_workflow(self) -> StateGraph:
        """Build complete workflow graph with all nodes and conditional edges"""
        workflow = StateGraph(AMLState)
        
        # Add all nodes
        workflow.add_node("initial_screening", lambda s: update_path(s, "start"))
        workflow.add_node("geo_analysis", geographic_risk_assessment)
        workflow.add_node("sanctions_check", sanctions_screening)
        workflow.add_node("pep_check", pep_screening)
        workflow.add_node("score_risk", risk_scoring)
        workflow.add_node("human_review", human_review)
        
        # Set entry point
        workflow.set_entry_point("initial_screening")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "initial_screening",
            route_initial_screening,
            {
                "LARGE_TRANSACTION": "geo_analysis",
                "HIGH_RISK_BANK": "geo_analysis",
                "STANDARD_FLOW": "sanctions_check"
            }
        )
        
        workflow.add_edge("geo_analysis", "sanctions_check")
        
        workflow.add_conditional_edges(
            "sanctions_check",
            route_sanctions_check,
            {
                "SANCTION_HIT": "score_risk",
                "NO_HIT": "pep_check"
            }
        )
        
        workflow.add_conditional_edges(
            "pep_check",
            route_pep_check,
            {
                "PEP_FOUND": "score_risk",
                "NO_PEP": "score_risk"
            }
        )
        
        workflow.add_conditional_edges(
            "score_risk",
            route_risk_score,
            {
                "HIGH_RISK": END,
                "MEDIUM_RISK": "human_review",
                "LOW_RISK": END
            }
        )
        
        workflow.add_edge("human_review", END)
        
        return workflow.compile()

# Execution interface
def run_analysis(
    transaction: Dict[str, Any],
    customer: Dict[str, Any],
    workflow_instance: ProductionAMLWorkflow
) -> Dict[str, Any]:
    """Execute complete AML workflow analysis"""
    # Unify transaction data
    unified_tx = unify_transaction_data(transaction)
    
    # Initialize state
    initial_state = AMLState(
        transaction=unified_tx,
        customer=customer,
        risk_score=0,
        alerts=[],
        investigation={},
        llm_analysis={},
        risk_factors=[],
        decision_path=[],
        pep_status=None,
        sanction_hits=[],
        documents=transaction.get("documents", []),
        document_risks=[],
        asset_type=transaction.get("asset_type", "FIAT"),
        crypto_details=transaction.get("crypto_details"),
        origin_country=transaction.get("origin_country"),
        destination_country=transaction.get("destination_country"),
        intermediate_countries=transaction.get("intermediate_countries", []),
        structuring_detected=False,
        smurfing_detected=False,
        layering_detected=False,
        reporting_status=None,
        case_id=None,
        sar_timestamp=None,
        review_status=None,
        review_deadline=None,
        transaction_count=len(customer.get("transaction_history", [])),
        workflow_complete=False
    )
    
    # Execute workflow
    result = workflow_instance.workflow.invoke(initial_state)
    
    # Format output
    return format_analysis_output(result)

def format_analysis_output(result: AMLState) -> Dict[str, Any]:
    """Format analysis output for display/API response"""
    output = {
        "analysis_report": {
            "risk_score": result["risk_score"],
            "risk_level": _determine_risk_level(result["risk_score"]),
            "decision_path": " → ".join(result["decision_path"]),
            "workflow_complete": True
        },
        "findings": {
            "alerts": list(set(result["alerts"])),
            "risk_factors": result["risk_factors"],
            "sanctions_hits": result.get("sanction_hits", []),
            "pep_status": result.get("pep_status", False),
            "structuring_detected": result.get("structuring_detected", False),
            "smurfing_detected": result.get("smurfing_detected", False)
        },
        "llm_analysis": result.get("llm_analysis", {}),
        "reporting": {
            "status": result.get("reporting_status"),
            "case_id": result.get("case_id"),
            "sar_timestamp": result.get("sar_timestamp"),
            "review_status": result.get("review_status"),
            "review_deadline": result.get("review_deadline")
        }
    }
    
    # Add ground truth comparison if available
    if result.get("ground_truth_label") is not None:
        predicted_ml = 1 if result["risk_score"] >= 65 else 0
        output["model_performance"] = {
            "ground_truth": result["ground_truth_label"],
            "predicted": predicted_ml,
            "correct": predicted_ml == result["ground_truth_label"]
        }
    
    return output

def _determine_risk_level(score: int) -> str:
    """Map risk score to risk level"""
    if score >= 80:
        return "CRITICAL"
    elif score >= 65:
        return "HIGH"
    elif score >= 40:
        return "MEDIUM"
    else:
        return "LOW"

# Chat functionality
def chat_with_investigations(user_query: str, thread_id: str, llm: ChatOpenAI) -> Dict[str, Any]:
    """Chat with the AML system about investigations"""
    thread = get_chat_thread(thread_id)
    
    if not thread:
        return {
            "error": "Thread not found. Please create a new chat thread.",
            "thread_id": thread_id
        }
    
    # Simple response for now
    response = f"Based on the investigations in this thread, I can help you analyze AML cases. You asked: {user_query}"
    
    # Update chat history
    thread["chat_history"].append(HumanMessage(content=user_query))
    thread["chat_history"].append(AIMessage(content=response))
    update_chat_thread(thread_id, thread)
    
    # Calculate statistics
    stats = _calculate_investigation_statistics(thread["investigation_results"])
    
    return {
        "thread_id": thread_id,
        "response": response,
        "chat_history": thread["chat_history"],
        "investigation_summary": {
            "risk_level": "HIGH" if stats["high_risk"] > 0 else "MEDIUM" if stats["medium_risk"] > 0 else "LOW",
            "risk_score": stats["high_risk"] * 10 + stats["medium_risk"] * 5 + stats["low_risk"] * 1,
            "key_findings": [f"Total investigations: {stats['total']}", f"High risk cases: {stats['high_risk']}"],
            "recommendations": ["Review high-risk cases", "Monitor medium-risk cases"] if stats["high_risk"] > 0 else ["Continue monitoring"]
        },
        "statistics": stats,
        "timestamp": datetime.datetime.now().isoformat()
    }

def _calculate_investigation_statistics(investigations: List[Dict[str, Any]]) -> Dict[str, int]:
    """Calculate statistics across all investigations"""
    stats = {
        "total": len(investigations),
        "high_risk": 0,
        "medium_risk": 0,
        "low_risk": 0,
        "sar_filed": 0,
        "human_review": 0
    }
    
    for inv in investigations:
        risk_level = inv.get("analysis_report", {}).get("risk_level", "LOW")
        status = inv.get("reporting", {}).get("status")
        
        if risk_level in ["HIGH", "CRITICAL"]:
            stats["high_risk"] += 1
        elif risk_level == "MEDIUM":
            stats["medium_risk"] += 1
        else:
            stats["low_risk"] += 1
        
        if status == "SAR_FILED":
            stats["sar_filed"] += 1
        elif status == "HUMAN_REVIEW":
            stats["human_review"] += 1
    
    return stats

def query_investigations(
    prompt: str,
    thread_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Query investigations conversationally
    
    Args:
        prompt: User's prompt/query (first message starts new conversation)
        thread_id: Optional existing thread ID, creates new one if not provided
        
    Returns:
        Chat response with answer and thread_id
    """
    # Create thread if not provided or if thread doesn't exist
    if not thread_id or thread_id not in CHAT_THREADS:
        all_results = list(INVESTIGATION_RESULTS.values())
        thread_id = create_chat_thread(all_results)
        logger.info(f"Created new thread: {thread_id}")
    else:
        logger.info(f"Using existing thread: {thread_id}")
    
    workflow = ProductionAMLWorkflow()
    return chat_with_investigations(prompt, thread_id, workflow.llm)

# Global workflow instance
production_workflow = ProductionAMLWorkflow()

# Convenience function
def analyze_transaction(
    transaction: Dict[str, Any],
    customer: Dict[str, Any],
    thread_id: Optional[str] = None
) -> Dict[str, Any]:
    """Convenience function for running analysis"""
    result = run_analysis(transaction, customer, production_workflow)
    
    # Add to thread if provided
    if thread_id:
        add_investigation_to_thread(thread_id, result)
    
    # Store globally
    case_id = result.get("reporting", {}).get("case_id")
    if case_id:
        INVESTIGATION_RESULTS[case_id] = result
    
    return result
