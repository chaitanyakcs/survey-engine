#!/usr/bin/env python3
"""
Railway Migration Verification Script

This script verifies that the database constraint for document_uploads.processing_status
includes the 'cancelled' status. It's designed to run in Railway environment to ensure
the migration was applied correctly.
"""

import os
import sys
import psycopg2
from psycopg2 import sql
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_database_connection():
    """Get database connection from DATABASE_URL or individual env vars"""
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        logger.info("Using DATABASE_URL for connection")
        return psycopg2.connect(database_url)
    else:
        # Fallback to individual environment variables
        host = os.getenv('DATABASE_HOST', 'localhost')
        port = os.getenv('DATABASE_PORT', '5432')
        database = os.getenv('DATABASE_NAME', 'survey_engine_db')
        user = os.getenv('DATABASE_USER', 'survey_engine')
        password = os.getenv('DATABASE_PASSWORD', '')
        
        logger.info(f"Using individual env vars: {host}:{port}/{database}")
        return psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )

def check_constraint_exists(cursor, table_name, constraint_name):
    """Check if a constraint exists on a table"""
    query = """
    SELECT constraint_name, check_clause
    FROM information_schema.check_constraints
    WHERE constraint_name = %s
    AND constraint_schema = 'public'
    """
    
    cursor.execute(query, (constraint_name,))
    result = cursor.fetchone()
    
    if result:
        logger.info(f"Found constraint '{constraint_name}': {result[1]}")
        return result[1]
    else:
        logger.warning(f"Constraint '{constraint_name}' not found")
        return None

def verify_processing_status_constraint():
    """Verify that the processing_status constraint includes 'cancelled'"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        logger.info("🔍 Checking document_uploads.processing_status constraint...")
        
        # Check if the constraint exists
        constraint_clause = check_constraint_exists(cursor, 'document_uploads', 'check_processing_status')
        
        if not constraint_clause:
            logger.error("❌ check_processing_status constraint not found!")
            return False
        
        # Check if 'cancelled' is in the constraint
        if "'cancelled'" in constraint_clause:
            logger.info("✅ Constraint includes 'cancelled' status")
            return True
        else:
            logger.error(f"❌ Constraint does not include 'cancelled' status. Current: {constraint_clause}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error checking constraint: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def test_cancelled_status():
    """Test that we can actually insert a 'cancelled' status"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        logger.info("🧪 Testing insertion of 'cancelled' status...")
        
        # Try to insert a test record with 'cancelled' status
        test_query = """
        INSERT INTO document_uploads (
            session_id, 
            filename, 
            file_size, 
            processing_status, 
            created_at
        ) VALUES (
            'test-cancelled-verification', 
            'test.docx', 
            1024, 
            'cancelled', 
            NOW()
        ) ON CONFLICT (session_id) DO UPDATE SET processing_status = 'cancelled'
        """
        
        cursor.execute(test_query)
        conn.commit()
        
        logger.info("✅ Successfully inserted/updated record with 'cancelled' status")
        
        # Clean up test record
        cursor.execute("DELETE FROM document_uploads WHERE session_id = 'test-cancelled-verification'")
        conn.commit()
        
        logger.info("🧹 Cleaned up test record")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing 'cancelled' status: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def main():
    """Main verification function"""
    logger.info("🚀 Starting Railway migration verification...")
    
    # Check if we're in Railway environment
    if os.getenv('RAILWAY_ENVIRONMENT'):
        logger.info("✅ Railway environment detected")
    else:
        logger.info("⚠️ Not in Railway environment, but continuing verification...")
    
    # Verify constraint exists and includes 'cancelled'
    constraint_ok = verify_processing_status_constraint()
    
    if not constraint_ok:
        logger.error("❌ Constraint verification failed!")
        sys.exit(1)
    
    # Test actual insertion of 'cancelled' status
    insertion_ok = test_cancelled_status()
    
    if not insertion_ok:
        logger.error("❌ Insertion test failed!")
        sys.exit(1)
    
    logger.info("✅ All verification tests passed!")
    logger.info("🎉 Railway migration verification completed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
