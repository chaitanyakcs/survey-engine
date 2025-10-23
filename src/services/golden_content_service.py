"""
Service for managing golden sections and questions
Provides CRUD operations and analytics for golden content
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from src.database.models import GoldenSection, GoldenQuestion
from src.utils.error_messages import UserFriendlyError
from uuid import UUID

logger = logging.getLogger(__name__)


class GoldenContentService:
    """
    Service for managing golden sections and questions
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    async def list_sections(
        self, 
        filters: Dict[str, Any], 
        skip: int = 0, 
        limit: int = 100
    ) -> List[GoldenSection]:
        """
        List golden sections with filtering and pagination
        """
        try:
            logger.info(f"🔍 [GoldenContentService] Listing sections with filters: {filters}")
            
            query = self.db.query(GoldenSection)
            
            # Apply filters
            if filters.get('section_type'):
                query = query.filter(GoldenSection.section_type == filters['section_type'])
            
            if filters.get('methodology_tags'):
                methodology_tags = filters['methodology_tags']
                query = query.filter(GoldenSection.methodology_tags.op('&&')(methodology_tags))
            
            if filters.get('industry'):
                industry_keyword = filters['industry'].lower()
                query = query.filter(
                    func.array_to_string(GoldenSection.industry_keywords, ' ').ilike(f'%{industry_keyword}%')
                )
            
            if filters.get('min_quality_score') is not None:
                query = query.filter(GoldenSection.quality_score >= filters['min_quality_score'])
            
            if filters.get('human_verified') is not None:
                query = query.filter(GoldenSection.human_verified == filters['human_verified'])
            
            if filters.get('search'):
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        GoldenSection.section_text.ilike(search_term),
                        GoldenSection.section_title.ilike(search_term)
                    )
                )
            
            # Order by usage count descending, then by quality score
            query = query.order_by(desc(GoldenSection.usage_count), desc(GoldenSection.quality_score))
            
            # Apply pagination
            sections = query.offset(skip).limit(limit).all()
            
            logger.info(f"✅ [GoldenContentService] Found {len(sections)} sections")
            return sections
            
        except Exception as e:
            logger.error(f"❌ [GoldenContentService] Failed to list sections: {str(e)}", exc_info=True)
            raise UserFriendlyError(
                message="Failed to retrieve golden sections",
                technical_details=str(e),
                action_required="Please try again or contact support if the issue persists"
            )
    
    async def get_section(self, section_id: UUID) -> Optional[GoldenSection]:
        """
        Get a single golden section by ID
        """
        try:
            logger.info(f"🔍 [GoldenContentService] Getting section: {section_id}")
            
            section = self.db.query(GoldenSection).filter(GoldenSection.id == section_id).first()
            
            if section:
                logger.info(f"✅ [GoldenContentService] Found section: {section_id}")
            else:
                logger.warning(f"⚠️ [GoldenContentService] Section not found: {section_id}")
            
            return section
            
        except Exception as e:
            logger.error(f"❌ [GoldenContentService] Failed to get section {section_id}: {str(e)}", exc_info=True)
            raise UserFriendlyError(
                message="Failed to retrieve golden section",
                technical_details=str(e),
                action_required="Please try again or contact support if the issue persists"
            )
    
    async def update_section(
        self, 
        section_id: UUID, 
        updates: Dict[str, Any]
    ) -> Optional[GoldenSection]:
        """
        Update a golden section
        """
        try:
            logger.info(f"🔧 [GoldenContentService] Updating section {section_id} with: {updates}")
            
            section = self.db.query(GoldenSection).filter(GoldenSection.id == section_id).first()
            
            if not section:
                logger.warning(f"⚠️ [GoldenContentService] Section not found for update: {section_id}")
                return None
            
            # Update fields
            for key, value in updates.items():
                if hasattr(section, key):
                    setattr(section, key, value)
                    logger.info(f"🔧 [GoldenContentService] Updated {key} to: {value}")
                else:
                    logger.warning(f"⚠️ [GoldenContentService] Unknown field: {key}")
            
            # Commit changes
            self.db.commit()
            self.db.refresh(section)
            
            logger.info(f"✅ [GoldenContentService] Successfully updated section: {section_id}")
            return section
            
        except Exception as e:
            logger.error(f"❌ [GoldenContentService] Failed to update section {section_id}: {str(e)}", exc_info=True)
            self.db.rollback()
            raise UserFriendlyError(
                message="Failed to update golden section",
                technical_details=str(e),
                action_required="Please try again or contact support if the issue persists"
            )
    
    async def delete_section(self, section_id: UUID) -> bool:
        """
        Delete a golden section
        """
        try:
            logger.info(f"🗑️ [GoldenContentService] Deleting section: {section_id}")
            
            section = self.db.query(GoldenSection).filter(GoldenSection.id == section_id).first()
            
            if not section:
                logger.warning(f"⚠️ [GoldenContentService] Section not found for deletion: {section_id}")
                return False
            
            self.db.delete(section)
            self.db.commit()
            
            logger.info(f"✅ [GoldenContentService] Successfully deleted section: {section_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ [GoldenContentService] Failed to delete section {section_id}: {str(e)}", exc_info=True)
            self.db.rollback()
            raise UserFriendlyError(
                message="Failed to delete golden section",
                technical_details=str(e),
                action_required="Please try again or contact support if the issue persists"
            )
    
    async def list_questions(
        self, 
        filters: Dict[str, Any], 
        skip: int = 0, 
        limit: int = 100
    ) -> List[GoldenQuestion]:
        """
        List golden questions with filtering and pagination
        """
        try:
            logger.info(f"🔍 [GoldenContentService] Listing questions with filters: {filters}")
            
            query = self.db.query(GoldenQuestion)
            
            # Apply filters
            if filters.get('question_type'):
                query = query.filter(GoldenQuestion.question_type == filters['question_type'])
            
            if filters.get('question_subtype'):
                query = query.filter(GoldenQuestion.question_subtype == filters['question_subtype'])
            
            if filters.get('methodology_tags'):
                methodology_tags = filters['methodology_tags']
                query = query.filter(GoldenQuestion.methodology_tags.op('&&')(methodology_tags))
            
            if filters.get('industry'):
                industry_keyword = filters['industry'].lower()
                query = query.filter(
                    func.array_to_string(GoldenQuestion.industry_keywords, ' ').ilike(f'%{industry_keyword}%')
                )
            
            if filters.get('min_quality_score') is not None:
                query = query.filter(GoldenQuestion.quality_score >= filters['min_quality_score'])
            
            if filters.get('human_verified') is not None:
                query = query.filter(GoldenQuestion.human_verified == filters['human_verified'])
            
            if filters.get('search'):
                search_term = f"%{filters['search']}%"
                query = query.filter(GoldenQuestion.question_text.ilike(search_term))
            
            # Order by usage count descending, then by quality score
            query = query.order_by(desc(GoldenQuestion.usage_count), desc(GoldenQuestion.quality_score))
            
            # Apply pagination
            questions = query.offset(skip).limit(limit).all()
            
            logger.info(f"✅ [GoldenContentService] Found {len(questions)} questions")
            return questions
            
        except Exception as e:
            logger.error(f"❌ [GoldenContentService] Failed to list questions: {str(e)}", exc_info=True)
            raise UserFriendlyError(
                message="Failed to retrieve golden questions",
                technical_details=str(e),
                action_required="Please try again or contact support if the issue persists"
            )
    
    async def get_question(self, question_id: UUID) -> Optional[GoldenQuestion]:
        """
        Get a single golden question by ID
        """
        try:
            logger.info(f"🔍 [GoldenContentService] Getting question: {question_id}")
            
            question = self.db.query(GoldenQuestion).filter(GoldenQuestion.id == question_id).first()
            
            if question:
                logger.info(f"✅ [GoldenContentService] Found question: {question_id}")
            else:
                logger.warning(f"⚠️ [GoldenContentService] Question not found: {question_id}")
            
            return question
            
        except Exception as e:
            logger.error(f"❌ [GoldenContentService] Failed to get question {question_id}: {str(e)}", exc_info=True)
            raise UserFriendlyError(
                message="Failed to retrieve golden question",
                technical_details=str(e),
                action_required="Please try again or contact support if the issue persists"
            )
    
    async def update_question(
        self, 
        question_id: UUID, 
        updates: Dict[str, Any]
    ) -> Optional[GoldenQuestion]:
        """
        Update a golden question
        """
        try:
            logger.info(f"🔧 [GoldenContentService] Updating question {question_id} with: {updates}")
            
            question = self.db.query(GoldenQuestion).filter(GoldenQuestion.id == question_id).first()
            
            if not question:
                logger.warning(f"⚠️ [GoldenContentService] Question not found for update: {question_id}")
                return None
            
            # Update fields
            for key, value in updates.items():
                if hasattr(question, key):
                    setattr(question, key, value)
                    logger.info(f"🔧 [GoldenContentService] Updated {key} to: {value}")
                else:
                    logger.warning(f"⚠️ [GoldenContentService] Unknown field: {key}")
            
            # Commit changes
            self.db.commit()
            self.db.refresh(question)
            
            logger.info(f"✅ [GoldenContentService] Successfully updated question: {question_id}")
            return question
            
        except Exception as e:
            logger.error(f"❌ [GoldenContentService] Failed to update question {question_id}: {str(e)}", exc_info=True)
            self.db.rollback()
            raise UserFriendlyError(
                message="Failed to update golden question",
                technical_details=str(e),
                action_required="Please try again or contact support if the issue persists"
            )
    
    async def delete_question(self, question_id: UUID) -> bool:
        """
        Delete a golden question
        """
        try:
            logger.info(f"🗑️ [GoldenContentService] Deleting question: {question_id}")
            
            question = self.db.query(GoldenQuestion).filter(GoldenQuestion.id == question_id).first()
            
            if not question:
                logger.warning(f"⚠️ [GoldenContentService] Question not found for deletion: {question_id}")
                return False
            
            self.db.delete(question)
            self.db.commit()
            
            logger.info(f"✅ [GoldenContentService] Successfully deleted question: {question_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ [GoldenContentService] Failed to delete question {question_id}: {str(e)}", exc_info=True)
            self.db.rollback()
            raise UserFriendlyError(
                message="Failed to delete golden question",
                technical_details=str(e),
                action_required="Please try again or contact support if the issue persists"
            )
    
    async def get_analytics(self) -> Dict[str, Any]:
        """
        Get analytics for golden content usage and quality
        """
        try:
            logger.info("📊 [GoldenContentService] Generating analytics")
            
            # Section analytics
            total_sections = self.db.query(GoldenSection).count()
            human_verified_sections = self.db.query(GoldenSection).filter(GoldenSection.human_verified == True).count()
            avg_section_quality = self.db.query(func.avg(GoldenSection.quality_score)).scalar() or 0.0
            
            # Question analytics
            total_questions = self.db.query(GoldenQuestion).count()
            human_verified_questions = self.db.query(GoldenQuestion).filter(GoldenQuestion.human_verified == True).count()
            avg_question_quality = self.db.query(func.avg(GoldenQuestion.quality_score)).scalar() or 0.0
            
            # Top section types
            top_section_types = (
                self.db.query(
                    GoldenSection.section_type,
                    func.count(GoldenSection.id).label('count')
                )
                .filter(GoldenSection.section_type.isnot(None))
                .group_by(GoldenSection.section_type)
                .order_by(desc('count'))
                .limit(10)
                .all()
            )
            
            # Top question types
            top_question_types = (
                self.db.query(
                    GoldenQuestion.question_type,
                    func.count(GoldenQuestion.id).label('count')
                )
                .filter(GoldenQuestion.question_type.isnot(None))
                .group_by(GoldenQuestion.question_type)
                .order_by(desc('count'))
                .limit(10)
                .all()
            )
            
            # Methodology coverage (sections)
            section_methodologies = (
                self.db.query(
                    func.unnest(GoldenSection.methodology_tags).label('methodology'),
                    func.count().label('count')
                )
                .filter(GoldenSection.methodology_tags.isnot(None))
                .group_by('methodology')
                .order_by(desc('count'))
                .all()
            )
            
            # Industry coverage (sections)
            section_industries = (
                self.db.query(
                    func.unnest(GoldenSection.industry_keywords).label('industry'),
                    func.count().label('count')
                )
                .filter(GoldenSection.industry_keywords.isnot(None))
                .group_by('industry')
                .order_by(desc('count'))
                .all()
            )
            
            analytics = {
                'total_sections': total_sections,
                'total_questions': total_questions,
                'human_verified_sections': human_verified_sections,
                'human_verified_questions': human_verified_questions,
                'avg_section_quality': float(avg_section_quality),
                'avg_question_quality': float(avg_question_quality),
                'top_section_types': [
                    {'type': item.section_type, 'count': item.count}
                    for item in top_section_types
                ],
                'top_question_types': [
                    {'type': item.question_type, 'count': item.count}
                    for item in top_question_types
                ],
                'methodology_coverage': {
                    item.methodology: item.count
                    for item in section_methodologies
                },
                'industry_coverage': {
                    item.industry: item.count
                    for item in section_industries
                }
            }
            
            logger.info(f"✅ [GoldenContentService] Generated analytics: {total_sections} sections, {total_questions} questions")
            return analytics
            
        except Exception as e:
            logger.error(f"❌ [GoldenContentService] Failed to generate analytics: {str(e)}", exc_info=True)
            raise UserFriendlyError(
                message="Failed to generate analytics",
                technical_details=str(e),
                action_required="Please try again or contact support if the issue persists"
            )
