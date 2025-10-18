#!/usr/bin/env python3
"""
Data Generation Runner

This script runs the complete data generation process for the Multi-Agent AML system.
"""

import os
import sys
import subprocess

def main():
    """Run the complete data generation process"""
    print("🚀 Multi-Agent AML Data Generation")
    print("=" * 50)
    
    # Change to scripts directory
    scripts_dir = os.path.join(os.path.dirname(__file__), 'scripts')
    
    try:
        # Step 1: Initialize database
        print("📊 Step 1: Initializing database...")
        subprocess.run([sys.executable, 'init_database.py'], cwd=scripts_dir, check=True)
        
        # Step 2: Generate synthetic data
        print("\n💳 Step 2: Generating synthetic data...")
        subprocess.run([sys.executable, 'generate_synthetic_data.py'], cwd=scripts_dir, check=True)
        
        print("\n✅ Data generation complete!")
        print("=" * 50)
        print("Your Multi-Agent AML system now has:")
        print("📁 Database: data/aml_database.db")
        print("📄 CSV files: data/raw/")
        print("📋 KYC documents: data/kyc_documents/")
        print("🔍 Vector database: data/kyc_vectordb/")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during data generation: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

