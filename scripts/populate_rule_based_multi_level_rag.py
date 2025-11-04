#!/usr/bin/env python3
"""
Populate rule-based multi-level RAG tables from existing golden pairs
Extracts sections and questions without requiring embeddings
"""

import asyncio
import sys
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.database.connection import SessionLocal
from src.database.models import GoldenRFQSurveyPair, GoldenSection, GoldenQuestion, Survey, QuestionAnnotation, SectionAnnotation
from src.utils.database_session_manager import DatabaseSessionManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RuleBasedRAGPopulator:
    """
    Populate rule-based multi-level RAG tables from golden pairs
    """
    
    def __init__(self, db_session):
        self.db = db_session
        
        # Section type detection patterns
        self.section_type_patterns = {
            'demographics': ['demographic', 'about you', 'personal information', 'background', 'profile', 'respondent'],
            'satisfaction': ['satisfaction', 'satisfied', 'experience', 'feedback', 'rating', 'nps'],
            'pricing': ['pricing', 'price', 'cost', 'value', 'budget', 'payment', 'willingness to pay'],
            'behavioral': ['behavior', 'behaviour', 'usage', 'habits', 'patterns', 'activities', 'frequency'],
            'preferences': ['preference', 'prefer', 'choice', 'option', 'favorite', 'favourite', 'ranking'],
            'intent': ['intent', 'intention', 'plan', 'consider', 'likely', 'probability', 'future'],
            'awareness': ['awareness', 'aware', 'know', 'familiar', 'recognition', 'heard of'],
            'loyalty': ['loyalty', 'loyal', 'recommend', 'advocate', 'promoter', 'repeat']
        }
        
        # Question type detection patterns
        self.question_type_patterns = {
            'multiple_choice': ['which', 'what is your', 'select', 'choose', 'option'],
            'rating_scale': ['rate', 'scale', 'satisfied', 'likely', 'important', 'agree', 'disagree'],
            'open_text': ['describe', 'explain', 'tell us', 'comments', 'thoughts', 'opinion'],
            'yes_no': ['do you', 'have you', 'are you', 'will you', 'would you'],
            'demographic': ['age', 'gender', 'income', 'education', 'location', 'occupation']
        }
        
        # Methodology detection patterns
        self.methodology_patterns = {
            'quantitative': ['rating', 'scale', 'score', 'number', 'percentage', 'statistical', 'numeric'],
            'qualitative': ['describe', 'explain', 'tell us', 'opinion', 'thoughts', 'comments', 'open'],
            'mixed_methods': ['both', 'combination', 'mix', 'quantitative and qualitative']
        }
    
    async def populate_multi_level_rag(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Populate golden_sections and golden_questions from multiple sources:
        1. Golden pairs (highest priority)
        2. Surveys with annotations (high priority)
        3. Surveys with quality scores (medium priority)
        4. All other surveys (low priority)
        """
        logger.info("🔍 [RuleBasedRAGPopulator] Starting comprehensive multi-level RAG population")
        
        stats = {
            'golden_pairs_processed': 0,
            'annotated_surveys_processed': 0,
            'quality_surveys_processed': 0,
            'other_surveys_processed': 0,
            'sections_created': 0,
            'questions_created': 0,
            'errors': []
        }
        
        try:
            # 1. Process golden pairs (highest priority)
            golden_pairs = DatabaseSessionManager.safe_query(
                self.db,
                lambda: self.db.query(GoldenRFQSurveyPair).all(),
                fallback_value=[],
                operation_name="get all golden pairs"
            )
            
            logger.info(f"📊 Found {len(golden_pairs)} golden pairs to process")
            
            for golden_pair in golden_pairs:
                try:
                    stats['golden_pairs_processed'] += 1
                    
                    if not golden_pair.survey_json:
                        logger.warning(f"⚠️ Golden pair {golden_pair.id} has no survey_json, skipping")
                        continue
                    
                    # Extract sections and questions
                    sections_created = await self._extract_sections(golden_pair, dry_run)
                    questions_created = await self._extract_questions(golden_pair, dry_run)
                    
                    stats['sections_created'] += sections_created
                    stats['questions_created'] += questions_created
                    
                    logger.info(f"✅ Processed golden pair {golden_pair.id}: {sections_created} sections, {questions_created} questions")
                    
                except Exception as e:
                    error_msg = f"Error processing golden pair {golden_pair.id}: {str(e)}"
                    logger.error(f"❌ {error_msg}")
                    stats['errors'].append(error_msg)
            
            # 2. Process surveys with annotations (high priority)
            annotated_surveys = DatabaseSessionManager.safe_query(
                self.db,
                lambda: self.db.query(Survey).join(QuestionAnnotation).filter(
                    Survey.final_output.isnot(None)
                ).distinct().all(),
                fallback_value=[],
                operation_name="get surveys with annotations"
            )
            
            logger.info(f"📊 Found {len(annotated_surveys)} surveys with annotations to process")
            
            for survey in annotated_surveys:
                try:
                    stats['annotated_surveys_processed'] += 1
                    
                    if not survey.final_output:
                        logger.warning(f"⚠️ Survey {survey.id} has no final_output, skipping")
                        continue
                    
                    # Extract sections and questions from survey
                    sections_created = await self._extract_sections_from_survey(survey, dry_run, priority='high')
                    questions_created = await self._extract_questions_from_survey(survey, dry_run, priority='high')
                    
                    stats['sections_created'] += sections_created
                    stats['questions_created'] += questions_created
                    
                    logger.info(f"✅ Processed annotated survey {survey.id}: {sections_created} sections, {questions_created} questions")
                    
                except Exception as e:
                    error_msg = f"Error processing annotated survey {survey.id}: {str(e)}"
                    logger.error(f"❌ {error_msg}")
                    stats['errors'].append(error_msg)
            
            # 3. Process surveys with quality scores (medium priority)
            quality_surveys = DatabaseSessionManager.safe_query(
                self.db,
                lambda: self.db.query(Survey).filter(
                    Survey.final_output.isnot(None),
                    Survey.golden_similarity_score.isnot(None),
                    Survey.golden_similarity_score > 0.7  # Only high-quality surveys
                ).all(),
                fallback_value=[],
                operation_name="get high-quality surveys"
            )
            
            logger.info(f"📊 Found {len(quality_surveys)} high-quality surveys to process")
            
            for survey in quality_surveys:
                try:
                    stats['quality_surveys_processed'] += 1
                    
                    if not survey.final_output:
                        logger.warning(f"⚠️ Survey {survey.id} has no final_output, skipping")
                        continue
                    
                    # Extract sections and questions from survey
                    sections_created = await self._extract_sections_from_survey(survey, dry_run, priority='medium')
                    questions_created = await self._extract_questions_from_survey(survey, dry_run, priority='medium')
                    
                    stats['sections_created'] += sections_created
                    stats['questions_created'] += questions_created
                    
                    logger.info(f"✅ Processed quality survey {survey.id}: {sections_created} sections, {questions_created} questions")
                    
                except Exception as e:
                    error_msg = f"Error processing quality survey {survey.id}: {str(e)}"
                    logger.error(f"❌ {error_msg}")
                    stats['errors'].append(error_msg)
            
            # 4. Process all other surveys (low priority)
            all_surveys = DatabaseSessionManager.safe_query(
                self.db,
                lambda: self.db.query(Survey).filter(
                    Survey.final_output.isnot(None)
                ).all(),
                fallback_value=[],
                operation_name="get all surveys"
            )
            
            # Filter out already processed surveys
            processed_survey_ids = {s.id for s in annotated_surveys + quality_surveys}
            other_surveys = [s for s in all_surveys if s.id not in processed_survey_ids]
            
            logger.info(f"📊 Found {len(other_surveys)} other surveys to process")
            
            for survey in other_surveys:
                try:
                    stats['other_surveys_processed'] += 1
                    
                    if not survey.final_output:
                        logger.warning(f"⚠️ Survey {survey.id} has no final_output, skipping")
                        continue
                    
                    # Extract sections and questions from survey
                    sections_created = await self._extract_sections_from_survey(survey, dry_run, priority='low')
                    questions_created = await self._extract_questions_from_survey(survey, dry_run, priority='low')
                    
                    stats['sections_created'] += sections_created
                    stats['questions_created'] += questions_created
                    
                    logger.info(f"✅ Processed other survey {survey.id}: {sections_created} sections, {questions_created} questions")
                    
                except Exception as e:
                    error_msg = f"Error processing other survey {survey.id}: {str(e)}"
                    logger.error(f"❌ {error_msg}")
                    stats['errors'].append(error_msg)
            
            if not dry_run:
                self.db.commit()
                logger.info("💾 Changes committed to database")
            
            logger.info(f"🎉 Rule-based multi-level RAG population completed!")
            logger.info(f"   - Golden pairs processed: {stats['golden_pairs_processed']}")
            logger.info(f"   - Sections created: {stats['sections_created']}")
            logger.info(f"   - Questions created: {stats['questions_created']}")
            logger.info(f"   - Errors: {len(stats['errors'])}")
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Multi-level RAG population failed: {str(e)}")
            stats['errors'].append(f"Population failed: {str(e)}")
            if not dry_run:
                self.db.rollback()
            return stats
    
    async def _extract_sections(self, golden_pair: GoldenRFQSurveyPair, dry_run: bool) -> int:
        """Extract sections from golden pair survey JSON"""
        sections_created = 0
        
        try:
            survey_data = golden_pair.survey_json
            # Handle both old and new JSON structures
            if 'final_output' in survey_data:
                sections = survey_data['final_output'].get('sections', [])
            else:
                sections = survey_data.get('sections', [])
            
            for section_data in sections:
                try:
                    section_id = section_data.get('id', f"section_{sections_created}")
                    section_title = section_data.get('title', '')
                    section_text = section_data.get('description', '')
                    
                    # Detect section type
                    section_type = self._detect_section_type(section_title + ' ' + section_text)
                    
                    # Extract methodology tags
                    methodology_tags = self._extract_methodology_tags(section_text)
                    
                    # Extract industry keywords
                    industry_keywords = self._extract_industry_keywords(section_text)
                    
                    # Extract question patterns
                    question_patterns = self._extract_question_patterns(section_text)
                    
                    if not dry_run:
                        # Create golden section
                        golden_section = GoldenSection(
                            section_id=section_id,
                            survey_id=str(golden_pair.id),
                            golden_pair_id=golden_pair.id,
                            section_title=section_title,
                            section_text=section_text,
                            section_type=section_type,
                            methodology_tags=methodology_tags,
                            industry_keywords=industry_keywords,
                            question_patterns=question_patterns,
                            quality_score=0.5,  # Default quality score
                            human_verified=False,
                            labels={}
                        )
                        
                        self.db.add(golden_section)
                    
                    sections_created += 1
                    
                except Exception as e:
                    logger.warning(f"⚠️ Error extracting section from {golden_pair.id}: {str(e)}")
            
        except Exception as e:
            logger.warning(f"⚠️ Error processing sections for {golden_pair.id}: {str(e)}")
        
        return sections_created
    
    async def _extract_questions(self, golden_pair: GoldenRFQSurveyPair, dry_run: bool) -> int:
        """Extract questions from golden pair survey JSON"""
        questions_created = 0
        
        # Initialize label normalizer
        from src.services.label_normalizer import LabelNormalizer
        label_normalizer = LabelNormalizer()
        
        try:
            survey_data = golden_pair.survey_json
            # Handle both old and new JSON structures
            if 'final_output' in survey_data:
                survey_data = survey_data['final_output']
            
            # Extract questions from both top-level and sections
            questions = []
            
            # Get top-level questions (legacy format)
            if 'questions' in survey_data:
                questions.extend(survey_data['questions'])
            
            # Get questions from sections (new format)
            if 'sections' in survey_data:
                for section in survey_data['sections']:
                    if 'questions' in section:
                        questions.extend(section['questions'])
            
            logger.info(f"📋 [RAGPopulator] Extracting {len(questions)} questions from golden pair {golden_pair.id}")
            
            for question_data in questions:
                try:
                    question_id = question_data.get('id', f"question_{questions_created}")
                    question_text = question_data.get('text', '')
                    question_type = question_data.get('type', '')
                    
                    # Extract and normalize labels
                    labels = question_data.get('labels', [])
                    if labels:
                        labels = label_normalizer.normalize_batch(labels)
                    
                    # Detect question type and subtype
                    detected_type, detected_subtype = self._detect_question_type(question_text, question_type)
                    
                    # Extract methodology tags
                    methodology_tags = self._extract_methodology_tags(question_text)
                    
                    # Extract industry keywords
                    industry_keywords = self._extract_industry_keywords(question_text)
                    
                    # Extract question patterns
                    question_patterns = self._extract_question_patterns(question_text)
                    
                    if not dry_run:
                        # Create golden question
                        golden_question = GoldenQuestion(
                            question_id=question_id,
                            survey_id=str(golden_pair.id),
                            golden_pair_id=golden_pair.id,
                            question_text=question_text,
                            question_type=detected_type,
                            question_subtype=detected_subtype,
                            methodology_tags=methodology_tags,
                            industry_keywords=industry_keywords,
                            question_patterns=question_patterns,
                            quality_score=0.5,  # Default quality score
                            human_verified=False,
                            labels=labels  # Use normalized labels
                        )
                        
                        self.db.add(golden_question)
                    
                    questions_created += 1
                    
                except Exception as e:
                    logger.warning(f"⚠️ Error extracting question from {golden_pair.id}: {str(e)}")
            
        except Exception as e:
            logger.warning(f"⚠️ Error processing questions for {golden_pair.id}: {str(e)}")
        
        return questions_created
    
    def _detect_section_type(self, text: str) -> str:
        """Detect section type from text"""
        text_lower = text.lower()
        
        for section_type, patterns in self.section_type_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                return section_type
        
        return 'general'
    
    def _detect_question_type(self, text: str, question_type: str) -> tuple[str, str]:
        """Detect question type and subtype from text"""
        text_lower = text.lower()
        
        # Check explicit question type first
        if question_type:
            if 'multiple' in question_type.lower() or 'choice' in question_type.lower():
                return 'multiple_choice', question_type.lower()
            elif 'rating' in question_type.lower() or 'scale' in question_type.lower():
                return 'rating_scale', question_type.lower()
            elif 'text' in question_type.lower() or 'open' in question_type.lower():
                return 'open_text', question_type.lower()
            elif 'yes' in question_type.lower() or 'no' in question_type.lower():
                return 'yes_no', question_type.lower()
        
        # Detect from text patterns
        for q_type, patterns in self.question_type_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                return q_type, 'detected'
        
        return 'general', 'unknown'
    
    def _extract_methodology_tags(self, text: str) -> List[str]:
        """Extract methodology tags from text"""
        text_lower = text.lower()
        tags = []
        
        for methodology, patterns in self.methodology_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                tags.append(methodology)
        
        return tags if tags else ['mixed_methods']
    
    def _extract_question_patterns(self, text: str) -> List[str]:
        """Extract question patterns from text"""
        text_lower = text.lower()
        patterns = []
        
        # Common question patterns
        if 'how often' in text_lower or 'frequency' in text_lower:
            patterns.append('frequency')
        if 'how much' in text_lower or 'how many' in text_lower:
            patterns.append('quantity')
        if 'how likely' in text_lower or 'probability' in text_lower:
            patterns.append('likelihood')
        if 'how important' in text_lower or 'priority' in text_lower:
            patterns.append('importance')
        if 'how satisfied' in text_lower or 'satisfaction' in text_lower:
            patterns.append('satisfaction')
        if 'how would you' in text_lower or 'preference' in text_lower:
            patterns.append('preference')
        if 'why' in text_lower or 'reason' in text_lower:
            patterns.append('reasoning')
        if 'when' in text_lower or 'timing' in text_lower:
            patterns.append('timing')
        if 'where' in text_lower or 'location' in text_lower:
            patterns.append('location')
        
        return patterns if patterns else ['general']
    
    async def _extract_sections_from_survey(self, survey: Survey, dry_run: bool = False, priority: str = 'medium') -> int:
        """Extract sections from a survey (not golden pair)"""
        try:
            # Surveys use final_output field, not survey_json
            survey_data = survey.final_output
            if not survey_data:
                logger.warning(f"⚠️ Survey {survey.id} has no final_output, skipping")
                return 0
            
            sections = survey_data.get('sections', [])
            
            sections_created = 0
            
            for i, section in enumerate(sections):
                if not isinstance(section, dict):
                    continue
                
                section_text = section.get('title', '') + ' ' + section.get('description', '')
                if not section_text.strip():
                    continue
                
                # Calculate quality score based on priority and survey quality
                base_quality = survey.golden_similarity_score or 0.5
                priority_multiplier = {'high': 1.2, 'medium': 1.0, 'low': 0.8}.get(priority, 1.0)
                quality_score = min(1.0, base_quality * priority_multiplier)
                
                if not dry_run:
                    golden_section = GoldenSection(
                        section_id=f"s_{i}_{survey.id}",
                        survey_id=str(survey.id),
                        golden_pair_id=None,  # Surveys don't have golden_pair_id
                        annotation_id=None,   # No annotation link for survey sections
                        section_title=section.get('title', ''),
                        section_text=section_text,
                        section_type=self._detect_section_type(section_text),
                        methodology_tags=self._extract_methodology_tags(section_text),
                        industry_keywords=self._extract_industry_keywords(section_text),
                        question_patterns=[],
                        quality_score=quality_score,
                        usage_count=0,
                        human_verified=False,
                        labels={},
                        created_at=survey.created_at or datetime.now()
                    )
                    
                    self.db.add(golden_section)
                
                sections_created += 1
            
            return sections_created
            
        except Exception as e:
            logger.error(f"❌ Error extracting sections from survey {survey.id}: {str(e)}")
            return 0
    
    async def _extract_questions_from_survey(self, survey: Survey, dry_run: bool = False, priority: str = 'medium') -> int:
        """Extract questions from a survey (not golden pair)"""
        try:
            # Surveys use final_output field, not survey_json
            survey_data = survey.final_output
            if not survey_data:
                logger.warning(f"⚠️ Survey {survey.id} has no final_output, skipping")
                return 0
            
            # Questions are nested within sections in survey structure
            all_questions = []
            sections = survey_data.get('sections', [])
            for section in sections:
                if isinstance(section, dict) and 'questions' in section:
                    section_questions = section['questions']
                    if isinstance(section_questions, list):
                        all_questions.extend(section_questions)
            
            questions = all_questions
            
            questions_created = 0
            
            for i, question in enumerate(questions):
                if not isinstance(question, dict):
                    continue
                
                question_text = question.get('text', '') or question.get('question', '')
                if not question_text.strip():
                    continue
                
                # Calculate quality score based on priority and survey quality
                base_quality = survey.golden_similarity_score or 0.5
                priority_multiplier = {'high': 1.2, 'medium': 1.0, 'low': 0.8}.get(priority, 1.0)
                quality_score = min(1.0, base_quality * priority_multiplier)
                
                if not dry_run:
                    question_type, question_subtype = self._detect_question_type(
                        question_text, 
                        question.get('type', '')
                    )
                    
                    golden_question = GoldenQuestion(
                        question_id=f"q_{i}_{survey.id}",
                        survey_id=str(survey.id),
                        golden_pair_id=None,  # Surveys don't have golden_pair_id
                        annotation_id=None,   # No annotation link for survey questions
                        question_text=question_text,
                        question_type=question_type,
                        question_subtype=question_subtype,
                        methodology_tags=self._extract_methodology_tags(question_text),
                        industry_keywords=self._extract_industry_keywords(question_text),
                        question_patterns=self._extract_question_patterns(question_text),
                        quality_score=quality_score,
                        usage_count=0,
                        human_verified=False,
                        labels={},
                        created_at=survey.created_at or datetime.now()
                    )
                    
                    self.db.add(golden_question)
                
                questions_created += 1
            
            return questions_created
            
        except Exception as e:
            logger.error(f"❌ Error extracting questions from survey {survey.id}: {str(e)}")
            return 0
    
    def _extract_industry_keywords(self, text: str) -> List[str]:
        """Extract industry keywords from text"""
        # Simple keyword extraction - can be enhanced
        industry_keywords = [
            'healthcare', 'finance', 'technology', 'retail', 'education', 'automotive',
            'fitness', 'food', 'travel', 'entertainment', 'real estate', 'insurance'
        ]
        
        text_lower = text.lower()
        found_keywords = []
        
        for keyword in industry_keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords
    
    def _extract_question_patterns(self, text: str) -> List[str]:
        """Extract question patterns from text"""
        patterns = []
        
        # Common question patterns
        if 'how satisfied' in text.lower():
            patterns.append('satisfaction_rating')
        if 'how likely' in text.lower():
            patterns.append('likelihood_rating')
        if 'how important' in text.lower():
            patterns.append('importance_rating')
        if 'recommend' in text.lower():
            patterns.append('recommendation')
        if 'prefer' in text.lower():
            patterns.append('preference')
        
        return patterns


async def populate_multi_level_rag(dry_run: bool = False) -> Dict[str, Any]:
    """
    Main function to populate rule-based multi-level RAG
    """
    db = SessionLocal()
    try:
        populator = RuleBasedRAGPopulator(db)
        return await populator.populate_multi_level_rag(dry_run=dry_run)
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Populate rule-based multi-level RAG tables")
    parser.add_argument("--dry-run", action="store_true", help="Run without making changes")
    
    args = parser.parse_args()
    
    result = asyncio.run(populate_multi_level_rag(dry_run=args.dry_run))
    
    print(f"\n📊 Population Results:")
    print(f"   Golden pairs processed: {result['golden_pairs_processed']}")
    print(f"   Sections created: {result['sections_created']}")
    print(f"   Questions created: {result['questions_created']}")
    print(f"   Errors: {len(result['errors'])}")
    
    if result['errors']:
        print(f"\n❌ Errors:")
        for error in result['errors']:
            print(f"   - {error}")
