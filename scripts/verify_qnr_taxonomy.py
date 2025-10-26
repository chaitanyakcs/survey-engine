#!/usr/bin/env python
"""Verify QNR Taxonomy Database Setup"""

from src.database.connection import SessionLocal
from sqlalchemy import text

def verify_qnr_taxonomy():
    db = SessionLocal()
    
    try:
        print("🔍 Verifying QNR Taxonomy Database Setup\n")
        
        # Check QNR tables
        expected_tables = ['qnr_sections', 'qnr_labels', 'qnr_label_history']
        
        print("📋 Checking QNR tables:")
        for table in expected_tables:
            result = db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            print(f"  ✅ {table}: {result} rows")
        
        # Check qnr_sections data
        print("\n📋 QNR Sections:")
        sections = db.execute(text("SELECT id, name, mandatory FROM qnr_sections ORDER BY id")).fetchall()
        for section in sections:
            mandatory_icon = "🟢" if section[2] else "⚪"
            print(f"  {mandatory_icon} Section {section[0]}: {section[1]}")
        
        # Check qnr_labels data
        print("\n📋 QNR Labels by category:")
        labels_by_category = db.execute(text("""
            SELECT category, COUNT(*) as count, 
                   COUNT(*) FILTER (WHERE mandatory = true) as mandatory_count
            FROM qnr_labels 
            GROUP BY category 
            ORDER BY category
        """)).fetchall()
        
        for row in labels_by_category:
            category, total, mandatory = row
            print(f"  {category}: {total} total ({mandatory} mandatory)")
        
        # Check indexes
        print("\n🔍 Checking indexes on qnr_labels:")
        indexes = db.execute(text("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'qnr_labels'
            ORDER BY indexname
        """)).fetchall()
        
        for idx in indexes:
            print(f"  ✅ {idx[0]}")
        
        # Check golden_questions section_id
        print("\n🔍 Checking golden_questions:")
        result = db.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(section_id) as with_section_id
            FROM golden_questions
        """)).fetchone()
        
        total, with_section = result
        print(f"  Total golden_questions: {total}")
        print(f"  With section_id: {with_section}")
        
        # Check indexes on golden_questions
        gq_indexes = db.execute(text("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'golden_questions' 
            AND (indexname LIKE '%section%' OR indexname = 'golden_questions_pkey')
            ORDER BY indexname
        """)).fetchall()
        
        print(f"\n🔍 Section-related indexes on golden_questions:")
        if gq_indexes:
            for idx in gq_indexes:
                print(f"  ✅ {idx[0]}")
        else:
            print("  ⚠️  No section indexes found")
        
        # Check old tables (should be removed)
        print("\n⚠️  Checking for old QNR tables (should be removed):")
        old_tables = ['qnr_label_definitions', 'qnr_tag_definitions']
        for table in old_tables:
            result = db.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                )
            """), (table,)).scalar()
            
            if result:
                count = db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                print(f"  ⚠️  {table}: {count} rows (should be dropped)")
        
        print("\n✅ QNR Taxonomy verification complete!")
        
    finally:
        db.close()

if __name__ == "__main__":
    verify_qnr_taxonomy()

