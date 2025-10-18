"""
PostgreSQL Session Management

This module handles PostgreSQL database session creation, configuration, and
connection management for the Multi-Agent AML Investigation System.
"""

from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.core.config_simple import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

# Create PostgreSQL database engine
postgres_engine = None
PostgresSessionLocal = None

def get_postgres_engine():
    """Get or create PostgreSQL engine"""
    global postgres_engine
    if postgres_engine is None:
        if not settings.POSTGRES_URL:
            raise ValueError("POSTGRES_URL not configured. Please set it in your environment variables.")
        
        # Validate POSTGRES_URL doesn't contain placeholder values
        if '[host]' in settings.POSTGRES_URL or '[password]' in settings.POSTGRES_URL:
            raise ValueError(f"POSTGRES_URL contains placeholder values: {settings.POSTGRES_URL}")
        
        if 'host' in settings.POSTGRES_URL and 'pooler.supabase.com' not in settings.POSTGRES_URL:
            raise ValueError(f"POSTGRES_URL appears to contain literal 'host' instead of actual hostname: {settings.POSTGRES_URL}")
        
        # Debug: Log the POSTGRES_URL being used (mask password for security)
        masked_url = settings.POSTGRES_URL
        if '@' in masked_url and ':' in masked_url:
            parts = masked_url.split('@')
            if len(parts) == 2:
                user_pass = parts[0]
                rest = parts[1]
                if ':' in user_pass:
                    user_part, pass_part = user_pass.rsplit(':', 1)
                    masked_url = f"{user_part}:***@{rest}"
        
        logger.info(f"Creating PostgreSQL engine with URL: {masked_url}")
        
        postgres_engine = create_engine(
            settings.POSTGRES_URL,
            echo=settings.DEBUG,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=10,
            max_overflow=20
        )
    return postgres_engine

def get_postgres_session_factory():
    """Get or create PostgreSQL session factory"""
    global PostgresSessionLocal
    if PostgresSessionLocal is None:
        engine = get_postgres_engine()
        PostgresSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return PostgresSessionLocal

def get_postgres_db() -> Generator[Session, None, None]:
    """
    Get PostgreSQL database session dependency
    
    Yields:
        PostgreSQL database session
    """
    SessionFactory = get_postgres_session_factory()
    db = SessionFactory()
    try:
        yield db
    except Exception as e:
        logger.error(f"PostgreSQL session error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

def create_postgres_tables():
    """Create PostgreSQL database tables"""
    try:
        # Import models to ensure they are registered
        from app.db.models import Base
        
        # Force a fresh engine to avoid cached connections with old config
        global postgres_engine
        if postgres_engine:
            postgres_engine.dispose()
            postgres_engine = None
            
        engine = get_postgres_engine()
        Base.metadata.create_all(bind=engine)
        logger.info("PostgreSQL database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create PostgreSQL database tables: {str(e)}")
        logger.error(f"POSTGRES_URL being used: {settings.POSTGRES_URL[:50]}...")
        raise

def drop_postgres_tables():
    """Drop PostgreSQL database tables"""
    try:
        from app.db.models import Base
        engine = get_postgres_engine()
        Base.metadata.drop_all(bind=engine)
        logger.info("PostgreSQL database tables dropped successfully")
    except Exception as e:
        logger.error(f"Failed to drop PostgreSQL database tables: {str(e)}")
        raise

def test_postgres_connection():
    """Test PostgreSQL connection and return connection info"""
    try:
        # Force a fresh engine to avoid cached connections with old config
        global postgres_engine
        if postgres_engine:
            postgres_engine.dispose()
            postgres_engine = None
            
        engine = get_postgres_engine()
        
        # Test basic connection
        with engine.connect() as conn:
            # Get connection info
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            
            # Get database info
            result = conn.execute(text("SELECT current_database(), current_user, inet_server_addr(), inet_server_port()"))
            db_info = result.fetchone()
            database, user, host, port = db_info
            
            # List existing tables
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            
            connection_info = {
                "status": "success",
                "version": version,
                "database": database,
                "user": user,
                "host": host,
                "port": port,
                "tables": tables
            }
            
            logger.info(f"PostgreSQL connection successful: {database}@{host}:{port}")
            return connection_info
            
    except Exception as e:
        error_info = {
            "status": "error",
            "error": str(e)
        }
        logger.error(f"PostgreSQL connection failed: {str(e)}")
        return error_info

def get_postgres_table_count(table_name: str):
    """Get row count for a specific table"""
    try:
        engine = get_postgres_engine()
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            count = result.fetchone()[0]
            return count
    except Exception as e:
        logger.error(f"Failed to get count for table {table_name}: {str(e)}")
        return 0

def reset_postgres_engine():
    """Reset the PostgreSQL engine cache - useful for configuration changes"""
    global postgres_engine, PostgresSessionLocal
    if postgres_engine:
        postgres_engine.dispose()
        postgres_engine = None
        PostgresSessionLocal = None
        logger.info("PostgreSQL engine cache reset")

def reload_postgres_config():
    """Reload PostgreSQL configuration from environment"""
    try:
        # Reset the engine cache
        reset_postgres_engine()
        
        # Reload the settings
        import importlib
        import app.core.config_simple
        importlib.reload(app.core.config_simple)
        
        # Get the new settings
        from app.core.config_simple import settings
        
        logger.info(f"PostgreSQL configuration reloaded. POSTGRES_URL: {settings.POSTGRES_URL[:50]}...")
        return True
    except Exception as e:
        logger.error(f"Failed to reload PostgreSQL configuration: {str(e)}")
        return False
