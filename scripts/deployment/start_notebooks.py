#!/usr/bin/env python3
"""
Start Jupyter Notebook for the Multi-Agent AML Investigation System.
"""

import subprocess
import sys
import os
from pathlib import Path

def start_jupyter():
    """Start Jupyter Notebook server"""
    print("🚀 Starting Jupyter Notebook for Multi-Agent AML Investigation System")
    print("=" * 70)
    print("📚 Available Notebooks:")
    print("  1. 01_database_setup.ipynb - Database setup and testing")
    print("  2. 02_document_chunking.ipynb - Document processing and vector DB")
    print("  3. 03_agent_testing.ipynb - Agent testing and workflow simulation")
    print("  4. 04_api_testing.ipynb - API testing and integration")
    print("=" * 70)
    print("🌐 Jupyter will be available at: http://localhost:8888")
    print("📁 Working directory: notebooks/")
    print("=" * 70)
    
    # Change to notebooks directory
    notebooks_dir = Path(__file__).parent / "notebooks"
    os.chdir(notebooks_dir)
    
    try:
        # Start Jupyter Notebook
        subprocess.run([
            sys.executable, "-m", "jupyter", "notebook",
            "--ip=0.0.0.0",
            "--port=8888",
            "--no-browser",
            "--allow-root"
        ])
    except KeyboardInterrupt:
        print("\n👋 Jupyter Notebook stopped.")
    except Exception as e:
        print(f"❌ Error starting Jupyter: {e}")

if __name__ == "__main__":
    start_jupyter()
