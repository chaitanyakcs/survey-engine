#!/usr/bin/env python3
"""
Annotation Insights Service
Extracts quality patterns from annotation data to improve survey generation
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from src.database.models import QuestionAnnotation, SectionAnnotation, SurveyAnnotation, GoldenRFQSurveyPair
from src.utils.database_session_manager import DatabaseSessionManager
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AnnotationInsightsService:
    """Service for extracting insights from annotation data"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def extract_quality_patterns(self) -> Dict[str, Any]:
        """
        Extract high-quality and low-quality patterns from annotations
        
        Returns:
            Dict containing high-quality patterns, low-quality patterns, and common issues
        """
        logger.info("🔍 [AnnotationInsights] Starting quality pattern extraction")
        
        try:
            # Get all annotations with proper session management
            question_annotations = DatabaseSessionManager.safe_query(
                self.db,
                lambda: self.db.query(QuestionAnnotation).all(),
                fallback_value=[],
                operation_name="question annotations query"
            )
            
            section_annotations = DatabaseSessionManager.safe_query(
                self.db,
                lambda: self.db.query(SectionAnnotation).all(),
                fallback_value=[],
                operation_name="section annotations query"
            )
            
            survey_annotations = DatabaseSessionManager.safe_query(
                self.db,
                lambda: self.db.query(SurveyAnnotation).all(),
                fallback_value=[],
                operation_name="survey annotations query"
            )
            
            logger.info(f"📊 [AnnotationInsights] Found {len(question_annotations)} question annotations, {len(section_annotations)} section annotations, {len(survey_annotations)} survey annotations")
            
            # Extract patterns
            high_quality_patterns = await self._extract_high_quality_patterns(question_annotations, section_annotations)
            low_quality_patterns = await self._extract_low_quality_patterns(question_annotations, section_annotations)
            common_issues = await self._extract_common_issues(question_annotations, section_annotations, survey_annotations)
            
            insights = {
                "high_quality_patterns": high_quality_patterns,
                "low_quality_patterns": low_quality_patterns,
                "common_issues": common_issues,
                "summary": {
                    "total_annotations": len(question_annotations) + len(section_annotations) + len(survey_annotations),
                    "high_quality_count": len([qa for qa in question_annotations if self._get_average_score(qa) >= 4.0]),
                    "low_quality_count": len([qa for qa in question_annotations if self._get_average_score(qa) < 3.0])
                }
            }
            
            logger.info(f"✅ [AnnotationInsights] Pattern extraction complete: {len(high_quality_patterns)} high-quality patterns, {len(low_quality_patterns)} low-quality patterns, {len(common_issues)} common issues")
            return insights
            
        except Exception as e:
            logger.error(f"❌ [AnnotationInsights] Failed to extract quality patterns: {str(e)}", exc_info=True)
            return {
                "high_quality_patterns": {},
                "low_quality_patterns": {},
                "common_issues": [],
                "summary": {"error": str(e)}
            }
    
    async def _extract_high_quality_patterns(self, question_annotations: List[QuestionAnnotation], section_annotations: List[SectionAnnotation]) -> Dict[str, Any]:
        """Extract patterns from high-quality annotations (score ≥4.0)"""
        logger.info("🔍 [AnnotationInsights] Extracting high-quality patterns")
        
        high_quality_questions = [qa for qa in question_annotations if self._get_average_score(qa) >= 4.0]
        high_quality_sections = [sa for sa in section_annotations if self._get_average_score(sa) >= 4.0]
        
        patterns = {
            "question_patterns": {},
            "section_patterns": {},
            "scale_designs": {},
            "phrasing_patterns": {},
            "structural_patterns": {}
        }
        
        # Analyze high-quality questions
        for qa in high_quality_questions:
            # Get the actual question text from the survey
            question_text = await self._get_question_text(qa.question_id, qa.survey_id)
            if question_text:
                # Extract question type
                question_type = self._classify_question_type(question_text)
                if question_type not in patterns["question_patterns"]:
                    patterns["question_patterns"][question_type] = []
                patterns["question_patterns"][question_type].append({
                    "text": question_text,
                    "score": self._get_average_score(qa),
                    "comment": qa.comment
                })
                
                # Extract phrasing patterns
                phrasing = self._extract_phrasing_patterns(question_text)
                for pattern in phrasing:
                    if pattern not in patterns["phrasing_patterns"]:
                        patterns["phrasing_patterns"][pattern] = []
                    patterns["phrasing_patterns"][pattern].append({
                        "example": question_text,
                        "score": self._get_average_score(qa)
                    })
        
        # Analyze high-quality sections
        for sa in high_quality_sections:
            # Get section structure
            section_structure = await self._get_section_structure(sa.section_id, sa.survey_id)
            if section_structure:
                structure_type = self._classify_section_structure(section_structure)
                if structure_type not in patterns["section_patterns"]:
                    patterns["section_patterns"][structure_type] = []
                patterns["section_patterns"][structure_type].append({
                    "structure": section_structure,
                    "score": self._get_average_score(sa),
                    "comment": sa.comment
                })
        
        # Extract scale design patterns
        patterns["scale_designs"] = self._extract_scale_patterns(high_quality_questions)
        
        logger.info(f"✅ [AnnotationInsights] Extracted {len(patterns['question_patterns'])} question patterns, {len(patterns['section_patterns'])} section patterns")
        return patterns
    
    async def _extract_low_quality_patterns(self, question_annotations: List[QuestionAnnotation], section_annotations: List[SectionAnnotation]) -> Dict[str, Any]:
        """Extract patterns from low-quality annotations (score <3.0)"""
        logger.info("🔍 [AnnotationInsights] Extracting low-quality patterns")
        
        low_quality_questions = [qa for qa in question_annotations if self._get_average_score(qa) < 3.0]
        low_quality_sections = [sa for sa in section_annotations if self._get_average_score(sa) < 3.0]
        
        patterns = {
            "problematic_questions": [],
            "problematic_sections": [],
            "bias_words": [],
            "unclear_scales": [],
            "double_barreled": [],
            "too_complex": []
        }
        
        # Analyze low-quality questions
        for qa in low_quality_questions:
            question_text = await self._get_question_text(qa.question_id, qa.survey_id)
            if question_text:
                patterns["problematic_questions"].append({
                    "text": question_text,
                    "score": self._get_average_score(qa),
                    "comment": qa.comment,
                    "issues": self._identify_question_issues(question_text, qa.comment)
                })
                
                # Extract bias words
                bias_words = self._extract_bias_words(question_text)
                patterns["bias_words"].extend(bias_words)
                
                # Check for double-barreled questions
                if self._is_double_barreled(question_text):
                    patterns["double_barreled"].append(question_text)
                
                # Check for complexity
                if self._is_too_complex(question_text):
                    patterns["too_complex"].append(question_text)
        
        # Analyze low-quality sections
        for sa in low_quality_sections:
            section_structure = await self._get_section_structure(sa.section_id, sa.survey_id)
            if section_structure:
                patterns["problematic_sections"].append({
                    "structure": section_structure,
                    "score": self._get_average_score(sa),
                    "comment": sa.comment
                })
        
        # Remove duplicates and count frequencies
        patterns["bias_words"] = list(Counter(patterns["bias_words"]).most_common(10))
        patterns["double_barreled"] = list(set(patterns["double_barreled"]))
        patterns["too_complex"] = list(set(patterns["too_complex"]))
        
        logger.info(f"✅ [AnnotationInsights] Extracted {len(patterns['problematic_questions'])} problematic questions, {len(patterns['bias_words'])} bias words")
        return patterns
    
    async def _extract_common_issues(self, question_annotations: List[QuestionAnnotation], section_annotations: List[SectionAnnotation], survey_annotations: List[SurveyAnnotation]) -> List[Dict[str, Any]]:
        """Extract common issues from annotation comments"""
        logger.info("🔍 [AnnotationInsights] Extracting common issues from comments")
        
        all_comments = []
        
        # Collect all comments
        for qa in question_annotations:
            if qa.comment:
                all_comments.append(qa.comment)
        
        for sa in section_annotations:
            if sa.comment:
                all_comments.append(sa.comment)
        
        for sa in survey_annotations:
            if sa.overall_comment:
                all_comments.append(sa.overall_comment)
        
        # Analyze comments for common themes
        issue_patterns = defaultdict(int)
        issue_examples = defaultdict(list)
        
        for comment in all_comments:
            if comment:
                # Extract issue keywords
                issues = self._extract_issue_keywords(comment)
                for issue in issues:
                    issue_patterns[issue] += 1
                    issue_examples[issue].append(comment[:100] + "..." if len(comment) > 100 else comment)
        
        # Format as list of issues with frequency
        common_issues = []
        for issue, count in sorted(issue_patterns.items(), key=lambda x: x[1], reverse=True):
            common_issues.append({
                "issue": issue,
                "frequency": count,
                "examples": issue_examples[issue][:3]  # Top 3 examples
            })
        
        logger.info(f"✅ [AnnotationInsights] Extracted {len(common_issues)} common issues")
        return common_issues
    
    def _get_average_score(self, annotation) -> float:
        """Calculate average score from pillar ratings"""
        if hasattr(annotation, 'methodological_rigor'):
            scores = [
                annotation.methodological_rigor,
                annotation.content_validity,
                annotation.respondent_experience,
                annotation.analytical_value,
                annotation.business_impact
            ]
            return sum(scores) / len(scores)
        return 3.0
    
    async def _get_question_text(self, question_id: str, survey_id: str) -> Optional[str]:
        """Get question text from survey JSON"""
        try:
            # Get the survey JSON from golden pairs
            golden_pair = self.db.query(GoldenRFQSurveyPair).filter(
                GoldenRFQSurveyPair.id == survey_id
            ).first()
            
            if golden_pair and golden_pair.survey_json:
                survey_data = golden_pair.survey_json
                
                # Search for question in survey structure
                questions = survey_data.get("questions", [])
                for question in questions:
                    if str(question.get("id", "")) == question_id:
                        return question.get("text", "")
                
                # Search in sections
                sections = survey_data.get("sections", [])
                for section in sections:
                    section_questions = section.get("questions", [])
                    for question in section_questions:
                        if str(question.get("id", "")) == question_id:
                            return question.get("text", "")
            
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ [AnnotationInsights] Failed to get question text for {question_id}: {e}")
            return None
    
    async def _get_section_structure(self, section_id: int, survey_id: str) -> Optional[Dict[str, Any]]:
        """Get section structure from survey JSON"""
        try:
            golden_pair = self.db.query(GoldenRFQSurveyPair).filter(
                GoldenRFQSurveyPair.id == survey_id
            ).first()
            
            if golden_pair and golden_pair.survey_json:
                survey_data = golden_pair.survey_json
                sections = survey_data.get("sections", [])
                
                for section in sections:
                    if section.get("id") == section_id:
                        return {
                            "title": section.get("title", ""),
                            "question_count": len(section.get("questions", [])),
                            "question_types": [q.get("type", "") for q in section.get("questions", [])]
                        }
            
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ [AnnotationInsights] Failed to get section structure for {section_id}: {e}")
            return None
    
    def _classify_question_type(self, question_text: str) -> str:
        """Classify question type based on text"""
        text_lower = question_text.lower()
        
        if "how satisfied" in text_lower or "rate" in text_lower:
            return "rating_scale"
        elif "how likely" in text_lower or "recommend" in text_lower:
            return "nps_scale"
        elif "yes" in text_lower and "no" in text_lower:
            return "yes_no"
        elif "which" in text_lower or "what" in text_lower:
            return "multiple_choice"
        elif "price" in text_lower or "cost" in text_lower:
            return "pricing"
        elif "age" in text_lower or "gender" in text_lower:
            return "demographic"
        else:
            return "general"
    
    def _classify_section_structure(self, section_structure: Dict[str, Any]) -> str:
        """Classify section structure type"""
        question_count = section_structure.get("question_count", 0)
        question_types = section_structure.get("question_types", [])
        
        if question_count <= 2:
            return "short_section"
        elif question_count <= 5:
            return "medium_section"
        else:
            return "long_section"
    
    def _extract_phrasing_patterns(self, question_text: str) -> List[str]:
        """Extract common phrasing patterns from question text"""
        patterns = []
        text_lower = question_text.lower()
        
        # Common high-quality patterns
        if "how satisfied are you" in text_lower:
            patterns.append("satisfaction_question")
        if "how likely are you" in text_lower:
            patterns.append("likelihood_question")
        if "on a scale of" in text_lower:
            patterns.append("scale_introduction")
        if "please rate" in text_lower:
            patterns.append("rating_request")
        
        return patterns
    
    def _extract_scale_patterns(self, high_quality_questions: List[QuestionAnnotation]) -> Dict[str, Any]:
        """Extract scale design patterns from high-quality questions"""
        scale_patterns = {
            "satisfaction_scales": [],
            "likert_scales": [],
            "nps_scales": [],
            "frequency_scales": []
        }
        
        # This would need to be implemented based on actual scale data
        # For now, return placeholder patterns
        scale_patterns["satisfaction_scales"] = [
            "1=Very Dissatisfied, 5=Very Satisfied",
            "1=Strongly Disagree, 5=Strongly Agree"
        ]
        
        return scale_patterns
    
    def _identify_question_issues(self, question_text: str, comment: str) -> List[str]:
        """Identify specific issues with a question"""
        issues = []
        text_lower = question_text.lower()
        
        if "and" in text_lower and len(text_lower.split()) > 15:
            issues.append("double_barreled")
        if any(word in text_lower for word in ["amazing", "terrible", "obviously", "clearly"]):
            issues.append("biased_language")
        if len(question_text.split()) > 25:
            issues.append("too_long")
        if "?" not in question_text:
            issues.append("not_a_question")
        
        if comment:
            comment_lower = comment.lower()
            if "confusing" in comment_lower:
                issues.append("confusing")
            if "unclear" in comment_lower:
                issues.append("unclear")
            if "leading" in comment_lower:
                issues.append("leading")
        
        return issues
    
    def _extract_bias_words(self, question_text: str) -> List[str]:
        """Extract potentially biased words from question text"""
        bias_words = ["amazing", "terrible", "obviously", "clearly", "definitely", "absolutely", "never", "always"]
        text_lower = question_text.lower()
        
        found_bias = []
        for word in bias_words:
            if word in text_lower:
                found_bias.append(word)
        
        return found_bias
    
    def _is_double_barreled(self, question_text: str) -> bool:
        """Check if question is double-barreled"""
        text_lower = question_text.lower()
        
        # Look for conjunctions that might indicate multiple concepts
        conjunctions = ["and", "or", "but", "while", "whereas"]
        conjunction_count = sum(1 for conj in conjunctions if conj in text_lower)
        
        # If multiple conjunctions or very long question, likely double-barreled
        return conjunction_count > 1 or len(question_text.split()) > 20
    
    def _is_too_complex(self, question_text: str) -> bool:
        """Check if question is too complex"""
        # Simple heuristic: very long or has complex sentence structure
        word_count = len(question_text.split())
        sentence_count = question_text.count('.') + question_text.count('?') + question_text.count('!')
        
        return word_count > 30 or (sentence_count > 1 and word_count > 20)
    
    def _extract_issue_keywords(self, comment: str) -> List[str]:
        """Extract issue keywords from comment text"""
        if not comment:
            return []
        
        comment_lower = comment.lower()
        issues = []
        
        # Map keywords to issue types
        issue_keywords = {
            "confusing": ["confusing", "unclear", "hard to understand"],
            "too_long": ["too long", "wordy", "verbose"],
            "leading": ["leading", "biased", "loaded"],
            "unclear_scale": ["unclear scale", "bad scale", "confusing options"],
            "double_barreled": ["double", "two questions", "multiple concepts"],
            "poor_grammar": ["grammar", "typo", "spelling"],
            "irrelevant": ["irrelevant", "not related", "off topic"]
        }
        
        for issue, keywords in issue_keywords.items():
            if any(keyword in comment_lower for keyword in keywords):
                issues.append(issue)
        
        return issues
    
    async def get_quality_guidelines(self) -> Dict[str, Any]:
        """Get formatted quality guidelines for prompt injection"""
        patterns = await self.extract_quality_patterns()
        
        guidelines = {
            "high_quality_examples": [],
            "avoid_patterns": [],
            "common_issues": []
        }
        
        # Format high-quality patterns
        for question_type, examples in patterns["high_quality_patterns"].get("question_patterns", {}).items():
            if examples:
                best_example = max(examples, key=lambda x: x["score"])
                guidelines["high_quality_examples"].append({
                    "type": question_type,
                    "example": best_example["text"],
                    "score": best_example["score"]
                })
        
        # Format patterns to avoid
        for pattern, examples in patterns["low_quality_patterns"].get("phrasing_patterns", {}).items():
            if examples:
                guidelines["avoid_patterns"].append({
                    "pattern": pattern,
                    "examples": [ex["example"] for ex in examples[:2]]
                })
        
        # Format common issues
        guidelines["common_issues"] = patterns["common_issues"][:5]  # Top 5 issues
        
        return guidelines
    
    async def calculate_improvement_trend(self) -> Dict[str, Any]:
        """
        Calculate improvement trend by comparing recent annotations vs baseline period
        
        Strategy:
        - Baseline Period: Days 2-8 ago (7-day baseline window)
        - Recent Period: Yesterday (most recent 24 hours)
        - Formula: ((recent_avg - baseline_avg) / baseline_avg) × 100
        
        Returns:
            Dict with improvement_trend percentage and metadata
        """
        logger.info("🔍 [AnnotationInsights] Calculating improvement trend")
        
        try:
            now = datetime.utcnow()
            
            # Define time periods
            yesterday_start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
            yesterday_end = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            baseline_start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=8)
            baseline_end = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
            
            # Get annotations for both periods
            recent_annotations = DatabaseSessionManager.safe_query(
                self.db,
                lambda: self.db.query(QuestionAnnotation).filter(
                    QuestionAnnotation.created_at >= yesterday_start,
                    QuestionAnnotation.created_at < yesterday_end
                ).all(),
                fallback_value=[],
                operation_name="recent annotations query"
            )
            
            recent_section_annotations = DatabaseSessionManager.safe_query(
                self.db,
                lambda: self.db.query(SectionAnnotation).filter(
                    SectionAnnotation.created_at >= yesterday_start,
                    SectionAnnotation.created_at < yesterday_end
                ).all(),
                fallback_value=[],
                operation_name="recent section annotations query"
            )
            
            baseline_annotations = DatabaseSessionManager.safe_query(
                self.db,
                lambda: self.db.query(QuestionAnnotation).filter(
                    QuestionAnnotation.created_at >= baseline_start,
                    QuestionAnnotation.created_at < baseline_end
                ).all(),
                fallback_value=[],
                operation_name="baseline annotations query"
            )
            
            baseline_section_annotations = DatabaseSessionManager.safe_query(
                self.db,
                lambda: self.db.query(SectionAnnotation).filter(
                    SectionAnnotation.created_at >= baseline_start,
                    SectionAnnotation.created_at < baseline_end
                ).all(),
                fallback_value=[],
                operation_name="baseline section annotations query"
            )
            
            # Combine question and section annotations
            all_recent_annotations = recent_annotations + recent_section_annotations
            all_baseline_annotations = baseline_annotations + baseline_section_annotations
            
            logger.info(f"📊 [AnnotationInsights] Found {len(all_recent_annotations)} recent annotations, {len(all_baseline_annotations)} baseline annotations")
            
            # Check for sufficient data
            if len(all_recent_annotations) == 0:
                logger.info("⚠️ [AnnotationInsights] No recent annotations found")
                return {
                    "improvement_trend": 0.0,
                    "status": "no_recent_data",
                    "message": "No annotations in the last 24 hours",
                    "baseline_period": f"{baseline_start.strftime('%Y-%m-%d')} to {baseline_end.strftime('%Y-%m-%d')}",
                    "recent_period": f"{yesterday_start.strftime('%Y-%m-%d')} to {yesterday_end.strftime('%Y-%m-%d')}",
                    "baseline_count": len(all_baseline_annotations),
                    "recent_count": 0
                }
            
            if len(all_baseline_annotations) == 0:
                logger.info("⚠️ [AnnotationInsights] No baseline annotations found")
                return {
                    "improvement_trend": 0.0,
                    "status": "establishing_baseline",
                    "message": "Establishing baseline - need 7+ days of history",
                    "baseline_period": f"{baseline_start.strftime('%Y-%m-%d')} to {baseline_end.strftime('%Y-%m-%d')}",
                    "recent_period": f"{yesterday_start.strftime('%Y-%m-%d')} to {yesterday_end.strftime('%Y-%m-%d')}",
                    "baseline_count": 0,
                    "recent_count": len(all_recent_annotations)
                }
            
            if len(all_recent_annotations) + len(all_baseline_annotations) < 10:
                logger.info("⚠️ [AnnotationInsights] Insufficient total annotations")
                return {
                    "improvement_trend": 0.0,
                    "status": "insufficient_data",
                    "message": f"Need at least 10 annotations (have {len(all_recent_annotations) + len(all_baseline_annotations)})",
                    "baseline_period": f"{baseline_start.strftime('%Y-%m-%d')} to {baseline_end.strftime('%Y-%m-%d')}",
                    "recent_period": f"{yesterday_start.strftime('%Y-%m-%d')} to {yesterday_end.strftime('%Y-%m-%d')}",
                    "baseline_count": len(all_baseline_annotations),
                    "recent_count": len(all_recent_annotations)
                }
            
            # Calculate average scores
            recent_scores = [self._get_average_score(ann) for ann in all_recent_annotations]
            baseline_scores = [self._get_average_score(ann) for ann in all_baseline_annotations]
            
            recent_avg = sum(recent_scores) / len(recent_scores) if recent_scores else 0.0
            baseline_avg = sum(baseline_scores) / len(baseline_scores) if baseline_scores else 0.0
            
            # Calculate improvement trend
            if baseline_avg > 0:
                improvement_trend = ((recent_avg - baseline_avg) / baseline_avg) * 100
            else:
                improvement_trend = 0.0
            
            logger.info(f"✅ [AnnotationInsights] Improvement trend calculated: {improvement_trend:.1f}% (recent: {recent_avg:.2f}, baseline: {baseline_avg:.2f})")
            
            return {
                "improvement_trend": round(improvement_trend, 1),
                "status": "success",
                "message": f"Quality {'improved' if improvement_trend > 0 else 'declined'} by {abs(improvement_trend):.1f}%",
                "baseline_period": f"{baseline_start.strftime('%Y-%m-%d')} to {baseline_end.strftime('%Y-%m-%d')}",
                "recent_period": f"{yesterday_start.strftime('%Y-%m-%d')} to {yesterday_end.strftime('%Y-%m-%d')}",
                "baseline_count": len(all_baseline_annotations),
                "recent_count": len(all_recent_annotations),
                "baseline_avg": round(baseline_avg, 2),
                "recent_avg": round(recent_avg, 2)
            }
            
        except Exception as e:
            logger.error(f"❌ [AnnotationInsights] Failed to calculate improvement trend: {str(e)}", exc_info=True)
            return {
                "improvement_trend": 0.0,
                "status": "error",
                "message": f"Error calculating trend: {str(e)}",
                "baseline_period": "N/A",
                "recent_period": "N/A",
                "baseline_count": 0,
                "recent_count": 0
            }
