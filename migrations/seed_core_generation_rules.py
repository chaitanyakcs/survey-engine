"""
Database migration to seed core generation rules
Populates SurveyRule table with 58 generation rules converted from AiRA v1 evaluation criteria
Organized by 5 quality pillars for seamless integration
"""

import sys
import os
import json
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add src to path for imports
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
sys.path.insert(0, src_path)

def seed_core_generation_rules(database_url: str):
    """Seed core generation rules into the database"""

    # Import after adding src to path
    try:
        from database.core_generation_rules import CORE_GENERATION_RULES
    except ImportError:
        # Alternative import approach
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "core_generation_rules",
            os.path.join(os.path.dirname(__file__), '..', 'src', 'database', 'core_generation_rules.py')
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        CORE_GENERATION_RULES = module.CORE_GENERATION_RULES

    # Create database connection
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print("🚀 Starting core generation rules seeding...")

        # Clear existing generation rules to avoid duplicates
        print("🧹 Clearing existing generation rules...")
        session.execute(text("""
            DELETE FROM survey_rules
            WHERE rule_type = 'generation'
            AND rule_content->>'source_framework' = 'aira_v1'
        """))

        # Insert all generation rules
        rules_inserted = 0

        for rule_data in CORE_GENERATION_RULES:
            # Prepare rule content
            rule_content = {
                "generation_guideline": rule_data["generation_guideline"],
                "implementation_notes": rule_data["implementation_notes"],
                "quality_indicators": rule_data["quality_indicators"],
                "source_framework": rule_data["source_framework"],
                "priority": rule_data["priority"],
                "weight": rule_data["weight"]
            }

            # Create rule name
            rule_name = f"Core Quality: {rule_data['generation_guideline'][:80]}..."
            if len(rule_data['generation_guideline']) <= 80:
                rule_name = f"Core Quality: {rule_data['generation_guideline']}"

            # Calculate priority value for database (higher number = higher priority)
            priority_values = {
                "core": 1000,
                "high": 800,
                "medium": 600,
                "low": 400
            }
            priority_value = priority_values.get(rule_data["priority"], 600)

            # Insert rule as SurveyRule
            insert_sql = text("""
                INSERT INTO survey_rules (
                    id,
                    rule_type,
                    category,
                    rule_name,
                    rule_description,
                    rule_content,
                    is_active,
                    priority,
                    created_at,
                    created_by
                ) VALUES (
                    gen_random_uuid(),
                    'generation',
                    :category,
                    :rule_name,
                    :rule_description,
                    :rule_content,
                    true,
                    :priority,
                    :created_at,
                    'core_generation_migration'
                )
            """)

            session.execute(insert_sql, {
                'category': rule_data['category'],
                'rule_name': rule_name,
                'rule_description': rule_data['generation_guideline'],
                'rule_content': json.dumps(rule_content),  # Convert dict to JSON string
                'priority': priority_value,
                'created_at': datetime.now()
            })

            rules_inserted += 1

            if rules_inserted % 10 == 0:
                print(f"  📝 Inserted {rules_inserted} generation rules...")

        # Commit all changes
        session.commit()

        print(f"✅ Successfully seeded {rules_inserted} core generation rules!")

        # Validate insertion
        validation_sql = text("""
            SELECT
                category,
                COUNT(*) as rule_count,
                AVG(CAST(rule_content->>'weight' AS FLOAT)) * COUNT(*) as total_pillar_weight
            FROM survey_rules
            WHERE rule_type = 'generation'
            AND rule_content->>'source_framework' = 'aira_v1'
            GROUP BY category
            ORDER BY category
        """)

        results = session.execute(validation_sql).fetchall()

        print("\n📊 Validation - Rules per pillar:")
        total_validated = 0
        total_weight = 0.0
        expected_weights = {
            'content_validity': 0.20,
            'methodological_rigor': 0.25,
            'clarity_comprehensibility': 0.25,
            'structural_coherence': 0.20,
            'deployment_readiness': 0.10
        }

        for category, count, pillar_weight in results:
            expected_weight = expected_weights.get(category, 0.0)
            weight_status = "✅" if abs(pillar_weight - expected_weight) < 0.01 else "❌"
            print(f"  {category}: {count} rules, weight: {pillar_weight:.3f} {weight_status}")
            total_validated += count
            total_weight += pillar_weight

        print(f"\n🎯 Total generation rules in database: {total_validated}")
        print(f"🎯 Total weight: {total_weight:.3f}")

        if total_validated == 58:
            print("✅ Validation passed: Exactly 58 rules as expected!")
        else:
            print(f"❌ Validation failed: Expected 58 rules, found {total_validated}")

        if abs(total_weight - 1.0) < 0.01:
            print("✅ Weight validation passed: Total weight ~1.000!")
        else:
            print(f"❌ Weight validation failed: Expected ~1.000, found {total_weight:.3f}")

        # Show priority distribution
        priority_sql = text("""
            SELECT
                rule_content->>'priority' as priority_level,
                COUNT(*) as count
            FROM survey_rules
            WHERE rule_type = 'generation'
            AND rule_content->>'source_framework' = 'aira_v1'
            GROUP BY rule_content->>'priority'
            ORDER BY count DESC
        """)

        priority_results = session.execute(priority_sql).fetchall()
        print("\n📈 Priority distribution:")
        for priority, count in priority_results:
            print(f"  {priority}: {count} rules")

    except Exception as e:
        print(f"❌ Error seeding core generation rules: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()

def main():
    """Main migration function"""
    # Get database URL from environment or default to local dev setup
    database_url = os.getenv(
        'DATABASE_URL',
        'postgresql://chaitanya@localhost:5432/survey_engine_db'  # Updated to port 5432
    )

    print(f"🗄️  Using database: {database_url.split('@')[1] if '@' in database_url else database_url}")

    try:
        seed_core_generation_rules(database_url)
        print("\n🎉 Core generation rules migration completed successfully!")
        print("\n📋 Next steps:")
        print("  1. Update PromptService to include generation rules")
        print("  2. Test generation with new quality rules")
        print("  3. Verify rules appear in existing UI")
    except Exception as e:
        print(f"\n💥 Migration failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()