#!/usr/bin/env python3
"""
Enable pgvector extension on Railway PostgreSQL
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def enable_pgvector():
    """Enable pgvector extension on Railway PostgreSQL"""
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("❌ DATABASE_URL environment variable not set")
        return False
    
    logger.info(f"🔧 Connecting to Railway database: {database_url.split('@')[1] if '@' in database_url else 'unknown'}")
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                # 1. Check if pgvector extension is available
                logger.info("🔍 Checking if pgvector extension is available...")
                result = conn.execute(text("""
                    SELECT * FROM pg_available_extensions 
                    WHERE name = 'vector';
                """))
                
                available = result.fetchone()
                if not available:
                    logger.error("❌ pgvector extension is not available on this Railway PostgreSQL instance")
                    logger.info("💡 You need to use Railway's pgvector template: https://railway.com/deploy/pgvector-latest")
                    return False
                
                logger.info("✅ pgvector extension is available")
                
                # 2. Enable pgvector extension
                logger.info("🔧 Enabling pgvector extension...")
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                logger.info("✅ pgvector extension enabled")
                
                # 3. Check if rfq_embedding column exists and fix its type
                logger.info("🔍 Checking rfq_embedding column...")
                result = conn.execute(text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'golden_rfq_survey_pairs' 
                    AND column_name = 'rfq_embedding';
                """))
                
                column_info = result.fetchone()
                if column_info:
                    logger.info(f"📋 Current column type: {column_info[1]}")
                    
                    if column_info[1] == 'text':
                        logger.info("🔧 Converting text column to vector(384)...")
                        # Drop and recreate column
                        conn.execute(text("ALTER TABLE golden_rfq_survey_pairs DROP COLUMN rfq_embedding;"))
                        conn.execute(text("ALTER TABLE golden_rfq_survey_pairs ADD COLUMN rfq_embedding vector(384);"))
                        logger.info("✅ Column converted to vector(384)")
                    elif column_info[1] == 'USER-DEFINED':
                        logger.info("✅ Column is already vector type")
                    else:
                        logger.warning(f"⚠️ Unexpected column type: {column_info[1]}")
                else:
                    logger.info("🔧 Creating rfq_embedding column...")
                    conn.execute(text("ALTER TABLE golden_rfq_survey_pairs ADD COLUMN rfq_embedding vector(384);"))
                    logger.info("✅ Column created")
                
                # 4. Create vector index
                logger.info("🔧 Creating vector similarity index...")
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_golden_rfq_survey_pairs_rfq_embedding 
                    ON golden_rfq_survey_pairs 
                    USING ivfflat (rfq_embedding vector_cosine_ops) 
                    WITH (lists = 100);
                """))
                logger.info("✅ Vector index created")
                
                # 5. Verify everything works
                logger.info("🔍 Verifying vector operations...")
                result = conn.execute(text("""
                    SELECT 
                        (SELECT COUNT(*) FROM golden_rfq_survey_pairs WHERE rfq_embedding IS NOT NULL) as vector_count,
                        (SELECT COUNT(*) FROM golden_rfq_survey_pairs) as total_count;
                """))
                
                counts = result.fetchone()
                logger.info(f"📊 Vector embeddings: {counts[0]}/{counts[1]}")
                
                # Test vector operation
                test_embedding = [0.1] * 384
                conn.execute(text("""
                    SELECT rfq_embedding <=> :embedding as similarity
                    FROM golden_rfq_survey_pairs 
                    WHERE rfq_embedding IS NOT NULL 
                    LIMIT 1;
                """), {"embedding": test_embedding})
                
                logger.info("✅ Vector operations working correctly")
                
                # Commit transaction
                trans.commit()
                logger.info("🎉 pgvector enabled successfully on Railway!")
                return True
                
            except Exception as e:
                logger.error(f"❌ Error enabling pgvector: {e}")
                trans.rollback()
                return False
                
    except SQLAlchemyError as e:
        logger.error(f"❌ Database connection error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = enable_pgvector()
    sys.exit(0 if success else 1)
