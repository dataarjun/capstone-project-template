"""
AML Data Loader

This module provides unified data loading for both operational AML system
and HI-Small_Trans batch processing, with feature engineering capabilities.
"""

import pandas as pd
import numpy as np
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from app.core.logger import get_logger
from app.models.aml_models import TxnEvent, Enrichment

logger = get_logger(__name__)


class AMLDataLoader:
    """
    Unified data loader for AML datasets with feature engineering
    """
    
    def __init__(self, data_root: str = "data"):
        self.data_root = Path(data_root)
        self.raw_data_path = self.data_root / "raw"
        self.sample_data_path = self.data_root / "sampledata"
        
        # Cache for loaded data
        self._alerts_cache = None
        self._customers_cache = None
        self._transactions_cache = None
        self._hi_trans_stats = None
        
        # Feature engineering parameters
        self.structuring_threshold = 10000.0
        self.suspicious_keywords = [
            "crypto", "bitcoin", "cash", "gift", "urgent", "refund",
            "invoice split", "transfer split", "exchange", "mixer",
            "darknet", "anonymizer", "tumbler", "structuring",
            "layering", "integration", "placement"
        ]
    
    def load_alerts(self, limit: Optional[int] = None) -> pd.DataFrame:
        """
        Load alerts from operational system
        
        Args:
            limit: Optional limit on number of alerts to load
            
        Returns:
            DataFrame with alerts data
        """
        if self._alerts_cache is not None:
            alerts_df = self._alerts_cache
        else:
            alerts_path = self.raw_data_path / "alerts.csv"
            if not alerts_path.exists():
                logger.error(f"Alerts file not found: {alerts_path}")
                return pd.DataFrame()
            
            alerts_df = pd.read_csv(alerts_path)
            # Handle different date column formats
            if 'created_at' in alerts_df.columns:
                alerts_df['created_at'] = pd.to_datetime(alerts_df['created_at'])
            self._alerts_cache = alerts_df
        
        if limit:
            return alerts_df.head(limit)
        
        return alerts_df
    
    def load_customers(self) -> pd.DataFrame:
        """
        Load customer data from operational system
        
        Returns:
            DataFrame with customer data
        """
        if self._customers_cache is not None:
            return self._customers_cache
        
        customers_path = self.raw_data_path / "customers.csv"
        if not customers_path.exists():
            logger.error(f"Customers file not found: {customers_path}")
            return pd.DataFrame()
        
        customers_df = pd.read_csv(customers_path)
        customers_df['created_at'] = pd.to_datetime(customers_df['created_at'])
        self._customers_cache = customers_df
        
        return customers_df
    
    def load_transactions(self) -> pd.DataFrame:
        """
        Load transaction data from operational system
        
        Returns:
            DataFrame with transaction data
        """
        if self._transactions_cache is not None:
            return self._transactions_cache
        
        transactions_path = self.raw_data_path / "transactions.csv"
        if not transactions_path.exists():
            logger.error(f"Transactions file not found: {transactions_path}")
            return pd.DataFrame()
        
        transactions_df = pd.read_csv(transactions_path)
        transactions_df['transaction_date'] = pd.to_datetime(transactions_df['transaction_date'])
        self._transactions_cache = transactions_df
        
        return transactions_df
    
    def load_operational_alert(self, alert_id: str) -> Tuple[Optional[Dict], Optional[Dict], Optional[Dict]]:
        """
        Load operational data for a specific alert
        
        Args:
            alert_id: Alert ID to load
            
        Returns:
            Tuple of (alert, transaction, customer) dictionaries
        """
        alerts_df = self.load_alerts()
        transactions_df = self.load_transactions()
        customers_df = self.load_customers()
        
        # Find alert
        alert_row = alerts_df[alerts_df['alert_id'] == alert_id]
        if alert_row.empty:
            logger.error(f"Alert {alert_id} not found")
            return None, None, None
        
        alert = alert_row.iloc[0].to_dict()
        
        # Find related transaction
        txn_id = alert['transaction_id']
        txn_row = transactions_df[transactions_df['transaction_id'] == txn_id]
        if txn_row.empty:
            logger.error(f"Transaction {txn_id} not found")
            return alert, None, None
        
        transaction = txn_row.iloc[0].to_dict()
        
        # Find related customer
        customer_id = transaction['customer_id']
        customer_row = customers_df[customers_df['customer_id'] == customer_id]
        if customer_row.empty:
            logger.error(f"Customer {customer_id} not found")
            return alert, transaction, None
        
        customer = customer_row.iloc[0].to_dict()
        
        return alert, transaction, customer
    
    def load_hi_trans_batch(self, batch_size: int = 10000, offset: int = 0) -> pd.DataFrame:
        """
        Load batch from HI-Small_Trans.csv
        
        Args:
            batch_size: Number of transactions to load
            offset: Starting offset
            
        Returns:
            DataFrame with HI-Small_Trans batch
        """
        hi_trans_path = self.sample_data_path / "HI-Small_Trans.csv"
        if not hi_trans_path.exists():
            logger.error(f"HI-Small_Trans file not found: {hi_trans_path}")
            return pd.DataFrame()
        
        # Load batch with offset
        df = pd.read_csv(hi_trans_path, skiprows=range(1, offset + 1), nrows=batch_size)
        
        # Convert timestamp
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        
        logger.info(f"Loaded HI-Small_Trans batch: {len(df)} transactions (offset: {offset})")
        return df
    
    def get_hi_trans_stats(self) -> Dict[str, Any]:
        """
        Get statistics about HI-Small_Trans dataset
        
        Returns:
            Dictionary with dataset statistics
        """
        if self._hi_trans_stats is not None:
            return self._hi_trans_stats
        
        hi_trans_path = self.sample_data_path / "HI-Small_Trans.csv"
        if not hi_trans_path.exists():
            return {}
        
        # Read sample for stats
        sample_df = pd.read_csv(hi_trans_path, nrows=1000)
        
        # Get full dataset info
        total_lines = sum(1 for _ in open(hi_trans_path)) - 1  # Subtract header
        
        stats = {
            "total_transactions": total_lines,
            "sample_size": len(sample_df),
            "columns": list(sample_df.columns),
            "laundering_distribution": sample_df['Is Laundering'].value_counts().to_dict(),
            "payment_formats": sample_df['Payment Format'].value_counts().to_dict(),
            "date_range": {
                "start": sample_df['Timestamp'].min(),
                "end": sample_df['Timestamp'].max()
            }
        }
        
        self._hi_trans_stats = stats
        return stats
    
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Engineer features for transaction dataset
        
        Args:
            df: DataFrame with transaction data
            
        Returns:
            DataFrame with engineered features
        """
        df = df.copy()
        
        # 1. Amount z-score normalization
        if 'Amount Received' in df.columns:
            amount_col = 'Amount Received'
        elif 'amount' in df.columns:
            amount_col = 'amount'
        else:
            logger.warning("No amount column found for z-score calculation")
            df['amount_z'] = 0.0
            return df
        
        # Calculate global statistics for z-score
        if len(df) > 1000:  # Use sample for large datasets
            sample_amounts = df[amount_col].sample(1000)
        else:
            sample_amounts = df[amount_col]
        
        mean_amount = sample_amounts.mean()
        std_amount = sample_amounts.std() or 1.0
        
        df['amount_z'] = (df[amount_col] - mean_amount) / std_amount
        
        # 2. Transaction velocity (7-day window)
        df['c_txn_7d'] = 0
        
        if 'Timestamp' in df.columns:
            df = df.sort_values('Timestamp')
            
            # Group by account and calculate velocity
            for account in df['Account'].unique() if 'Account' in df.columns else ['default']:
                if 'Account' in df.columns:
                    account_mask = df['Account'] == account
                    account_df = df[account_mask].copy()
                else:
                    account_df = df.copy()
                
                for i, (idx, row) in enumerate(account_df.iterrows()):
                    current_time = row['Timestamp']
                    week_ago = current_time - timedelta(days=7)
                    
                    # Count transactions in the past 7 days
                    past_transactions = account_df[
                        (account_df['Timestamp'] >= week_ago) & 
                        (account_df['Timestamp'] < current_time)
                    ]
                    
                    df.loc[idx, 'c_txn_7d'] = len(past_transactions)
        
        # 3. Keyword flags
        description_col = None
        for col in ['description', 'Description']:
            if col in df.columns:
                description_col = col
                break
        
        if description_col:
            df['kw_flag'] = df[description_col].fillna("").str.lower().apply(
                lambda x: 1 if any(keyword in x for keyword in self.suspicious_keywords) else 0
            )
        else:
            df['kw_flag'] = 0
        
        logger.info(f"Engineered features for {len(df)} transactions")
        return df
    
    def make_txn_event(self, row: pd.Series) -> TxnEvent:
        """
        Convert DataFrame row to TxnEvent
        
        Args:
            row: Pandas Series row from DataFrame
            
        Returns:
            TxnEvent object
        """
        # Handle both operational and HI-Small_Trans formats
        if 'transaction_id' in row:
            # Operational format
            return TxnEvent(
                transaction_id=str(row['transaction_id']),
                timestamp=pd.to_datetime(row['transaction_date']),
                customer_id=str(row['customer_id']),
                counterparty_id=str(row.get('counterparty_id', '')),
                amount=float(row['amount']),
                currency=str(row.get('currency', 'USD')),
                transaction_type=str(row['transaction_type']),
                location=str(row.get('location', '')),
                country=str(row.get('country', 'US')),
                description=str(row.get('description', '')),
                amount_z=float(row.get('amount_z', 0.0)),
                c_txn_7d=int(row.get('c_txn_7d', 0)),
                kw_flag=int(row.get('kw_flag', 0))
            )
        
        else:
            # HI-Small_Trans format
            return TxnEvent(
                transaction_id=f"HI_{row.name}",
                timestamp=pd.to_datetime(row['Timestamp']),
                customer_id=str(row['Account']),
                amount=float(row['Amount Received']),
                currency=str(row.get('Receiving Currency', 'USD')),
                transaction_type=str(row.get('Payment Format', 'Unknown')),
                location="Unknown",
                country="US",  # Default for HI-Small_Trans
                description="HI-Small_Trans transaction",
                # HI-Small_Trans specific fields
                from_bank=str(row.get('From Bank', '')),
                from_account=str(row.get('Account', '')),
                to_bank=str(row.get('To Bank', '')),
                to_account=str(row.get('Account.1', '')),
                payment_format=str(row.get('Payment Format', '')),
                is_laundering=int(row.get('Is Laundering', 0)),
                # Engineered features
                amount_z=float(row.get('amount_z', 0.0)),
                c_txn_7d=int(row.get('c_txn_7d', 0)),
                kw_flag=int(row.get('kw_flag', 0))
            )
    
    def create_enrichment(self, customer_data: Dict[str, Any], 
                         transaction_data: Dict[str, Any]) -> Enrichment:
        """
        Create enrichment data from customer and transaction information
        
        Args:
            customer_data: Customer information dictionary
            transaction_data: Transaction information dictionary
            
        Returns:
            Enrichment object
        """
        # Extract customer type and risk indicators
        customer_type = customer_data.get('customer_type', 'Unknown')
        risk_level = customer_data.get('risk_level', 'low')
        
        # Determine PEP status (mock logic)
        pep_flag = False
        if customer_type and 'gov' in customer_type.lower():
            pep_flag = True
        
        # Determine country risk
        country_risk = "Low"
        if risk_level == 'high':
            country_risk = "High"
        elif risk_level == 'medium':
            country_risk = "Medium"
        
        # Mock prior alerts
        prior_alerts_90d = 0
        if customer_type in ['CRIM', 'MULE']:
            prior_alerts_90d = np.random.randint(1, 5)
        
        # Mock sanctions hits
        sanction_hits = []
        if customer_type == 'CRIM':
            sanction_hits = ['criminal_entity_xyz']
        
        # Mock KYC documents
        kyc_documents = []
        if customer_data.get('kyc_status') == 'verified':
            kyc_documents = [f"customer_{customer_data.get('customer_id', 'unknown')}.pdf"]
        
        return Enrichment(
            customer_id=str(customer_data.get('customer_id', 'unknown')),
            customer_name=customer_data.get('customer_name', 'Unknown'),
            customer_type=customer_type,
            pep_flag=pep_flag,
            country_risk=country_risk,
            prior_alerts_90d=prior_alerts_90d,
            sanction_hits=sanction_hits,
            kyc_documents=kyc_documents,
            extra={
                'risk_level': risk_level,
                'location': customer_data.get('location', ''),
                'country': customer_data.get('country', 'US')
            }
        )
    
    def convert_hi_trans_to_operational(self, row: pd.Series) -> Dict[str, Any]:
        """
        Convert HI-Small_Trans row to operational format for testing
        
        Args:
            row: HI-Small_Trans DataFrame row
            
        Returns:
            Dictionary in operational format
        """
        # Generate mock operational data from HI-Small_Trans
        customer_id = f"HI_{row['Account']}"
        
        return {
            'alert_id': f"ALT_HI_{row.name}",
            'transaction_id': f"TXN_HI_{row.name}",
            'customer_id': customer_id,
            'amount': float(row['Amount Received']),
            'currency': str(row.get('Receiving Currency', 'USD')),
            'transaction_type': str(row.get('Payment Format', 'Unknown')),
            'location': "Unknown",
            'country': "US",
            'description': f"HI-Small_Trans transaction {row.name}",
            'customer': {
                'customer_id': customer_id,
                'customer_name': f"Account {row['Account']}",
                'customer_type': 'LEG',  # Default to legitimate
                'risk_level': 'low',
                'kyc_status': 'verified',
                'location': 'Unknown',
                'country': 'US'
            }
        }
    
    def get_operational_dataset_summary(self) -> Dict[str, Any]:
        """
        Get summary of operational dataset
        
        Returns:
            Dictionary with dataset summary
        """
        alerts_df = self.load_alerts()
        customers_df = self.load_customers()
        transactions_df = self.load_transactions()
        
        return {
            'alerts': {
                'count': len(alerts_df),
                'columns': list(alerts_df.columns),
                'alert_types': alerts_df['alert_type'].value_counts().to_dict() if 'alert_type' in alerts_df.columns else {}
            },
            'customers': {
                'count': len(customers_df),
                'columns': list(customers_df.columns),
                'customer_types': customers_df['customer_type'].value_counts().to_dict() if 'customer_type' in customers_df.columns else {},
                'risk_levels': customers_df['risk_level'].value_counts().to_dict() if 'risk_level' in customers_df.columns else {}
            },
            'transactions': {
                'count': len(transactions_df),
                'columns': list(transactions_df.columns),
                'transaction_types': transactions_df['transaction_type'].value_counts().to_dict() if 'transaction_type' in transactions_df.columns else {},
                'amount_stats': {
                    'mean': float(transactions_df['amount'].mean()) if 'amount' in transactions_df.columns else 0,
                    'median': float(transactions_df['amount'].median()) if 'amount' in transactions_df.columns else 0,
                    'max': float(transactions_df['amount'].max()) if 'amount' in transactions_df.columns else 0
                }
            }
        }
    
    def clear_cache(self):
        """Clear loaded data cache"""
        self._alerts_cache = None
        self._customers_cache = None
        self._transactions_cache = None
        self._hi_trans_stats = None
        logger.info("Data cache cleared")
