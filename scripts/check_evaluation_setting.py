#!/usr/bin/env python3
"""
Script to check and update enable_llm_evaluation setting in production
"""
import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database.connection import get_db
from src.services.settings_service import SettingsService

def check_setting():
    """Check current evaluation setting"""
    db = next(get_db())
    try:
        settings_service = SettingsService(db)
        evaluation_settings = settings_service.get_evaluation_settings()
        
        enable_llm_evaluation = evaluation_settings.get('enable_llm_evaluation', True)
        
        print("=" * 60)
        print("Current Evaluation Settings")
        print("=" * 60)
        print(f"enable_llm_evaluation: {enable_llm_evaluation}")
        print(f"Type: {type(enable_llm_evaluation)}")
        print()
        print("Full settings:")
        print(json.dumps(evaluation_settings, indent=2))
        print()
        
        if enable_llm_evaluation:
            print("⚠️  Evaluation is ENABLED - evaluations will run automatically")
            print()
            print("To disable, run:")
            print("  python scripts/check_evaluation_setting.py --disable")
        else:
            print("✅ Evaluation is DISABLED - evaluations will not run")
        
        return enable_llm_evaluation
    finally:
        db.close()

def update_setting(disable: bool = False):
    """Update evaluation setting"""
    db = next(get_db())
    try:
        settings_service = SettingsService(db)
        current_settings = settings_service.get_evaluation_settings()
        
        # Update the setting
        current_settings['enable_llm_evaluation'] = not disable
        
        # Save back to database
        success = settings_service.update_evaluation_settings(current_settings)
        
        if success:
            new_value = current_settings['enable_llm_evaluation']
            print("=" * 60)
            print("Settings Updated Successfully")
            print("=" * 60)
            print(f"enable_llm_evaluation: {new_value}")
            if new_value:
                print("✅ Evaluation is now ENABLED")
            else:
                print("✅ Evaluation is now DISABLED")
        else:
            print("❌ Failed to update settings")
            return False
        
        return True
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Check or update enable_llm_evaluation setting')
    parser.add_argument('--disable', action='store_true', help='Disable LLM evaluation')
    parser.add_argument('--enable', action='store_true', help='Enable LLM evaluation')
    
    args = parser.parse_args()
    
    if args.disable:
        print("Disabling LLM evaluation...")
        update_setting(disable=True)
    elif args.enable:
        print("Enabling LLM evaluation...")
        update_setting(disable=False)
    else:
        check_setting()

