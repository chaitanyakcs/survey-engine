"""
Rule-based multi-level RAG service for sections and questions
Uses deterministic matching instead of vector embeddings for Railway compatibility
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_
from src.database.models import GoldenSection, GoldenQuestion, QuestionAnnotation
from src.utils.database_session_manager import DatabaseSessionManager
import re

logger = logging.getLogger(__name__)


class RuleBasedMultiLevelRAGService:
    """
    Rule-based retrieval service for sections and questions
    Uses exact matching, keyword matching, and pattern matching instead of embeddings
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        
        # Section type mappings for exact matching
        self.section_type_patterns = {
            'demographics': ['demographic', 'about you', 'personal information', 'background', 'profile'],
            'satisfaction': ['satisfaction', 'satisfied', 'experience', 'feedback', 'rating'],
            'pricing': ['pricing', 'price', 'cost', 'value', 'budget', 'payment'],
            'behavioral': ['behavior', 'behaviour', 'usage', 'habits', 'patterns', 'activities'],
            'preferences': ['preference', 'prefer', 'choice', 'option', 'favorite', 'favourite'],
            'intent': ['intent', 'intention', 'plan', 'consider', 'likely', 'probability'],
            'awareness': ['awareness', 'aware', 'know', 'familiar', 'recognition'],
            'loyalty': ['loyalty', 'loyal', 'recommend', 'advocate', 'promoter']
        }
        
        # Question type mappings for exact matching
        self.question_type_patterns = {
            'multiple_choice': ['which', 'what is your', 'select', 'choose'],
            'rating_scale': ['rate', 'scale', 'satisfied', 'likely', 'important'],
            'open_text': ['describe', 'explain', 'tell us', 'comments', 'thoughts'],
            'yes_no': ['do you', 'have you', 'are you', 'will you'],
            'demographic': ['age', 'gender', 'income', 'education', 'location']
        }
        
        # Methodology tag mappings
        self.methodology_patterns = {
            'quantitative': ['rating', 'scale', 'score', 'number', 'percentage', 'statistical'],
            'qualitative': ['describe', 'explain', 'tell us', 'opinion', 'thoughts', 'comments'],
            'mixed_methods': ['both', 'combination', 'mix', 'quantitative and qualitative']
        }
    
    async def retrieve_golden_sections(
        self,
        rfq_text: str,
        methodology_tags: Optional[List[str]] = None,
        industry: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve golden sections using rule-based matching
        """
        try:
            logger.info(f"🔍 [RuleBasedRAG] Retrieving sections for RFQ: {rfq_text[:100]}...")
            
            # Extract patterns from RFQ text
            rfq_lower = rfq_text.lower()
            detected_section_types = self._detect_section_types(rfq_lower)
            detected_keywords = self._extract_keywords(rfq_lower)
            detected_methodology = self._detect_methodology(rfq_lower)
            
            logger.info(f"🔍 [RuleBasedRAG] Detected section types: {detected_section_types}")
            logger.info(f"🔍 [RuleBasedRAG] Detected keywords: {detected_keywords}")
            logger.info(f"🔍 [RuleBasedRAG] Detected methodology: {detected_methodology}")
            
            # Build query conditions
            conditions = []
            
            # Exact section type matching (highest priority)
            if detected_section_types:
                conditions.append(
                    or_(*[GoldenSection.section_type == st for st in detected_section_types])
                )
            
            # Methodology tag matching
            if detected_methodology:
                conditions.append(
                    GoldenSection.methodology_tags.op('&&')(detected_methodology)
                )
            
            # Industry keyword matching
            if industry:
                industry_keywords = [industry.lower()]
                conditions.append(
                    GoldenSection.industry_keywords.op('&&')(industry_keywords)
                )
            
            # Keyword matching in section text
            if detected_keywords:
                keyword_conditions = []
                for keyword in detected_keywords:
                    keyword_conditions.append(
                        GoldenSection.section_text.ilike(f'%{keyword}%')
                    )
                conditions.append(or_(*keyword_conditions))
            
            # Execute query with fallback
            if conditions:
                sections = DatabaseSessionManager.safe_query(
                    self.db,
                    lambda: self.db.query(GoldenSection)
                    .filter(and_(*conditions))
                    .filter(GoldenSection.quality_score >= 0.5)
                    .order_by(GoldenSection.human_verified.desc(), GoldenSection.quality_score.desc())
                    .limit(limit)
                    .all(),
                    fallback_value=[],
                    operation_name="retrieve golden sections with conditions"
                )
            else:
                # Fallback: get top sections by quality
                sections = DatabaseSessionManager.safe_query(
                    self.db,
                    lambda: self.db.query(GoldenSection)
                    .filter(GoldenSection.quality_score >= 0.5)
                    .order_by(GoldenSection.human_verified.desc(), GoldenSection.quality_score.desc())
                    .limit(limit)
                    .all(),
                    fallback_value=[],
                    operation_name="retrieve golden sections fallback"
                )
            
            # Convert to dict format
            result = []
            for section in sections:
                result.append({
                    'id': str(section.id),
                    'section_id': section.section_id,
                    'survey_id': section.survey_id,
                    'golden_pair_id': str(section.golden_pair_id),
                    'section_title': section.section_title,
                    'section_text': section.section_text,
                    'section_type': section.section_type,
                    'methodology_tags': section.methodology_tags or [],
                    'industry_keywords': section.industry_keywords or [],
                    'quality_score': float(section.quality_score) if section.quality_score else 0.5,
                    'human_verified': section.human_verified,
                    'labels': section.labels or {}
                })
            
            logger.info(f"✅ [RuleBasedRAG] Retrieved {len(result)} sections")
            return result
            
        except Exception as e:
            logger.error(f"❌ [RuleBasedRAG] Section retrieval failed: {str(e)}")
            return []
    
    async def retrieve_golden_questions(
        self,
        rfq_text: str,
        methodology_tags: Optional[List[str]] = None,
        industry: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve golden questions using rule-based matching
        """
        try:
            logger.info(f"🔍 [RuleBasedRAG] Retrieving questions for RFQ: {rfq_text[:100]}...")
            
            # Extract patterns from RFQ text
            rfq_lower = rfq_text.lower()
            detected_question_types = self._detect_question_types(rfq_lower)
            detected_keywords = self._extract_keywords(rfq_lower)
            detected_methodology = self._detect_methodology(rfq_lower)
            
            logger.info(f"🔍 [RuleBasedRAG] Detected question types: {detected_question_types}")
            logger.info(f"🔍 [RuleBasedRAG] Detected keywords: {detected_keywords}")
            logger.info(f"🔍 [RuleBasedRAG] Detected methodology: {detected_methodology}")
            
            # Build query conditions
            conditions = []
            
            # Exact question type matching (highest priority)
            if detected_question_types:
                conditions.append(
                    or_(*[GoldenQuestion.question_type == qt for qt in detected_question_types])
                )
            
            # Methodology tag matching
            if detected_methodology:
                conditions.append(
                    GoldenQuestion.methodology_tags.op('&&')(detected_methodology)
                )
            
            # Industry keyword matching
            if industry:
                industry_keywords = [industry.lower()]
                conditions.append(
                    GoldenQuestion.industry_keywords.op('&&')(industry_keywords)
                )
            
            # Keyword matching in question text
            if detected_keywords:
                keyword_conditions = []
                for keyword in detected_keywords:
                    keyword_conditions.append(
                        GoldenQuestion.question_text.ilike(f'%{keyword}%')
                    )
                conditions.append(or_(*keyword_conditions))
            
            # Execute query with fallback
            if conditions:
                questions = DatabaseSessionManager.safe_query(
                    self.db,
                    lambda: self.db.query(GoldenQuestion)
                    .filter(and_(*conditions))
                    .filter(GoldenQuestion.quality_score >= 0.5)
                    .order_by(GoldenQuestion.human_verified.desc(), GoldenQuestion.quality_score.desc())
                    .limit(limit)
                    .all(),
                    fallback_value=[],
                    operation_name="retrieve golden questions with conditions"
                )
            else:
                # Fallback: get top questions by quality
                questions = DatabaseSessionManager.safe_query(
                    self.db,
                    lambda: self.db.query(GoldenQuestion)
                    .filter(GoldenQuestion.quality_score >= 0.5)
                    .order_by(GoldenQuestion.human_verified.desc(), GoldenQuestion.quality_score.desc())
                    .limit(limit)
                    .all(),
                    fallback_value=[],
                    operation_name="retrieve golden questions fallback"
                )
            
            # Convert to dict format and include annotation comments
            result = []
            for question in questions:
                # Fetch annotation comment and relevance if available
                annotation_comment = None
                annotation_relevance = None
                if question.annotation_id:
                    annotation = DatabaseSessionManager.safe_query(
                        self.db,
                        lambda: self.db.query(QuestionAnnotation)
                        .filter(QuestionAnnotation.id == question.annotation_id)
                        .first(),
                        fallback_value=None,
                        operation_name="fetch annotation data"
                    )
                    if annotation:
                        if annotation.comment:
                            annotation_comment = annotation.comment
                        annotation_relevance = annotation.relevant  # 1-5 scale
                
                result.append({
                    'id': str(question.id),
                    'question_id': question.question_id,
                    'survey_id': question.survey_id,
                    'golden_pair_id': str(question.golden_pair_id),
                    'question_text': question.question_text,
                    'question_type': question.question_type,
                    'question_subtype': question.question_subtype,
                    'methodology_tags': question.methodology_tags or [],
                    'industry_keywords': question.industry_keywords or [],
                    'quality_score': float(question.quality_score) if question.quality_score else 0.5,
                    'human_verified': question.human_verified,
                    'labels': question.labels or {},
                    'annotation_comment': annotation_comment,  # Include actionable comment
                    'annotation_relevance': annotation_relevance  # Include for transparency
                })
            
            logger.info(f"✅ [RuleBasedRAG] Retrieved {len(result)} questions")
            return result
            
        except Exception as e:
            logger.error(f"❌ [RuleBasedRAG] Question retrieval failed: {str(e)}")
            return []
    
    async def retrieve_golden_questions_by_labels(
        self,
        required_labels: List[str],
        methodology_tags: Optional[List[str]] = None,
        industry: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve golden questions matching required QNR labels
        Returns max 1 question per label, up to limit total
        
        Args:
            required_labels: List of QNR label names to match
            methodology_tags: Optional methodology filters
            industry: Optional industry filter
            limit: Maximum number of questions to return
            
        Returns:
            List of golden questions with label metadata
        """
        try:
            logger.info(f"🏷️ [RuleBasedRAG] Retrieving questions for labels: {required_labels}")
            
            if not required_labels:
                logger.warning("⚠️ [RuleBasedRAG] No required labels provided, falling back to quality-based retrieval")
                return await self.retrieve_golden_questions(
                    rfq_text="",
                    methodology_tags=methodology_tags,
                    industry=industry,
                    limit=limit
                )
            
            # Import QNRLabel model for join
            from src.database.models import QNRLabel
            
            # Build query to get questions with matching labels
            # Strategy: Get 1 question per label, prioritizing quality
            questions_by_label = {}
            
            for label_name in required_labels[:limit]:  # Limit to avoid too many queries
                # Query for questions with this specific label
                # Using JSONB containment operator @>
                # Query for questions with this specific label
                # Labels field is JSONB array of strings like ["Recent_Participation", "CoI_Check"]
                # Use @> operator to check if label_name is in the array
                label_name_escaped = label_name.replace("'", "''")  # Escape single quotes for SQL
                questions = DatabaseSessionManager.safe_query(
                    self.db,
                    lambda: self.db.query(GoldenQuestion, QNRLabel)
                    .join(QNRLabel, QNRLabel.name == label_name)
                    .filter(
                        or_(
                            # Check if labels array contains the label name
                            GoldenQuestion.labels.op('@>')(text(f'\'["{label_name_escaped}"]\'')),
                            # Check if labels array contains the label name (alternative syntax)
                            text(f"golden_questions.labels ? '{label_name_escaped}'")
                        )
                    )
                    .filter(GoldenQuestion.quality_score >= 0.5)
                    .order_by(GoldenQuestion.human_verified.desc(), GoldenQuestion.quality_score.desc())
                    .limit(1)
                    .all(),
                    fallback_value=[],
                    operation_name=f"retrieve question for label {label_name}"
                )
                
                if questions:
                    question, qnr_label = questions[0]
                    questions_by_label[label_name] = (question, qnr_label)
                    logger.info(f"✅ [RuleBasedRAG] Found question for label '{label_name}': {question.question_text[:50]}...")
                else:
                    logger.warning(f"⚠️ [RuleBasedRAG] No question found for label '{label_name}'")
            
            # If we don't have enough questions, fill with high-quality questions
            if len(questions_by_label) < limit:
                remaining = limit - len(questions_by_label)
                logger.info(f"🔍 [RuleBasedRAG] Need {remaining} more questions, fetching high-quality fallbacks")
                
                # Get IDs of questions we already have
                existing_ids = [q.id for q, _ in questions_by_label.values()]
                
                # Fetch additional high-quality questions
                fallback_questions = DatabaseSessionManager.safe_query(
                    self.db,
                    lambda: self.db.query(GoldenQuestion)
                    .filter(GoldenQuestion.id.notin_(existing_ids) if existing_ids else text("1=1"))
                    .filter(GoldenQuestion.quality_score >= 0.5)
                    .order_by(GoldenQuestion.human_verified.desc(), GoldenQuestion.quality_score.desc())
                    .limit(remaining)
                    .all(),
                    fallback_value=[],
                    operation_name="retrieve fallback questions"
                )
                
                # Add fallback questions with no specific label
                for question in fallback_questions:
                    questions_by_label[f"fallback_{question.id}"] = (question, None)
            
            # Convert to result format with label metadata
            result = []
            for label_key, (question, qnr_label) in questions_by_label.items():
                # Fetch annotation comment if available
                annotation_comment = None
                annotation_relevance = None
                if question.annotation_id:
                    annotation = DatabaseSessionManager.safe_query(
                        self.db,
                        lambda: self.db.query(QuestionAnnotation)
                        .filter(QuestionAnnotation.id == question.annotation_id)
                        .first(),
                        fallback_value=None,
                        operation_name="fetch annotation data"
                    )
                    if annotation:
                        if annotation.comment:
                            annotation_comment = annotation.comment
                        annotation_relevance = annotation.relevant
                
                question_dict = {
                    'id': str(question.id),
                    'question_id': question.question_id,
                    'survey_id': question.survey_id,
                    'golden_pair_id': str(question.golden_pair_id),
                    'question_text': question.question_text,
                    'question_type': question.question_type,
                    'question_subtype': question.question_subtype,
                    'methodology_tags': question.methodology_tags or [],
                    'industry_keywords': question.industry_keywords or [],
                    'quality_score': float(question.quality_score) if question.quality_score else 0.5,
                    'human_verified': question.human_verified,
                    'labels': question.labels or {},
                    'annotation_comment': annotation_comment,
                    'annotation_relevance': annotation_relevance,
                    # Label metadata for prompt building and UI display
                    'primary_label': qnr_label.name if qnr_label else None,
                    'label_description': qnr_label.description if qnr_label else None,
                    'label_mandatory': qnr_label.mandatory if qnr_label else False,
                    'label_section_id': qnr_label.section_id if qnr_label else question.section_id,
                    'label_category': qnr_label.category if qnr_label else None
                }
                result.append(question_dict)
            
            logger.info(f"✅ [RuleBasedRAG] Retrieved {len(result)} questions ({len(questions_by_label)} with labels)")
            return result[:limit]  # Ensure we don't exceed limit
            
        except Exception as e:
            logger.error(f"❌ [RuleBasedRAG] Label-based question retrieval failed: {str(e)}")
            logger.exception(e)
            # Fallback to regular retrieval
            return await self.retrieve_golden_questions(
                rfq_text="",
                methodology_tags=methodology_tags,
                industry=industry,
                limit=limit
            )
    
    def _detect_section_types(self, text: str) -> List[str]:
        """Detect section types from RFQ text"""
        detected = []
        for section_type, patterns in self.section_type_patterns.items():
            if any(pattern in text for pattern in patterns):
                detected.append(section_type)
        return detected
    
    def _detect_question_types(self, text: str) -> List[str]:
        """Detect question types from RFQ text"""
        detected = []
        for question_type, patterns in self.question_type_patterns.items():
            if any(pattern in text for pattern in patterns):
                detected.append(question_type)
        return detected
    
    def _detect_methodology(self, text: str) -> List[str]:
        """Detect methodology from RFQ text"""
        detected = []
        for methodology, patterns in self.methodology_patterns.items():
            if any(pattern in text for pattern in patterns):
                detected.append(methodology)
        return detected
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from RFQ text"""
        # Simple keyword extraction - can be enhanced
        keywords = []
        
        # Common survey keywords
        survey_keywords = [
            'customer', 'user', 'client', 'satisfaction', 'experience', 'feedback',
            'product', 'service', 'quality', 'value', 'price', 'cost', 'budget',
            'recommend', 'loyalty', 'brand', 'awareness', 'preference', 'choice'
        ]
        
        for keyword in survey_keywords:
            if keyword in text:
                keywords.append(keyword)
        
        return keywords[:10]  # Limit to top 10 keywords
