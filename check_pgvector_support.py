#!/usr/bin/env python3
"""
Check if Railway PostgreSQL supports pgvector extension
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_pgvector_support():
    """Check if pgvector is available on current Railway PostgreSQL"""
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("❌ DATABASE_URL environment variable not set")
        return False
    
    logger.info(f"🔍 Checking Railway PostgreSQL: {database_url.split('@')[1] if '@' in database_url else 'unknown'}")
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Check PostgreSQL version
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            logger.info(f"📋 PostgreSQL version: {version}")
            
            # Check if pgvector extension is available
            logger.info("🔍 Checking if pgvector extension is available...")
            result = conn.execute(text("""
                SELECT * FROM pg_available_extensions 
                WHERE name = 'vector';
            """))
            
            available = result.fetchone()
            if available:
                logger.info("✅ pgvector extension is AVAILABLE!")
                logger.info(f"📋 Extension details: {available}")
                
                # Try to enable it
                logger.info("🔧 Attempting to enable pgvector extension...")
                try:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                    logger.info("🎉 pgvector extension enabled successfully!")
                    return True
                except Exception as e:
                    logger.error(f"❌ Failed to enable pgvector: {e}")
                    return False
            else:
                logger.error("❌ pgvector extension is NOT available on this Railway PostgreSQL instance")
                logger.info("💡 You need to add a new PostgreSQL service with pgvector template")
                return False
                
    except SQLAlchemyError as e:
        logger.error(f"❌ Database connection error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = check_pgvector_support()
    sys.exit(0 if success else 1)
