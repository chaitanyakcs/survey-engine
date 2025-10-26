"""
Golden Content Usage Tracking Service
Handles tracking which surveys use which golden questions and sections
"""

import logging
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


class GoldenContentTrackingService:
    """Service for tracking usage of golden questions and sections in surveys"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    async def track_question_usage(
        self,
        survey_id: UUID,
        question_ids: List[UUID]
    ) -> None:
        """
        Track usage of golden questions in a survey.
        Updates usage_count and records in golden_question_usage table.
        
        Args:
            survey_id: UUID of the survey
            question_ids: List of golden question UUIDs used
        """
        if not question_ids:
            logger.info("No golden questions to track")
            return
        
        try:
            logger.info(f"📊 Tracking {len(question_ids)} golden questions for survey {survey_id}")
            
            for question_id in question_ids:
                # Insert usage record (ON CONFLICT DO NOTHING for idempotency)
                self.db.execute(
                    text("""
                        INSERT INTO golden_question_usage (golden_question_id, survey_id, used_at)
                        VALUES (:question_id, :survey_id, NOW())
                        ON CONFLICT (golden_question_id, survey_id) DO NOTHING
                    """),
                    {"question_id": question_id, "survey_id": survey_id}
                )
                
                # Increment usage count
                self.db.execute(
                    text("""
                        UPDATE golden_questions 
                        SET usage_count = usage_count + 1 
                        WHERE id = :question_id
                    """),
                    {"question_id": question_id}
                )
            
            self.db.commit()
            logger.info(f"✅ Successfully tracked {len(question_ids)} golden questions")
            
        except Exception as e:
            logger.error(f"❌ Failed to track golden question usage: {str(e)}")
            self.db.rollback()
            # Don't raise - tracking failure shouldn't break survey generation
    
    async def track_section_usage(
        self,
        survey_id: UUID,
        section_ids: List[UUID]
    ) -> None:
        """
        Track usage of golden sections in a survey.
        Updates usage_count and records in golden_section_usage table.
        
        Args:
            survey_id: UUID of the survey
            section_ids: List of golden section UUIDs used
        """
        if not section_ids:
            logger.info("No golden sections to track")
            return
        
        try:
            logger.info(f"📊 Tracking {len(section_ids)} golden sections for survey {survey_id}")
            
            for section_id in section_ids:
                # Insert usage record (ON CONFLICT DO NOTHING for idempotency)
                self.db.execute(
                    text("""
                        INSERT INTO golden_section_usage (golden_section_id, survey_id, used_at)
                        VALUES (:section_id, :survey_id, NOW())
                        ON CONFLICT (golden_section_id, survey_id) DO NOTHING
                    """),
                    {"section_id": section_id, "survey_id": survey_id}
                )
                
                # Increment usage count
                self.db.execute(
                    text("""
                        UPDATE golden_sections 
                        SET usage_count = usage_count + 1 
                        WHERE id = :section_id
                    """),
                    {"section_id": section_id}
                )
            
            self.db.commit()
            logger.info(f"✅ Successfully tracked {len(section_ids)} golden sections")
            
        except Exception as e:
            logger.error(f"❌ Failed to track golden section usage: {str(e)}")
            self.db.rollback()
            # Don't raise - tracking failure shouldn't break survey generation
    
    async def track_golden_content_usage(
        self,
        survey_id: UUID,
        question_ids: Optional[List[UUID]] = None,
        section_ids: Optional[List[UUID]] = None
    ) -> None:
        """
        Track usage of both questions and sections in a single call.
        
        Args:
            survey_id: UUID of the survey
            question_ids: List of golden question UUIDs used
            section_ids: List of golden section UUIDs used
        """
        try:
            if question_ids:
                await self.track_question_usage(survey_id, question_ids)
            
            if section_ids:
                await self.track_section_usage(survey_id, section_ids)
            
            logger.info(f"✅ Completed tracking for survey {survey_id}")
            
        except Exception as e:
            logger.error(f"❌ Error in track_golden_content_usage: {str(e)}")
            # Don't raise - non-critical operation

