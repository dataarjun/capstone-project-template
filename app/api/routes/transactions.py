"""
Transaction API Routes

FastAPI endpoints for querying, checking, and inserting transaction records
into the PostgreSQL database.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime
import pandas as pd
from pydantic import BaseModel, Field

from app.services.postgres_transaction_service import PostgreSQLTransactionService
from app.core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/transactions", tags=["transactions"])

# Pydantic models for request/response
class TransactionResponse(BaseModel):
    """Transaction response model"""
    transaction_id: str
    sender_account_id: str
    receiver_account_id: str
    tx_type: str
    amount: float
    timestamp: int
    is_fraud: bool
    alert_id: int
    created_at: str

class TransactionStatsResponse(BaseModel):
    """Transaction statistics response model"""
    total_transactions: int
    unique_senders: int
    unique_receivers: int
    min_amount: float
    max_amount: float
    avg_amount: float
    fraud_count: int
    earliest_transaction: str
    latest_transaction: str

class TransactionInsertRequest(BaseModel):
    """Single transaction insert request"""
    transaction_id: int
    sender_account_id: int
    receiver_account_id: int
    tx_type: str
    amount: float
    timestamp: int
    is_fraud: bool = False
    alert_id: int = -1

class BulkTransactionInsertRequest(BaseModel):
    """Bulk transaction insert request"""
    transactions: List[TransactionInsertRequest]

class TransactionQueryParams(BaseModel):
    """Transaction query parameters"""
    limit: int = Field(default=100, ge=1, le=10000)
    offset: int = Field(default=0, ge=0)
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    fraud_only: bool = False
    tx_type: Optional[str] = None
    sender_account_id: Optional[int] = None
    receiver_account_id: Optional[int] = None

# Dependency to get transaction service
async def get_transaction_service():
    """Get transaction service dependency"""
    service = PostgreSQLTransactionService()
    await service.connect()
    try:
        yield service
    finally:
        await service.disconnect()

@router.get("/health", summary="Check database health")
async def health_check():
    """Check if the transaction database is healthy"""
    try:
        service = PostgreSQLTransactionService()
        await service.connect()
        
        # Test basic connection
        stats = await service.get_transaction_statistics()
        
        await service.disconnect()
        
        return {
            "status": "healthy",
            "database": "postgresql",
            "table": "csv_transactions",
            "total_transactions": stats.get('total_transactions', 0),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error("Health check failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Database health check failed: {str(e)}") from e

@router.get("/stats", response_model=TransactionStatsResponse, summary="Get transaction statistics")
async def get_transaction_stats(service: PostgreSQLTransactionService = Depends(get_transaction_service)):
    """Get comprehensive transaction statistics"""
    try:
        stats = await service.get_transaction_statistics()
        
        if not stats:
            raise HTTPException(status_code=404, detail="No transaction data found")
        
        return TransactionStatsResponse(
            total_transactions=stats.get('total_transactions', 0),
            unique_senders=stats.get('unique_senders', 0),
            unique_receivers=stats.get('unique_receivers', 0),
            min_amount=float(stats.get('min_amount', 0)),
            max_amount=float(stats.get('max_amount', 0)),
            avg_amount=float(stats.get('avg_amount', 0)),
            fraud_count=stats.get('fraud_count', 0),
            earliest_transaction=stats.get('earliest_transaction', '').isoformat() if stats.get('earliest_transaction') else '',
            latest_transaction=stats.get('latest_transaction', '').isoformat() if stats.get('latest_transaction') else ''
        )
    except Exception as e:
        logger.error("Failed to get transaction stats: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}") from e

@router.get("/", response_model=List[TransactionResponse], summary="Get transactions")
async def get_transactions(
    limit: int = Query(default=100, ge=1, le=10000, description="Number of transactions to retrieve"),
    offset: int = Query(default=0, ge=0, description="Number of transactions to skip"),
    min_amount: Optional[float] = Query(default=None, description="Minimum transaction amount"),
    max_amount: Optional[float] = Query(default=None, description="Maximum transaction amount"),
    fraud_only: bool = Query(default=False, description="Only return fraud transactions"),
    tx_type: Optional[str] = Query(default=None, description="Filter by transaction type"),
    sender_account_id: Optional[int] = Query(default=None, description="Filter by sender account ID"),
    receiver_account_id: Optional[int] = Query(default=None, description="Filter by receiver account ID"),
    service: PostgreSQLTransactionService = Depends(get_transaction_service)
):
    """Get transactions with optional filtering"""
    try:
        # Get transactions based on filters
        if fraud_only:
            transactions = await service.get_fraud_transactions(limit=limit)
        elif min_amount is not None:
            transactions = await service.get_high_value_transactions(min_amount=min_amount, limit=limit)
        else:
            transactions = await service.get_transactions_for_batch_processing(
                batch_size=limit, offset=offset
            )
        
        # Apply additional filters if needed
        if tx_type:
            transactions = [t for t in transactions if t.get('tx_type', '').lower() == tx_type.lower()]
        
        if sender_account_id:
            transactions = [t for t in transactions if int(t.get('sender_account_id', 0)) == sender_account_id]
        
        if receiver_account_id:
            transactions = [t for t in transactions if int(t.get('receiver_account_id', 0)) == receiver_account_id]
        
        if max_amount is not None:
            transactions = [t for t in transactions if t.get('amount', 0) <= max_amount]
        
        # Convert to response format
        response_transactions = []
        for txn in transactions:
            response_transactions.append(TransactionResponse(
                transaction_id=txn['transaction_id'],
                sender_account_id=txn['sender_account_id'],
                receiver_account_id=txn['receiver_account_id'],
                tx_type=txn.get('tx_type', ''),
                amount=txn['amount'],
                timestamp=txn.get('original_timestamp', 0),
                is_fraud=txn.get('is_fraud', False),
                alert_id=txn.get('alert_id', -1),
                created_at=txn.get('created_at', '')
            ))
        
        return response_transactions
        
    except Exception as e:
        logger.error("Failed to get transactions: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve transactions: {str(e)}") from e

@router.get("/{transaction_id}", response_model=TransactionResponse, summary="Get transaction by ID")
async def get_transaction_by_id(
    transaction_id: str,
    service: PostgreSQLTransactionService = Depends(get_transaction_service)
):
    """Get a specific transaction by ID"""
    try:
        transaction = await service.get_transaction_by_id(transaction_id)
        
        if not transaction:
            raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found")
        
        return TransactionResponse(
            transaction_id=transaction['transaction_id'],
            sender_account_id=transaction['sender_account_id'],
            receiver_account_id=transaction['receiver_account_id'],
            tx_type=transaction.get('tx_type', ''),
            amount=transaction['amount'],
            timestamp=transaction.get('original_timestamp', 0),
            is_fraud=transaction.get('is_fraud', False),
            alert_id=transaction.get('alert_id', -1),
            created_at=transaction.get('created_at', '')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get transaction %s: %s", transaction_id, e)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve transaction: {str(e)}") from e

@router.get("/fraud/list", response_model=List[TransactionResponse], summary="Get fraud transactions")
async def get_fraud_transactions(
    limit: int = Query(default=100, ge=1, le=1000, description="Number of fraud transactions to retrieve"),
    service: PostgreSQLTransactionService = Depends(get_transaction_service)
):
    """Get transactions marked as fraud"""
    try:
        fraud_transactions = await service.get_fraud_transactions(limit=limit)
        
        response_transactions = []
        for txn in fraud_transactions:
            response_transactions.append(TransactionResponse(
                transaction_id=txn['transaction_id'],
                sender_account_id=txn['sender_account_id'],
                receiver_account_id=txn['receiver_account_id'],
                tx_type=txn.get('tx_type', ''),
                amount=txn['amount'],
                timestamp=txn.get('original_timestamp', 0),
                is_fraud=txn.get('is_fraud', False),
                alert_id=txn.get('alert_id', -1),
                created_at=txn.get('created_at', '')
            ))
        
        return response_transactions
        
    except Exception as e:
        logger.error("Failed to get fraud transactions: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve fraud transactions: {str(e)}") from e

@router.get("/high-value/list", response_model=List[TransactionResponse], summary="Get high-value transactions")
async def get_high_value_transactions(
    min_amount: float = Query(default=10000.0, ge=0, description="Minimum transaction amount"),
    limit: int = Query(default=100, ge=1, le=1000, description="Number of high-value transactions to retrieve"),
    service: PostgreSQLTransactionService = Depends(get_transaction_service)
):
    """Get high-value transactions"""
    try:
        high_value_transactions = await service.get_high_value_transactions(
            min_amount=min_amount, limit=limit
        )
        
        response_transactions = []
        for txn in high_value_transactions:
            response_transactions.append(TransactionResponse(
                transaction_id=txn['transaction_id'],
                sender_account_id=txn['sender_account_id'],
                receiver_account_id=txn['receiver_account_id'],
                tx_type=txn.get('tx_type', ''),
                amount=txn['amount'],
                timestamp=txn.get('original_timestamp', 0),
                is_fraud=txn.get('is_fraud', False),
                alert_id=txn.get('alert_id', -1),
                created_at=txn.get('created_at', '')
            ))
        
        return response_transactions
        
    except Exception as e:
        logger.error("Failed to get high-value transactions: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve high-value transactions: {str(e)}") from e

@router.post("/", response_model=Dict[str, Any], summary="Insert single transaction")
async def insert_transaction(
    transaction: TransactionInsertRequest,
    service: PostgreSQLTransactionService = Depends(get_transaction_service)
):
    """Insert a single transaction"""
    try:
        # Prepare transaction data for insertion
        
        # Insert into database
        await service.connection.execute("""
            INSERT INTO csv_transactions 
            (transaction_id, sender_account_id, receiver_account_id, tx_type, amount, timestamp, is_fraud, alert_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (transaction_id) DO UPDATE SET
                sender_account_id = EXCLUDED.sender_account_id,
                receiver_account_id = EXCLUDED.receiver_account_id,
                tx_type = EXCLUDED.tx_type,
                amount = EXCLUDED.amount,
                timestamp = EXCLUDED.timestamp,
                is_fraud = EXCLUDED.is_fraud,
                alert_id = EXCLUDED.alert_id,
                updated_at = CURRENT_TIMESTAMP
        """, 
        transaction.transaction_id,
        transaction.sender_account_id,
        transaction.receiver_account_id,
        transaction.tx_type,
        transaction.amount,
        transaction.timestamp,
        transaction.is_fraud,
        transaction.alert_id
        )
        
        return {
            "status": "success",
            "message": f"Transaction {transaction.transaction_id} inserted successfully",
            "transaction_id": str(transaction.transaction_id),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to insert transaction: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to insert transaction: {str(e)}") from e

@router.post("/bulk", response_model=Dict[str, Any], summary="Insert multiple transactions")
async def insert_bulk_transactions(
    request: BulkTransactionInsertRequest,
    background_tasks: BackgroundTasks,
    service: PostgreSQLTransactionService = Depends(get_transaction_service)
):
    """Insert multiple transactions in bulk"""
    try:
        # Note: background_tasks parameter available for future async processing
        _ = background_tasks  # Acknowledge parameter for future use
        if not request.transactions:
            raise HTTPException(status_code=400, detail="No transactions provided")
        
        if len(request.transactions) > 10000:
            raise HTTPException(status_code=400, detail="Too many transactions. Maximum 10,000 per request")
        
        # Prepare bulk insert data
        records = []
        for txn in request.transactions:
            records.append((
                txn.transaction_id,
                txn.sender_account_id,
                txn.receiver_account_id,
                txn.tx_type,
                txn.amount,
                txn.timestamp,
                txn.is_fraud,
                txn.alert_id
            ))
        
        # Execute bulk insert
        await service.connection.executemany("""
            INSERT INTO csv_transactions 
            (transaction_id, sender_account_id, receiver_account_id, tx_type, amount, timestamp, is_fraud, alert_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (transaction_id) DO UPDATE SET
                sender_account_id = EXCLUDED.sender_account_id,
                receiver_account_id = EXCLUDED.receiver_account_id,
                tx_type = EXCLUDED.tx_type,
                amount = EXCLUDED.amount,
                timestamp = EXCLUDED.timestamp,
                is_fraud = EXCLUDED.is_fraud,
                alert_id = EXCLUDED.alert_id,
                updated_at = CURRENT_TIMESTAMP
        """, records)
        
        return {
            "status": "success",
            "message": f"{len(request.transactions)} transactions inserted successfully",
            "count": len(request.transactions),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to insert bulk transactions: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to insert bulk transactions: {str(e)}") from e

@router.delete("/{transaction_id}", response_model=Dict[str, Any], summary="Delete transaction")
async def delete_transaction(
    transaction_id: str,
    service: PostgreSQLTransactionService = Depends(get_transaction_service)
):
    """Delete a specific transaction"""
    try:
        # Check if transaction exists
        existing = await service.get_transaction_by_id(transaction_id)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found")
        
        # Delete transaction
        await service.connection.execute(
            "DELETE FROM csv_transactions WHERE transaction_id = $1",
            int(transaction_id)
        )
        
        return {
            "status": "success",
            "message": f"Transaction {transaction_id} deleted successfully",
            "transaction_id": transaction_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete transaction %s: %s", transaction_id, e)
        raise HTTPException(status_code=500, detail=f"Failed to delete transaction: {str(e)}") from e

@router.get("/search/amount", response_model=List[TransactionResponse], summary="Search transactions by amount range")
async def search_by_amount(
    min_amount: float = Query(..., description="Minimum amount"),
    max_amount: float = Query(..., description="Maximum amount"),
    limit: int = Query(default=100, ge=1, le=1000, description="Number of results to return"),
    service: PostgreSQLTransactionService = Depends(get_transaction_service)
):
    """Search transactions by amount range"""
    try:
        # Get high-value transactions with custom range
        transactions = await service.get_high_value_transactions(min_amount=min_amount, limit=limit)
        
        # Filter by max amount if needed
        if max_amount:
            transactions = [t for t in transactions if t['amount'] <= max_amount]
        
        response_transactions = []
        for txn in transactions:
            response_transactions.append(TransactionResponse(
                transaction_id=txn['transaction_id'],
                sender_account_id=txn['sender_account_id'],
                receiver_account_id=txn['receiver_account_id'],
                tx_type=txn.get('tx_type', ''),
                amount=txn['amount'],
                timestamp=txn.get('original_timestamp', 0),
                is_fraud=txn.get('is_fraud', False),
                alert_id=txn.get('alert_id', -1),
                created_at=txn.get('created_at', '')
            ))
        
        return response_transactions
        
    except Exception as e:
        logger.error("Failed to search transactions by amount: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to search transactions: {str(e)}") from e

@router.get("/export/csv", summary="Export transactions to CSV")
async def export_transactions_csv(
    limit: int = Query(default=1000, ge=1, le=10000, description="Number of transactions to export"),
    fraud_only: bool = Query(default=False, description="Export only fraud transactions"),
    min_amount: Optional[float] = Query(default=None, description="Minimum amount filter"),
    service: PostgreSQLTransactionService = Depends(get_transaction_service)
):
    """Export transactions to CSV format"""
    try:
        # Get transactions based on filters
        if fraud_only:
            transactions = await service.get_fraud_transactions(limit=limit)
        elif min_amount is not None:
            transactions = await service.get_high_value_transactions(min_amount=min_amount, limit=limit)
        else:
            transactions = await service.get_transactions_for_batch_processing(batch_size=limit, offset=0)
        
        # Convert to DataFrame
        df = pd.DataFrame(transactions)
        
        # Generate CSV content
        csv_content = df.to_csv(index=False)
        
        return JSONResponse(
            content={
                "status": "success",
                "message": f"Exported {len(transactions)} transactions",
                "count": len(transactions),
                "csv_data": csv_content,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error("Failed to export transactions: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to export transactions: {str(e)}") from e
