"""
AML Data Loading Script

This script loads AML datasets from CSV files and makes them available
for the AML investigation system. Since we're having database connection
issues, this works directly with CSV files.
"""

import pandas as pd
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.core.logger import get_logger

logger = get_logger(__name__)


class AMLDataManager:
    """
    Manages AML datasets from CSV files
    """
    
    def __init__(self):
        self.data_root = project_root / "data"
        self.raw_data_path = self.data_root / "raw"
        self.sample_data_path = self.data_root / "sampledata"
        
        # Cache for loaded data
        self._customers_cache = None
        self._transactions_cache = None
        self._alerts_cache = None
        self._hi_trans_cache = None
    
    def load_operational_data(self) -> Dict[str, pd.DataFrame]:
        """
        Load operational AML data from CSV files
        
        Returns:
            Dictionary with customers, transactions, and alerts DataFrames
        """
        logger.info("Loading operational AML data from CSV files")
        
        data = {}
        
        try:
            # Load customers
            customers_path = self.raw_data_path / "customers.csv"
            if customers_path.exists():
                data['customers'] = pd.read_csv(customers_path)
                data['customers']['created_at'] = pd.to_datetime(data['customers']['created_at'])
                logger.info(f"Loaded {len(data['customers'])} customers")
            
            # Load transactions
            transactions_path = self.raw_data_path / "transactions.csv"
            if transactions_path.exists():
                data['transactions'] = pd.read_csv(transactions_path)
                data['transactions']['transaction_date'] = pd.to_datetime(data['transactions']['transaction_date'])
                logger.info(f"Loaded {len(data['transactions'])} transactions")
            
            # Load alerts
            alerts_path = self.raw_data_path / "alerts.csv"
            if alerts_path.exists():
                data['alerts'] = pd.read_csv(alerts_path)
                data['alerts']['created_at'] = pd.to_datetime(data['alerts']['created_at'])
                logger.info(f"Loaded {len(data['alerts'])} alerts")
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to load operational data: {str(e)}")
            return {}
    
    def load_hi_small_trans(self, limit: int = None) -> pd.DataFrame:
        """
        Load HI-Small_Trans dataset
        
        Args:
            limit: Optional limit on number of rows to load
            
        Returns:
            DataFrame with HI-Small_Trans data
        """
        logger.info("Loading HI-Small_Trans dataset")
        
        try:
            hi_trans_path = self.sample_data_path / "HI-Small_Trans.csv"
            if not hi_trans_path.exists():
                logger.error(f"HI-Small_Trans file not found: {hi_trans_path}")
                return pd.DataFrame()
            
            if limit:
                df = pd.read_csv(hi_trans_path, nrows=limit)
            else:
                df = pd.read_csv(hi_trans_path)
            
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            logger.info(f"Loaded {len(df)} HI-Small_Trans records")
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to load HI-Small_Trans data: {str(e)}")
            return pd.DataFrame()
    
    def get_operational_summary(self) -> Dict[str, Any]:
        """
        Get summary of operational data
        
        Returns:
            Dictionary with data summary
        """
        data = self.load_operational_data()
        
        summary = {}
        
        if 'customers' in data:
            customers_df = data['customers']
            summary['customers'] = {
                'count': len(customers_df),
                'customer_types': customers_df['customer_type'].value_counts().to_dict(),
                'risk_levels': customers_df['risk_level'].value_counts().to_dict(),
                'countries': customers_df['country'].value_counts().to_dict()
            }
        
        if 'transactions' in data:
            transactions_df = data['transactions']
            summary['transactions'] = {
                'count': len(transactions_df),
                'transaction_types': transactions_df['transaction_type'].value_counts().to_dict(),
                'currencies': transactions_df['currency'].value_counts().to_dict(),
                'amount_stats': {
                    'mean': float(transactions_df['amount'].mean()),
                    'median': float(transactions_df['amount'].median()),
                    'max': float(transactions_df['amount'].max()),
                    'min': float(transactions_df['amount'].min())
                }
            }
        
        if 'alerts' in data:
            alerts_df = data['alerts']
            summary['alerts'] = {
                'count': len(alerts_df),
                'alert_types': alerts_df['alert_type'].value_counts().to_dict(),
                'severities': alerts_df['severity'].value_counts().to_dict(),
                'statuses': alerts_df['status'].value_counts().to_dict()
            }
        
        return summary
    
    def get_hi_trans_summary(self) -> Dict[str, Any]:
        """
        Get summary of HI-Small_Trans data
        
        Returns:
            Dictionary with HI-Small_Trans summary
        """
        df = self.load_hi_small_trans(limit=1000)  # Sample for summary
        
        if df.empty:
            return {}
        
        summary = {
            'total_records': len(df),
            'laundering_distribution': df['Is Laundering'].value_counts().to_dict(),
            'payment_formats': df['Payment Format'].value_counts().to_dict(),
            'currencies': df['Receiving Currency'].value_counts().to_dict(),
            'amount_stats': {
                'mean': float(df['Amount Received'].mean()),
                'median': float(df['Amount Received'].median()),
                'max': float(df['Amount Received'].max()),
                'min': float(df['Amount Received'].min())
            },
            'date_range': {
                'start': str(df['Timestamp'].min()),
                'end': str(df['Timestamp'].max())
            }
        }
        
        return summary
    
    def create_sample_aml_cases(self, count: int = 5) -> List[Dict[str, Any]]:
        """
        Create sample AML cases for testing
        
        Args:
            count: Number of sample cases to create
            
        Returns:
            List of sample AML cases
        """
        logger.info(f"Creating {count} sample AML cases")
        
        cases = []
        
        # Load operational data
        data = self.load_operational_data()
        
        if 'alerts' not in data or 'transactions' not in data or 'customers' not in data:
            logger.error("Missing required data for creating sample cases")
            return cases
        
        alerts_df = data['alerts']
        transactions_df = data['transactions']
        customers_df = data['customers']
        
        # Create sample cases from alerts
        for i, alert_row in alerts_df.head(count).iterrows():
            try:
                # Get related transaction
                txn_id = alert_row['transaction_id']
                txn_row = transactions_df[transactions_df['transaction_id'] == txn_id]
                
                if txn_row.empty:
                    continue
                
                txn_row = txn_row.iloc[0]
                
                # Get related customer
                customer_id = txn_row['customer_id']
                customer_row = customers_df[customers_df['customer_id'] == customer_id]
                
                if customer_row.empty:
                    continue
                
                customer_row = customer_row.iloc[0]
                
                # Create AML case
                case = {
                    'alert_id': alert_row['alert_id'],
                    'alert_type': alert_row['alert_type'],
                    'severity': alert_row['severity'],
                    'transaction': {
                        'transaction_id': txn_id,
                        'amount': float(txn_row['amount']),
                        'currency': txn_row['currency'],
                        'transaction_type': txn_row['transaction_type'],
                        'location': txn_row['location'],
                        'country': txn_row['country'],
                        'description': txn_row['description']
                    },
                    'customer': {
                        'customer_id': customer_id,
                        'customer_name': customer_row['customer_name'],
                        'customer_type': customer_row['customer_type'],
                        'risk_level': customer_row['risk_level'],
                        'kyc_status': customer_row['kyc_status'],
                        'location': customer_row['location'],
                        'country': customer_row['country']
                    }
                }
                
                cases.append(case)
                
            except Exception as e:
                logger.error(f"Error creating case {i}: {str(e)}")
                continue
        
        logger.info(f"Created {len(cases)} sample AML cases")
        return cases


