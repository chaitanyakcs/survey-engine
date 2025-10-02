#!/usr/bin/env python3
"""
Script to fix the RFQ parsing model in the database
"""

import os
import sys
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add src to path
sys.path.append('src')

def fix_rfq_model():
    """Update the RFQ parsing model in the database"""
    
    # Get database URL from environment or use default
    database_url = os.getenv('DATABASE_URL', 'postgresql://chaitanya@localhost:5432/survey_engine_db')
    
    # Check if we're running in Railway environment
    if os.getenv('RAILWAY_ENVIRONMENT'):
        print("🚂 Running in Railway environment")
    else:
        print("💻 Running in local environment")
    
    print(f"🔧 Connecting to database: {database_url}")
    
    try:
        # Create engine and session
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check current RFQ parsing settings
        result = session.execute(text("""
            SELECT setting_key, setting_value 
            FROM settings 
            WHERE setting_key = 'rfq_parsing_settings' AND is_active = true
        """)).fetchone()
        
        if result:
            print(f"📋 Current RFQ parsing settings: {result[1]}")
            
            # Update the model to the correct one
            new_settings = {
                "parsing_model": "openai/gpt-5"
            }
            
            # Update the setting
            session.execute(text("""
                UPDATE settings 
                SET setting_value = :new_value 
                WHERE setting_key = 'rfq_parsing_settings' AND is_active = true
            """), {"new_value": json.dumps(new_settings)})
            
            session.commit()
            print(f"✅ Updated RFQ parsing settings to: {new_settings}")
            
        else:
            print("📋 No RFQ parsing settings found, creating new ones...")
            
            # Insert new setting
            session.execute(text("""
                INSERT INTO settings (setting_key, setting_value, description, is_active)
                VALUES ('rfq_parsing_settings', :value, 'RFQ parsing configuration', true)
            """), {"value": json.dumps({"parsing_model": "openai/gpt-5"})})
            
            session.commit()
            print("✅ Created new RFQ parsing settings with model: openai/gpt-5")
        
        # Verify the update
        result = session.execute(text("""
            SELECT setting_key, setting_value 
            FROM settings 
            WHERE setting_key = 'rfq_parsing_settings' AND is_active = true
        """)).fetchone()
        
        print(f"🔍 Verified settings: {result[1]}")
        
        session.close()
        print("🎉 Database update completed successfully!")
        
    except Exception as e:
        print(f"❌ Error updating database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    fix_rfq_model()
