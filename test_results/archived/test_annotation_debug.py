#!/usr/bin/env python3
"""
Debug script to test annotation generation
"""

import asyncio
import json
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.connection import get_db
from services.ai_annotation_service import AIAnnotationService
from evaluations.modules.single_call_evaluator import SingleCallEvaluationResult

async def test_annotation_generation():
    """Test annotation generation with sample data"""
    
    # Get database session
    db = next(get_db())
    
    # Create sample evaluation result with annotations
    sample_result = SingleCallEvaluationResult(
        pillar_scores={
            "content_validity": 0.85,
            "methodological_rigor": 0.78,
            "clarity_comprehensibility": 0.82,
            "structural_coherence": 0.80,
            "deployment_readiness": 0.88
        },
        weighted_score=0.82,
        overall_grade="B+",
        detailed_analysis={},
        cross_pillar_insights=[],
        overall_recommendations=[],
        question_annotations=[
            {
                "question_id": "q1",
                "question_text": "What is your age group?",
                "content_validity": 4,
                "methodological_rigor": 5,
                "respondent_experience": 4,
                "analytical_value": 3,
                "business_impact": 4,
                "quality": 4,
                "relevant": 5,
                "ai_confidence": 0.85,
                "comment": "Clear demographic question with good response options"
            }
        ],
        section_annotations=[
            {
                "section_id": 1,
                "section_title": "Demographics",
                "content_validity": 4,
                "methodological_rigor": 5,
                "respondent_experience": 4,
                "analytical_value": 4,
                "business_impact": 4,
                "quality": 4,
                "relevant": 5,
                "ai_confidence": 0.88,
                "comment": "Good demographic section"
            }
        ],
        evaluation_metadata={},
        cost_savings={}
    )
    
    print(f"🔍 Testing annotation generation...")
    print(f"🔍 Question annotations count: {len(sample_result.question_annotations)}")
    print(f"🔍 Section annotations count: {len(sample_result.section_annotations)}")
    
    # Test AI annotation service
    ai_service = AIAnnotationService(db)
    
    try:
        result = await ai_service.create_annotations_from_evaluation(
            sample_result, 
            "test-survey-123", 
            "ai_system"
        )
        
        print(f"✅ Annotation generation result: {result}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_annotation_generation())
