"""
Direct test of AnnotationRAGSyncService without web server
Tests the core sync functionality in isolation
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.database.connection import get_db
from src.services.annotation_rag_sync_service import AnnotationRAGSyncService
from src.database.models import (
    QuestionAnnotation,
    SectionAnnotation,
    GoldenQuestion,
    GoldenSection,
)


async def test_direct_sync():
    """Test annotation sync service directly"""
    print("\n" + "=" * 80)
    print("🧪 Testing Annotation RAG Sync Service (Direct)")
    print("=" * 80)
    
    db = next(get_db())
    
    try:
        # Test 1: Check for annotations
        print("\n📊 Test 1: Checking for existing annotations...")
        
        question_annotations = db.query(QuestionAnnotation).filter(
            QuestionAnnotation.annotator_id == "current-user"
        ).limit(3).all()
        
        section_annotations = db.query(SectionAnnotation).filter(
            SectionAnnotation.annotator_id == "current-user"
        ).limit(2).all()
        
        print(f"  ✓ Found {len(question_annotations)} question annotations to test")
        print(f"  ✓ Found {len(section_annotations)} section annotations to test")
        
        if not question_annotations and not section_annotations:
            print("\n⚠️ No annotations found to test with.")
            return
        
        # Test 2: Test question annotation sync
        if question_annotations:
            print("\n🔗 Test 2: Testing question annotation sync...")
            
            qa = question_annotations[0]
            print(f"  📝 Testing with question annotation ID: {qa.id}")
            print(f"     Survey ID: {qa.survey_id}, Question ID: {qa.question_id}")
            print(f"     Quality: {qa.quality}, Human Verified: {qa.human_verified}")
            
            sync_service = AnnotationRAGSyncService(db)
            result = await sync_service.sync_question_annotation(qa.id)
            
            print(f"  📊 Sync result: {result}")
            
            if result.get("success"):
                print(f"  ✅ Question sync successful: {result.get('action')}")
                
                # Verify the golden question exists
                golden_q = db.query(GoldenQuestion).filter(
                    GoldenQuestion.annotation_id == qa.id
                ).first()
                
                if golden_q:
                    print(f"  ✓ Verified golden question in database")
                    print(f"     ID: {golden_q.id}")
                    print(f"     Text: {golden_q.question_text[:100]}...")
                    print(f"     Quality Score: {golden_q.quality_score}")
                    print(f"     Type: {golden_q.question_type}")
                    print(f"     Human Verified: {golden_q.human_verified}")
                else:
                    print(f"  ❌ Golden question not found in database!")
            else:
                print(f"  ❌ Question sync failed: {result.get('error')}")
        
        # Test 3: Test section annotation sync
        if section_annotations:
            print("\n🔗 Test 3: Testing section annotation sync...")
            
            sa = section_annotations[0]
            print(f"  📝 Testing with section annotation ID: {sa.id}")
            print(f"     Survey ID: {sa.survey_id}, Section ID: {sa.section_id}")
            print(f"     Quality: {sa.quality}, Human Verified: {sa.human_verified}")
            
            sync_service = AnnotationRAGSyncService(db)
            result = await sync_service.sync_section_annotation(sa.id)
            
            print(f"  📊 Sync result: {result}")
            
            if result.get("success"):
                print(f"  ✅ Section sync successful: {result.get('action')}")
                
                # Verify the golden section exists
                golden_s = db.query(GoldenSection).filter(
                    GoldenSection.annotation_id == sa.id
                ).first()
                
                if golden_s:
                    print(f"  ✓ Verified golden section in database")
                    print(f"     ID: {golden_s.id}")
                    print(f"     Title: {golden_s.section_title}")
                    print(f"     Quality Score: {golden_s.quality_score}")
                    print(f"     Type: {golden_s.section_type}")
                    print(f"     Human Verified: {golden_s.human_verified}")
                else:
                    print(f"  ❌ Golden section not found in database!")
            else:
                print(f"  ❌ Section sync failed: {result.get('error')}")
        
        # Test 4: Check overall RAG data
        print("\n📊 Test 4: Checking overall RAG data...")
        
        total_golden_questions = db.query(GoldenQuestion).count()
        annotated_golden_questions = db.query(GoldenQuestion).filter(
            GoldenQuestion.annotation_id.isnot(None)
        ).count()
        
        total_golden_sections = db.query(GoldenSection).count()
        annotated_golden_sections = db.query(GoldenSection).filter(
            GoldenSection.annotation_id.isnot(None)
        ).count()
        
        print(f"  ✓ Total golden questions: {total_golden_questions}")
        print(f"    - From annotations: {annotated_golden_questions}")
        print(f"    - From golden pairs: {total_golden_questions - annotated_golden_questions}")
        
        print(f"  ✓ Total golden sections: {total_golden_sections}")
        print(f"    - From annotations: {annotated_golden_sections}")
        print(f"    - From golden pairs: {total_golden_sections - annotated_golden_sections}")
        
        print("\n" + "=" * 80)
        print("✅ Direct Annotation RAG Sync Test Complete!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_direct_sync())

