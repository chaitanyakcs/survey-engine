#!/usr/bin/env python3
"""
Standalone Database Migration Runner
Runs all database migrations using the admin API migration functions
"""

import os
import sys
import asyncio
import logging
from sqlalchemy.orm import Session
from src.database.connection import get_db
from src.api.admin import migrate_all

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def run_migrations() -> bool:
    """Run all database migrations"""
    try:
        logger.info("🚀 Starting database migrations...")
        
        # Get database session
        db = next(get_db())
        
        # Run migrations using the admin API function
        result = await migrate_all(db)
        
        if result.get("status") == "success":
            logger.info("✅ All migrations completed successfully!")
            return True
        else:
            logger.error(f"❌ Migration failed: {result}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error running migrations: {str(e)}")
        return False
    finally:
        if 'db' in locals():
            db.close()

def main() -> None:
    """Main function"""
    logger.info("🔧 Database Migration Runner")
    logger.info("=" * 50)
    
    # Check if we're in Railway environment
    if os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('RAILWAY_PROJECT_ID'):
        logger.info("✅ Railway environment detected")
    else:
        logger.info("⚠️ Not in Railway environment, but continuing...")
    
    # Run migrations
    success = asyncio.run(run_migrations())
    
    if success:
        logger.info("🎉 Migration process completed successfully!")
        sys.exit(0)
    else:
        logger.error("💥 Migration process failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
