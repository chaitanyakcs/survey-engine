#!/usr/bin/env python3
"""
Script to fix missing annotations for golden examples that have comments but no annotations.
This processes the specific golden example: 7ec7162c-fc33-4b2a-9655-8d8a16973b7d
"""

import sys
import os
sys.path.append('src')

from database.connection import get_db
from database.models import GoldenRFQSurveyPair, QuestionAnnotation
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_missing_annotations(golden_example_id: str):
    """Fix missing annotations for a specific golden example"""
    
    # Get database session
    db = next(get_db())
    
    try:
        # Find the golden example
        golden_example = db.query(GoldenRFQSurveyPair).filter(
            GoldenRFQSurveyPair.id == golden_example_id
        ).first()
        
        if not golden_example:
            logger.error(f"Golden example {golden_example_id} not found")
            return False
            
        logger.info(f"Found golden example: {golden_example.id}")
        
        # Check if it has comment metadata
        if not golden_example.survey_json or 'comment_metadata' not in golden_example.survey_json:
            logger.warning(f"No comment metadata found for golden example {golden_example_id}")
            return False
            
        comment_metadata = golden_example.survey_json['comment_metadata']
        logger.info(f"Comment metadata: {comment_metadata['total_comments']} comments found")
        
        # Get questions from final_output
        if 'final_output' not in golden_example.survey_json or 'questions' not in golden_example.survey_json['final_output']:
            logger.error("No questions found in final_output")
            return False
            
        questions = golden_example.survey_json['final_output']['questions']
        logger.info(f"Found {len(questions)} questions to process")
        
        # Get survey_id
        survey_id = golden_example.survey_json.get('survey_id', golden_example_id)
        logger.info(f"Using survey_id: {survey_id}")
        
        # Check if annotations already exist
        existing_annotations = db.query(QuestionAnnotation).filter(
            QuestionAnnotation.survey_id == survey_id
        ).count()
        
        if existing_annotations > 0:
            logger.warning(f"Found {existing_annotations} existing annotations. Skipping to avoid duplicates.")
            return True
            
        # No need for DocumentParser - we'll create annotations directly
        
        # Process questions and create annotations
        annotations_created = 0
        
        for i, question in enumerate(questions):
            question_id = question.get("id", f"q_{i+1}")
            
            # Check if this question has an annotation field
            if "annotation" in question and isinstance(question["annotation"], dict):
                annotation_data = question["annotation"]
                
                # Extract annotation details
                comment_text = annotation_data.get("comment", "")
                anchored_text = annotation_data.get("anchored_text", "")
                author = annotation_data.get("author", "docx_parser")
                date = annotation_data.get("date", "")
                
                if comment_text:  # Only create annotation if there's actual comment text
                    # Create advanced_labels with full context
                    advanced_labels = {
                        "comment_text": comment_text,
                        "anchored_text": anchored_text,
                        "comment_author": author,
                        "comment_date": date,
                        "matching_method": "llm_with_anchored_text",
                        "matching_confidence": 1.0
                    }
                    
                    # Create annotation with full context
                    annotation = QuestionAnnotation(
                        question_id=question_id,
                        survey_id=survey_id,
                        
                        # Store comment text in the comment field (primary) and labels field (backup)
                        comment=comment_text,
                        labels=[comment_text],
                        
                        # Store full context in advanced_labels
                        advanced_labels=advanced_labels,
                        
                        # Use comment author as annotator_id
                        annotator_id=author,
                        
                        # Default values for required fields
                        required=True,
                        quality=3,
                        relevant=3,
                        methodological_rigor=3,
                        content_validity=3,
                        respondent_experience=3,
                        analytical_value=3,
                        business_impact=3,
                        
                        # Mark as AI-generated from DOCX parsing
                        ai_generated=True,
                        ai_confidence=1.0,
                        generation_timestamp=datetime.now()
                    )
                    
                    db.add(annotation)
                    annotations_created += 1
                    logger.info(f"Created annotation for question {question_id}: '{comment_text[:50]}...'")
                else:
                    logger.debug(f"Question {question_id} has annotation field but no comment text")
            else:
                logger.debug(f"Question {question_id} has no annotation field")
        
        # Commit all annotations
        db.commit()
        logger.info(f"✅ Successfully created {annotations_created} annotations for golden example {golden_example_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error processing golden example {golden_example_id}: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    golden_example_id = "7ec7162c-fc33-4b2a-9655-8d8a16973b7d"
    success = fix_missing_annotations(golden_example_id)
    
    if success:
        print(f"✅ Successfully fixed annotations for golden example {golden_example_id}")
    else:
        print(f"❌ Failed to fix annotations for golden example {golden_example_id}")
        sys.exit(1)
