"""
Service to sync human-annotated questions and sections to the RAG system.
Extracts quality insights from annotations and adds them to golden_questions/golden_sections.
"""

import logging
import uuid
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime

from src.database.models import (
    QuestionAnnotation,
    SectionAnnotation,
    Survey,
    GoldenQuestion,
    GoldenSection,
)
from src.utils.database_session_manager import DatabaseSessionManager

logger = logging.getLogger(__name__)


class AnnotationRAGSyncService:
    """
    Service to sync annotations to RAG tables for multi-level retrieval.
    Extracts questions/sections from surveys and enriches with annotation metadata.
    """

    def __init__(self, db_session: Session):
        self.db = db_session

    async def sync_question_annotation(
        self, annotation_id: int
    ) -> Dict[str, Any]:
        """
        Sync a question annotation to the golden_questions RAG table.

        Args:
            annotation_id: ID of the QuestionAnnotation to sync

        Returns:
            Dict with success status and created/updated question ID
        """
        try:
            # Fetch the annotation data fresh within this session
            annotation = self.db.query(QuestionAnnotation).filter(
                QuestionAnnotation.id == annotation_id
            ).first()

            if not annotation:
                logger.warning(
                    f"⚠️ Annotation {annotation_id} not found, skipping sync"
                )
                return {"success": False, "error": "Annotation not found"}

            # Extract annotation values to avoid session binding issues
            annotation_quality = annotation.quality
            annotation_human_verified = annotation.human_verified
            annotation_labels = annotation.labels
            annotation_question_id = annotation.question_id
            annotation_survey_id = annotation.survey_id
            
            # Normalize labels
            from src.services.label_normalizer import LabelNormalizer
            label_normalizer = LabelNormalizer()
            
            if isinstance(annotation_labels, list):
                annotation_labels = label_normalizer.normalize_batch(annotation_labels)
            elif isinstance(annotation_labels, str):
                annotation_labels = [label_normalizer.normalize(annotation_labels)]
            elif annotation_labels is None:
                annotation_labels = []

            # Validate survey_id is a valid UUID
            try:
                uuid.UUID(str(annotation_survey_id))
            except (ValueError, TypeError):
                logger.warning(
                    f"⚠️ Invalid survey_id format '{annotation_survey_id}' for annotation {annotation_id}, skipping sync"
                )
                return {"success": False, "error": "Invalid survey_id format"}

            # Fetch the survey to get question text
            survey = self.db.query(Survey).filter(Survey.id == annotation_survey_id).first()

            if not survey or not survey.final_output:
                logger.warning(
                    f"⚠️ Survey {annotation_survey_id} not found or has no "
                    f"final_output, skipping sync"
                )
                return {"success": False, "error": "Survey data not available"}

            # Extract question data from survey
            question_data = self._extract_question_from_survey(
                survey.final_output, annotation_question_id
            )

            if not question_data:
                logger.warning(
                    f"⚠️ Question {annotation_question_id} not found in survey "
                    f"{annotation_survey_id}, skipping sync"
                )
                return {"success": False, "error": "Question not found in survey"}

            # Calculate quality score from annotation
            quality_score = self._calculate_quality_score(
                annotation_quality,
                annotation_human_verified,
                annotation_labels
            )

            # Extract metadata
            methodology_tags = self._extract_methodology_tags(
                question_data, annotation_labels
            )
            industry_keywords = self._extract_industry_keywords(
                question_data, annotation_labels
            )
            question_patterns = self._extract_question_patterns(question_data)

            # Check if golden question already exists (deduplication)
            existing_golden = DatabaseSessionManager.safe_query(
                self.db,
                lambda: self.db.query(GoldenQuestion)
                .filter(
                    GoldenQuestion.survey_id == str(annotation_survey_id),
                    GoldenQuestion.question_id == annotation_question_id,
                )
                .first(),
                fallback_value=None,
                operation_name="check existing golden question",
            )

            if existing_golden:
                # Update existing golden question
                existing_golden.quality_score = quality_score
                existing_golden.annotation_id = annotation_id
                existing_golden.human_verified = annotation_human_verified
                existing_golden.methodology_tags = methodology_tags
                existing_golden.industry_keywords = industry_keywords
                existing_golden.question_patterns = question_patterns
                existing_golden.labels = annotation_labels
                existing_golden.updated_at = datetime.now()
                self.db.commit()  # Commit the transaction

                logger.info(
                    f"✅ Updated golden question {existing_golden.id} "
                    f"from annotation {annotation_id}"
                )
                return {
                    "success": True,
                    "action": "updated",
                    "golden_question_id": str(existing_golden.id),
                }
            else:
                # Create new golden question
                golden_question = GoldenQuestion(
                    question_id=annotation_question_id,
                    survey_id=str(annotation_survey_id),
                    golden_pair_id=None,  # Not from a golden pair
                    annotation_id=annotation_id,
                    question_text=question_data["text"],
                    question_type=question_data.get("type", "general"),
                    question_subtype=question_data.get("subtype", "unknown"),
                    methodology_tags=methodology_tags,
                    industry_keywords=industry_keywords,
                    question_patterns=question_patterns,
                    quality_score=quality_score,
                    usage_count=0,
                    human_verified=annotation_human_verified,
                    labels=annotation_labels,
                    created_at=datetime.now(),
                )

                self.db.add(golden_question)
                self.db.commit()  # Commit the transaction

                logger.info(
                    f"✅ Created golden question from annotation {annotation_id}"
                )
                return {
                    "success": True,
                    "action": "created",
                    "golden_question_id": str(golden_question.id),
                }

        except Exception as e:
            logger.error(
                f"❌ Error syncing question annotation {annotation_id}: {str(e)}"
            )
            # Rollback the transaction to clear any aborted state
            try:
                self.db.rollback()
            except Exception as rollback_error:
                logger.error(f"❌ Error during rollback: {str(rollback_error)}")
            return {"success": False, "error": str(e)}

    async def sync_section_annotation(self, annotation_id: int) -> Dict[str, Any]:
        """
        Sync a section annotation to the golden_sections RAG table.

        Args:
            annotation_id: ID of the SectionAnnotation to sync

        Returns:
            Dict with success status and created/updated section ID
        """
        try:
            # Fetch the annotation data fresh within this session
            annotation = self.db.query(SectionAnnotation).filter(
                SectionAnnotation.id == annotation_id
            ).first()

            if not annotation:
                logger.warning(
                    f"⚠️ Annotation {annotation_id} not found, skipping sync"
                )
                return {"success": False, "error": "Annotation not found"}

            # Extract annotation values to avoid session binding issues
            annotation_quality = annotation.quality
            annotation_human_verified = annotation.human_verified
            annotation_labels = annotation.labels
            annotation_section_id = annotation.section_id
            annotation_survey_id = annotation.survey_id
            
            # Normalize labels
            from src.services.label_normalizer import LabelNormalizer
            label_normalizer = LabelNormalizer()
            
            if isinstance(annotation_labels, list):
                annotation_labels = label_normalizer.normalize_batch(annotation_labels)
            elif isinstance(annotation_labels, str):
                annotation_labels = [label_normalizer.normalize(annotation_labels)]
            elif annotation_labels is None:
                annotation_labels = []

            # Validate survey_id is a valid UUID
            try:
                uuid.UUID(str(annotation_survey_id))
            except (ValueError, TypeError):
                logger.warning(
                    f"⚠️ Invalid survey_id format '{annotation_survey_id}' for annotation {annotation_id}, skipping sync"
                )
                return {"success": False, "error": "Invalid survey_id format"}

            # Fetch the survey to get section text
            survey = self.db.query(Survey).filter(Survey.id == annotation_survey_id).first()

            if not survey or not survey.final_output:
                logger.warning(
                    f"⚠️ Survey {annotation_survey_id} not found or has no "
                    f"final_output, skipping sync"
                )
                return {"success": False, "error": "Survey data not available"}

            # Extract section data from survey
            section_data = self._extract_section_from_survey(
                survey.final_output, annotation_section_id
            )

            if not section_data:
                logger.warning(
                    f"⚠️ Section {annotation_section_id} not found in survey "
                    f"{annotation_survey_id}, skipping sync"
                )
                return {"success": False, "error": "Section not found in survey"}

            # Calculate quality score from annotation
            quality_score = self._calculate_quality_score(
                annotation_quality,
                annotation_human_verified,
                annotation_labels
            )

            # Extract metadata
            methodology_tags = self._extract_methodology_tags(
                section_data, annotation_labels
            )
            industry_keywords = self._extract_industry_keywords(
                section_data, annotation_labels
            )
            section_type = self._detect_section_type(section_data)

            # Check if golden section already exists (deduplication)
            existing_golden = DatabaseSessionManager.safe_query(
                self.db,
                lambda: self.db.query(GoldenSection)
                .filter(
                    GoldenSection.survey_id == str(annotation_survey_id),
                    GoldenSection.section_id == str(annotation_section_id),
                )
                .first(),
                fallback_value=None,
                operation_name="check existing golden section",
            )

            if existing_golden:
                # Update existing golden section
                existing_golden.quality_score = quality_score
                existing_golden.annotation_id = annotation_id
                existing_golden.human_verified = annotation_human_verified
                existing_golden.methodology_tags = methodology_tags
                existing_golden.industry_keywords = industry_keywords
                existing_golden.section_type = section_type
                existing_golden.updated_at = datetime.now()
                self.db.commit()  # Commit the transaction

                logger.info(
                    f"✅ Updated golden section {existing_golden.id} "
                    f"from annotation {annotation_id}"
                )
                return {
                    "success": True,
                    "action": "updated",
                    "golden_section_id": str(existing_golden.id),
                }
            else:
                # Create new golden section
                golden_section = GoldenSection(
                    survey_id=str(annotation_survey_id),
                    golden_pair_id=None,  # Not from a golden pair
                    annotation_id=annotation_id,
                    section_id=str(annotation_section_id),
                    section_title=section_data.get("title", ""),
                    section_text=(
                        section_data.get("title", "")
                        + " "
                        + section_data.get("description", "")
                    ),
                    section_type=section_type,
                    methodology_tags=methodology_tags,
                    industry_keywords=industry_keywords,
                    quality_score=quality_score,
                    usage_count=0,
                    human_verified=annotation_human_verified,
                    created_at=datetime.now(),
                )

                self.db.add(golden_section)
                self.db.commit()  # Commit the transaction

                logger.info(
                    f"✅ Created golden section from annotation {annotation_id}"
                )
                return {
                    "success": True,
                    "action": "created",
                    "golden_section_id": str(golden_section.id),
                }

        except Exception as e:
            logger.error(
                f"❌ Error syncing section annotation {annotation_id}: {str(e)}"
            )
            # Rollback the transaction to clear any aborted state
            try:
                self.db.rollback()
            except Exception as rollback_error:
                logger.error(f"❌ Error during rollback: {str(rollback_error)}")
            return {"success": False, "error": str(e)}

    def _calculate_quality_score(
        self, quality: int, human_verified: bool, labels: list
    ) -> float:
        """
        Calculate quality score from annotation metadata.

        Base score: normalize quality field (1-5) to 0.0-1.0
        +0.2 if human verified
        +0.1 if has positive labels

        Args:
            quality: Quality score (1-5)
            human_verified: Whether annotation is human verified
            labels: List of labels

        Returns:
            Quality score between 0.0 and 1.0
        """
        # Normalize quality (1-5 scale) to 0.0-1.0
        # Map: 1→0.2, 2→0.4, 3→0.6, 4→0.8, 5→1.0
        base_score = (quality - 1) / 4.0

        # Boost for human verification
        if human_verified:
            base_score += 0.2

        # Boost for positive labels
        if labels and len(labels) > 0:
            # Check for positive quality indicators in labels
            positive_labels = {
                "high_quality",
                "well_structured",
                "clear",
                "relevant",
                "comprehensive",
            }
            has_positive = any(
                label.lower() in positive_labels for label in labels
            )
            if has_positive:
                base_score += 0.1

        # Cap at 1.0
        return min(1.0, base_score)

    def _extract_question_from_survey(
        self, survey_data: Dict[str, Any], question_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Extract question data from survey final_output.
        Questions are nested within sections.

        Args:
            survey_data: Survey final_output JSONB
            question_id: Question ID to find (e.g., "q1", "q2")

        Returns:
            Question dict with text, type, etc., or None if not found
        """
        sections = survey_data.get("sections", [])

        for section in sections:
            if not isinstance(section, dict):
                continue

            questions = section.get("questions", [])
            for question in questions:
                if not isinstance(question, dict):
                    continue

                # Match by id field
                if question.get("id") == question_id:
                    return {
                        "text": question.get("text", ""),
                        "type": question.get("type", "general"),
                        "subtype": question.get("subtype", "unknown"),
                        "section_id": section.get("id"),
                    }

        return None

    def _extract_section_from_survey(
        self, survey_data: Dict[str, Any], section_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Extract section data from survey final_output.

        Args:
            survey_data: Survey final_output JSONB
            section_id: Section index to find

        Returns:
            Section dict with title, description, etc., or None if not found
        """
        sections = survey_data.get("sections", [])

        if 0 <= section_id < len(sections):
            section = sections[section_id]
            if isinstance(section, dict):
                return {
                    "title": section.get("title", ""),
                    "description": section.get("description", ""),
                    "id": section.get("id"),
                }

        return None

    def _extract_methodology_tags(
        self, data: Dict[str, Any], labels: list
    ) -> List[str]:
        """
        Extract methodology tags from question/section data and labels.

        Args:
            data: Question or section data
            labels: List of labels from annotation

        Returns:
            List of methodology tags
        """
        tags = set()

        # Extract from labels
        if labels:
            for label in labels:
                label_lower = label.lower()
                if any(
                    method in label_lower
                    for method in [
                        "quantitative",
                        "qualitative",
                        "rating",
                        "scale",
                        "multiple_choice",
                        "open_ended",
                        "demographic",
                        "behavioral",
                        "attitudinal",
                    ]
                ):
                    tags.add(label_lower)

        # Default tag if none found
        if not tags:
            tags.add("mixed_methods")

        return list(tags)

    def _extract_industry_keywords(
        self, data: Dict[str, Any], labels: list
    ) -> List[str]:
        """
        Extract industry keywords from question/section text and labels.

        Args:
            data: Question or section data
            labels: List of labels from annotation

        Returns:
            List of industry keywords
        """
        keywords = set()

        # Extract from text
        text = data.get("text", "") or data.get("title", "")
        text_lower = text.lower()

        industry_terms = [
            "healthcare",
            "finance",
            "technology",
            "retail",
            "education",
            "automotive",
            "fitness",
            "food",
            "travel",
            "entertainment",
            "real estate",
            "insurance",
        ]

        for term in industry_terms:
            if term in text_lower:
                keywords.add(term)

        # Extract from labels
        if labels:
            for label in labels:
                label_lower = label.lower()
                for term in industry_terms:
                    if term in label_lower:
                        keywords.add(term)

        return list(keywords)

    def _extract_question_patterns(
        self, question_data: Dict[str, Any]
    ) -> List[str]:
        """
        Extract question patterns from question text.

        Args:
            question_data: Question data dict

        Returns:
            List of patterns
        """
        patterns = set()
        text = question_data.get("text", "").lower()

        pattern_map = {
            "frequency": ["how often", "frequency"],
            "quantity": ["how much", "how many"],
            "likelihood": ["how likely", "probability"],
            "importance": ["how important", "priority"],
            "satisfaction": ["how satisfied", "satisfaction"],
            "preference": ["how would you", "preference"],
            "reasoning": ["why", "reason"],
            "timing": ["when", "timing"],
            "location": ["where", "location"],
        }

        for pattern_name, keywords in pattern_map.items():
            if any(keyword in text for keyword in keywords):
                patterns.add(pattern_name)

        return list(patterns) if patterns else ["general"]

    def _detect_section_type(self, section_data: Dict[str, Any]) -> str:
        """
        Detect section type from title/description.

        Args:
            section_data: Section data dict

        Returns:
            Section type string
        """
        text = (
            section_data.get("title", "") + " " + section_data.get("description", "")
        ).lower()

        type_patterns = {
            "demographics": [
                "demographic",
                "about you",
                "personal information",
                "background",
            ],
            "satisfaction": ["satisfaction", "satisfied", "experience", "feedback"],
            "pricing": ["pricing", "price", "cost", "value", "budget"],
            "behavioral": ["behavior", "usage", "habits", "patterns"],
            "preferences": ["preference", "prefer", "choice", "option"],
            "intent": ["intent", "intention", "plan", "consider"],
            "awareness": ["awareness", "aware", "know", "familiar"],
        }

        for section_type, patterns in type_patterns.items():
            if any(pattern in text for pattern in patterns):
                return section_type

        return "general"

