"""
Database migration to add labels column to annotation tables
Adds basic labels functionality to question, section, and survey annotations
"""

import sys
import os
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

def add_labels_columns(database_url: str):
    """Add labels column to existing annotation tables"""

    # Create database connection
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print("🚀 Starting labels migration...")

        # Check if labels column already exists
        print("🔍 Checking for existing labels columns...")

        check_columns_sql = text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name IN ('question_annotations', 'section_annotations', 'survey_annotations')
            AND column_name = 'labels'
        """)

        existing_columns = session.execute(check_columns_sql).fetchall()

        if existing_columns:
            print(f"⚠️  Found existing labels columns: {[col[0] for col in existing_columns]}")
            print("Migration may have already been applied.")
            return

        # Add labels column to question_annotations table
        print("📝 Adding labels column to question_annotations...")
        try:
            session.execute(text("""
                ALTER TABLE question_annotations
                ADD COLUMN labels JSONB
            """))
            print("  ✅ Added labels column to question_annotations")
        except Exception as e:
            print(f"  ⚠️  question_annotations labels column: {e}")

        # Add labels column to section_annotations table
        print("📝 Adding labels column to section_annotations...")
        try:
            session.execute(text("""
                ALTER TABLE section_annotations
                ADD COLUMN labels JSONB
            """))
            print("  ✅ Added labels column to section_annotations")
        except Exception as e:
            print(f"  ⚠️  section_annotations labels column: {e}")

        # Add labels column to survey_annotations table
        print("📝 Adding labels column to survey_annotations...")
        try:
            session.execute(text("""
                ALTER TABLE survey_annotations
                ADD COLUMN labels JSONB
            """))
            print("  ✅ Added labels column to survey_annotations")
        except Exception as e:
            print(f"  ⚠️  survey_annotations labels column: {e}")

        # Create performance indexes for labels
        print("📊 Creating performance indexes for labels...")

        try:
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_qa_labels
                ON question_annotations USING GIN(labels)
            """))
            print("  ✅ Created GIN index on question_annotations.labels")
        except Exception as e:
            print(f"  ⚠️  question_annotations labels index: {e}")

        try:
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_sa_labels
                ON section_annotations USING GIN(labels)
            """))
            print("  ✅ Created GIN index on section_annotations.labels")
        except Exception as e:
            print(f"  ⚠️  section_annotations labels index: {e}")

        try:
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_surv_labels
                ON survey_annotations USING GIN(labels)
            """))
            print("  ✅ Created GIN index on survey_annotations.labels")
        except Exception as e:
            print(f"  ⚠️  survey_annotations labels index: {e}")

        # Commit all changes
        session.commit()

        print("✅ Successfully added labels columns to annotation tables!")

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
            AND column_name = 'labels'
            ORDER BY table_name, column_name
        """)

        validation_results = session.execute(validation_sql).fetchall()

        print(f"\n📊 Migration validation - Found {len(validation_results)} labels columns:")
        for table, column, data_type, nullable in validation_results:
            print(f"  {table}.{column}: {data_type} (nullable: {nullable})")

        # Check indexes
        index_validation_sql = text("""
            SELECT indexname, tablename
            FROM pg_indexes
            WHERE tablename IN ('question_annotations', 'section_annotations', 'survey_annotations')
            AND indexname LIKE 'idx_%_labels'
            ORDER BY tablename, indexname
        """)

        index_results = session.execute(index_validation_sql).fetchall()

        print(f"\n📊 Index validation - Found {len(index_results)} labels indexes:")
        for index_name, table_name in index_results:
            print(f"  {table_name}.{index_name}")

        if len(validation_results) == 3:  # Expected 3 tables
            print("\n🎯 Migration validation passed!")
        else:
            print(f"\n❌ Migration validation failed: Expected 3 labels columns, found {len(validation_results)}")

    except Exception as e:
        print(f"❌ Error during labels migration: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()

def rollback_labels_columns(database_url: str):
    """Rollback labels columns (for development/testing)"""

    # Create database connection
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print("🔄 Rolling back labels migration...")

        # Drop indexes first
        print("🗑️  Dropping labels indexes...")
        indexes_to_drop = [
            "idx_qa_labels", "idx_sa_labels", "idx_surv_labels"
        ]

        for index_name in indexes_to_drop:
            try:
                session.execute(text(f"DROP INDEX IF EXISTS {index_name}"))
                print(f"  ✅ Dropped index {index_name}")
            except Exception as e:
                print(f"  ⚠️  Error dropping {index_name}: {e}")

        # Drop columns from all annotation tables
        print("🗑️  Dropping labels columns...")
        tables = ["question_annotations", "section_annotations", "survey_annotations"]

        for table_name in tables:
            try:
                session.execute(text(f"ALTER TABLE {table_name} DROP COLUMN IF EXISTS labels"))
                print(f"  ✅ Dropped labels column from {table_name}")
            except Exception as e:
                print(f"  ⚠️  Error dropping labels from {table_name}: {e}")

        # Commit rollback
        session.commit()
        print("✅ Labels migration rolled back successfully!")

    except Exception as e:
        print(f"❌ Error during rollback: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()

def main():
    """Main migration function"""
    import argparse

    parser = argparse.ArgumentParser(description="Labels migration for annotation tables")
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
            rollback_labels_columns(database_url)
            print("\n🔄 Labels rollback completed successfully!")
        else:
            add_labels_columns(database_url)
            print("\n🎉 Labels migration completed successfully!")
    except Exception as e:
        print(f"\n💥 Migration failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