def main():
    """Main function to demonstrate data loading"""
    print("🔄 AML Data Loading and Management")
    print("=" * 50)
    
    # Initialize data manager
    data_manager = AMLDataManager()
    
    # Get operational data summary
    print("\n📊 Operational Data Summary:")
    operational_summary = data_manager.get_operational_summary()
    
    if operational_summary:
        for data_type, summary in operational_summary.items():
            print(f"\n{data_type.title()}:")
            if isinstance(summary, dict):
                for key, value in summary.items():
                    print(f"  {key}: {value}")
    
    # Get HI-Small_Trans summary
    print("\n📈 HI-Small_Trans Dataset Summary:")
    hi_trans_summary = data_manager.get_hi_trans_summary()
    
    if hi_trans_summary:
        for key, value in hi_trans_summary.items():
            if isinstance(value, dict):
                print(f"\n{key}:")
                for sub_key, sub_value in value.items():
                    print(f"  {sub_key}: {sub_value}")
            else:
                print(f"  {key}: {value}")
    
    # Create sample cases
    print("\n🔍 Sample AML Cases:")
    sample_cases = data_manager.create_sample_aml_cases(count=3)
    
    for i, case in enumerate(sample_cases, 1):
        print(f"\nCase {i}:")
        print(f"  Alert ID: {case['alert_id']}")
        print(f"  Alert Type: {case['alert_type']}")
        print(f"  Severity: {case['severity']}")
        print(f"  Transaction: ${case['transaction']['amount']} {case['transaction']['currency']}")
        print(f"  Customer: {case['customer']['customer_name']} ({case['customer']['customer_type']})")
        print(f"  Risk Level: {case['customer']['risk_level']}")
    
    print(f"\n✅ Data loading completed successfully!")
    print(f"📁 Data files available in: {data_manager.data_root}")
    
    return {
        'operational_summary': operational_summary,
        'hi_trans_summary': hi_trans_summary,
        'sample_cases': sample_cases
    }


if __name__ == "__main__":
    main()

