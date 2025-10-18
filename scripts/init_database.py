#!/usr/bin/env python3
"""
Database Initialization Script

This script initializes the database and creates the necessary tables
for the Multi-Agent AML Investigation System.
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the app directory to the path
sys.path.append('../')

from app.core.config_simple import settings
from app.db.models import Base

def init_database():
    """Initialize the database with all tables"""
    print("🚀 Initializing Multi-Agent AML Database")
    print("=" * 50)
    
    # Create database directory if it doesn't exist
    db_dir = os.path.dirname(settings.DATABASE_URL.replace('sqlite:///', ''))
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        print(f"📁 Created database directory: {db_dir}")
    
    # Create engine
    engine = create_engine(settings.DATABASE_URL, echo=False)
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        
        # Test connection
        with engine.connect() as connection:
            from sqlalchemy import text
            result = connection.execute(text("SELECT 1"))
            print("✅ Database connection test passed")
        
        print(f"📊 Database URL: {settings.DATABASE_URL}")
        print("✅ Database initialization complete!")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise

if __name__ == "__main__":
    init_database()
