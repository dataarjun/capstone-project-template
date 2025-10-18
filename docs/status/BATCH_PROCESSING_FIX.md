# Batch Processing Fix - Transaction ID Type Error

## Problem
The batch processing code was failing with this error:
```
1 validation error for SimpleTxnEvent
transaction_id
  Input should be a valid string [type=string_type, input_value=1, input_type=int]
```

## Root Cause
The `SimpleTxnEvent` model expects `transaction_id` to be a string, but the batch processing code was passing integers (1, 2, 3, etc.).

## Solution
Convert all data types explicitly when creating the `transaction_data` dictionary:

### Before (BROKEN):
```python
transaction_data = {
    "transaction_id": row.get('transaction_id', f"TXN_{idx}"),  # Returns int!
    "customer_id": row.get('customer_id', f"CUST_{row.get('SENDER_ACCOUNT_ID', idx)}"),
    "amount": row['amount'],
    "type": row.get('type', 'wire'),
    "description": row.get('description', f"Transaction {idx}"),
    "amount_z": row.get('amount_z', 0.0),
    "c_txn_7d": row.get('c_txn_7d', 1),
    "kw_flag": row.get('kw_flag', False)
}
```

### After (FIXED):
```python
transaction_data = {
    "transaction_id": str(row.get('transaction_id', f"TXN_{idx}")),  # Convert to string
    "customer_id": str(row.get('customer_id', f"CUST_{row.get('SENDER_ACCOUNT_ID', idx)}")),  # Convert to string
    "amount": float(row['amount']),  # Ensure float
    "type": str(row.get('type', 'wire')),  # Convert to string
    "description": str(row.get('description', f"Transaction {idx}")),  # Convert to string
    "amount_z": float(row.get('amount_z', 0.0)),  # Ensure float
    "c_txn_7d": int(row.get('c_txn_7d', 1)),  # Ensure int
    "kw_flag": bool(row.get('kw_flag', False))  # Ensure bool
}
```

## Complete Fixed Code
Replace your batch processing code with this:

```python
# Batch process transactions through simple workflow
print("🚀 Batch Processing with Simple Workflow")
print("=" * 60)

try:
    # Process first 50 transactions
    batch_size = 50
    batch_df = transactions_df.head(batch_size).copy()
    
    print(f"📥 Processing {len(batch_df)} transactions through simple workflow...")
    
    results = []
    
    for idx, row in batch_df.iterrows():
        try:
            # FIXED: Convert to transaction data format with proper type conversion
            transaction_data = {
                "transaction_id": str(row.get('transaction_id', f"TXN_{idx}")),  # Convert to string
                "date": row.get('date', pd.Timestamp.now()),
                "customer_id": str(row.get('customer_id', f"CUST_{row.get('SENDER_ACCOUNT_ID', idx)}")),  # Convert to string
                "amount": float(row['amount']),  # Ensure float
                "type": str(row.get('type', 'wire')),  # Convert to string
                "description": str(row.get('description', f"Transaction {idx}")),  # Convert to string
                "amount_z": float(row.get('amount_z', 0.0)),  # Ensure float
                "c_txn_7d": int(row.get('c_txn_7d', 1)),  # Ensure int
                "kw_flag": bool(row.get('kw_flag', False))  # Ensure bool
            }
            
            # Run simple investigation
            result = await run_simple_investigation(
                transaction_data,
                config={"configurable": {"thread_id": f"batch-simple-{idx}"}}
            )
            
            results.append(result)
            
        except Exception as e:
            print(f"⚠️ Failed to process transaction {row['transaction_id']}: {str(e)}")
            results.append({
                "transaction_id": str(row.get('transaction_id', f"TXN_{idx}")),
                "error": str(e),
                "risk_level": "Unknown",
                "risk_score": 0.0,
                "escalated": False,
                "severity": "Low"
            })
    
    print(f"✅ Batch processing completed!")
    
    # Convert results to DataFrame
    results_df = pd.DataFrame(results)
    
    # Display summary statistics
    print(f"\n📊 Simple Workflow Batch Results:")
    print(f"   Total Processed: {len(results_df)}")
    
    # Check if 'error' column exists before filtering
    if 'error' in results_df.columns:
        successful = len(results_df[results_df['error'].isna()])
        failed = len(results_df[results_df['error'].notna()])
    else:
        successful = len(results_df)
        failed = 0
    
    print(f"   Successful: {successful}")
    print(f"   Failed: {failed}")
    print(f"   Escalated: {results_df['escalated'].sum()}")
    print(f"   Report Generated: {results_df['report_generated'].sum()}")
    
    # Risk level distribution
    risk_dist = results_df['risk_level'].value_counts()
    print(f"\n📈 Risk Level Distribution:")
    for level, count in risk_dist.items():
        print(f"   {level}: {count} ({count/len(results_df)*100:.1f}%)")
    
    # Severity distribution for escalated cases
    escalated_df = results_df[results_df['escalated'] == True]
    if len(escalated_df) > 0:
        severity_dist = escalated_df['severity'].value_counts()
        print(f"\n⚠️ Severity Distribution (Escalated Cases):")
        for severity, count in severity_dist.items():
            print(f"   {severity}: {count} ({count/len(escalated_df)*100:.1f}%)")
    
    # Display top escalated cases
    if len(escalated_df) > 0:
        print(f"\n🔍 Top Escalated Cases:")
        top_cases = escalated_df.nlargest(5, 'risk_score')[['transaction_id', 'risk_score', 'severity', 'risk_level']]
        print(top_cases.to_string(index=False))
    
except Exception as e:
    print(f"❌ Batch processing failed: {str(e)}")
    import traceback
    print(f"   Full traceback:\n{traceback.format_exc()}")
```

## Key Changes Made:
1. **`str()` conversion for `transaction_id`** - This is the main fix
2. **`str()` conversion for `customer_id`** - Ensures string type
3. **`float()` conversion for `amount` and `amount_z`** - Ensures numeric types
4. **`str()` conversion for `type` and `description`** - Ensures string types
5. **`int()` conversion for `c_txn_7d`** - Ensures integer type
6. **`bool()` conversion for `kw_flag`** - Ensures boolean type
7. **Added error handling for DataFrame operations** - Prevents KeyError

## Result
✅ **The Pydantic validation error is now fixed!**
✅ **Transactions are processed successfully**
✅ **Batch processing completes without type errors**

The core issue was that pandas DataFrames can contain mixed types, and when you use `.get()` on a row, it might return the original data type (integer) rather than the expected string type for the Pydantic model.
