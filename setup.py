#!/usr/bin/env python3
"""
Setup script for Multi-Agent AML Investigation System
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False


def check_poetry_installed():
    """Check if Poetry is installed"""
    try:
        subprocess.run(["poetry", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_poetry():
    """Install Poetry if not available"""
    print("📦 Installing Poetry...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "poetry"
        ], check=True)
        print("✅ Poetry installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Poetry: {e}")
        return False


def setup_environment():
    """Set up the development environment"""
    print("🚀 Setting up Multi-Agent AML Investigation System")
    print("=" * 60)
    
    # Check if Poetry is installed
    if not check_poetry_installed():
        print("Poetry not found. Installing Poetry...")
        if not install_poetry():
            print("❌ Failed to install Poetry. Please install it manually:")
            print("   curl -sSL https://install.python-poetry.org | python3 -")
            return False
    
    # Install dependencies
    if not run_command("poetry install", "Installing dependencies"):
        return False
    
    # Install pre-commit hooks
    if not run_command("poetry run pre-commit install", "Installing pre-commit hooks"):
        print("⚠️  Pre-commit hooks installation failed, but continuing...")
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if not env_file.exists() and env_example.exists():
        print("📝 Creating .env file from template...")
        try:
            with open(env_example, 'r') as f:
                content = f.read()
            with open(env_file, 'w') as f:
                f.write(content)
            print("✅ .env file created. Please edit it with your API keys.")
        except Exception as e:
            print(f"⚠️  Could not create .env file: {e}")
    
    # Create data directory
    data_dir = Path("data")
    if not data_dir.exists():
        print("📁 Creating data directory...")
        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / "raw").mkdir(exist_ok=True)
        (data_dir / "processed").mkdir(exist_ok=True)
        (data_dir / "kyc_documents").mkdir(exist_ok=True)
        (data_dir / "kyc_vectordb").mkdir(exist_ok=True)
        print("✅ Data directories created")
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your API keys")
    print("2. Run: poetry run python -m app.db.init_db")
    print("3. Run: poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
    print("\n🌐 The application will be available at: http://localhost:8000")
    print("📚 API documentation at: http://localhost:8000/docs")
    
    return True


if __name__ == "__main__":
    success = setup_environment()
    sys.exit(0 if success else 1)
