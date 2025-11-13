"""
Version Service for managing survey versions
Handles version tracking, current version management, and version history
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from uuid import UUID
import logging

from src.database.models import Survey, RFQ

logger = logging.getLogger(__name__)


class VersionService:
    """Service for managing survey versions"""

    def __init__(self, db: Session):
        self.db = db

    def get_survey_versions(self, rfq_id: UUID) -> List[Survey]:
        """
        Get all versions for an RFQ, ordered by version number
        
        Args:
            rfq_id: The RFQ ID to get versions for
            
        Returns:
            List of Survey objects ordered by version number
        """
        return (
            self.db.query(Survey)
            .filter(Survey.rfq_id == rfq_id)
            .order_by(Survey.version.asc())
            .all()
        )

    def get_current_version(self, rfq_id: UUID) -> Optional[Survey]:
        """
        Get the current version for an RFQ
        
        Args:
            rfq_id: The RFQ ID
            
        Returns:
            Current Survey or None if no current version exists
        """
        return (
            self.db.query(Survey)
            .filter(Survey.rfq_id == rfq_id, Survey.is_current == True)
            .first()
        )

    def set_current_version(self, survey_id: UUID) -> Survey:
        """
        Mark a survey as the current version for its RFQ
        Automatically sets is_current=False for other versions of the same RFQ
        
        Args:
            survey_id: The survey ID to mark as current
            
        Returns:
            The updated Survey object
        """
        survey = self.db.query(Survey).filter(Survey.id == survey_id).first()
        if not survey:
            raise ValueError(f"Survey not found: {survey_id}")

        # Set all other versions of the same RFQ to is_current=False
        self.db.query(Survey).filter(
            Survey.rfq_id == survey.rfq_id,
            Survey.id != survey_id
        ).update({"is_current": False})

        # Set this survey as current
        survey.is_current = True
        self.db.commit()
        self.db.refresh(survey)

        logger.info(f"✅ [VersionService] Set survey {survey_id} as current version for RFQ {survey.rfq_id}")
        return survey

    def get_version_history(self, survey_id: UUID) -> List[Survey]:
        """
        Get version chain (parent → current → children) for a survey
        
        Args:
            survey_id: The survey ID to get history for
            
        Returns:
            List of Survey objects in version order (oldest to newest)
        """
        survey = self.db.query(Survey).filter(Survey.id == survey_id).first()
        if not survey:
            raise ValueError(f"Survey not found: {survey_id}")

        # Get all versions for the same RFQ
        return self.get_survey_versions(survey.rfq_id)

    def increment_version(self, rfq_id: UUID) -> int:
        """
        Get the next version number for an RFQ
        
        Args:
            rfq_id: The RFQ ID
            
        Returns:
            Next version number (1 if no versions exist)
        """
        max_version = (
            self.db.query(Survey)
            .filter(Survey.rfq_id == rfq_id)
            .order_by(desc(Survey.version))
            .first()
        )

        if max_version:
            return max_version.version + 1
        return 1

    def get_parent_survey(self, survey_id: UUID) -> Optional[Survey]:
        """
        Get the parent survey for a given survey
        
        Args:
            survey_id: The survey ID
            
        Returns:
            Parent Survey or None if this is v1
        """
        survey = self.db.query(Survey).filter(Survey.id == survey_id).first()
        if not survey:
            raise ValueError(f"Survey not found: {survey_id}")

        if survey.parent_survey_id:
            return self.db.query(Survey).filter(Survey.id == survey.parent_survey_id).first()
        return None

