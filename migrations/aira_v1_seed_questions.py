"""
Database migration to seed AiRA v1 evaluation questions
Populates SurveyRule table with all 58 AiRA v1 evaluation criteria
"""

import sys
import os
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

def seed_aira_v1_questions(database_url: str):
    """Seed AiRA v1 evaluation questions into the database"""

    # Import after adding src to path
    from database.aira_v1_questions_full import AIRA_V1_COMPLETE_QUESTIONS
    from database.aira_rule_schema import get_aira_v1_rule_content

    # Create database connection
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print("🚀 Starting AiRA v1 evaluation questions seeding...")

        # Clear existing AiRA v1 pillar rules to avoid duplicates
        print("🧹 Clearing existing AiRA v1 pillar rules...")
        session.execute(text("""
            DELETE FROM survey_rules
            WHERE rule_type = 'pillar'
            AND rule_content->>'aira_version' = 'v1'
        """))

        # Insert all AiRA v1 questions
        questions_inserted = 0

        for question_data in AIRA_V1_COMPLETE_QUESTIONS:
            # Prepare rule content
            rule_content = get_aira_v1_rule_content(question_data)

            # Create pillar category (handle 'overall' pillar)
            pillar_category = question_data['pillar']
            if pillar_category == 'overall':
                pillar_category = 'summary_evaluation'

            # Create rule name
            rule_name = f"AiRA v1: {question_data['question_text'][:100]}..."
            if len(question_data['question_text']) <= 100:
                rule_name = f"AiRA v1: {question_data['question_text']}"

            # Insert question as SurveyRule
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
                    'pillar',
                    :category,
                    :rule_name,
                    :rule_description,
                    :rule_content,
                    true,
                    :priority,
                    :created_at,
                    'aira_v1_migration'
                )
            """)

            session.execute(insert_sql, {
                'category': pillar_category,
                'rule_name': rule_name,
                'rule_description': question_data['question_text'],
                'rule_content': rule_content,
                'priority': int(question_data['scoring_weight'] * 1000),  # Convert weight to priority
                'created_at': datetime.now()
            })

            questions_inserted += 1

            if questions_inserted % 10 == 0:
                print(f"  📝 Inserted {questions_inserted} questions...")

        # Commit all changes
        session.commit()

        print(f"✅ Successfully seeded {questions_inserted} AiRA v1 evaluation questions!")

        # Validate insertion
        validation_sql = text("""
            SELECT
                category,
                COUNT(*) as question_count
            FROM survey_rules
            WHERE rule_type = 'pillar'
            AND rule_content->>'aira_version' = 'v1'
            GROUP BY category
            ORDER BY category
        """)

        results = session.execute(validation_sql).fetchall()

        print("\n📊 Validation - Questions per pillar:")
        total_validated = 0
        for category, count in results:
            print(f"  {category}: {count} questions")
            total_validated += count

        print(f"\n🎯 Total AiRA v1 questions in database: {total_validated}")

        if total_validated == 58:
            print("✅ Validation passed: Exactly 58 questions as expected!")
        else:
            print(f"❌ Validation failed: Expected 58 questions, found {total_validated}")

    except Exception as e:
        print(f"❌ Error seeding AiRA v1 questions: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()

def main():
    """Main migration function"""
    # Get database URL from environment or default
    database_url = os.getenv(
        'DATABASE_URL',
        'postgresql://chaitanya@localhost:5432/survey_engine_db'
    )

    print(f"🗄️  Using database: {database_url.split('@')[1] if '@' in database_url else database_url}")

    try:
        seed_aira_v1_questions(database_url)
        print("\n🎉 AiRA v1 migration completed successfully!")
    except Exception as e:
        print(f"\n💥 Migration failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()