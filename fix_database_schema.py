#!/usr/bin/env python3
"""
Database Schema Fix Script
=========================

This script fixes the missing session_id column in the document_uploads table.
It can be run directly against the Railway database to resolve the migration issue.

Usage:
    python fix_database_schema.py [--dry-run] [--force]

Options:
    --dry-run    Show what would be done without making changes
    --force      Skip confirmation prompts
"""

import os
import sys
import argparse
import psycopg2
from psycopg2 import sql
from urllib.parse import urlparse

def get_database_url():
    """Get database URL from environment variables"""
    # Try different environment variable names
    db_url = os.getenv('DATABASE_URL') or os.getenv('RAILWAY_DATABASE_URL') or os.getenv('POSTGRES_URL')
    
    if not db_url:
        print("❌ Error: No database URL found in environment variables")
        print("   Please set DATABASE_URL, RAILWAY_DATABASE_URL, or POSTGRES_URL")
        sys.exit(1)
    
    return db_url

def check_column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    query = """
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = %s AND column_name = %s
    """
    cursor.execute(query, (table_name, column_name))
    return cursor.fetchone() is not None

def check_index_exists(cursor, index_name):
    """Check if an index exists"""
    query = """
    SELECT indexname 
    FROM pg_indexes 
    WHERE indexname = %s
    """
    cursor.execute(query, (index_name,))
    return cursor.fetchone() is not None

def fix_document_uploads_schema(cursor, dry_run=False):
    """Fix the document_uploads table schema"""
    print("🔍 Checking document_uploads table schema...")
    
    # Check if session_id column exists
    if check_column_exists(cursor, 'document_uploads', 'session_id'):
        print("✅ session_id column already exists")
    else:
        print("❌ session_id column missing - will add it")
        if not dry_run:
            cursor.execute("""
                ALTER TABLE document_uploads 
                ADD COLUMN session_id VARCHAR(100)
            """)
            print("✅ Added session_id column")
        else:
            print("   [DRY RUN] Would add session_id column")
    
    # Check if uploaded_by column exists
    if check_column_exists(cursor, 'document_uploads', 'uploaded_by'):
        print("✅ uploaded_by column already exists")
    else:
        print("❌ uploaded_by column missing - will add it")
        if not dry_run:
            cursor.execute("""
                ALTER TABLE document_uploads 
                ADD COLUMN uploaded_by VARCHAR(255)
            """)
            print("✅ Added uploaded_by column")
        else:
            print("   [DRY RUN] Would add uploaded_by column")
    
    # Check if original_filename is nullable
    cursor.execute("""
        SELECT is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'document_uploads' AND column_name = 'original_filename'
    """)
    result = cursor.fetchone()
    if result and result[0] == 'NO':
        print("❌ original_filename is not nullable - will make it nullable")
        if not dry_run:
            cursor.execute("""
                ALTER TABLE document_uploads 
                ALTER COLUMN original_filename DROP NOT NULL
            """)
            print("✅ Made original_filename nullable")
        else:
            print("   [DRY RUN] Would make original_filename nullable")
    else:
        print("✅ original_filename is already nullable")
    
    # Check if file_size is nullable
    cursor.execute("""
        SELECT is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'document_uploads' AND column_name = 'file_size'
    """)
    result = cursor.fetchone()
    if result and result[0] == 'NO':
        print("❌ file_size is not nullable - will make it nullable")
        if not dry_run:
            cursor.execute("""
                ALTER TABLE document_uploads 
                ALTER COLUMN file_size DROP NOT NULL
            """)
            print("✅ Made file_size nullable")
        else:
            print("   [DRY RUN] Would make file_size nullable")
    else:
        print("✅ file_size is already nullable")
    
    # Check if session_id index exists
    if check_index_exists(cursor, 'idx_document_uploads_session_id'):
        print("✅ session_id index already exists")
    else:
        print("❌ session_id index missing - will add it")
        if not dry_run:
            cursor.execute("""
                CREATE INDEX idx_document_uploads_session_id 
                ON document_uploads (session_id)
            """)
            print("✅ Added session_id index")
        else:
            print("   [DRY RUN] Would add session_id index")

def main():
    parser = argparse.ArgumentParser(description='Fix database schema for document_uploads table')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--force', action='store_true', help='Skip confirmation prompts')
    args = parser.parse_args()
    
    print("🔧 Database Schema Fix Script")
    print("=" * 40)
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
        print("=" * 40)
    
    # Get database connection
    try:
        db_url = get_database_url()
        print(f"🔗 Connecting to database...")
        
        # Parse the database URL
        parsed_url = urlparse(db_url)
        
        conn = psycopg2.connect(
            host=parsed_url.hostname,
            port=parsed_url.port,
            database=parsed_url.path[1:],  # Remove leading slash
            user=parsed_url.username,
            password=parsed_url.password,
            sslmode='require' if parsed_url.hostname else 'prefer'
        )
        
        cursor = conn.cursor()
        print("✅ Connected to database successfully")
        
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        sys.exit(1)
    
    try:
        # Check if document_uploads table exists
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'document_uploads'
        """)
        
        if not cursor.fetchone():
            print("❌ document_uploads table does not exist!")
            print("   This script only fixes existing tables. Please run migrations first.")
            sys.exit(1)
        
        print("✅ document_uploads table exists")
        
        # Fix the schema
        fix_document_uploads_schema(cursor, args.dry_run)
        
        if not args.dry_run:
            # Commit changes
            conn.commit()
            print("\n✅ All changes committed successfully!")
        else:
            print("\n🔍 Dry run completed - no changes were made")
            print("   Run without --dry-run to apply the changes")
        
    except Exception as e:
        print(f"❌ Error during schema fix: {e}")
        conn.rollback()
        sys.exit(1)
    
    finally:
        cursor.close()
        conn.close()
        print("🔌 Database connection closed")

if __name__ == "__main__":
    main()
