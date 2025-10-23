#!/usr/bin/env python3
"""
Script to fix missing updated_at columns in production database
This script runs the migration fix directly via SQLAlchemy
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def run_migration_fix():
    """Run the migration fix for missing updated_at columns"""
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        return False
    
    try:
        # Create database connection
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print("🔧 Running migration fix for missing updated_at columns...")
        
        # Read the migration SQL file
        migration_file = "migrations/026_fix_missing_updated_at_columns.sql"
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        # Execute the migration SQL
        session.execute(text(migration_sql))
        session.commit()
        
        print("✅ Migration fix completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration fix failed: {str(e)}")
        session.rollback()
        return False
    finally:
        session.close()

if __name__ == "__main__":
    success = run_migration_fix()
    sys.exit(0 if success else 1)
