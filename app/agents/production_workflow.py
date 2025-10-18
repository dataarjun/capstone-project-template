"""
Production-Ready AML Agent Workflow

Comprehensive multi-agent AML detection system implementing:
- Structuring and smurfing detection
- Cryptocurrency risk analysis
- PEP and sanctions screening
- Geographic risk assessment
- Behavioral anomaly detection
- Document analysis with pattern recognition
- Enhanced due diligence
- SAR generation
- Human review workflow
- Chat interface with thread management
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
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.core.logger import get_logger
from app.core.config_simple import settings

logger = get_logger(__name__)

# ============================================================================
# CONFIGURATION VARIABLES
# ============================================================================

# High-risk jurisdiction configurations
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

# High-risk banks for HI-Small_Trans dataset
HIGH_RISK_BANKS = ["03208", "03209", "0211050", "0245335"]

# Reporting thresholds
CTR_THRESHOLD = 10000.0  # Currency Transaction Report threshold
SUSPICIOUS_THRESHOLD = CTR_THRESHOLD * 0.95  # 95% of threshold

# Risk scoring weights
RISK_WEIGHTS = {
    "sanctions": 0.40,
    "pep": 0.35,
    "crypto": 0.25,
    "geographic": 0.20,
    "documents": 0.15,
    "behavioral": 0.10,
    "structuring": 0.30,
    "smurfing": 0.25
}

# ============================================================================
# STATE DEFINITIONS
# ============================================================================

class AMLState(TypedDict):
    """
    Complete state for AML workflow supporting both datasets
    """
    # Transaction data (unified across datasets)
    transaction: Dict[str, Any]
    customer: Dict[str, Any]
    
    # Dataset-specific fields
    from_bank: Optional[str]
    to_bank: Optional[str]
    payment_format: Optional[str]
    ground_truth_label: Optional[int]  # is_laundering from HI-Small_Trans
    
    # Analysis results
    risk_score: int  # 0-100
    alerts: List[str]
    investigation: Dict[str, Any]
    llm_analysis: Dict[str, Any]
    risk_factors: List[str]
    decision_path: List[str]
    
    # Screening results
    pep_status: Optional[bool]
    sanction_hits: List[str]
    documents: List[str]
    document_risks: List[str]
    
    # Asset-specific analysis
    asset_type: Optional[str]  # FIAT, CRYPTO, etc.
    crypto_details: Optional[Dict[str, Any]]
    
    # Geographic analysis
    origin_country: Optional[str]
    destination_country: Optional[str]
    intermediate_countries: List[str]
    
    # Pattern detection
    structuring_detected: bool
    smurfing_detected: bool
    layering_detected: bool
    
    # Reporting
    reporting_status: Optional[str]  # None, "SAR_FILED", "HUMAN_REVIEW"
    case_id: Optional[str]
    sar_timestamp: Optional[datetime.datetime]
    review_status: Optional[str]
    review_deadline: Optional[datetime.datetime]
    
    # Workflow control
    transaction_count: int
    workflow_complete: bool

class ChatState(TypedDict):
    """State for chat conversations with investigation context"""
    thread_id: str
    investigation_results: List[Dict[str, Any]]  # All investigation results
    chat_history: List[BaseMessage]
    created_at: datetime.datetime
    last_updated: datetime.datetime

# Global storage for chat threads (in production, use database)
CHAT_THREADS: Dict[str, ChatState] = {}
INVESTIGATION_RESULTS: Dict[str, Dict[str, Any]] = {}  # Store all investigation results

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_case_id() -> str:
    """Generate unique case ID using timestamp hash"""
    timestamp = str(datetime.datetime.now())
    return hashlib.sha256(timestamp.encode()).hexdigest()[:12]

def check_pep_database(name: str) -> bool:
    """
    Check if customer is a Politically Exposed Person
    Uses keyword matching for demonstration
    """
    pep_keywords = ["gov", "minister", "official", "senator", 
                    "president", "director", "ambassador"]
    return any(keyword in name.lower() for keyword in pep_keywords)

def check_sanctions_list(entities: List[str]) -> List[str]:
    """Check entities against sanctions list"""
    hits = []
    for entity in entities:
        for sanctioned in SANCTIONED_ENTITIES:
            if sanctioned.lower() in entity.lower():
                hits.append(entity)
    return hits

def load_prompts() -> Dict[str, Any]:
    """Load prompts from YAML files"""
    prompts = {}
    prompt_dir = Path(__file__).parent.parent.parent / "prompts"
    
    prompt_files = [
        "production_prompts.yaml",
        "risk_assessment.yaml",
        "sar_generation.yaml",
        "behavior_analysis.yaml",
        "document_analysis.yaml",
        "edd_report.yaml"
    ]
    
    for file in prompt_files:
        path = prompt_dir / file
        if path.exists():
            with open(path, encoding='utf-8') as f:
                prompts[file.replace(".yaml", "")] = yaml.safe_load(f)
    
    return prompts

def update_path(state: AMLState, step: str) -> AMLState:
    """Update decision path tracking"""
    return {**state, "decision_path": state["decision_path"] + [step]}

def unify_transaction_data(transaction: Dict[str, Any]) -> Dict[str, Any]:
    """
    Unify transaction data from both datasets into common format
    Handles both HI-Small_Trans and operational transaction formats
    """
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

# ============================================================================
# CHAT THREAD MANAGEMENT
# ============================================================================

def create_chat_thread(investigation_results: Optional[List[Dict[str, Any]]] = None) -> str:
    """
    Create a new chat thread with UUID
    
    Args:
        investigation_results: Optional initial investigation results to load
    
    Returns:
        thread_id: UUID string for the chat thread
    """
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

# ============================================================================
# LLM-DRIVEN ANALYSIS NODES
# ============================================================================

async def async_document_analysis(state: AMLState, llm: ChatOpenAI) -> AMLState:
    """
    Enhanced document analysis with LLM pattern recognition
    Detects: INVOICE_MISMATCH, PHANTOM_SHIPMENT, PROHIBITED_GOODS,
             SHELL_COMPANY, DARKNET_CONNECTION, TRADE_BASED_LAUNDERING
    """
    state = update_path(state, "document_analysis")
    
    if not state.get("documents"):
        return {**state, "alerts": state["alerts"] + ["MISSING_DOCUMENTS"]}
    
    # Create document analysis prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert AML document analyst. Analyze documents for risk indicators.
        
        Respond with RISK CODES from this list:
        - INVOICE_MISMATCH: Invoice values don't match customs/shipping
        - PHANTOM_SHIPMENT: Shipment documentation inconsistencies
        - PROHIBITED_GOODS: Evidence of illegal goods trading
        - SHELL_COMPANY: Shell company involvement indicators
        - DARKNET_CONNECTION: Links to darknet markets
        - TRADE_BASED_LAUNDERING: Trade-based money laundering patterns
        
        Provide ONLY the risk codes that apply, one per line."""),
        ("human", "Documents: {documents}")
    ])
    
    chain = prompt | llm | StrOutputParser()
    analysis = await chain.ainvoke({"documents": state["documents"]})
    
    # Extract risk codes using regex
    risk_codes = re.findall(r"\b[A-Z_]{4,}\b", analysis)
    
    return {
        **state,
        "llm_analysis": {
            **state.get("llm_analysis", {}),
            "document_risks": risk_codes,
            "document_analysis_detail": analysis
        },
        "risk_factors": state["risk_factors"] + risk_codes,
        "document_risks": risk_codes
    }

