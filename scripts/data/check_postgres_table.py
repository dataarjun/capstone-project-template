"""
Check existing PostgreSQL table structure
"""

import asyncio
import asyncpg
from app.core.config_simple import settings

async def check_table_structure():
    """Check the structure of existing tables"""
    connection = None
    
    try:
        connection = await asyncpg.connect(settings.POSTGRES_URL)
        print("✅ Connected to PostgreSQL database")
        
        # Check if transactions table exists
        table_exists = await connection.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'transactions'
            );
        """)
        
        if table_exists:
            print("📋 Transactions table exists")
            
            # Get table structure
            columns = await connection.fetch("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'transactions'
                ORDER BY ordinal_position;
            """)
            
            print("📊 Table structure:")
            for col in columns:
                print(f"   {col['column_name']}: {col['data_type']} {'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'}")
            
            # Get row count
            count = await connection.fetchval("SELECT COUNT(*) FROM transactions")
            print(f"📈 Row count: {count:,}")
            
        else:
            print("❌ Transactions table does not exist")
        
        # List all tables
        tables = await connection.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        print(f"\n📋 All tables in database:")
        for table in tables:
            print(f"   - {table['table_name']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        if connection:
            await connection.close()

if __name__ == "__main__":
    asyncio.run(check_table_structure())
