#!/usr/bin/env python3
"""
Simple script to migrate data from Railway to a new database
This script exports data from Railway and prepares it for import elsewhere
"""

import os
import sys
import json
import subprocess
from datetime import datetime

def export_railway_data():
    """Export data from Railway database"""
    print("🔄 Starting Railway data export...")
    
    # Get database URL from environment
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ No DATABASE_URL found in environment")
        return False
    
    print(f"📊 Database URL: {db_url[:50]}...")
    
    try:
        # Try to export using pg_dump
        print("📤 Attempting pg_dump export...")
        result = subprocess.run(['pg_dump', db_url], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            # Save the dump
            with open('railway_export.sql', 'w') as f:
                f.write(result.stdout)
            print("✅ Database exported to railway_export.sql")
            return True
        else:
            print(f"❌ pg_dump failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Export timed out")
        return False
    except Exception as e:
        print(f"❌ Export error: {e}")
        return False

def create_migration_instructions():
    """Create instructions for migrating to different platforms"""
    
    instructions = """
# Railway to AWS Migration Instructions

## What we have:
- PostgreSQL database with pgvector extension
- Survey Engine application data
- ~200MB of data in Railway volumes

## Migration Options:

### Option 1: AWS RDS (Recommended)
1. Create RDS PostgreSQL instance
2. Install pgvector extension: `CREATE EXTENSION vector;`
3. Import data: `psql -h your-rds-endpoint -U postgres -d survey_engine < railway_export.sql`

### Option 2: Railway Fresh Start
1. Create new Railway project
2. Add PostgreSQL service
3. Import data: `psql -h new-postgres.railway.internal -U postgres -d railway < railway_export.sql`

### Option 3: Render
1. Create Render PostgreSQL database
2. Import data using Render's database tools

### Option 4: DigitalOcean
1. Create DigitalOcean PostgreSQL cluster
2. Import data using their migration tools

## Environment Variables to Set:
- DATABASE_URL: postgresql://user:pass@host:port/database
- REPLICATE_API_TOKEN: your-replicate-token
- ENVIRONMENT: production

## Next Steps:
1. Choose your target platform
2. Create new database
3. Import railway_export.sql
4. Update application with new DATABASE_URL
5. Deploy application
"""
    
    with open('MIGRATION_INSTRUCTIONS.md', 'w') as f:
        f.write(instructions)
    
    print("📋 Migration instructions saved to MIGRATION_INSTRUCTIONS.md")

def main():
    print("🚀 Railway Data Migration Tool")
    print("=" * 40)
    
    # Try to export data
    if export_railway_data():
        print("\n✅ Data export successful!")
        print("📁 Files created:")
        print("   - railway_export.sql (database dump)")
        
        # Create migration instructions
        create_migration_instructions()
        print("   - MIGRATION_INSTRUCTIONS.md (migration guide)")
        
        print("\n🎯 Next steps:")
        print("1. Choose your target platform (AWS, Railway, Render, etc.)")
        print("2. Create a new database")
        print("3. Import railway_export.sql")
        print("4. Update your app with new DATABASE_URL")
        print("5. Deploy!")
        
    else:
        print("\n❌ Data export failed")
        print("💡 Alternative: Use Railway dashboard to export data")
        print("   1. Go to Railway dashboard")
        print("   2. Select your PostgreSQL service")
        print("   3. Use the 'Data' tab to export")
        
        # Still create instructions
        create_migration_instructions()
        print("\n📋 Migration instructions saved to MIGRATION_INSTRUCTIONS.md")

if __name__ == "__main__":
    main()