def document_analysis(state: AMLState, llm: ChatOpenAI) -> AMLState:
    """Synchronous wrapper for document analysis"""
    return asyncio.run(async_document_analysis(state, llm))

def geographic_risk_assessment(state: AMLState) -> AMLState:
    """
    Comprehensive geographic risk assessment
    Checks origin, destination, and intermediate countries
    """
    state = update_path(state, "geo_analysis")
    tx = state["transaction"]
    risk_factors = []
    
    # Collect all locations in transaction path
    locations = [
        tx.get("origin_country", ""),
        tx.get("destination_country", ""),
        tx.get("country", "")  # Operational dataset field
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

async def async_behavioral_analysis(state: AMLState, llm: ChatOpenAI) -> AMLState:
    """
    Enhanced behavioral analysis with structuring detection
    Uses LLM to analyze transaction patterns
    """
    state = update_path(state, "behavior_analysis")
    history = state["customer"].get("transaction_history", [])
    current = state["transaction"]
    
    # Structuring detection
    current_timestamp = current.get("timestamp", datetime.datetime.now())
    if isinstance(current_timestamp, str):
        current_timestamp = datetime.datetime.fromisoformat(current_timestamp.replace('Z', '+00:00'))
    
    recent_txs = []
    for tx in history:
        tx_timestamp = tx.get("timestamp", current_timestamp)
        if isinstance(tx_timestamp, str):
            tx_timestamp = datetime.datetime.fromisoformat(tx_timestamp.replace('Z', '+00:00'))
        
        if (current_timestamp - tx_timestamp).days < 1:
            recent_txs.append(tx)
    
    recent_txs.append(current)
    
    structuring_alerts = []
    
    # Check for multiple sub-threshold transactions
    if len(recent_txs) > 3:
        if all(float(tx.get("amount", 0)) < CTR_THRESHOLD for tx in recent_txs):
            structuring_alerts.append("STRUCTURING_PATTERN")
    
    # Check for uniform transaction amounts (smurfing indicator)
    if len(recent_txs) > 5:
        amounts = [float(tx.get("amount", 0)) for tx in recent_txs]
        if len(amounts) > 1 and statistics.stdev(amounts) < 500:
            structuring_alerts.append("UNIFORM_TRANSACTIONS")
    
    # LLM analysis for complex patterns
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert AML behavioral analyst. 
        Analyze transaction patterns for suspicious behavior.
        
        Focus on:
        - Structuring (breaking large amounts into small transactions)
        - Smurfing (multiple accounts coordinating)
        - Unusual velocity or frequency
        - Deviation from customer baseline
        
        Provide risk codes:
        - RAPID_ESCALATION
        - VELOCITY_SPIKE
        - BASELINE_DEVIATION
        - COORDINATED_ACTIVITY"""),
        ("human", """Current Transaction: {current}
        Transaction History: {history}
        Recent Transactions: {recent}
        
        Identify suspicious behavioral patterns.""")
    ])
    
    chain = prompt | llm | StrOutputParser()
    analysis = await chain.ainvoke({
        "current": current,
        "history": history[:10],  # Last 10 transactions
        "recent": recent_txs
    })
    
    behavioral_codes = re.findall(r"\b[A-Z_]{4,}\b", analysis)
            
            return {
                **state,
        "alerts": state["alerts"] + structuring_alerts,
        "risk_factors": state["risk_factors"] + behavioral_codes,
        "llm_analysis": {
            **state.get("llm_analysis", {}),
            "behavioral_analysis": analysis
        },
        "structuring_detected": "STRUCTURING_PATTERN" in structuring_alerts
    }

def behavioral_analysis(state: AMLState, llm: ChatOpenAI) -> AMLState:
    """Synchronous wrapper"""
    return asyncio.run(async_behavioral_analysis(state, llm))

async def async_crypto_risk_analysis(state: AMLState, llm: ChatOpenAI) -> AMLState:
    """
    Cryptocurrency-specific risk assessment
    Detects mixer usage, darknet connections, new wallets
    """
    state = update_path(state, "crypto_analysis")
    
    if state["transaction"].get("asset_type") != "CRYPTO":
        return state
    
    details = state["transaction"].get("crypto_details", {})
    risks = []
    
    # Rule-based detection
    if details.get("mixer_used"):
        risks.append("CRYPTO_MIXER")
    if details.get("darknet_market") in DARKNET_MARKETS:
        risks.append("DARKNET_CONNECTION")
    if details.get("wallet_age_days", 0) < 7:
        risks.append("NEW_WALLET")
    if details.get("cross_chain_swaps", 0) > 3:
        risks.append("COMPLEX_ROUTING")
    
    # LLM analysis for crypto patterns
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a cryptocurrency AML specialist.
        Analyze crypto transaction for money laundering indicators.
        
        Risk factors:
        - Privacy coin usage (Monero, Zcash)
        - Mixing services / tumblers
        - Darknet market connections
        - Chain hopping / complex routing
        - New wallet with large transactions
        
        Provide risk codes."""),
        ("human", "Crypto Details: {crypto_details}")
    ])
    
    chain = prompt | llm | StrOutputParser()
    analysis = await chain.ainvoke({"crypto_details": details})
    
    llm_risks = re.findall(r"\b[A-Z_]{4,}\b", analysis)
    risks.extend(llm_risks)
    
            return {
                **state,
        "risk_factors": state["risk_factors"] + risks,
        "crypto_details": details,
        "llm_analysis": {
            **state.get("llm_analysis", {}),
            "crypto_analysis": analysis
        }
    }

