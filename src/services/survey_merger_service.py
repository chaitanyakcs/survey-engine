"""
Survey Merger Service
Intelligently merges regenerated sections with preserved sections
"""

from typing import Dict, List, Any
import copy
import logging

logger = logging.getLogger(__name__)


class SurveyMergerService:
    """Intelligently merges regenerated sections with preserved sections"""

    def __init__(self):
        pass

    def merge_surveys(
        self,
        previous_survey: Dict[str, Any],
        regenerated_sections: List[Dict[str, Any]],
        preserve_section_ids: List[int]
    ) -> Dict[str, Any]:
        """
        Merge regenerated sections with preserved sections from previous survey
        
        Handles:
        - Question ID renumbering
        - Section ordering
        - Metadata updates
        - Validation
        
        Args:
            previous_survey: Full previous survey JSON structure
            regenerated_sections: List of newly generated sections
            preserve_section_ids: List of section IDs to preserve from previous survey
            
        Returns:
            Merged survey with regenerated sections integrated
        """
        logger.info(f"🔬 [SurveyMerger] Merging surveys: {len(regenerated_sections)} regenerated, {len(preserve_section_ids)} preserved")
        
        # Deep copy to avoid modifying original
        merged = copy.deepcopy(previous_survey)
        
        # Create lookup for regenerated sections by ID
        regenerated_by_id = {s.get('id'): s for s in regenerated_sections}
        
        logger.info(f"🔬 [SurveyMerger] Regenerated section IDs: {list(regenerated_by_id.keys())}")
        logger.info(f"🔬 [SurveyMerger] Preserved section IDs: {preserve_section_ids}")
        
        # Build new sections list in proper order
        new_sections = []
        previous_sections = previous_survey.get('sections', [])
        
        for section in previous_sections:
            section_id = section.get('id')
            
            if section_id in regenerated_by_id:
                # Use regenerated version
                new_section = regenerated_by_id[section_id]
                new_sections.append(new_section)
                logger.info(f"  → Section {section_id}: Using regenerated version")
            elif section_id in preserve_section_ids:
                # Preserve original
                new_sections.append(copy.deepcopy(section))
                logger.info(f"  → Section {section_id}: Preserving original")
            else:
                # Section not in either list - preserve it anyway
                logger.warning(f"  ⚠️ Section {section_id}: Not in regenerated or preserved lists, preserving original")
                new_sections.append(copy.deepcopy(section))
        
        merged['sections'] = new_sections
        
        # Renumber questions globally
        merged = self._renumber_questions(merged)
        
        # Update metadata
        if 'metadata' not in merged:
            merged['metadata'] = {}
        
        merged['metadata']['regenerated_sections'] = list(regenerated_by_id.keys())
        merged['metadata']['preserved_sections'] = preserve_section_ids
        merged['metadata']['is_surgical_regeneration'] = True
        
        # Count total questions
        total_questions = sum(len(s.get('questions', [])) for s in new_sections)
        merged['metadata']['total_questions'] = total_questions
        
        logger.info(f"🔬 [SurveyMerger] Merge complete:")
        logger.info(f"  - Total sections: {len(new_sections)}")
        logger.info(f"  - Total questions: {total_questions}")
        logger.info(f"  - Regenerated sections: {merged['metadata']['regenerated_sections']}")
        logger.info(f"  - Preserved sections: {merged['metadata']['preserved_sections']}")
        
        return merged

    def _renumber_questions(self, survey: Dict[str, Any]) -> Dict[str, Any]:
        """
        Renumber all questions globally (q1, q2, q3, ...) across all sections
        
        Args:
            survey: Survey JSON structure
            
        Returns:
            Survey with renumbered question IDs
        """
        logger.info("🔢 [SurveyMerger] Renumbering questions globally")
        
        question_counter = 1
        sections = survey.get('sections', [])
        
        for section in sections:
            questions = section.get('questions', [])
            
            for question in questions:
                old_id = question.get('id')
                new_id = f"q{question_counter}"
                question['id'] = new_id
                
                if old_id != new_id:
                    logger.debug(f"  - Renumbered: {old_id} → {new_id}")
                
                question_counter += 1
        
        # Also update flat questions array if it exists
        if 'questions' in survey and isinstance(survey['questions'], list):
            # Rebuild flat questions array from sections
            all_questions = []
            for section in sections:
                all_questions.extend(section.get('questions', []))
            survey['questions'] = all_questions
        
        logger.info(f"🔢 [SurveyMerger] Renumbered {question_counter - 1} questions")
        
        return survey

    def validate_merged_survey(self, survey: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the merged survey structure
        
        Args:
            survey: Merged survey JSON structure
            
        Returns:
            {
                "valid": True/False,
                "errors": ["error1", "error2"],
                "warnings": ["warning1"]
            }
        """
        errors = []
        warnings = []
        
        # Check basic structure
        if 'sections' not in survey:
            errors.append("Missing 'sections' field")
        
        if 'metadata' not in survey:
            warnings.append("Missing 'metadata' field")
        
        # Check sections
        sections = survey.get('sections', [])
        section_ids = [s.get('id') for s in sections]
        
        # Check for duplicate section IDs
        if len(section_ids) != len(set(section_ids)):
            errors.append(f"Duplicate section IDs found: {section_ids}")
        
        # Check questions
        all_question_ids = []
        for section in sections:
            questions = section.get('questions', [])
            for question in questions:
                q_id = question.get('id')
                if q_id:
                    all_question_ids.append(q_id)
        
        # Check for duplicate question IDs
        if len(all_question_ids) != len(set(all_question_ids)):
            errors.append(f"Duplicate question IDs found")
        
        # Check question ID sequence
        expected_ids = [f"q{i}" for i in range(1, len(all_question_ids) + 1)]
        if all_question_ids != expected_ids:
            warnings.append(f"Question IDs not sequential: expected {len(expected_ids)} sequential IDs")
        
        valid = len(errors) == 0
        
        if valid:
            logger.info("✅ [SurveyMerger] Merged survey validation passed")
        else:
            logger.error(f"❌ [SurveyMerger] Merged survey validation failed: {errors}")
        
        if warnings:
            logger.warning(f"⚠️ [SurveyMerger] Validation warnings: {warnings}")
        
        return {
            "valid": valid,
            "errors": errors,
            "warnings": warnings
        }

