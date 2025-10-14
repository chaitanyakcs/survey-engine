#!/usr/bin/env python3
"""
Migration script to create survey records for existing golden pairs
This ensures all existing reference examples have proper survey records for annotation support
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database.connection import get_db
from src.database.models import GoldenRFQSurveyPair, Survey
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_existing_golden_pairs():
    """Create survey records for existing golden pairs that don't have them"""
    
    db = next(get_db())
    
    try:
        # Get all golden pairs
        golden_pairs = db.query(GoldenRFQSurveyPair).all()
        logger.info(f"Found {len(golden_pairs)} golden pairs to check")
        
        created_count = 0
        updated_count = 0
        
        for pair in golden_pairs:
            survey_id = pair.id  # Use the golden pair ID directly as UUID
            
            # Check if survey record already exists
            existing_survey = db.query(Survey).filter(Survey.id == survey_id).first()
            
            if existing_survey:
                logger.info(f"Survey record already exists for golden pair {pair.id}")
                # Update survey_json to include survey_id if not present
                if isinstance(pair.survey_json, dict) and "survey_id" not in pair.survey_json:
                    pair.survey_json["survey_id"] = str(survey_id)  # Convert UUID to string for JSON
                    updated_count += 1
                    logger.info(f"Updated survey_json for golden pair {pair.id}")
            else:
                # Create new survey record
                logger.info(f"Creating survey record for golden pair {pair.id}")
                
                # Ensure survey_json has survey_id
                survey_json = pair.survey_json.copy() if isinstance(pair.survey_json, dict) else {}
                survey_json["survey_id"] = str(survey_id)  # Convert UUID to string for JSON
                
                # Update the golden pair's survey_json
                pair.survey_json = survey_json
                
                # Create the survey record
                reference_survey = Survey(
                    id=survey_id,  # Use the golden pair ID directly as UUID
                    rfq_id=None,  # Reference examples don't have RFQ
                    status="reference",  # Special status for reference examples
                    raw_output=survey_json,
                    final_output=survey_json,
                    created_at=datetime.now()
                )
                
                db.add(reference_survey)
                created_count += 1
                logger.info(f"Created survey record {survey_id} for golden pair {pair.id}")
        
        # Step 5: Update survey status constraint to include 'reference'
        logger.info("📝 Updating survey status constraint to include 'reference' status...")
        try:
            # Read and execute the migration SQL file
            migration_file = "migrations/018_update_survey_status_constraint.sql"
            with open(migration_file, 'r') as f:
                migration_sql = f.read()
            
            db.execute(text(migration_sql))
            logger.info("✅ Survey status constraint updated successfully")
        except Exception as e:
            logger.error(f"❌ Failed to update survey status constraint: {str(e)}")
            db.rollback()
            raise
        
        # Commit all changes
        db.commit()
        logger.info(f"Migration completed successfully!")
        logger.info(f"Created {created_count} new survey records")
        logger.info(f"Updated {updated_count} existing golden pairs")
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_existing_golden_pairs()
