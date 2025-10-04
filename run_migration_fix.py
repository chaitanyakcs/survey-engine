#!/usr/bin/env python3
"""
Local Migration Fix Script
==========================

This script runs the existing Alembic migration to add the missing session_id column.
It can be run locally to fix the database schema issue.

Usage:
    python run_migration_fix.py [--dry-run]
"""

import os
import sys
import subprocess
import argparse

def run_command(cmd, dry_run=False):
    """Run a command and return the result"""
    print(f"🔧 Running: {' '.join(cmd)}")
    
    if dry_run:
        print("   [DRY RUN] Command would be executed")
        return True
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ Command succeeded: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e.stderr}")
        return False

def check_alembic_status():
    """Check the current Alembic migration status"""
    print("🔍 Checking current migration status...")
    
    # Check if alembic is available
    try:
        result = subprocess.run(['alembic', 'current'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Current migration: {result.stdout.strip()}")
        else:
            print(f"❌ Failed to get current migration: {result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ Alembic not found. Please install it or activate your virtual environment.")
        return False
    
    return True

def run_migration(dry_run=False):
    """Run the migration to add session_id column"""
    print("🚀 Running migration to add session_id column...")
    
    # First check current status
    if not check_alembic_status():
        return False
    
    # Run the migration
    cmd = ['alembic', 'upgrade', 'head']
    if not run_command(cmd, dry_run):
        print("❌ Migration failed!")
        return False
    
    print("✅ Migration completed successfully!")
    return True

def main():
    parser = argparse.ArgumentParser(description='Run migration to fix database schema')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    args = parser.parse_args()
    
    print("🔧 Local Migration Fix Script")
    print("=" * 40)
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
        print("=" * 40)
    
    # Check if we're in the right directory
    if not os.path.exists('alembic.ini'):
        print("❌ Error: alembic.ini not found. Please run from project root.")
        sys.exit(1)
    
    # Check if we have the right environment
    if not os.getenv('DATABASE_URL'):
        print("❌ Error: DATABASE_URL environment variable not set.")
        print("   Please set your database URL before running migrations.")
        sys.exit(1)
    
    # Run the migration
    if run_migration(args.dry_run):
        print("\n🎉 Migration fix completed successfully!")
        print("   The session_id column should now be available in document_uploads table.")
    else:
        print("\n❌ Migration fix failed!")
        print("   Please check the error messages above and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()