def crypto_risk_analysis(state: AMLState, llm: ChatOpenAI) -> AMLState:
    """Synchronous wrapper"""
    return asyncio.run(async_crypto_risk_analysis(state, llm))

def sanctions_screening(state: AMLState) -> AMLState:
    """
    Screen transaction parties against sanctions lists
    """
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
    """
    Check for Politically Exposed Person status
    """
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

async def async_enhanced_due_diligence(state: AMLState, llm: ChatOpenAI) -> AMLState:
    """
    Deep AML investigation using LLM
    Combines all risk factors for comprehensive analysis
    """
    state = update_path(state, "enhanced_dd")
    
    # Load EDD prompt from YAML
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are conducting Enhanced Due Diligence for AML compliance.
        
        Analyze all available information and provide critical risk indicators.
        
        Consider:
        - PEP status and sanctions hits
        - Geographic risks and jurisdictions
        - Transaction patterns and amounts
        - Document analysis results
        - Behavioral anomalies
        - Crypto risk factors
        
        Identify CRITICAL RISK INDICATORS in UPPERCASE.
        Provide detailed analysis and recommendations."""),
        ("human", """
        PEP Status: {pep_status}
        Sanctions Hits: {sanction_hits}
        Risk Factors: {risk_factors}
        Transaction: {transaction}
        Customer: {customer}
        LLM Analysis: {llm_analysis}
        
        Conduct comprehensive enhanced due diligence.""")
    ])
    
    chain = prompt | llm | StrOutputParser()
    analysis = await chain.ainvoke({
        "pep_status": state.get("pep_status"),
        "sanction_hits": state.get("sanction_hits", []),
        "risk_factors": state.get("risk_factors", []),
        "transaction": state.get("transaction"),
        "customer": state.get("customer"),
        "llm_analysis": state.get("llm_analysis", {})
    })
    
    # Extract critical risk indicators
    critical_risks = re.findall(r"\b[A-Z_]{3,}\b", analysis)
            
            return {
                **state,
        "risk_factors": state["risk_factors"] + critical_risks,
        "llm_analysis": {
            **state["llm_analysis"],
            "edd_report": analysis,
            "critical_risks": critical_risks
        }
    }

def enhanced_due_diligence(state: AMLState, llm: ChatOpenAI) -> AMLState:
    """Synchronous wrapper"""
    return asyncio.run(async_enhanced_due_diligence(state, llm))

def risk_scoring(state: AMLState) -> AMLState:
    """
    Comprehensive weighted risk scoring
    Based on reference implementation with proper factor weighting
    """
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

async def async_generate_sar(state: AMLState, llm: ChatOpenAI) -> AMLState:
    """
    Generate Suspicious Activity Report using LLM
    """
    state = update_path(state, "sar_generation")
    
    # Load SAR prompt from YAML
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are generating a Suspicious Activity Report (SAR) for FinCEN.
        
        Create a comprehensive, legally compliant SAR with:
        - Clear title
        - Executive summary
        - Specific indicators (red flags)
        - Counterparty context
        - Chronological timeline
        - Regulatory recommendation
        
        Use factual, objective language without speculation."""),
        ("human", """
        Case ID: {case_id}
        Transaction: {transaction}
        Customer: {customer}
        Risk Score: {risk_score}
        Risk Factors: {risk_factors}
        Sanctions Hits: {sanction_hits}
        PEP Status: {pep_status}
        LLM Analysis: {llm_analysis}
        
        Generate SAR in JSON format with title, summary, indicators, 
        counterparty_context, timeline, recommendation.""")
    ])
    
    chain = prompt | llm | StrOutputParser()
    
    case_id = generate_case_id()
    
    sar_content = await chain.ainvoke({
        "case_id": case_id,
        "transaction": state["transaction"],
        "customer": state["customer"],
        "risk_score": state["risk_score"],
        "risk_factors": state["risk_factors"],
        "sanction_hits": state.get("sanction_hits", []),
        "pep_status": state.get("pep_status"),
        "llm_analysis": state.get("llm_analysis", {})
            })
            
            return {
                **state,
        "reporting_status": "SAR_FILED",
        "case_id": case_id,
        "sar_timestamp": datetime.datetime.now(),
        "llm_analysis": {
            **state["llm_analysis"],
            "sar_report": sar_content
        }
    }

