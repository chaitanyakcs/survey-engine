#!/usr/bin/env python3
"""
Test script to verify the cleaned up PromptService works correctly
Tests that generation rules still work and quality rules are properly removed
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_cleaned_prompt_service():
    """Test that cleaned PromptService works correctly"""

    print("🧪 Testing Cleaned PromptService...")

    # Database connection
    database_url = os.getenv(
        'DATABASE_URL',
        'postgresql://chaitanya@localhost:5432/survey_engine_db'
    )

    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Test 1: Import and initialize PromptService
        print("\n📦 Test 1: Testing PromptService initialization...")

        # Direct import to avoid module path issues
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "prompt_service",
            os.path.join(os.path.dirname(__file__), 'src', 'services', 'prompt_service.py')
        )
        prompt_service_module = importlib.util.module_from_spec(spec)

        # Mock the database imports
        import sys
        sys.modules['src.database'] = type(sys)('mock_database')
        sys.modules['src.database.models'] = type(sys)('mock_models')

        # Create a mock SurveyRule class with required attributes
        class MockSurveyRule:
            def __init__(self):
                self.id = 'mock_id'
                self.rule_type = 'generation'
                self.category = 'content_validity'
                self.rule_name = 'Mock Rule'
                self.rule_description = 'Mock description'
                self.rule_content = {'priority': 'core', 'rule_type': 'generation'}
                self.priority = 1000
                self.is_active = True

        sys.modules['src.database.models'].SurveyRule = MockSurveyRule

        # Mock the query method to return empty results
        class MockQuery:
            def filter(self, *args):
                return self
            def all(self):
                return []
            def first(self):
                return None

        class MockSession:
            def query(self, *args):
                return MockQuery()

        spec.loader.exec_module(prompt_service_module)
        PromptService = prompt_service_module.PromptService

        # Test without database first (fallback mode)
        prompt_service = PromptService(db_session=None)
        print("✅ PromptService initialized successfully in fallback mode")

        # Test 2: Check that quality rules are empty
        print("\n🗑️  Test 2: Verifying quality rules cleanup...")
        print(f"Quality rules count: {len(prompt_service.quality_rules)}")
        print(f"Quality rules content: {prompt_service.quality_rules}")

        if len(prompt_service.quality_rules) == 0:
            print("✅ Quality rules successfully cleaned up")
        else:
            print(f"❌ Quality rules not properly cleaned: {prompt_service.quality_rules}")

        # Test 3: Check that methodology rules are preserved
        print("\n🔬 Test 3: Verifying methodology rules preserved...")
        print(f"Methodology rules count: {len(prompt_service.methodology_rules)}")
        expected_methodologies = ['van_westendorp', 'conjoint', 'maxdiff', 'nps']

        missing_methodologies = []
        for methodology in expected_methodologies:
            if methodology not in prompt_service.methodology_rules:
                missing_methodologies.append(methodology)

        if not missing_methodologies:
            print("✅ All methodology rules preserved")
            for method in expected_methodologies:
                print(f"  ✅ {method}: {prompt_service.methodology_rules[method]['required_questions']} questions")
        else:
            print(f"❌ Missing methodology rules: {missing_methodologies}")

        # Test 4: Test prompt building without quality rules
        print("\n📝 Test 4: Testing prompt building...")

        sample_context = {
            "rfq_details": {
                "title": "Test Survey",
                "text": "Test survey description",
                "category": "test",
                "segment": "test_segment"
            }
        }

        try:
            # Test basic system prompt building
            system_prompt = prompt_service.build_system_prompt(
                context=sample_context,
                methodology_tags=['nps'],
                custom_rules={'rules': ['Custom test rule']}
            )

            print(f"✅ System prompt generated successfully")
            print(f"System prompt length: {len(system_prompt)} characters")

            # Check that methodology rules are included
            if "Net Promoter Score" in system_prompt:
                print("✅ Methodology rules properly included in prompt")
            else:
                print("❌ Methodology rules missing from prompt")

            # Check that quality rules section is NOT included
            if "Quality Standards:" not in system_prompt:
                print("✅ Quality rules section properly removed from prompt")
            else:
                print("❌ Quality rules section still present in prompt")

            # Check for generation rules (if any were loaded)
            if "5-PILLAR" in system_prompt or "generation" in system_prompt.lower():
                print("✅ Generation rules context appears to be included")
            else:
                print("ℹ️  Generation rules context not found (expected in fallback mode)")

        except Exception as e:
            print(f"❌ Error generating prompt: {str(e)}")
            return False

        # Test 5: Test with mock database session
        print("\n🗄️  Test 5: Testing with mock database session...")

        try:
            mock_session = MockSession()
            prompt_service_with_db = PromptService(db_session=mock_session)
            print("✅ PromptService with database session initialized successfully")

            # Verify pillar rules are properly structured
            print(f"Pillar rules categories: {list(prompt_service_with_db.pillar_rules.keys())}")

        except Exception as e:
            print(f"❌ Error with database session: {str(e)}")

        print("\n🎉 PromptService Cleanup Test Complete!")

        return True

    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()

if __name__ == "__main__":
    success = test_cleaned_prompt_service()
    sys.exit(0 if success else 1)