#!/usr/bin/env python3
"""
Synthetic Financial Data Generator for Multi-Agent AML System

This script generates realistic financial data with embedded money laundering patterns
following the multi-agent virtual world approach where laundering is implicit in
criminal entity behavior.

Key Features:
- Criminal entities with illicit fund sources
- Transitive laundering through fund transfers
- Natural laundering (payroll, supplies) vs methodical patterns
- Standard AML patterns: scatter-gather, cyclic, structuring, smurfing
- Legitimate businesses for false positive testing
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import json
from typing import List, Dict, Tuple
import uuid

# Add the app directory to the path
sys.path.append('../')

from app.core.config_simple import settings
from app.db.session import engine
from app.db.models import Base, Investigation, Alert, Transaction, Customer, AgentExecution, SystemMetrics, AgentTrace

class SyntheticDataGenerator:
    """Generate synthetic financial data with embedded AML patterns"""
    
    def __init__(self, num_customers: int = 100, num_transactions: int = 1000):
        self.num_customers = num_customers
        self.num_transactions = num_transactions
        self.customers = []
        self.transactions = []
        self.alerts = []
        
        # Define entity types and their characteristics
        self.entity_types = {
            'legitimate_business': {
                'risk_level': 'low',
                'kyc_status': 'verified',
                'laundering_probability': 0.0,
                'business_types': ['restaurant', 'retail', 'consulting', 'tech', 'healthcare']
            },
            'criminal_organization': {
                'risk_level': 'high',
                'kyc_status': 'pending',
                'laundering_probability': 0.8,
                'business_types': ['shell_company', 'import_export', 'cash_business']
            },
            'money_mule': {
                'risk_level': 'medium',
                'kyc_status': 'pending',
                'laundering_probability': 0.6,
                'business_types': ['personal', 'freelance']
            }
        }
        
        # AML Pattern definitions
        self.aml_patterns = {
            'structuring': {
                'description': 'Transactions just under reporting thresholds',
                'threshold': 10000,
                'pattern': 'multiple_transactions_under_threshold'
            },
            'smurfing': {
                'description': 'Coordinated small transactions from multiple accounts',
                'threshold': 5000,
                'pattern': 'coordinated_small_transfers'
            },
            'scatter_gather': {
                'description': 'Funds scattered to multiple accounts then gathered',
                'pattern': 'distribute_then_consolidate'
            },
            'cyclic': {
                'description': 'Circular money flows between accounts',
                'pattern': 'round_trip_transfers'
            }
        }

    def generate_customers(self) -> List[Dict]:
        """Generate customer entities with realistic profiles"""
        customers = []
        
        # Generate legitimate businesses (70%)
        for i in range(int(self.num_customers * 0.7)):
            customer = self._create_legitimate_customer(i)
            customers.append(customer)
        
        # Generate criminal organizations (20%)
        for i in range(int(self.num_customers * 0.2)):
            customer = self._create_criminal_customer(i)
            customers.append(customer)
        
        # Generate money mules (10%)
        for i in range(int(self.num_customers * 0.1)):
            customer = self._create_money_mule_customer(i)
            customers.append(customer)
        
        self.customers = customers
        return customers

    def _create_legitimate_customer(self, index: int) -> Dict:
        """Create a legitimate business customer"""
        business_type = random.choice(self.entity_types['legitimate_business']['business_types'])
        
        return {
            'customer_id': f'LEG{index:03d}',
            'customer_name': f'Legitimate Business {index}',
            'customer_type': 'business',
            'risk_level': 'low',
            'kyc_status': 'verified',
            'location': random.choice(['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix']),
            'country': 'US',
            'created_at': datetime.now() - timedelta(days=random.randint(30, 365))
        }

    def _create_criminal_customer(self, index: int) -> Dict:
        """Create a criminal organization customer"""
        business_type = random.choice(self.entity_types['criminal_organization']['business_types'])
        illicit_sources = ['drug_trafficking', 'fraud', 'theft', 'corruption', 'tax_evasion']
        
        return {
            'customer_id': f'CRIM{index:03d}',
            'customer_name': f'Criminal Entity {index}',
            'customer_type': 'business',
            'risk_level': 'high',
            'kyc_status': 'pending',
            'location': random.choice(['Miami', 'Los Angeles', 'New York', 'Chicago', 'Houston']),
            'country': 'US',
            'created_at': datetime.now() - timedelta(days=random.randint(30, 365))
        }

    def _create_money_mule_customer(self, index: int) -> Dict:
        """Create a money mule customer"""
        return {
            'customer_id': f'MULE{index:03d}',
            'customer_name': f'Money Mule {index}',
            'customer_type': 'individual',
            'risk_level': 'medium',
            'kyc_status': 'pending',
            'location': random.choice(['Miami', 'Los Angeles', 'New York', 'Chicago', 'Houston']),
            'country': 'US',
            'created_at': datetime.now() - timedelta(days=random.randint(30, 365))
        }

    def generate_transactions(self) -> List[Dict]:
        """Generate transactions with embedded laundering patterns"""
        transactions = []
        
        # Get high-risk customers for laundering scenarios
        criminal_customers = [c for c in self.customers if c['risk_level'] == 'high']
        legitimate_customers = [c for c in self.customers if c['risk_level'] != 'high']
        
        # Generate legitimate transactions (60%)
        for i in range(int(self.num_transactions * 0.6)):
            transaction = self._create_legitimate_transaction(i, legitimate_customers)
            transactions.append(transaction)
        
        # Generate laundering transactions (40%)
        laundering_transactions = self._generate_laundering_scenarios(criminal_customers, legitimate_customers)
        transactions.extend(laundering_transactions)
        
        # Sort by date
        transactions.sort(key=lambda x: x['transaction_date'])
        
        self.transactions = transactions
        return transactions

    def _create_legitimate_transaction(self, index: int, customers: List[Dict]) -> Dict:
        """Create a legitimate business transaction"""
        from_customer = random.choice(customers)
        to_customer = random.choice([c for c in customers if c['customer_id'] != from_customer['customer_id']])
        
        # Realistic transaction amounts
        amount = random.uniform(100, 10000)
        
        return {
            'transaction_id': f'TXN{index:06d}',
            'customer_id': from_customer['customer_id'],
            'counterparty_id': to_customer['customer_id'],
            'amount': round(amount, 2),
            'currency': 'USD',
            'transaction_type': random.choice(['wire', 'ach', 'check', 'cash']),
            'transaction_date': datetime.now() - timedelta(days=random.randint(1, 30)),
            'location': from_customer['location'],
            'country': from_customer['country'],
            'description': f'Payment for {random.choice(["services", "goods", "consulting"])}',
            'status': 'completed'
        }

    def _generate_laundering_scenarios(self, criminal_customers: List[Dict], legitimate_customers: List[Dict]) -> List[Dict]:
        """Generate complex laundering scenarios"""
        laundering_transactions = []
        transaction_counter = len(self.transactions)
        
        # Create some suspicious transactions with higher amounts
        for i in range(20):  # 20 suspicious transactions
            from_customer = random.choice(criminal_customers) if criminal_customers else random.choice(legitimate_customers)
            to_customer = random.choice(legitimate_customers)
            
            # Higher amounts for suspicious activity
            amount = random.uniform(5000, 50000)
            
            transaction = {
                'transaction_id': f'SUS{transaction_counter + i:06d}',
                'customer_id': from_customer['customer_id'],
                'counterparty_id': to_customer['customer_id'],
                'amount': round(amount, 2),
                'currency': 'USD',
                'transaction_type': random.choice(['wire', 'ach']),
                'transaction_date': datetime.now() - timedelta(days=random.randint(1, 7)),
                'location': from_customer['location'],
                'country': from_customer['country'],
                'description': f'Suspicious transaction {i+1}',
                'status': 'completed'
            }
            laundering_transactions.append(transaction)
        
        return laundering_transactions


    def generate_alerts(self) -> List[Dict]:
        """Generate alerts based on suspicious transactions"""
        alerts = []
        alert_counter = 1
        
        # Find high-value transactions (potential suspicious activity)
        suspicious_transactions = [t for t in self.transactions if t['amount'] > 10000]
        
        for transaction in suspicious_transactions:
            alert = {
                'alert_id': f'ALT{alert_counter:03d}',
                'transaction_id': transaction['transaction_id'],
                'alert_type': 'high_value_transaction',
                'severity': 'medium' if transaction['amount'] < 25000 else 'high',
                'status': 'open',
                'description': f'High-value transaction detected: ${transaction["amount"]:,.2f}',
                'created_at': transaction['transaction_date'],
                'resolved_at': None,
                'resolved_by': None
            }
            alerts.append(alert)
            alert_counter += 1
        
        self.alerts = alerts
        return alerts


    def save_to_database(self):
        """Save generated data to database"""
        from sqlalchemy.orm import sessionmaker
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        # Create session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        try:
            # Clear existing data
            session.query(Alert).delete()
            session.query(Transaction).delete()
            session.query(Customer).delete()
            session.commit()
            print("🗑️ Cleared existing data")
            
            # Insert customers
            for customer_data in self.customers:
                customer = Customer(**customer_data)
                session.add(customer)
            
            # Insert transactions
            for transaction_data in self.transactions:
                transaction = Transaction(**transaction_data)
                session.add(transaction)
            
            # Insert alerts
            for alert_data in self.alerts:
                alert = Alert(**alert_data)
                session.add(alert)
            
            session.commit()
            print(f"✅ Successfully saved {len(self.customers)} customers, {len(self.transactions)} transactions, and {len(self.alerts)} alerts to database")
            
        except Exception as e:
            session.rollback()
            print(f"❌ Error saving to database: {e}")
            raise
        finally:
            session.close()

    def save_to_csv(self, output_dir: str = '../data/raw'):
        """Save generated data to CSV files"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Save customers
        customers_df = pd.DataFrame(self.customers)
        customers_df.to_csv(f'{output_dir}/customers.csv', index=False)
        
        # Save transactions
        transactions_df = pd.DataFrame(self.transactions)
        transactions_df.to_csv(f'{output_dir}/transactions.csv', index=False)
        
        # Save alerts
        alerts_df = pd.DataFrame(self.alerts)
        alerts_df.to_csv(f'{output_dir}/alerts.csv', index=False)
        
        print(f"✅ Data saved to CSV files in {output_dir}")
        print(f"   - customers.csv: {len(self.customers)} records")
        print(f"   - transactions.csv: {len(self.transactions)} records")
        print(f"   - alerts.csv: {len(self.alerts)} records")

    def generate_kyc_documents(self, output_dir: str = '../data/kyc_documents'):
        """Generate KYC documents for customers"""
        os.makedirs(output_dir, exist_ok=True)
        
        for customer in self.customers:
            kyc_content = self._create_kyc_document(customer)
            
            filename = f'{output_dir}/customer_{customer["customer_id"]}.txt'
            with open(filename, 'w') as f:
                f.write(kyc_content)
        
        print(f"✅ Generated {len(self.customers)} KYC documents in {output_dir}")

    def _create_kyc_document(self, customer: Dict) -> str:
        """Create a KYC document for a customer"""
        if customer['risk_level'] == 'high':
            # Red flags for high-risk customers
            red_flags = [
                "Incomplete documentation provided",
                "Unusual business structure",
                "High-risk jurisdiction connections",
                "Cash-intensive business model",
                "Limited business history"
            ]
            
            kyc_content = f"""
KYC Document - {customer['customer_name']}
Customer ID: {customer['customer_id']}
Date: {datetime.now().strftime('%Y-%m-%d')}

CUSTOMER INFORMATION:
- Name: {customer['customer_name']}
- Type: {customer['customer_type']}
- Location: {customer['location']}, {customer['country']}
- Risk Level: {customer['risk_level'].upper()}
- KYC Status: {customer['kyc_status']}

BUSINESS DETAILS:
- Established: {customer['created_at'].strftime('%Y-%m-%d')}
- Primary Activities: {customer['customer_type']} operations

RISK INDICATORS:
{chr(10).join(f"- {flag}" for flag in red_flags)}

COMPLIANCE NOTES:
- Enhanced due diligence required
- Regular monitoring recommended
- Potential PEP connections
- Unusual transaction patterns observed

DOCUMENTATION STATUS:
- Identity verification: PENDING
- Address verification: PENDING
- Business registration: PENDING
- Financial statements: INCOMPLETE
"""
        else:
            # Standard KYC for legitimate customers
            kyc_content = f"""
KYC Document - {customer['customer_name']}
Customer ID: {customer['customer_id']}
Date: {datetime.now().strftime('%Y-%m-%d')}

CUSTOMER INFORMATION:
- Name: {customer['customer_name']}
- Type: {customer['customer_type']}
- Location: {customer['location']}, {customer['country']}
- Risk Level: {customer['risk_level'].upper()}
- KYC Status: {customer['kyc_status']}

BUSINESS DETAILS:
- Established: {customer['created_at'].strftime('%Y-%m-%d')}
- Primary Activities: {customer['customer_type']} operations

COMPLIANCE STATUS:
- Identity verification: COMPLETED
- Address verification: COMPLETED
- Business registration: VERIFIED
- Financial statements: PROVIDED
- No adverse media found
- Standard risk profile
"""
        
        return kyc_content