def generate_sar(state: AMLState, llm: ChatOpenAI) -> AMLState:
    """Synchronous wrapper"""
    return asyncio.run(async_generate_sar(state, llm))

def human_review(state: AMLState) -> AMLState:
    """
    Route to human review for medium-risk cases
    """
    state = update_path(state, "human_review")
    
            return {
                **state,
        "reporting_status": "HUMAN_REVIEW",
        "review_status": "PENDING",
        "review_deadline": datetime.datetime.now() + datetime.timedelta(hours=24)
    }

# ============================================================================
# CONDITIONAL ROUTING LOGIC
# ============================================================================

def route_initial_screening(state: AMLState) -> str:
    """
    Route based on transaction characteristics
    """
    tx = state["transaction"]
    customer = state["customer"]
    
    # Crypto transactions go to crypto analysis
    if tx.get("asset_type") == "CRYPTO":
        return "CRYPTO_TRANSACTION"
    
    # Large transactions (>$100k) go to geographic analysis
    if float(tx.get("amount", 0)) > 100000:
        return "LARGE_TRANSACTION"
    
    # New accounts (<7 days) go straight to EDD
    if customer.get("account_age_days", 365) < 7:
        return "NEW_ACCOUNT"
    
    # High-risk bank in HI-Small_Trans dataset
    if tx.get("from_bank") in HIGH_RISK_BANKS or tx.get("to_bank") in HIGH_RISK_BANKS:
        return "HIGH_RISK_BANK"
    
    # Standard flow
    return "STANDARD_FLOW"

