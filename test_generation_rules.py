#!/usr/bin/env python3
"""
Test script to verify core generation rules integration
Tests that the rules are loaded and included in survey generation prompts
"""

import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_generation_rules_integration():
    """Test that generation rules are properly integrated"""

    print("🧪 Testing Generation Rules Integration...")

    # Database connection
    database_url = os.getenv(
        'DATABASE_URL',
        'postgresql://chaitanya@localhost:5432/survey_engine_db'
    )

    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Test 1: Import PromptService
        print("\n📦 Test 1: Importing PromptService...")
        try:
            # Direct import to avoid module path issues
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "prompt_service",
                os.path.join(os.path.dirname(__file__), 'src', 'services', 'prompt_service.py')
            )
            prompt_service_module = importlib.util.module_from_spec(spec)

            # Mock the database imports that cause issues
            import sys
            sys.modules['src.database'] = type(sys)('mock_database')
            sys.modules['src.database.models'] = type(sys)('mock_models')

            # Create a mock SurveyRule class
            class MockSurveyRule:
                def __init__(self):
                    pass
            sys.modules['src.database.models'].SurveyRule = MockSurveyRule

            spec.loader.exec_module(prompt_service_module)
            PromptService = prompt_service_module.PromptService

            # Initialize with database session
            prompt_service = PromptService(db_session=session)
            print("✅ PromptService imported and initialized successfully")
        except Exception as e:
            print(f"❌ Import failed: {e}")
            # Fallback to direct database test
            prompt_service = None

        # Test 2: Check that generation rules are loaded
        print("\n📊 Test 2: Checking generation rules are loaded...")
        print(f"Pillar rules loaded: {len(prompt_service.pillar_rules)} pillars")

        generation_rule_count = 0
        for pillar, rules in prompt_service.pillar_rules.items():
            gen_rules = [r for r in rules if r.get('rule_type') == 'generation']
            generation_rule_count += len(gen_rules)
            print(f"  {pillar}: {len(gen_rules)} generation rules")

        print(f"Total generation rules: {generation_rule_count}")
        if generation_rule_count == 58:
            print("✅ All 58 generation rules loaded successfully")
        else:
            print(f"❌ Expected 58 generation rules, found {generation_rule_count}")

        # Test 3: Check pillar rules context generation
        print("\n📝 Test 3: Testing pillar rules context generation...")
        context = prompt_service.get_pillar_rules_context()

        if context:
            print("✅ Pillar rules context generated successfully")
            print(f"Context length: {len(context)} characters")

            # Check that all pillars are included
            pillars_in_context = []
            for pillar in ['Content Validity', 'Methodological Rigor', 'Clarity & Comprehensibility', 'Structural Coherence', 'Deployment Readiness']:
                if pillar in context:
                    pillars_in_context.append(pillar)

            print(f"Pillars in context: {len(pillars_in_context)}/5")
            for pillar in pillars_in_context:
                print(f"  ✅ {pillar}")

            # Check for priority indicators
            priority_indicators = ['🔴', '🟡', '🔵']
            indicators_found = [indicator for indicator in priority_indicators if indicator in context]
            print(f"Priority indicators found: {indicators_found}")

        else:
            print("❌ No pillar rules context generated")

        # Test 4: Test prompt generation with rules
        print("\n🤖 Test 4: Testing prompt generation with rules...")

        sample_context = {
            "rfq_details": {
                "title": "Customer Satisfaction Survey",
                "text": "We need to understand customer satisfaction with our product",
                "category": "customer_feedback",
                "segment": "existing_customers",
                "goal": "measure_satisfaction"
            }
        }

        try:
            prompt = prompt_service.build_golden_enhanced_prompt(
                context=sample_context,
                golden_examples=[],
                methodology_blocks=[]
            )

            print("✅ Survey generation prompt created successfully")
            print(f"Prompt length: {len(prompt)} characters")

            # Check that generation rules are included
            if "5-PILLAR" in prompt and ("🔴" in prompt or "🟡" in prompt or "🔵" in prompt):
                print("✅ Generation rules appear to be included in prompt")
            else:
                print("❌ Generation rules may not be included in prompt")

            # Show a sample of the rules section
            if "## Content Validity" in prompt:
                start = prompt.find("## Content Validity")
                end = prompt.find("## Methodological Rigor", start)
                if end == -1:
                    end = start + 500
                sample = prompt[start:end]
                print("\n📋 Sample Content Validity rules in prompt:")
                print(sample[:300] + "..." if len(sample) > 300 else sample)

        except Exception as e:
            print(f"❌ Error generating prompt: {str(e)}")

        # Test 5: Database verification
        print("\n🗄️  Test 5: Direct database verification...")
        from sqlalchemy import text

        result = session.execute(text("""
            SELECT
                rule_type,
                category,
                COUNT(*) as count
            FROM survey_rules
            WHERE is_active = true
            GROUP BY rule_type, category
            ORDER BY rule_type, category
        """)).fetchall()

        print("Database rules summary:")
        generation_total = 0
        for rule_type, category, count in result:
            print(f"  {rule_type}.{category}: {count} rules")
            if rule_type == 'generation':
                generation_total += count

        print(f"\nTotal generation rules in database: {generation_total}")

        print("\n🎉 Generation Rules Integration Test Complete!")

        # Summary
        success_criteria = [
            generation_rule_count == 58,
            len(context) > 0,
            generation_total == 58,
            len(pillars_in_context) == 5
        ]

        if all(success_criteria):
            print("✅ ALL TESTS PASSED - Generation rules integration successful!")
            return True
        else:
            print("❌ Some tests failed - check output above")
            return False

    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()

if __name__ == "__main__":
    success = test_generation_rules_integration()
    sys.exit(0 if success else 1)