"""
Survey Diff Service
Unified service for computing diffs between any two surveys.
Handles version comparisons, reference comparisons, and arbitrary comparisons.
"""

from typing import Dict, List, Any, Optional, Set, Tuple
import logging
from uuid import UUID

from src.utils.survey_comparison import (
    compare_surveys_detailed,
    _extract_actual_survey
)
from src.utils.survey_utils import extract_all_questions

logger = logging.getLogger(__name__)


class SurveyDiffService:
    """
    Unified diff service for ALL comparison types:
    - Version-to-version (same RFQ, parent-child or arbitrary)
    - Generated vs reference (cross-survey)
    - Any two surveys
    """

    def __init__(self):
        pass

    def compute_diff(
        self,
        survey1: Dict[str, Any],
        survey2: Dict[str, Any],
        survey1_metadata: Optional[Dict[str, Any]] = None,
        survey2_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Compute detailed diff between any two surveys.

        Args:
            survey1: First survey (current/newer version) - can be Survey model or dict
            survey2: Second survey (parent/older/reference) - can be Survey model or dict
            survey1_metadata: Optional Survey model metadata (for regeneration info)
            survey2_metadata: Optional Survey model metadata (for regeneration info)

        Returns:
            Dictionary with comprehensive diff analysis
        """
        try:
            # Extract actual survey data (handle nested structures)
            survey1_data = self._extract_survey_data(survey1)
            survey2_data = self._extract_survey_data(survey2)

            if not survey1_data or not survey2_data:
                logger.warning("⚠️ [SurveyDiff] One or both surveys are empty")
                return self._create_empty_diff()

            # Detect comparison type
            comparison_type = self._detect_comparison_type(survey1_metadata, survey2_metadata)

            logger.info(f"🔍 [SurveyDiff] Computing diff: type={comparison_type}")

            # Core diff computation (shared for all types)
            # Compute question diff first so we can use it for section diff
            question_diff = self._compute_question_diff(survey1_data, survey2_data)
            section_diff = self._compute_section_diff(survey1_data, survey2_data, question_diff)
            quality_diff = self._compute_quality_diff(survey1_data, survey2_data)

            # Build summary
            summary = self._build_summary(question_diff, section_diff, comparison_type, survey1_data)

            # Build result
            result = {
                "comparison_type": comparison_type,
                "summary": summary,
                "sections": section_diff,
                "questions": question_diff,
                "quality_scores": quality_diff
            }

            # Add context-specific metadata (only when applicable)
            if comparison_type == "version" and self._is_parent_child(survey1_metadata, survey2_metadata):
                regeneration_metadata = self._extract_regeneration_metadata(survey1_data)
                if regeneration_metadata:
                    result["regeneration_metadata"] = regeneration_metadata
            
            # Analyze comment action status for any version comparison (not just parent-child)
            # Check if survey1 has comment tracking data
            if comparison_type == "version" and survey1_metadata:
                has_comment_tracking = False
                if isinstance(survey1_metadata, dict):
                    has_comment_tracking = bool(survey1_metadata.get('used_annotation_comment_ids') or survey1_metadata.get('comments_addressed'))
                elif hasattr(survey1_metadata, 'used_annotation_comment_ids') or hasattr(survey1_metadata, 'comments_addressed'):
                    has_comment_tracking = bool(getattr(survey1_metadata, 'used_annotation_comment_ids', None) or getattr(survey1_metadata, 'comments_addressed', None))
                
                if has_comment_tracking:
                    comment_action_status = self._analyze_comment_actions(
                        survey1_metadata,
                        result
                    )
                    if comment_action_status:
                        result["comment_action_status"] = comment_action_status

            if comparison_type == "reference":
                reference_context = self._extract_reference_context(survey2_metadata)
                if reference_context:
                    result["reference_context"] = reference_context

            logger.info(f"✅ [SurveyDiff] Diff computation complete: {summary.get('questions_added', 0)} added, {summary.get('questions_modified', 0)} modified, {summary.get('questions_removed', 0)} removed")
            return result

        except Exception as e:
            logger.error(f"❌ [SurveyDiff] Error computing diff: {e}", exc_info=True)
            return self._create_error_diff(str(e))

    def _extract_survey_data(self, survey: Any) -> Optional[Dict[str, Any]]:
        """Extract survey data from Survey model or dict"""
        if survey is None:
            return None

        # If it's a Survey model, extract final_output or raw_output
        if hasattr(survey, 'final_output'):
            if survey.final_output:
                return _extract_actual_survey(survey.final_output)
            elif survey.raw_output:
                return _extract_actual_survey(survey.raw_output)
            return None

        # If it's already a dict, extract actual survey
        if isinstance(survey, dict):
            return _extract_actual_survey(survey)

        return None

    def _detect_comparison_type(self, meta1: Optional[Dict], meta2: Optional[Dict]) -> str:
        """Detect if version, reference, or arbitrary comparison"""
        if meta1 and meta2:
            rfq1 = meta1.get('rfq_id') if isinstance(meta1, dict) else (meta1.rfq_id if hasattr(meta1, 'rfq_id') else None)
            rfq2 = meta2.get('rfq_id') if isinstance(meta2, dict) else (meta2.rfq_id if hasattr(meta2, 'rfq_id') else None)
            status2 = meta2.get('status') if isinstance(meta2, dict) else (meta2.status if hasattr(meta2, 'status') else None)

            if rfq1 and rfq2 and rfq1 == rfq2:
                return "version"  # Same RFQ = version comparison
            elif status2 == 'reference':
                return "reference"  # Comparing with reference example

        return "arbitrary"  # Generic comparison

    def _is_parent_child(self, meta1: Optional[Dict], meta2: Optional[Dict]) -> bool:
        """Check if survey1 is a child of survey2 (parent-child relationship)"""
        if not meta1 or not meta2:
            return False

        parent_id1 = meta1.get('parent_survey_id') if isinstance(meta1, dict) else (meta1.parent_survey_id if hasattr(meta1, 'parent_survey_id') else None)
        id2 = meta2.get('id') if isinstance(meta2, dict) else (meta2.id if hasattr(meta2, 'id') else None)

        if parent_id1 and id2:
            return str(parent_id1) == str(id2)

        return False

    def _compute_question_diff(self, survey1: Dict[str, Any], survey2: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Compute question-level differences"""
        questions1 = extract_all_questions(survey1)
        questions2 = extract_all_questions(survey2)

        # Use existing comparison utility for question matching
        comparison_result = compare_surveys_detailed(survey1, survey2)
        matched_pairs = comparison_result.get('question_match', {}).get('matched_pairs', [])

        # Build question diff list
        question_diff = []

        # Track which questions have been matched
        matched_indices_1: Set[int] = set()
        matched_indices_2: Set[int] = set()

        # Process matched pairs
        for match in matched_pairs:
            idx1 = match.get('a_index')
            idx2 = match.get('b_index')
            similarity = match.get('score', 0.0)

            if idx1 is not None and idx2 is not None:
                matched_indices_1.add(idx1)
                matched_indices_2.add(idx2)

                q1 = questions1[idx1] if idx1 < len(questions1) else {}
                q2 = questions2[idx2] if idx2 < len(questions2) else {}

                # Detect what changed first
                changes = self._detect_question_changes(q1, q2)
                
                # Determine status based on similarity AND actual changes
                # If there are actual changes detected, always mark as modified
                if changes:
                    status = "modified"
                elif similarity >= 0.9:
                    status = "preserved"
                elif similarity >= 0.5:
                    status = "modified"
                else:
                    status = "modified"  # Low similarity but matched = significant change

                question_diff.append({
                    "id": q1.get('id', f"q{idx1}"),
                    "status": status,
                    "similarity": round(similarity, 3),
                    "section_id": self._get_question_section_id(survey1, idx1),
                    "changes": changes,
                    "question1": q1,
                    "question2": q2,
                    "match_index_1": idx1,
                    "match_index_2": idx2
                })

        # Process unmatched questions from survey1 (added)
        for idx1, q1 in enumerate(questions1):
            if idx1 not in matched_indices_1:
                question_diff.append({
                    "id": q1.get('id', f"q{idx1}"),
                    "status": "added",
                    "similarity": None,
                    "section_id": self._get_question_section_id(survey1, idx1),
                    "changes": [],
                    "question1": q1,
                    "question2": None,
                    "match_index_1": idx1,
                    "match_index_2": None
                })

        # Process unmatched questions from survey2 (removed)
        for idx2, q2 in enumerate(questions2):
            if idx2 not in matched_indices_2:
                question_diff.append({
                    "id": q2.get('id', f"q{idx2}"),
                    "status": "removed",
                    "similarity": None,
                    "section_id": self._get_question_section_id(survey2, idx2),
                    "changes": [],
                    "question1": None,
                    "question2": q2,
                    "match_index_1": None,
                    "match_index_2": idx2
                })

        return question_diff

    def _detect_question_changes(self, q1: Dict[str, Any], q2: Dict[str, Any]) -> List[str]:
        """Detect what aspects of a question changed"""
        changes = []

        text1 = q1.get('text', '').strip().lower()
        text2 = q2.get('text', '').strip().lower()
        if text1 != text2:
            changes.append("text")

        type1 = q1.get('type', '')
        type2 = q2.get('type', '')
        if type1 != type2:
            changes.append("type")

        options1 = q1.get('options', [])
        options2 = q2.get('options', [])
        if set(str(o).lower() for o in options1) != set(str(o).lower() for o in options2):
            changes.append("options")

        required1 = q1.get('required', False)
        required2 = q2.get('required', False)
        if required1 != required2:
            changes.append("required")

        return changes

    def _get_question_section_id(self, survey: Dict[str, Any], question_index: int) -> Optional[int]:
        """Get section ID for a question by its index"""
        questions = extract_all_questions(survey)
        if question_index >= len(questions):
            return None

        # If survey has sections, find which section contains this question
        sections = survey.get('sections', [])
        if sections:
            current_idx = 0
            for section in sections:
                section_questions = section.get('questions', [])
                if current_idx <= question_index < current_idx + len(section_questions):
                    return section.get('id')
                current_idx += len(section_questions)

        return None

    def _compute_section_diff(
        self, 
        survey1: Dict[str, Any], 
        survey2: Dict[str, Any],
        question_diff: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Compute section-level differences using question diff results"""
        sections1 = survey1.get('sections', [])
        sections2 = survey2.get('sections', [])

        # If no sections structure, create synthetic sections
        if not sections1 and not sections2:
            return []

        # Build section diff
        section_diff = []

        # Get section IDs
        section_ids_1 = {s.get('id') for s in sections1 if s.get('id') is not None}
        section_ids_2 = {s.get('id') for s in sections2 if s.get('id') is not None}

        all_section_ids = section_ids_1.union(section_ids_2)

        # Build a map of section_id -> question changes from question_diff
        section_question_changes = {}
        if question_diff:
            for q in question_diff:
                section_id = q.get('section_id')
                if section_id is not None:
                    if section_id not in section_question_changes:
                        section_question_changes[section_id] = {
                            'added': 0,
                            'modified': 0,
                            'removed': 0,
                            'preserved': 0
                        }
                    status = q.get('status', 'preserved')
                    section_question_changes[section_id][status] = section_question_changes[section_id].get(status, 0) + 1

        for section_id in sorted(all_section_ids):
            section1 = next((s for s in sections1 if s.get('id') == section_id), None)
            section2 = next((s for s in sections2 if s.get('id') == section_id), None)

            if section1 and section2:
                # Both exist - check for changes using question diff
                questions1 = section1.get('questions', [])
                questions2 = section2.get('questions', [])
                
                # Check if any questions in this section changed
                section_changes = section_question_changes.get(section_id, {})
                has_changes = (
                    section_changes.get('added', 0) > 0 or
                    section_changes.get('modified', 0) > 0 or
                    section_changes.get('removed', 0) > 0 or
                    len(questions1) != len(questions2)
                )
                
                status = "modified" if has_changes else "preserved"
                questions_changed = (
                    section_changes.get('added', 0) +
                    section_changes.get('modified', 0) +
                    section_changes.get('removed', 0)
                )
                
                section_diff.append({
                    "id": section_id,
                    "status": status,
                    "name": section1.get('title', f"Section {section_id}"),
                    "questions_count_1": len(questions1),
                    "questions_count_2": len(questions2),
                    "questions_changed": questions_changed if questions_changed > 0 else abs(len(questions1) - len(questions2))
                })
            elif section1:
                # Only in survey1 (added)
                section_diff.append({
                    "id": section_id,
                    "status": "added",
                    "name": section1.get('title', f"Section {section_id}"),
                    "questions_count_1": len(section1.get('questions', [])),
                    "questions_count_2": 0,
                    "questions_changed": len(section1.get('questions', []))
                })
            elif section2:
                # Only in survey2 (removed)
                section_diff.append({
                    "id": section_id,
                    "status": "removed",
                    "name": section2.get('title', f"Section {section_id}"),
                    "questions_count_1": 0,
                    "questions_count_2": len(section2.get('questions', [])),
                    "questions_changed": len(section2.get('questions', []))
                })

        return section_diff

    def _compute_quality_diff(self, survey1: Dict[str, Any], survey2: Dict[str, Any]) -> Dict[str, Any]:
        """Compute quality score differences if available"""
        quality1 = survey1.get('pillar_scores') or survey1.get('metadata', {}).get('pillar_scores')
        quality2 = survey2.get('pillar_scores') or survey2.get('metadata', {}).get('pillar_scores')

        if not quality1 and not quality2:
            return {}

        result = {}
        if quality1:
            result["survey1"] = quality1
        if quality2:
            result["survey2"] = quality2

        # Compute delta if both available
        if quality1 and quality2:
            delta = {}
            for key in set(quality1.keys()).union(set(quality2.keys())):
                val1 = quality1.get(key, 0)
                val2 = quality2.get(key, 0)
                if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                    delta[key] = round(val1 - val2, 3)
            result["delta"] = delta

        return result

    def _build_summary(
        self,
        question_diff: List[Dict[str, Any]],
        section_diff: List[Dict[str, Any]],
        comparison_type: str,
        survey1_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build summary statistics"""
        questions_added = sum(1 for q in question_diff if q.get('status') == 'added')
        questions_modified = sum(1 for q in question_diff if q.get('status') == 'modified')
        questions_removed = sum(1 for q in question_diff if q.get('status') == 'removed')
        questions_preserved = sum(1 for q in question_diff if q.get('status') == 'preserved')

        summary = {
            "questions_added": questions_added,
            "questions_modified": questions_modified,
            "questions_removed": questions_removed,
            "questions_preserved": questions_preserved,
            "total_questions_1": len(extract_all_questions(survey1_data)),
            "total_questions_2": questions_preserved + questions_modified + questions_removed,
            "sections_changed": sum(1 for s in section_diff if s.get('status') != 'preserved'),
            "sections_preserved": sum(1 for s in section_diff if s.get('status') == 'preserved')
        }

        # Add regeneration-specific summary if applicable
        if comparison_type == "version":
            regeneration_metadata = self._extract_regeneration_metadata(survey1_data)
            if regeneration_metadata:
                summary["sections_regenerated"] = regeneration_metadata.get('sections_regenerated', [])
                summary["sections_preserved"] = regeneration_metadata.get('sections_preserved', [])

        return summary

    def _extract_regeneration_metadata(self, survey: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract regeneration metadata from survey if available"""
        metadata = survey.get('metadata', {})
        if metadata.get('is_surgical_regeneration'):
            return {
                "sections_regenerated": metadata.get('regenerated_sections', []),
                "sections_preserved": metadata.get('preserved_sections', []),
                "is_surgical": True
            }
        return None

    def _extract_reference_context(self, survey_metadata: Optional[Dict]) -> Optional[Dict[str, Any]]:
        """Extract reference example context"""
        if not survey_metadata:
            return None

        status = survey_metadata.get('status') if isinstance(survey_metadata, dict) else (survey_metadata.status if hasattr(survey_metadata, 'status') else None)
        if status == 'reference':
            return {
                "is_reference": True,
                "reference_id": survey_metadata.get('id') if isinstance(survey_metadata, dict) else (survey_metadata.id if hasattr(survey_metadata, 'id') else None)
            }
        return None

    def _analyze_comment_actions(
        self,
        survey_metadata: Optional[Any],
        survey_diff: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze comment action status for regeneration.
        
        Args:
            survey_metadata: Survey model or dict with used_annotation_comment_ids and comments_addressed
            survey_diff: Computed survey diff for validation
            
        Returns:
            Dict with comment action analysis or None if not applicable
        """
        try:
            # Extract used_annotation_comment_ids and comments_addressed from metadata
            if survey_metadata is None:
                return None
            
            # Handle Survey model
            if hasattr(survey_metadata, 'used_annotation_comment_ids'):
                used_annotation_ids = survey_metadata.used_annotation_comment_ids
                comments_addressed = survey_metadata.comments_addressed
            elif isinstance(survey_metadata, dict):
                used_annotation_ids = survey_metadata.get('used_annotation_comment_ids')
                comments_addressed = survey_metadata.get('comments_addressed')
            else:
                return None
            
            # Only analyze if we have comment tracking data
            if not used_annotation_ids and not comments_addressed:
                return None
            
            # Use CommentActionAnalyzer to analyze
            from src.services.comment_action_analyzer import CommentActionAnalyzer
            analyzer = CommentActionAnalyzer()
            
            analysis = analyzer.analyze_comment_actions(
                used_annotation_ids=used_annotation_ids,
                comments_addressed=comments_addressed,
                survey_diff=survey_diff
            )
            
            logger.info(f"✅ [SurveyDiff] Comment action analysis complete: {analysis.get('summary', {}).get('addressed_count', 0)} addressed")
            return analysis
            
        except Exception as e:
            logger.warning(f"⚠️ [SurveyDiff] Failed to analyze comment actions: {e}")
            return None

    def _create_empty_diff(self) -> Dict[str, Any]:
        """Create empty diff result"""
        return {
            "comparison_type": "arbitrary",
            "summary": {
                "questions_added": 0,
                "questions_modified": 0,
                "questions_removed": 0,
                "questions_preserved": 0
            },
            "sections": [],
            "questions": [],
            "quality_scores": {},
            "error": "One or both surveys are empty"
        }

    def _create_error_diff(self, error_message: str) -> Dict[str, Any]:
        """Create error diff result"""
        return {
            "comparison_type": "arbitrary",
            "summary": {
                "questions_added": 0,
                "questions_modified": 0,
                "questions_removed": 0,
                "questions_preserved": 0
            },
            "sections": [],
            "questions": [],
            "quality_scores": {},
            "error": error_message
        }

