#!/usr/bin/env python3
"""
Script to run single call evaluation for a specific survey
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.database.connection import get_db, SessionLocal
from src.services.evaluator_service import EvaluatorService
from src.services.ai_annotation_service import AIAnnotationService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_evaluation(survey_id: str):
    """Run single call evaluation for a survey"""
    
    logger.info(f"🚀 Starting single call evaluation for survey: {survey_id}")
    
    try:
        db = SessionLocal()
        try:
            # Initialize evaluator service
            evaluator_service = EvaluatorService(db_session=db)
            
            # Run single call evaluation
            logger.info("📊 Running single call evaluation...")
            evaluation_result = await evaluator_service.evaluate_survey_single_call(survey_id)
            
            if evaluation_result:
                logger.info("✅ Evaluation completed successfully")
                
                # Create AI annotations from evaluation result
                logger.info("🤖 Creating AI annotations...")
                ai_service = AIAnnotationService(db)
                annotation_result = await ai_service.create_annotations_from_evaluation(
                    evaluation_result, 
                    survey_id, 
                    "ai_system"
                )
                
                logger.info(f"✅ Created {annotation_result.get('question_annotations_created', 0)} question annotations")
                logger.info(f"✅ Created {annotation_result.get('section_annotations_created', 0)} section annotations")
                
                # Commit changes
                db.commit()
                logger.info("💾 Changes committed to database")
                
            else:
                logger.error("❌ Evaluation failed - no result returned")
                
        finally:
            db.close()
                
    except Exception as e:
        logger.error(f"❌ Error during evaluation: {str(e)}")
        raise

def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python run_single_call_evaluation.py <survey_id>")
        sys.exit(1)
    
    survey_id = sys.argv[1]
    
    # Run the evaluation
    asyncio.run(run_evaluation(survey_id))

if __name__ == "__main__":
    main()
