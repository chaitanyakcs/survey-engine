#!/usr/bin/env python3
"""
Test script to verify the rules system is working
"""
import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all our new modules can be imported"""
    try:
        from src.database.models import SurveyRule, RuleValidation
        print("✅ Database models imported successfully")
        
        from src.services.prompt_service import PromptService
        print("✅ PromptService imported successfully")
        
        from src.api.rules import router as rules_router
        print("✅ Rules API router imported successfully")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_database_connection():
    """Test database connection and table existence"""
    try:
        from src.database import get_db, SurveyRule
        from sqlalchemy.orm import Session
        
        db = next(get_db())
        
        # Test if we can query the survey_rules table
        rules_count = db.query(SurveyRule).count()
        print(f"✅ Database connection successful - found {rules_count} rules")
        
        # Show some example rules
        if rules_count > 0:
            print("📋 Sample rules:")
            sample_rules = db.query(SurveyRule).limit(3).all()
            for rule in sample_rules:
                print(f"  • {rule.rule_type}/{rule.category}: {rule.rule_name}")
        
        db.close()
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_prompt_service():
    """Test the prompt service functionality"""
    try:
        from src.services.prompt_service import PromptService
        
        prompt_service = PromptService()
        
        # Test building a system prompt
        context = {
            "rfq_details": {
                "title": "Test RFQ",
                "text": "Test description",
                "category": "general",
                "segment": "general",
                "goal": "market_research"
            }
        }
        
        system_prompt = prompt_service.build_system_prompt(
            context=context,
            methodology_tags=["van_westendorp"],
            custom_rules={"rules": ["Test custom rule"]}
        )
        
        print("✅ PromptService working - generated system prompt")
        print(f"📝 System prompt length: {len(system_prompt)} characters")
        
        return True
    except Exception as e:
        print(f"❌ PromptService test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Survey Engine Rules System")
    print("=" * 40)
    
    tests = [
        ("Import Test", test_imports),
        ("Database Test", test_database_connection),
        ("Prompt Service Test", test_prompt_service),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Rules system is ready.")
        return True
    else:
        print("❌ Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)







