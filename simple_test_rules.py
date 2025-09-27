#!/usr/bin/env python3
"""
Simple test to verify generation rules are in database and working
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def test_generation_rules_database():
    """Test that generation rules are properly in database"""

    print("🧪 Testing Generation Rules in Database...")

    # Database connection
    database_url = os.getenv(
        'DATABASE_URL',
        'postgresql://chaitanya@localhost:5432/survey_engine_db'
    )

    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Test 1: Count generation rules
        print("\n📊 Test 1: Counting generation rules...")
        result = session.execute(text("""
            SELECT COUNT(*) as count
            FROM survey_rules
            WHERE rule_type = 'generation'
            AND is_active = true
        """)).fetchone()

        total_rules = result[0]
        print(f"Total generation rules: {total_rules}")

        if total_rules == 58:
            print("✅ All 58 generation rules found in database")
        else:
            print(f"❌ Expected 58 rules, found {total_rules}")

        # Test 2: Check rules by pillar
        print("\n🏛️  Test 2: Rules by pillar...")
        result = session.execute(text("""
            SELECT
                category,
                COUNT(*) as count,
                AVG(CAST(rule_content->>'weight' AS FLOAT)) * COUNT(*) as total_weight
            FROM survey_rules
            WHERE rule_type = 'generation'
            AND is_active = true
            GROUP BY category
            ORDER BY category
        """)).fetchall()

        expected_counts = {
            'content_validity': 11,
            'methodological_rigor': 15,
            'clarity_comprehensibility': 13,
            'structural_coherence': 12,
            'deployment_readiness': 7
        }

        all_correct = True
        for category, count, weight in result:
            expected = expected_counts.get(category, 0)
            status = "✅" if count == expected else "❌"
            print(f"  {status} {category}: {count} rules (expected: {expected}), weight: {weight:.3f}")
            if count != expected:
                all_correct = False

        # Test 3: Check rule content structure
        print("\n📋 Test 3: Sample rule content...")
        result = session.execute(text("""
            SELECT
                rule_name,
                rule_description,
                rule_content
            FROM survey_rules
            WHERE rule_type = 'generation'
            AND category = 'content_validity'
            AND is_active = true
            LIMIT 1
        """)).fetchone()

        if result:
            name, description, content = result
            print(f"Sample rule name: {name[:60]}...")
            print(f"Sample description: {description[:80]}...")

            # Check content structure (already parsed by SQLAlchemy JSONB)
            if isinstance(content, dict):
                parsed_content = content
                print("✅ Rule content is valid JSON")

                required_fields = ['generation_guideline', 'implementation_notes', 'quality_indicators', 'priority']
                for field in required_fields:
                    if field in parsed_content:
                        print(f"  ✅ {field}: present")
                    else:
                        print(f"  ❌ {field}: missing")
                        all_correct = False

            else:
                print(f"❌ Rule content is not a dict: {type(content)}")
                all_correct = False
        else:
            print("❌ No sample rule found")
            all_correct = False

        # Test 4: Check priority distribution
        print("\n📈 Test 4: Priority distribution...")
        result = session.execute(text("""
            SELECT
                rule_content->>'priority' as priority,
                COUNT(*) as count
            FROM survey_rules
            WHERE rule_type = 'generation'
            AND is_active = true
            GROUP BY rule_content->>'priority'
            ORDER BY count DESC
        """)).fetchall()

        for priority, count in result:
            print(f"  {priority}: {count} rules")

        # Test 5: Verify rules are active and queryable
        print("\n🔍 Test 5: Query test (like PromptService would do)...")
        result = session.execute(text("""
            SELECT
                id,
                category,
                rule_name,
                rule_description,
                rule_content->>'priority' as priority,
                rule_content->>'generation_guideline' as guideline
            FROM survey_rules
            WHERE rule_type = 'generation'
            AND is_active = true
            ORDER BY priority DESC
            LIMIT 5
        """)).fetchall()

        print("Top 5 generation rules (by priority):")
        for rule_id, category, name, description, priority, guideline in result:
            print(f"  🔸 [{priority.upper()}] {category}: {guideline[:60]}...")

        # Summary
        print(f"\n🎉 Database Test Complete!")

        if all_correct and total_rules == 58:
            print("✅ ALL TESTS PASSED - Generation rules are properly stored and structured!")
            print("\n📋 Next Steps:")
            print("  1. ✅ Generation rules are in database")
            print("  2. ⏳ Test PromptService integration")
            print("  3. ⏳ Test actual survey generation with rules")
            print("  4. ⏳ Verify rules appear in UI")
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
    success = test_generation_rules_database()
    exit(0 if success else 1)