def route_crypto_analysis(state: AMLState) -> str:
    """
    Route after crypto analysis
    """
    crypto_risks = [rf for rf in state["risk_factors"] if "CRYPTO" in rf]
    
    if len(crypto_risks) >= 2:  # Multiple crypto risks
        return "HIGH_RISK_CRYPTO"
    
    return "NORMAL_CRYPTO"

def route_sanctions_check(state: AMLState) -> str:
    """
    Route based on sanctions screening results
    """
    if state.get("sanction_hits"):
        return "SANCTION_HIT"
    
    return "NO_HIT"

def route_pep_check(state: AMLState) -> str:
    """
    Route based on PEP status
    """
    if state.get("pep_status"):
        return "PEP_FOUND"
    
    return "NO_PEP"

def route_risk_score(state: AMLState) -> str:
    """
    Final routing based on risk score
    """
    risk_score = state.get("risk_score", 0)
    
    # Critical/High risk (>=65) -> SAR
    if risk_score >= 65:
        return "HIGH_RISK"
    
    # Medium risk (40-64) -> Human review
    if risk_score >= 40:
        return "MEDIUM_RISK"
    
    # Low risk (<40) -> Close case
    return "LOW_RISK"

# ============================================================================
# WORKFLOW GRAPH CONSTRUCTION
# ============================================================================

