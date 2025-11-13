"""
Survey Encoder Service
Compresses survey structure for LLM context to reduce token usage
Reduces full survey JSON (~50KB) to encoded summary (~2KB)
"""

from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class SurveyEncoderService:
    """Service for encoding/compressing survey structure"""

    def encode_survey_structure(self, survey_json: Dict[str, Any], include_full_questions_for_sections: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Compress survey to compact representation for LLM context
        
        Args:
            survey_json: Full survey JSON structure
            include_full_questions_for_sections: Optional list of section IDs to include ALL questions for (not just summaries)
            
        Returns:
            Compressed survey structure with:
            - Summary (section count, question count, methodology)
            - Sections (title, question count, question types, key questions)
            - Structure pattern
            - Total questions
            - Methodology tags
        """
        try:
            sections = survey_json.get('sections', [])
            questions = survey_json.get('questions', [])
            metadata = survey_json.get('metadata', {})
            
            # Extract methodology tags
            methodology_tags = metadata.get('methodology_tags', [])
            if not methodology_tags:
                # Try to infer from survey structure
                methodology_tags = self._infer_methodology_tags(survey_json)
            
            # Build section summaries
            section_summaries = []
            include_full = include_full_questions_for_sections or []
            # Normalize include_full to handle both int and string IDs
            include_full_normalized = []
            for sid in include_full:
                try:
                    include_full_normalized.append(int(sid))
                except (ValueError, TypeError):
                    include_full_normalized.append(sid)
            
            for section in sections[:20]:  # Limit to first 20 sections
                section_questions = section.get('questions', [])
                section_id = section.get('id')
                # Normalize section_id for comparison
                try:
                    section_id_normalized = int(section_id)
                except (ValueError, TypeError):
                    section_id_normalized = section_id
                
                question_types = list(set([q.get('type', 'text') for q in section_questions]))
                
                # If this section should have full questions, include all; otherwise just first 3
                should_include_full = section_id_normalized in include_full_normalized or section_id in include_full
                max_questions = len(section_questions) if should_include_full else min(3, len(section_questions))
                
                key_questions = []
                for q in section_questions[:max_questions]:
                    q_text = q.get('text', '')
                    if q_text:
                        # For full questions, include complete text; for summaries, truncate
                        if should_include_full:
                            key_questions.append(q_text)
                        else:
                            key_questions.append(q_text[:100] + ('...' if len(q_text) > 100 else ''))
                
                section_summaries.append({
                    'id': section_id,
                    'title': section.get('title', 'Section'),
                    'question_count': len(section_questions),
                    'question_types': question_types,
                    'key_questions': key_questions,
                    'has_full_questions': should_include_full
                })
            
            # Build structure pattern
            structure_pattern = " → ".join([
                s.get('title', 'Section')[:30] 
                for s in sections[:10]  # Limit to first 10 sections
            ])
            
            # Calculate total questions
            total_questions = len(questions)
            if not total_questions:
                # Count from sections if questions array is empty
                total_questions = sum(len(s.get('questions', [])) for s in sections)
            
            # Build summary
            summary = (
                f"Survey with {len(sections)} sections, {total_questions} questions, "
                f"methodology: {', '.join(methodology_tags) if methodology_tags else 'general'}"
            )
            
            encoded = {
                'summary': summary,
                'sections': section_summaries,
                'structure_pattern': structure_pattern,
                'total_questions': total_questions,
                'methodology_tags': methodology_tags,
                'title': survey_json.get('title', 'Survey'),
                'description': survey_json.get('description', '')[:200]  # First 200 chars
            }
            
            logger.info(f"📦 [SurveyEncoder] Encoded survey: {len(sections)} sections, {total_questions} questions → ~{len(str(encoded))} chars")
            return encoded
            
        except Exception as e:
            logger.error(f"❌ [SurveyEncoder] Failed to encode survey structure: {str(e)}")
            # Return minimal fallback
            return {
                'summary': 'Survey structure encoding failed',
                'sections': [],
                'structure_pattern': 'unknown',
                'total_questions': 0,
                'methodology_tags': [],
                'title': survey_json.get('title', 'Survey'),
                'description': ''
            }

    def _infer_methodology_tags(self, survey_json: Dict[str, Any]) -> List[str]:
        """
        Infer methodology tags from survey structure
        
        Args:
            survey_json: Survey JSON structure
            
        Returns:
            List of inferred methodology tags
        """
        methodology_tags = []
        questions = survey_json.get('questions', [])
        question_texts = [q.get('text', '').lower() for q in questions]
        all_text = ' '.join(question_texts)
        
        # Simple keyword detection
        if 'too cheap' in all_text or 'too expensive' in all_text:
            methodology_tags.append('van_westendorp')
        if 'most important' in all_text or 'least important' in all_text:
            methodology_tags.append('maxdiff')
        if 'recommend' in all_text or 'nps' in all_text.lower():
            methodology_tags.append('nps')
        if 'satisfaction' in all_text or 'satisfied' in all_text:
            methodology_tags.append('satisfaction')
        if 'conjoint' in all_text.lower() or 'choice' in all_text:
            methodology_tags.append('conjoint')
        
        return methodology_tags if methodology_tags else ['basic_survey']

