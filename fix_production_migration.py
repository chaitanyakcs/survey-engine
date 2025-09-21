#!/usr/bin/env python3
"""
Script to manually run the human_reviews prompt editing migration in production.
This fixes the missing columns that are causing the database errors.
"""

import os
import psycopg2
from urllib.parse import urlparse

def run_migration():
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        return False
    
    try:
        # Parse the database URL
        parsed_url = urlparse(database_url)
        
        # Connect to the database
        conn = psycopg2.connect(
            host=parsed_url.hostname,
            port=parsed_url.port,
            database=parsed_url.path[1:],  # Remove leading slash
            user=parsed_url.username,
            password=parsed_url.password
        )
        
        print(f"✅ Connected to database: {parsed_url.hostname}:{parsed_url.port}/{parsed_url.path[1:]}")
        
        # Read the migration file
        with open('migrations/014_add_human_review_prompt_editing.sql', 'r') as f:
            migration_sql = f.read()
        
        # Execute the migration
        cursor = conn.cursor()
        cursor.execute(migration_sql)
        conn.commit()
        
        print("✅ Migration executed successfully")
        
        # Verify the columns exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'human_reviews' 
            AND column_name IN ('edited_prompt_data', 'original_prompt_data', 'prompt_edited', 'prompt_edit_timestamp', 'edited_by', 'edit_reason')
            ORDER BY column_name;
        """)
        
        columns = cursor.fetchall()
        print(f"✅ Found {len(columns)} prompt editing columns:")
        for col in columns:
            print(f"   - {col[0]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_migration()
    exit(0 if success else 1)