class ProductionAMLWorkflow:
    """
    Complete LLM-driven AML workflow implementation
    Following reference architecture with comprehensive nodes
    """
    
    def __init__(self):
        """Initialize workflow with LLM and memory"""
        self.llm = self._initialize_llm()
        self.memory = MemorySaver()
        self.prompts = load_prompts()
        self.workflow = self._build_workflow()
    
    def _initialize_llm(self) -> ChatOpenAI:
        """Initialize OpenAI LLM"""
        return ChatOpenAI(
            model="gpt-4o",
            temperature=0.1,
            api_key=settings.OPENAI_API_KEY
        )
    
    def _build_workflow(self) -> StateGraph:
        """
        Build complete workflow graph with all nodes and conditional edges
        """
        workflow = StateGraph(AMLState)
        
        # Add all nodes
        workflow.add_node("initial_screening", 
                         lambda s: update_path(s, "start"))
        workflow.add_node("crypto_analysis", 
                         lambda s: crypto_risk_analysis(s, self.llm))
        workflow.add_node("geo_analysis", 
                         lambda s: geographic_risk_assessment(s))
        workflow.add_node("document_check", 
                         lambda s: document_analysis(s, self.llm))
        workflow.add_node("behavior_check", 
                         lambda s: behavioral_analysis(s, self.llm))
        workflow.add_node("sanctions_check", 
                         lambda s: sanctions_screening(s))
        workflow.add_node("pep_check", 
                         lambda s: pep_screening(s))
        workflow.add_node("edd", 
                         lambda s: enhanced_due_diligence(s, self.llm))
        workflow.add_node("score_risk", 
                         lambda s: risk_scoring(s))
        workflow.add_node("generate_sar", 
                         lambda s: generate_sar(s, self.llm))
        workflow.add_node("human_review", 
                         lambda s: human_review(s))
        
        # Set entry point
        workflow.set_entry_point("initial_screening")
        
        # Add conditional edges following reference architecture
        workflow.add_conditional_edges(
            "initial_screening",
            route_initial_screening,
            {
                "CRYPTO_TRANSACTION": "crypto_analysis",
                "LARGE_TRANSACTION": "geo_analysis",
                "NEW_ACCOUNT": "edd",
                "HIGH_RISK_BANK": "geo_analysis",
                "STANDARD_FLOW": "document_check"
            }
        )
        
        workflow.add_conditional_edges(
            "crypto_analysis",
            route_crypto_analysis,
            {
                "HIGH_RISK_CRYPTO": "edd",
                "NORMAL_CRYPTO": "document_check"
            }
        )
        
        # Standard analysis flow
        workflow.add_edge("geo_analysis", "document_check")
        workflow.add_edge("document_check", "behavior_check")
        workflow.add_edge("behavior_check", "sanctions_check")
        
        workflow.add_conditional_edges(
            "sanctions_check",
            route_sanctions_check,
            {
                "SANCTION_HIT": "generate_sar",
                "NO_HIT": "pep_check"
            }
        )
        
        workflow.add_conditional_edges(
            "pep_check",
            route_pep_check,
            {
                "PEP_FOUND": "edd",
                "NO_PEP": "score_risk"
            }
        )
        
        workflow.add_edge("edd", "score_risk")
        
        workflow.add_conditional_edges(
            "score_risk",
            route_risk_score,
            {
                "HIGH_RISK": "generate_sar",
                "MEDIUM_RISK": "human_review",
                "LOW_RISK": END
            }
        )
        
        workflow.add_edge("generate_sar", END)
        workflow.add_edge("human_review", END)
        
        return workflow.compile(checkpointer=self.memory)

