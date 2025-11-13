"""
Annotation Feedback Service
Collects annotation feedback from all previous versions of surveys for the same RFQ
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import Dict, List, Any, Optional
from uuid import UUID
import logging

from src.database.models import (
    QuestionAnnotation,
    SectionAnnotation,
    SurveyAnnotation,
    Survey
)
from src.services.version_service import VersionService

logger = logging.getLogger(__name__)


class AnnotationFeedbackService:
    """Service for collecting annotation feedback from all previous versions"""

    def __init__(self, db: Session):
        self.db = db
        self.version_service = VersionService(db)

    def collect_question_feedback(
        self,
        rfq_id: UUID,
        exclude_survey_ids: Optional[List[UUID]] = None,
        section_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Collect question-level comments from ALL previous versions of the RFQ
        
        Args:
            rfq_id: The RFQ ID to collect feedback for
            exclude_survey_ids: Optional list of survey IDs to exclude (e.g., current survey being regenerated)
            section_ids: Optional list of section IDs to filter by
            
        Returns:
            List of question feedback dictionaries with version information
        """
        # Get all surveys for this RFQ
        all_versions = self.version_service.get_survey_versions(rfq_id)
        survey_ids = [str(survey.id) for survey in all_versions]
        
        # Exclude specified survey IDs if provided
        if exclude_survey_ids:
            exclude_ids = [str(sid) for sid in exclude_survey_ids]
            survey_ids = [sid for sid in survey_ids if sid not in exclude_ids]
        
        if not survey_ids:
            logger.info(f"📝 [AnnotationFeedback] No survey versions found for RFQ {rfq_id}")
            return []
        
        # Query question annotations from all versions
        query = self.db.query(QuestionAnnotation).filter(
            QuestionAnnotation.survey_id.in_(survey_ids),
            QuestionAnnotation.comment.isnot(None),
            QuestionAnnotation.comment != '',
            # Only include human-verified annotations (exclude AI-generated)
            QuestionAnnotation.ai_generated == False,
            QuestionAnnotation.annotator_id != 'ai_system'
        )
        
        question_annotations = query.all()
        
        # Group by question_id and aggregate feedback from all versions
        feedback_by_question: Dict[str, Dict[str, Any]] = {}
        
        for annotation in question_annotations:
            question_id = annotation.question_id
            survey_id = annotation.survey_id
            
            # Get survey version number
            survey = self.db.query(Survey).filter(Survey.id == UUID(survey_id)).first()
            version = survey.version if survey else None
            
            if question_id not in feedback_by_question:
                feedback_by_question[question_id] = {
                    'question_id': question_id,
                    'versions': [],
                    'comments': [],
                    'latest_quality': annotation.quality,
                    'latest_relevant': annotation.relevant
                }
            
            feedback_by_question[question_id]['versions'].append(version)
            feedback_by_question[question_id]['comments'].append({
                'version': version,
                'comment': annotation.comment,
                'quality': annotation.quality,
                'relevant': annotation.relevant,
                'methodological_rigor': annotation.methodological_rigor,
                'content_validity': annotation.content_validity,
                'respondent_experience': annotation.respondent_experience,
                'analytical_value': annotation.analytical_value,
                'business_impact': annotation.business_impact,
                'human_verified': annotation.human_verified
            })
            
            # Update latest quality/relevant if this is a newer version
            if version and feedback_by_question[question_id]['latest_quality']:
                if version > max([v for v in feedback_by_question[question_id]['versions'] if v is not None], default=0):
                    feedback_by_question[question_id]['latest_quality'] = annotation.quality
                    feedback_by_question[question_id]['latest_relevant'] = annotation.relevant
        
        # Convert to list and sort by priority (low quality first, then by version)
        result = list(feedback_by_question.values())
        result.sort(key=lambda x: (
            x['latest_quality'] or 5,  # Lower quality = higher priority
            -max([v for v in x['versions'] if v is not None], default=0)  # Newer versions first
        ))
        
        logger.info(f"📝 [AnnotationFeedback] Collected question feedback from {len(survey_ids)} versions: {len(result)} questions with feedback")
        return result

    def collect_section_feedback(
        self,
        rfq_id: UUID,
        exclude_survey_ids: Optional[List[UUID]] = None,
        section_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Collect section-level comments from ALL previous versions of the RFQ
        
        Args:
            rfq_id: The RFQ ID to collect feedback for
            exclude_survey_ids: Optional list of survey IDs to exclude
            section_ids: Optional list of section IDs to filter by
            
        Returns:
            List of section feedback dictionaries with version information
        """
        # Get all surveys for this RFQ
        all_versions = self.version_service.get_survey_versions(rfq_id)
        survey_ids = [str(survey.id) for survey in all_versions]
        
        # Exclude specified survey IDs if provided
        if exclude_survey_ids:
            exclude_ids = [str(sid) for sid in exclude_survey_ids]
            survey_ids = [sid for sid in survey_ids if sid not in exclude_ids]
        
        if not survey_ids:
            return []
        
        # Query section annotations from all versions
        query = self.db.query(SectionAnnotation).filter(
            SectionAnnotation.survey_id.in_(survey_ids),
            SectionAnnotation.comment.isnot(None),
            SectionAnnotation.comment != '',
            # Only include human-verified annotations
            SectionAnnotation.ai_generated == False,
            SectionAnnotation.annotator_id != 'ai_system'
        )
        
        if section_ids:
            # Convert section_ids to integers if they're strings
            section_id_ints = [int(sid) if isinstance(sid, str) else sid for sid in section_ids]
            query = query.filter(SectionAnnotation.section_id.in_(section_id_ints))
        
        section_annotations = query.all()
        
        # Group by section_id and aggregate feedback from all versions
        feedback_by_section: Dict[int, Dict[str, Any]] = {}
        
        for annotation in section_annotations:
            section_id = annotation.section_id
            survey_id = annotation.survey_id
            
            # Get survey version number
            survey = self.db.query(Survey).filter(Survey.id == UUID(survey_id)).first()
            version = survey.version if survey else None
            
            if section_id not in feedback_by_section:
                feedback_by_section[section_id] = {
                    'section_id': section_id,
                    'versions': [],
                    'comments': [],
                    'latest_quality': annotation.quality
                }
            
            feedback_by_section[section_id]['versions'].append(version)
            feedback_by_section[section_id]['comments'].append({
                'version': version,
                'comment': annotation.comment,
                'quality': annotation.quality,
                'relevant': annotation.relevant,
                'methodological_rigor': annotation.methodological_rigor,
                'content_validity': annotation.content_validity,
                'respondent_experience': annotation.respondent_experience,
                'analytical_value': annotation.analytical_value,
                'business_impact': annotation.business_impact,
                'human_verified': annotation.human_verified
            })
        
        result = list(feedback_by_section.values())
        result.sort(key=lambda x: (
            x['latest_quality'] or 5,  # Lower quality = higher priority
            -max([v for v in x['versions'] if v is not None], default=0)
        ))
        
        logger.info(f"📝 [AnnotationFeedback] Collected section feedback from {len(survey_ids)} versions: {len(result)} sections with feedback")
        return result

    def collect_survey_feedback(
        self,
        rfq_id: UUID,
        exclude_survey_ids: Optional[List[UUID]] = None
    ) -> List[Dict[str, Any]]:
        """
        Collect survey-level overall_comment from ALL previous versions of the RFQ
        
        Args:
            rfq_id: The RFQ ID to collect feedback for
            exclude_survey_ids: Optional list of survey IDs to exclude
            
        Returns:
            List of survey-level feedback dictionaries with version information
        """
        # Get all surveys for this RFQ
        all_versions = self.version_service.get_survey_versions(rfq_id)
        survey_ids = [str(survey.id) for survey in all_versions]
        
        # Exclude specified survey IDs if provided
        if exclude_survey_ids:
            exclude_ids = [str(sid) for sid in exclude_survey_ids]
            survey_ids = [sid for sid in survey_ids if sid not in exclude_ids]
        
        if not survey_ids:
            return []
        
        # Query survey annotations from all versions
        survey_annotations = self.db.query(SurveyAnnotation).filter(
            SurveyAnnotation.survey_id.in_(survey_ids),
            SurveyAnnotation.overall_comment.isnot(None),
            SurveyAnnotation.overall_comment != ''
        ).all()
        
        result = []
        for annotation in survey_annotations:
            survey_id = annotation.survey_id
            
            # Get survey version number
            survey = self.db.query(Survey).filter(Survey.id == UUID(survey_id)).first()
            version = survey.version if survey else None
            
            result.append({
                'version': version,
                'comment': annotation.overall_comment,
                'compliance_report': annotation.compliance_report,
                'advanced_metadata': annotation.advanced_metadata
            })
        
        # Sort by version (newest first)
        result.sort(key=lambda x: x['version'] or 0, reverse=True)
        
        logger.info(f"📝 [AnnotationFeedback] Collected survey-level feedback from {len(survey_ids)} versions: {len(result)} overall comments")
        return result

    async def build_feedback_digest(
        self,
        rfq_id: UUID,
        section_ids: Optional[List[str]] = None,
        prioritize_annotated: bool = True
    ) -> Dict[str, Any]:
        """
        Build comprehensive feedback digest from all previous versions
        
        Args:
            rfq_id: The RFQ ID
            section_ids: Optional list of section IDs to filter by
            prioritize_annotated: Whether to prioritize annotated areas in the digest
            
        Returns:
            Dictionary with structured feedback digest
        """
        logger.info(f"📝 [AnnotationFeedback] Building feedback digest for RFQ {rfq_id}")
        
        # Collect feedback from all previous versions
        question_feedback = self.collect_question_feedback(rfq_id, section_ids=section_ids)
        section_feedback = self.collect_section_feedback(rfq_id, section_ids=section_ids)
        survey_feedback = self.collect_survey_feedback(rfq_id)
        
        # Build digest summaries
        question_digest_lines = []
        if question_feedback:
            for qf in question_feedback[:20]:  # Limit to top 20
                comments = qf.get('comments', [])
                if comments:
                    latest_comment = max(comments, key=lambda c: c.get('version', 0) or 0)
                    quality = latest_comment.get('quality', 3)
                    comment_text = latest_comment.get('comment', '')
                    if comment_text:
                        priority_marker = "⚠️ PRIORITY: " if quality < 3 else "✅ MAINTAIN: " if quality >= 4 else ""
                        question_digest_lines.append(
                            f"{priority_marker}Question {qf['question_id']} (v{latest_comment.get('version', '?')}): {comment_text[:200]} - Quality: {quality}/5"
                        )
        
        section_digest_lines = []
        if section_feedback:
            for sf in section_feedback[:10]:  # Limit to top 10
                comments = sf.get('comments', [])
                if comments:
                    latest_comment = max(comments, key=lambda c: c.get('version', 0) or 0)
                    quality = latest_comment.get('quality', 3)
                    comment_text = latest_comment.get('comment', '')
                    if comment_text:
                        priority_marker = "⚠️ PRIORITY: " if quality < 3 else "✅ MAINTAIN: " if quality >= 4 else ""
                        section_digest_lines.append(
                            f"{priority_marker}Section {sf['section_id']} (v{latest_comment.get('version', '?')}): {comment_text[:200]} - Quality: {quality}/5"
                        )
        
        survey_digest_lines = []
        if survey_feedback:
            for sf in survey_feedback:
                version = sf.get('version', '?')
                comment = sf.get('comment', '')
                if comment:
                    survey_digest_lines.append(f"Overall feedback (v{version}): {comment[:300]}")
        
        # Combine all digests
        combined_digest_parts = []
        if question_digest_lines:
            combined_digest_parts.append("Question-Level Feedback:")
            combined_digest_parts.extend(question_digest_lines)
        if section_digest_lines:
            combined_digest_parts.append("\nSection-Level Feedback:")
            combined_digest_parts.extend(section_digest_lines)
        if survey_digest_lines:
            combined_digest_parts.append("\nSurvey-Level Feedback:")
            combined_digest_parts.extend(survey_digest_lines)
        
        combined_digest = "\n".join(combined_digest_parts) if combined_digest_parts else "No feedback comments available from previous versions."
        
        return {
            "question_feedback": {
                "digest": "\n".join(question_digest_lines) if question_digest_lines else "No question-level feedback available.",
                "questions_with_feedback": question_feedback,
                "total_count": len(question_feedback)
            },
            "section_feedback": {
                "digest": "\n".join(section_digest_lines) if section_digest_lines else "No section-level feedback available.",
                "sections_with_feedback": section_feedback,
                "total_count": len(section_feedback)
            },
            "survey_feedback": {
                "overall_comments": survey_feedback,
                "compliance_insights": {},
                "total_count": len(survey_feedback)
            },
            "combined_digest": combined_digest
        }

