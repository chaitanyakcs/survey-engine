"""
Feedback Analyzer Service
Analyzes annotation feedback to identify what sections need regeneration
"""

from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class FeedbackAnalyzerService:
    """Analyzes annotation feedback to identify what needs regeneration"""

    def __init__(self):
        pass

    def analyze_feedback_for_surgical_regeneration(
        self,
        annotation_feedback: Dict[str, Any],
        previous_survey: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Identify sections/questions that need regeneration based on feedback comments
        
        Args:
            annotation_feedback: Structured feedback from AnnotationFeedbackService
            previous_survey: Previous survey JSON structure
            
        Returns:
            {
                "sections_to_regenerate": [1, 3],  # Section IDs
                "sections_to_preserve": [2, 4, 5, 6, 7],
                "regeneration_rationale": {
                    1: ["Question q5: \"Missing ethnicity question\""],
                    3: ["Section feedback: \"Confusing scale labels\""]
                },
                "total_sections": 7,
                "regeneration_percentage": 28.57
            }
        """
        logger.info(f"🔬 [FeedbackAnalyzer] Analyzing feedback for surgical regeneration (comment-based)")
        
        sections_with_feedback = set()
        rationale = {}
        
        # Analyze question-level feedback - only use comments, not quality scores
        question_feedback = annotation_feedback.get('question_feedback', {})
        questions_with_feedback = question_feedback.get('questions_with_feedback', [])
        
        logger.info(f"🔬 [FeedbackAnalyzer] Processing {len(questions_with_feedback)} questions with feedback")
        
        for qf in questions_with_feedback:
            question_id = qf.get('question_id')
            
            # Find which section this question belongs to
            section_id = self._get_section_from_question(question_id, previous_survey)
            
            if section_id is not None:
                # Only add section if it has comments (not based on quality score)
                comments = qf.get('comments', [])
                for comment in comments:
                    comment_text = comment.get('comment', '')
                    if comment_text and len(comment_text) > 10:  # Non-trivial comment
                        sections_with_feedback.add(section_id)
                        reason = f"Question {question_id}: \"{comment_text[:100]}\""
                        if reason not in rationale.get(section_id, []):
                            rationale.setdefault(section_id, []).append(reason)
                            logger.info(f"  → Section {section_id} needs regeneration: {reason}")
        
        # Analyze section-level feedback
        section_feedback = annotation_feedback.get('section_feedback', {})
        sections_with_feedback_list = section_feedback.get('sections_with_feedback', [])
        
        logger.info(f"🔬 [FeedbackAnalyzer] Processing {len(sections_with_feedback_list)} sections with feedback")
        
        for sf in sections_with_feedback_list:
            section_id = sf.get('section_id')
            comments = sf.get('comments', [])
            
            # Add section if it has comments (not based on quality score)
            if comments:
                sections_with_feedback.add(section_id)
                
                # Get latest comment
                latest_comment = comments[0].get('comment', '')[:100]
                if latest_comment:
                    reason = f"Section feedback: \"{latest_comment}\""
                    rationale.setdefault(section_id, []).append(reason)
                    logger.info(f"  → Section {section_id} needs regeneration: {reason}")
        
        # Get all section IDs from previous survey
        all_sections = previous_survey.get('sections', [])
        all_section_ids = {s.get('id') for s in all_sections if s.get('id') is not None}
        
        # Calculate sections to preserve
        sections_to_preserve = all_section_ids - sections_with_feedback
        
        # Convert sets to sorted lists
        sections_to_regenerate = sorted(list(sections_with_feedback))
        sections_to_preserve = sorted(list(sections_to_preserve))
        
        total_sections = len(all_section_ids)
        regeneration_percentage = (len(sections_to_regenerate) / total_sections * 100) if total_sections > 0 else 0
        
        result = {
            "sections_to_regenerate": sections_to_regenerate,
            "sections_to_preserve": sections_to_preserve,
            "regeneration_rationale": rationale,
            "total_sections": total_sections,
            "regeneration_percentage": regeneration_percentage
        }
        
        logger.info(f"🔬 [FeedbackAnalyzer] Analysis complete:")
        logger.info(f"  - Total sections: {total_sections}")
        logger.info(f"  - Sections to regenerate: {len(sections_to_regenerate)} ({regeneration_percentage:.1f}%)")
        logger.info(f"  - Sections to preserve: {len(sections_to_preserve)} ({100-regeneration_percentage:.1f}%)")
        
        return result

    def _get_section_from_question(
        self,
        question_id: str,
        previous_survey: Dict[str, Any]
    ) -> Optional[int]:
        """
        Find which section a question belongs to
        
        Args:
            question_id: Question ID (e.g., "q1", "q15")
            previous_survey: Previous survey JSON structure
            
        Returns:
            Section ID (int) or None if not found
        """
        sections = previous_survey.get('sections', [])
        
        for section in sections:
            section_id = section.get('id')
            questions = section.get('questions', [])
            
            for question in questions:
                if question.get('id') == question_id:
                    return section_id
        
        # If not found in sections, try the flat questions array
        questions = previous_survey.get('questions', [])
        for question in questions:
            if question.get('id') == question_id:
                # Try to infer section from question metadata or position
                # For now, return None as we can't determine section
                logger.warning(f"⚠️ [FeedbackAnalyzer] Question {question_id} found in flat questions array, cannot determine section")
                return None
        
        logger.warning(f"⚠️ [FeedbackAnalyzer] Question {question_id} not found in survey")
        return None