def main():
    """Main function to generate synthetic data"""
    print("🚀 Starting Multi-Agent AML Synthetic Data Generation")
    print("=" * 60)
    
    # Initialize generator
    generator = SyntheticDataGenerator(
        num_customers=50,  # Adjust as needed
        num_transactions=200  # Adjust as needed
    )
    
    # Generate data
    print("📊 Generating customers...")
    customers = generator.generate_customers()
    print(f"   Generated {len(customers)} customers")
    
    print("💳 Generating transactions...")
    transactions = generator.generate_transactions()
    print(f"   Generated {len(transactions)} transactions")
    
    print("🚨 Generating alerts...")
    alerts = generator.generate_alerts()
    print(f"   Generated {len(alerts)} alerts")
    
    # Save to database
    print("💾 Saving to database...")
    generator.save_to_database()
    
    # Save to CSV
    print("📁 Saving to CSV files...")
    generator.save_to_csv()
    
    # Generate KYC documents
    print("📄 Generating KYC documents...")
    generator.generate_kyc_documents()
    
    print("✅ Data generation complete!")
    print("=" * 60)
    print("Generated data includes:")
    print(f"- {len(customers)} customers (legitimate businesses, criminal entities, money mules)")
    print(f"- {len(transactions)} transactions with embedded laundering patterns")
    print(f"- {len(alerts)} alerts for suspicious activity")
    print("- KYC documents for all customers")
    print("\nLaundering patterns included:")
    print("- Structuring (multiple transactions under $10k)")
    print("- Smurfing (coordinated small transfers)")
    print("- Scatter-gather (distribute then consolidate)")
    print("- Natural laundering (payroll, supplies)")

if __name__ == "__main__":
    main()