# ============================================================================
# EXECUTION INTERFACE
# ============================================================================

def run_analysis(
    transaction: Dict[str, Any],
    customer: Dict[str, Any],
    workflow_instance: ProductionAMLWorkflow
) -> Dict[str, Any]:
    """
    Execute complete AML workflow analysis
    Supports both dataset formats
    """
    # Unify transaction data
    unified_tx = unify_transaction_data(transaction)
    
    # Initialize state
    initial_state = AMLState(
        transaction=unified_tx,
        customer=customer,
        from_bank=transaction.get("from_bank"),
        to_bank=transaction.get("to_bank"),
        payment_format=transaction.get("payment_format"),
        ground_truth_label=transaction.get("is_laundering"),
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
    """
    Format analysis output for display/API response
    """
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

# ============================================================================
# CHAT INTERFACE WITH THREAD MANAGEMENT
# ============================================================================

async def async_chat_with_investigations(
    user_query: str,
    thread_id: str,
    llm: ChatOpenAI
) -> Dict[str, Any]:
    """
    Chat with the AML system about investigations
    Answers analytical questions like:
    - "How many accounts have AML cases?"
    - "Why are they flagged as fraudulent?"
    - "Show me all high-risk cases"
    """
    thread = get_chat_thread(thread_id)
    
    if not thread:
            return {
            "error": "Thread not found. Please create a new chat thread.",
            "thread_id": thread_id
        }
    
    # Prepare investigation summary for context
    investigation_summary = _prepare_investigation_summary(thread["investigation_results"])
    
    # Create chat prompt with analytical capabilities
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert AML Investigation Assistant with access to complete investigation results.

Your capabilities:
- Answer analytical questions about AML cases and investigations
- Provide statistics and summaries (e.g., "How many accounts have AML cases?")
- Explain why accounts are flagged as fraudulent
- Compare risk levels and patterns across investigations
- Provide insights on suspicious activities and risk factors

Available Investigation Data:
                {investigation_summary}
                
Statistics:
- Total Investigations: {total_investigations}
- High Risk Cases: {high_risk_count}
- Medium Risk Cases: {medium_risk_count}
- SAR Filed: {sar_filed_count}
- Human Review Required: {human_review_count}

When answering:
1. Be specific and cite case IDs when relevant
2. Provide quantitative answers when asked for counts
3. Explain risk factors and patterns clearly
4. Reference specific findings from investigations
5. Use professional AML terminology

Previous conversation:
{chat_history}"""),
                ("human", "{user_query}")
            ])
            
    # Get statistics
    stats = _calculate_investigation_statistics(thread["investigation_results"])
    
    # Format chat history
    chat_history_text = "\n".join([
        f"{'User' if isinstance(msg, HumanMessage) else 'Assistant'}: {msg.content}"
        for msg in thread["chat_history"][-6:]  # Last 3 exchanges
    ])
    
    chain = prompt | llm | StrOutputParser()
    
    response = await chain.ainvoke({
                "user_query": user_query,
        "investigation_summary": investigation_summary,
        "total_investigations": stats["total"],
        "high_risk_count": stats["high_risk"],
        "medium_risk_count": stats["medium_risk"],
        "sar_filed_count": stats["sar_filed"],
        "human_review_count": stats["human_review"],
        "chat_history": chat_history_text or "No previous conversation"
            })
            
            # Update chat history
    thread["chat_history"].append(HumanMessage(content=user_query))
    thread["chat_history"].append(AIMessage(content=response))
    update_chat_thread(thread_id, thread)
            
            return {
        "thread_id": thread_id,
        "response": response,
        "statistics": stats,
        "timestamp": datetime.datetime.now().isoformat()
    }

def chat_with_investigations(user_query: str, thread_id: str, llm: ChatOpenAI) -> Dict[str, Any]:
    """Synchronous wrapper for chat"""
    return asyncio.run(async_chat_with_investigations(user_query, thread_id, llm))

def _prepare_investigation_summary(investigations: List[Dict[str, Any]]) -> str:
    """Prepare concise summary of all investigations for LLM context"""
    if not investigations:
        return "No investigations available yet."
    
    summary_parts = []
    for inv in investigations:
        report = inv.get("analysis_report", {})
        findings = inv.get("findings", {})
        reporting = inv.get("reporting", {})
        
        summary = f"""
Case ID: {reporting.get('case_id', 'N/A')}
Risk Score: {report.get('risk_score', 0)}/100 ({report.get('risk_level', 'UNKNOWN')})
Decision Path: {report.get('decision_path', 'N/A')}
Alerts: {', '.join(findings.get('alerts', []))}
Risk Factors: {', '.join(findings.get('risk_factors', [])[:5])}...
Sanctions: {len(findings.get('sanctions_hits', []))} hits
PEP: {'Yes' if findings.get('pep_status') else 'No'}
Structuring: {'Detected' if findings.get('structuring_detected') else 'No'}
Status: {reporting.get('status', 'N/A')}
"""
        summary_parts.append(summary.strip())
    
    return "\n---\n".join(summary_parts)

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

# ============================================================================
# GLOBAL WORKFLOW INSTANCE AND API
# ============================================================================

# Create global workflow instance
production_workflow = ProductionAMLWorkflow()

# Convenience function
def analyze_transaction(
    transaction: Dict[str, Any],
    customer: Dict[str, Any],
    thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
    Convenience function for running analysis
    Optionally adds result to chat thread
        
        Args:
        transaction: Transaction data
        customer: Customer data
        thread_id: Optional thread ID to add results to
            
        Returns:
        Investigation results
    """
    result = run_analysis(transaction, customer, production_workflow)
    
    # Add to thread if provided
    if thread_id:
        add_investigation_to_thread(thread_id, result)
    
    # Store globally
    case_id = result.get("reporting", {}).get("case_id")
    if case_id:
        INVESTIGATION_RESULTS[case_id] = result
            
            return result
            
def analyze_batch(
    transactions: List[Dict[str, Any]],
    customers: Dict[str, Dict[str, Any]],
    create_thread: bool = True
    ) -> Dict[str, Any]:
        """
    Batch process multiple transactions
    Creates a chat thread automatically for querying results
        
        Args:
        transactions: List of transactions
        customers: Customer lookup dictionary
        create_thread: Whether to create a chat thread
            
        Returns:
        Dict with results and thread_id
    """
    results = []
    
    # Create thread if requested
    thread_id = create_chat_thread() if create_thread else None
    
    for tx in transactions:
        customer_id = tx.get("from_account", tx.get("customer_id"))
        customer = customers.get(customer_id, {
            "name": f"Customer_{customer_id}",
            "account_age_days": 30,
            "transaction_history": []
        })
        
        result = analyze_transaction(tx, customer, thread_id)
        results.append(result)
    
            return {
        "thread_id": thread_id,
        "results": results,
        "total_processed": len(results),
        "statistics": _calculate_investigation_statistics(results)
    }

def query_investigations(
    query: str,
    thread_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Query investigations conversationally
    
    Args:
        query: Natural language query (e.g., "How many accounts have AML cases?")
        thread_id: Optional existing thread ID, creates new one if not provided
        
    Returns:
        Chat response with answer
    """
    # Create thread if not provided
    if not thread_id:
        # Load all investigations into new thread
        all_results = list(INVESTIGATION_RESULTS.values())
        thread_id = create_chat_thread(all_results)
    
    return chat_with_investigations(query, thread_id, production_workflow.llm)
