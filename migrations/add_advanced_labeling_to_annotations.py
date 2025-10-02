"""
Database migration to add advanced labeling fields to annotation tables
Extends existing annotation system with industry classification, methodology tags, and compliance tracking
"""

import sys
import os
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

def add_advanced_labeling_columns(database_url: str):
    """Add advanced labeling columns to existing annotation tables"""

    # Create database connection
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print("🚀 Starting advanced labeling migration...")

        # Check if columns already exist to avoid duplicate migrations
        print("🔍 Checking for existing advanced labeling columns...")

        check_columns_sql = text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'question_annotations'
            AND column_name IN ('advanced_labels', 'industry_classification', 'methodology_tags')
        """)

        existing_columns = session.execute(check_columns_sql).fetchall()

        if existing_columns:
            print(f"⚠️  Found existing advanced labeling columns: {[col[0] for col in existing_columns]}")
            print("Migration may have already been applied. Checking each table...")

        # Add columns to question_annotations table
        print("📝 Adding advanced labeling columns to question_annotations...")

        # Advanced labels storage (flexible JSONB)
        try:
            session.execute(text("""
                ALTER TABLE question_annotations
                ADD COLUMN IF NOT EXISTS advanced_labels JSONB
            """))
            print("  ✅ Added advanced_labels column")
        except Exception as e:
            print(f"  ⚠️  advanced_labels column: {e}")

        # Industry classification
        try:
            session.execute(text("""
                ALTER TABLE question_annotations
                ADD COLUMN IF NOT EXISTS industry_classification VARCHAR(100)
            """))
            print("  ✅ Added industry_classification column")
        except Exception as e:
            print(f"  ⚠️  industry_classification column: {e}")

        # Respondent type
        try:
            session.execute(text("""
                ALTER TABLE question_annotations
                ADD COLUMN IF NOT EXISTS respondent_type VARCHAR(100)
            """))
            print("  ✅ Added respondent_type column")
        except Exception as e:
            print(f"  ⚠️  respondent_type column: {e}")

        # Methodology tags (array of strings)
        try:
            session.execute(text("""
                ALTER TABLE question_annotations
                ADD COLUMN IF NOT EXISTS methodology_tags TEXT[]
            """))
            print("  ✅ Added methodology_tags column")
        except Exception as e:
            print(f"  ⚠️  methodology_tags column: {e}")

        # Mandatory flag
        try:
            session.execute(text("""
                ALTER TABLE question_annotations
                ADD COLUMN IF NOT EXISTS is_mandatory BOOLEAN DEFAULT FALSE
            """))
            print("  ✅ Added is_mandatory column")
        except Exception as e:
            print(f"  ⚠️  is_mandatory column: {e}")

        # Compliance status
        try:
            session.execute(text("""
                ALTER TABLE question_annotations
                ADD COLUMN IF NOT EXISTS compliance_status VARCHAR(50)
            """))
            print("  ✅ Added compliance_status column")
        except Exception as e:
            print(f"  ⚠️  compliance_status column: {e}")

        # Add columns to section_annotations table
        print("📝 Adding advanced labeling columns to section_annotations...")

        try:
            session.execute(text("""
                ALTER TABLE section_annotations
                ADD COLUMN IF NOT EXISTS section_classification VARCHAR(100)
            """))
            print("  ✅ Added section_classification column")
        except Exception as e:
            print(f"  ⚠️  section_classification column: {e}")

        try:
            session.execute(text("""
                ALTER TABLE section_annotations
                ADD COLUMN IF NOT EXISTS mandatory_elements JSONB
            """))
            print("  ✅ Added mandatory_elements column")
        except Exception as e:
            print(f"  ⚠️  mandatory_elements column: {e}")

        try:
            session.execute(text("""
                ALTER TABLE section_annotations
                ADD COLUMN IF NOT EXISTS compliance_score INTEGER
            """))
            print("  ✅ Added compliance_score column")
        except Exception as e:
            print(f"  ⚠️  compliance_score column: {e}")

        # Add columns to survey_annotations table
        print("📝 Adding advanced labeling columns to survey_annotations...")

        try:
            session.execute(text("""
                ALTER TABLE survey_annotations
                ADD COLUMN IF NOT EXISTS detected_labels JSONB
            """))
            print("  ✅ Added detected_labels column")
        except Exception as e:
            print(f"  ⚠️  detected_labels column: {e}")

        try:
            session.execute(text("""
                ALTER TABLE survey_annotations
                ADD COLUMN IF NOT EXISTS compliance_report JSONB
            """))
            print("  ✅ Added compliance_report column")
        except Exception as e:
            print(f"  ⚠️  compliance_report column: {e}")

        try:
            session.execute(text("""
                ALTER TABLE survey_annotations
                ADD COLUMN IF NOT EXISTS advanced_metadata JSONB
            """))
            print("  ✅ Added advanced_metadata column")
        except Exception as e:
            print(f"  ⚠️  advanced_metadata column: {e}")

        # Create performance indexes
        print("📊 Creating performance indexes for advanced labeling...")

        try:
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_qa_industry
                ON question_annotations(industry_classification)
            """))
            print("  ✅ Created index on industry_classification")
        except Exception as e:
            print(f"  ⚠️  industry_classification index: {e}")

        try:
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_qa_respondent
                ON question_annotations(respondent_type)
            """))
            print("  ✅ Created index on respondent_type")
        except Exception as e:
            print(f"  ⚠️  respondent_type index: {e}")

        try:
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_qa_methodology
                ON question_annotations USING GIN(methodology_tags)
            """))
            print("  ✅ Created GIN index on methodology_tags")
        except Exception as e:
            print(f"  ⚠️  methodology_tags index: {e}")

        try:
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_qa_mandatory
                ON question_annotations(is_mandatory)
            """))
            print("  ✅ Created index on is_mandatory")
        except Exception as e:
            print(f"  ⚠️  is_mandatory index: {e}")

        try:
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_qa_compliance
                ON question_annotations(compliance_status)
            """))
            print("  ✅ Created index on compliance_status")
        except Exception as e:
            print(f"  ⚠️  compliance_status index: {e}")

        # Commit all changes
        session.commit()

        print("✅ Successfully added advanced labeling columns to annotation tables!")

        # Validate the migration
        print("🔍 Validating migration...")

        validation_sql = text("""
            SELECT
                table_name,
                column_name,
                data_type,
                is_nullable
            FROM information_schema.columns
            WHERE table_name IN ('question_annotations', 'section_annotations', 'survey_annotations')
            AND column_name IN (
                'advanced_labels', 'industry_classification', 'respondent_type',
                'methodology_tags', 'is_mandatory', 'compliance_status',
                'section_classification', 'mandatory_elements', 'compliance_score',
                'detected_labels', 'compliance_report', 'advanced_metadata'
            )
            ORDER BY table_name, column_name
        """)

        validation_results = session.execute(validation_sql).fetchall()

        print(f"\n📊 Migration validation - Found {len(validation_results)} new columns:")
        for table, column, data_type, nullable in validation_results:
            print(f"  {table}.{column}: {data_type} (nullable: {nullable})")

        # Check indexes
        index_validation_sql = text("""
            SELECT indexname, tablename
            FROM pg_indexes
            WHERE tablename IN ('question_annotations', 'section_annotations', 'survey_annotations')
            AND indexname LIKE 'idx_qa_%'
            ORDER BY tablename, indexname
        """)

        index_results = session.execute(index_validation_sql).fetchall()

        print(f"\n📊 Index validation - Found {len(index_results)} advanced labeling indexes:")
        for index_name, table_name in index_results:
            print(f"  {table_name}.{index_name}")

        if len(validation_results) >= 12:  # Expected minimum columns added
            print("\n🎯 Migration validation passed!")
        else:
            print(f"\n❌ Migration validation failed: Expected at least 12 columns, found {len(validation_results)}")

    except Exception as e:
        print(f"❌ Error during advanced labeling migration: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()

def rollback_advanced_labeling_columns(database_url: str):
    """Rollback advanced labeling columns (for development/testing)"""

    # Create database connection
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print("🔄 Rolling back advanced labeling migration...")

        # Drop indexes first
        print("🗑️  Dropping advanced labeling indexes...")
        indexes_to_drop = [
            "idx_qa_industry", "idx_qa_respondent", "idx_qa_methodology",
            "idx_qa_mandatory", "idx_qa_compliance"
        ]

        for index_name in indexes_to_drop:
            try:
                session.execute(text(f"DROP INDEX IF EXISTS {index_name}"))
                print(f"  ✅ Dropped index {index_name}")
            except Exception as e:
                print(f"  ⚠️  Error dropping {index_name}: {e}")

        # Drop columns from question_annotations
        print("🗑️  Dropping columns from question_annotations...")
        qa_columns_to_drop = [
            "advanced_labels", "industry_classification", "respondent_type",
            "methodology_tags", "is_mandatory", "compliance_status"
        ]

        for column_name in qa_columns_to_drop:
            try:
                session.execute(text(f"ALTER TABLE question_annotations DROP COLUMN IF EXISTS {column_name}"))
                print(f"  ✅ Dropped column {column_name}")
            except Exception as e:
                print(f"  ⚠️  Error dropping {column_name}: {e}")

        # Drop columns from section_annotations
        print("🗑️  Dropping columns from section_annotations...")
        sa_columns_to_drop = [
            "section_classification", "mandatory_elements", "compliance_score"
        ]

        for column_name in sa_columns_to_drop:
            try:
                session.execute(text(f"ALTER TABLE section_annotations DROP COLUMN IF EXISTS {column_name}"))
                print(f"  ✅ Dropped column {column_name}")
            except Exception as e:
                print(f"  ⚠️  Error dropping {column_name}: {e}")

        # Drop columns from survey_annotations
        print("🗑️  Dropping columns from survey_annotations...")
        surv_columns_to_drop = [
            "detected_labels", "compliance_report", "advanced_metadata"
        ]

        for column_name in surv_columns_to_drop:
            try:
                session.execute(text(f"ALTER TABLE survey_annotations DROP COLUMN IF EXISTS {column_name}"))
                print(f"  ✅ Dropped column {column_name}")
            except Exception as e:
                print(f"  ⚠️  Error dropping {column_name}: {e}")

        # Commit rollback
        session.commit()
        print("✅ Advanced labeling migration rolled back successfully!")

    except Exception as e:
        print(f"❌ Error during rollback: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()

def main():
    """Main migration function"""
    import argparse

    parser = argparse.ArgumentParser(description="Advanced labeling migration for annotation tables")
    parser.add_argument("--rollback", action="store_true", help="Rollback the migration")
    parser.add_argument("--database-url", default=None, help="Database URL override")

    args = parser.parse_args()

    # Get database URL from environment or argument
    database_url = args.database_url or os.getenv(
        'DATABASE_URL',
        'postgresql://chaitanya@localhost:5432/survey_engine_db'
    )

    print(f"🗄️  Using database: {database_url.split('@')[1] if '@' in database_url else database_url}")

    try:
        if args.rollback:
            rollback_advanced_labeling_columns(database_url)
            print("\n🔄 Advanced labeling rollback completed successfully!")
        else:
            add_advanced_labeling_columns(database_url)
            print("\n🎉 Advanced labeling migration completed successfully!")
    except Exception as e:
        print(f"\n💥 Migration failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()