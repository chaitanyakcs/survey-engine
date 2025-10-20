"""
Multi-Level RAG Service for Section and Question Retrieval

This service handles:
1. Extracting sections and questions from golden survey pairs
2. Generating embeddings for sections and questions
3. Storing them in golden_sections and golden_questions tables
4. Retrieving sections and questions based on similarity
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from src.database.models import GoldenRFQSurveyPair, GoldenSection, GoldenQuestion, SectionAnnotation, QuestionAnnotation
from src.services.embedding_service import EmbeddingService
import uuid
import hashlib

logger = logging.getLogger(__name__)


class MultiLevelRAGService:
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService()
    
    async def extract_and_index_sections_questions(self, golden_pair_id: str) -> Dict[str, int]:
        """
        Extract sections and questions from a golden pair and create embeddings
        
        Args:
            golden_pair_id: UUID of the golden pair to process
            
        Returns:
            Dict with counts of sections and questions created
        """
        logger.info(f"🔍 [MultiLevelRAG] Starting extraction for golden pair {golden_pair_id}")
        
        # Get the golden pair
        golden_pair = self.db.query(GoldenRFQSurveyPair).filter(
            GoldenRFQSurveyPair.id == golden_pair_id
        ).first()
        
        if not golden_pair:
            logger.error(f"❌ [MultiLevelRAG] Golden pair {golden_pair_id} not found")
            return {"sections_created": 0, "questions_created": 0}
        
        survey_json = golden_pair.survey_json
        if not survey_json or 'sections' not in survey_json:
            logger.warning(f"⚠️ [MultiLevelRAG] No sections found in golden pair {golden_pair_id}")
            return {"sections_created": 0, "questions_created": 0}
        
        sections_created = 0
        questions_created = 0
        
        try:
            # Process each section
            for section_idx, section in enumerate(survey_json['sections']):
                section_id = f"{golden_pair_id}_section_{section_idx}"
                section_title = section.get('title', f'Section {section_idx + 1}')
                section_text = self._extract_section_text(section)
                
                if not section_text.strip():
                    logger.warning(f"⚠️ [MultiLevelRAG] Empty section text for section {section_idx}")
                    continue
                
                # Generate section embedding
                section_embedding = await self.embedding_service.get_embedding(section_text)
                
                # Determine section type
                section_type = self._classify_section_type(section_title, section_text)
                
                # Get methodology tags for this section
                methodology_tags = self._extract_section_methodology_tags(section)
                
                # Calculate quality score from annotations
                quality_score = 0.5  # Default score - skip annotation lookup for now
                
                # Create golden section
                golden_section = GoldenSection(
                    section_id=section_id,
                    survey_id=str(golden_pair.id),  # Use golden_pair.id as survey_id
                    golden_pair_id=golden_pair.id,  # Use UUID object directly
                    section_title=section_title,
                    section_text=section_text,
                    section_embedding=section_embedding,
                    section_type=section_type,
                    methodology_tags=methodology_tags,
                    quality_score=quality_score,
                    human_verified=golden_pair.human_verified,
                    labels={}
                )
                
                self.db.add(golden_section)
                sections_created += 1
                
                # Process questions in this section
                if 'questions' in section:
                    for question_idx, question in enumerate(section['questions']):
                        question_id = f"{section_id}_question_{question_idx}"
                        question_text = self._extract_question_text(question)
                        
                        if not question_text.strip():
                            continue
                        
                        # Generate question embedding
                        question_embedding = await self.embedding_service.get_embedding(question_text)
                        
                        # Determine question type
                        question_type = self._classify_question_type(question)
                        
                        # Get methodology tags for this question
                        question_methodology_tags = self._extract_question_methodology_tags(question)
                        
                        # Calculate quality score from annotations
                        question_quality_score = 0.5  # Default score - skip annotation lookup for now
                        
                        # Create golden question
                        golden_question = GoldenQuestion(
                            question_id=question_id,
                            survey_id=str(golden_pair.id),  # Use golden_pair.id as survey_id
                            golden_pair_id=golden_pair.id,  # Use UUID object directly
                            section_id=section_id,
                            question_text=question_text,
                            question_embedding=question_embedding,
                            question_type=question_type,
                            methodology_tags=question_methodology_tags,
                            quality_score=question_quality_score,
                            human_verified=golden_pair.human_verified,
                            labels={}
                        )
                        
                        self.db.add(golden_question)
                        questions_created += 1
            
            self.db.commit()
            logger.info(f"✅ [MultiLevelRAG] Created {sections_created} sections and {questions_created} questions")
            
            return {
                "sections_created": sections_created,
                "questions_created": questions_created
            }
            
        except Exception as e:
            logger.error(f"❌ [MultiLevelRAG] Error processing golden pair {golden_pair_id}: {str(e)}")
            self.db.rollback()
            raise
    
    def _extract_section_text(self, section: Dict[str, Any]) -> str:
        """Extract text content from a section"""
        text_parts = []
        
        # Add section title
        if section.get('title'):
            text_parts.append(section['title'])
        
        # Add section description
        if section.get('description'):
            text_parts.append(section['description'])
        
        # Add instruction text
        if section.get('instruction'):
            text_parts.append(section['instruction'])
        
        # Add question texts
        if 'questions' in section:
            for question in section['questions']:
                if question.get('text'):
                    text_parts.append(question['text'])
        
        return " ".join(text_parts)
    
    def _extract_question_text(self, question: Dict[str, Any]) -> str:
        """Extract text content from a question"""
        text_parts = []
        
        # Add question text
        if question.get('text'):
            text_parts.append(question['text'])
        
        # Add question instruction
        if question.get('instruction'):
            text_parts.append(question['instruction'])
        
        # Add option texts
        if 'options' in question:
            for option in question['options']:
                if isinstance(option, dict) and option.get('text'):
                    text_parts.append(option['text'])
                elif isinstance(option, str):
                    text_parts.append(option)
        
        return " ".join(text_parts)
    
    def _classify_section_type(self, title: str, text: str) -> str:
        """Classify section type based on title and content"""
        title_lower = title.lower()
        text_lower = text.lower()
        
        # Demographics
        if any(keyword in title_lower for keyword in ['demographic', 'profile', 'background', 'about you']):
            return 'demographics'
        
        # Pricing
        if any(keyword in title_lower for keyword in ['price', 'pricing', 'cost', 'value', 'willing to pay']):
            return 'pricing'
        
        # Satisfaction
        if any(keyword in title_lower for keyword in ['satisfaction', 'experience', 'rating', 'feedback']):
            return 'satisfaction'
        
        # Product features
        if any(keyword in title_lower for keyword in ['feature', 'attribute', 'characteristic', 'benefit']):
            return 'product_features'
        
        # Brand perception
        if any(keyword in title_lower for keyword in ['brand', 'reputation', 'image', 'perception']):
            return 'brand_perception'
        
        # Purchase intent
        if any(keyword in title_lower for keyword in ['purchase', 'buy', 'intent', 'consideration']):
            return 'purchase_intent'
        
        return 'general'
    
    def _classify_question_type(self, question: Dict[str, Any]) -> str:
        """Classify question type based on structure"""
        if 'options' in question and question['options']:
            if len(question['options']) == 2:
                return 'yes_no'
            elif len(question['options']) <= 5:
                return 'multiple_choice'
            else:
                return 'multiple_choice_many'
        elif 'scale' in question or 'rating' in question:
            return 'rating_scale'
        else:
            return 'open_text'
    
    def _extract_section_methodology_tags(self, section: Dict[str, Any]) -> List[str]:
        """Extract methodology tags from section"""
        tags = []
        
        # Check for methodology indicators in section
        section_text = self._extract_section_text(section).lower()
        
        if 'van westendorp' in section_text or 'vw' in section_text:
            tags.append('van_westendorp')
        if 'gabor granger' in section_text or 'gg' in section_text:
            tags.append('gabor_granger')
        if 'conjoint' in section_text or 'cbc' in section_text:
            tags.append('conjoint')
        if 'maxdiff' in section_text:
            tags.append('maxdiff')
        if 'nps' in section_text:
            tags.append('nps')
        if 'csat' in section_text:
            tags.append('csat')
        
        return tags
    
    def _extract_question_methodology_tags(self, question: Dict[str, Any]) -> List[str]:
        """Extract methodology tags from question"""
        tags = []
        
        question_text = self._extract_question_text(question).lower()
        
        if 'van westendorp' in question_text or 'vw' in question_text:
            tags.append('van_westendorp')
        if 'gabor granger' in question_text or 'gg' in question_text:
            tags.append('gabor_granger')
        if 'conjoint' in question_text or 'cbc' in question_text:
            tags.append('conjoint')
        if 'maxdiff' in question_text:
            tags.append('maxdiff')
        if 'nps' in question_text:
            tags.append('nps')
        if 'csat' in question_text:
            tags.append('csat')
        
        return tags
    
    async def _calculate_section_quality_score(self, survey_id: str, section_id: str) -> float:
        """Calculate quality score from section annotations"""
        annotations = self.db.query(SectionAnnotation).filter(
            SectionAnnotation.survey_id == survey_id,
            SectionAnnotation.section_id == section_id
        ).all()
        
        if not annotations:
            return 0.5  # Default score if no annotations
        
        # Calculate average quality score
        total_score = 0
        count = 0
        
        for annotation in annotations:
            # Use weighted average of all pillar scores
            pillar_scores = [
                annotation.methodological_rigor,
                annotation.content_validity,
                annotation.respondent_experience,
                annotation.analytical_value,
                annotation.business_impact
            ]
            avg_pillar_score = sum(pillar_scores) / len(pillar_scores)
            total_score += avg_pillar_score
            count += 1
        
        return total_score / count if count > 0 else 0.5
    
    async def _calculate_question_quality_score(self, survey_id: str, question_id: str) -> float:
        """Calculate quality score from question annotations"""
        annotations = self.db.query(QuestionAnnotation).filter(
            QuestionAnnotation.survey_id == survey_id,
            QuestionAnnotation.question_id == question_id
        ).all()
        
        if not annotations:
            return 0.5  # Default score if no annotations
        
        # Calculate average quality score
        total_score = 0
        count = 0
        
        for annotation in annotations:
            # Use weighted average of all pillar scores
            pillar_scores = [
                annotation.methodological_rigor,
                annotation.content_validity,
                annotation.respondent_experience,
                annotation.analytical_value,
                annotation.business_impact
            ]
            avg_pillar_score = sum(pillar_scores) / len(pillar_scores)
            total_score += avg_pillar_score
            count += 1
        
        return total_score / count if count > 0 else 0.5
    
    async def retrieve_golden_sections(
        self,
        embedding: List[float],
        section_type: Optional[str] = None,
        methodology_tags: Optional[List[str]] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve golden sections based on similarity"""
        logger.info(f"🔍 [MultiLevelRAG] Retrieving golden sections (type: {section_type}, limit: {limit})")
        
        try:
            from pgvector.sqlalchemy import Vector
            
            # Base query with cosine distance
            try:
                similarity_expr = GoldenSection.section_embedding.cosine_distance(embedding)
            except Exception as e:
                logger.warning(f"⚠️ [MultiLevelRAG] cosine_distance not available, using l2_distance: {e}")
                similarity_expr = GoldenSection.section_embedding.l2_distance(embedding)
            
            query = self.db.query(
                GoldenSection.id,
                GoldenSection.section_id,
                GoldenSection.survey_id,
                GoldenSection.section_title,
                GoldenSection.section_text,
                GoldenSection.section_type,
                GoldenSection.methodology_tags,
                GoldenSection.quality_score,
                GoldenSection.human_verified,
                similarity_expr.label('similarity')
            ).filter(GoldenSection.section_embedding.is_not(None))
            
            # Filter by section type if specified
            if section_type:
                query = query.filter(GoldenSection.section_type == section_type)
            
            # Filter by methodology tags if specified
            if methodology_tags:
                query = query.filter(GoldenSection.methodology_tags.overlap(methodology_tags))
            
            # Order by human verification first, then similarity
            query = query.order_by(
                GoldenSection.human_verified.desc(),
                'similarity'
            ).limit(limit)
            
            rows = query.all()
            logger.info(f"🔍 [MultiLevelRAG] Found {len(rows)} golden sections")
            
            sections = []
            for row in rows:
                # Apply human verification boost
                human_verification_boost = 0.0
                if row.human_verified:
                    human_verification_boost = 0.3  # 30% boost for human-verified sections
                
                final_score = float(row.similarity) + human_verification_boost
                
                sections.append({
                    "id": str(row.id),
                    "section_id": row.section_id,
                    "survey_id": row.survey_id,
                    "section_title": row.section_title,
                    "section_text": row.section_text,
                    "section_type": row.section_type,
                    "methodology_tags": row.methodology_tags,
                    "quality_score": float(row.quality_score) if row.quality_score else 0.5,
                    "human_verified": row.human_verified,
                    "similarity": float(row.similarity),
                    "final_score": final_score
                })
            
            # Sort by final score (lower is better for distance)
            sections.sort(key=lambda x: x['final_score'])
            
            return sections[:limit]
            
        except Exception as e:
            logger.error(f"❌ [MultiLevelRAG] Error retrieving golden sections: {str(e)}")
            return []
    
    async def retrieve_golden_questions(
        self,
        embedding: List[float],
        question_type: Optional[str] = None,
        methodology_tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve golden questions based on similarity"""
        logger.info(f"🔍 [MultiLevelRAG] Retrieving golden questions (type: {question_type}, limit: {limit})")
        
        try:
            from pgvector.sqlalchemy import Vector
            
            # Base query with cosine distance
            try:
                similarity_expr = GoldenQuestion.question_embedding.cosine_distance(embedding)
            except Exception as e:
                logger.warning(f"⚠️ [MultiLevelRAG] cosine_distance not available, using l2_distance: {e}")
                similarity_expr = GoldenQuestion.question_embedding.l2_distance(embedding)
            
            query = self.db.query(
                GoldenQuestion.id,
                GoldenQuestion.question_id,
                GoldenQuestion.survey_id,
                GoldenQuestion.section_id,
                GoldenQuestion.question_text,
                GoldenQuestion.question_type,
                GoldenQuestion.methodology_tags,
                GoldenQuestion.quality_score,
                GoldenQuestion.human_verified,
                similarity_expr.label('similarity')
            ).filter(GoldenQuestion.question_embedding.is_not(None))
            
            # Filter by question type if specified
            if question_type:
                query = query.filter(GoldenQuestion.question_type == question_type)
            
            # Filter by methodology tags if specified
            if methodology_tags:
                query = query.filter(GoldenQuestion.methodology_tags.overlap(methodology_tags))
            
            # Order by human verification first, then similarity
            query = query.order_by(
                GoldenQuestion.human_verified.desc(),
                'similarity'
            ).limit(limit)
            
            rows = query.all()
            logger.info(f"🔍 [MultiLevelRAG] Found {len(rows)} golden questions")
            
            questions = []
            for row in rows:
                # Apply human verification boost
                human_verification_boost = 0.0
                if row.human_verified:
                    human_verification_boost = 0.3  # 30% boost for human-verified questions
                
                final_score = float(row.similarity) + human_verification_boost
                
                questions.append({
                    "id": str(row.id),
                    "question_id": row.question_id,
                    "survey_id": row.survey_id,
                    "section_id": row.section_id,
                    "question_text": row.question_text,
                    "question_type": row.question_type,
                    "methodology_tags": row.methodology_tags,
                    "quality_score": float(row.quality_score) if row.quality_score else 0.5,
                    "human_verified": row.human_verified,
                    "similarity": float(row.similarity),
                    "final_score": final_score
                })
            
            # Sort by final score (lower is better for distance)
            questions.sort(key=lambda x: x['final_score'])
            
            return questions[:limit]
            
        except Exception as e:
            logger.error(f"❌ [MultiLevelRAG] Error retrieving golden questions: {str(e)}")
            return []
