"""
Comment Action Analyzer Service
Analyzes whether annotation comments were actually addressed by the LLM during regeneration.
Uses LLM self-report (comments_addressed) and validates against actual survey changes.
"""

from typing import Dict, List, Any, Optional, Set
import logging
from uuid import UUID

logger = logging.getLogger(__name__)


class CommentActionAnalyzer:
    """
    Analyzes comment action status by:
    1. Comparing LLM self-report (comments_addressed) with used annotation IDs
    2. Validating that reported comments actually have corresponding changes
    3. Computing confidence scores (high/medium/low)
    4. Detecting discrepancies
    """

    def __init__(self):
        pass

    def analyze_comment_actions(
        self,
        used_annotation_ids: Optional[Dict[str, List[int]]],
        comments_addressed: Optional[List[str]],
        survey_diff: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze which comments were addressed based on LLM self-report and actual changes.
        
        Args:
            used_annotation_ids: Dict with question_annotations, section_annotations, survey_annotations lists
            comments_addressed: List of comment IDs that LLM reported as addressed
            survey_diff: Optional diff between old and new survey for validation
            
        Returns:
            Dict with comment action status for each comment
        """
        if not used_annotation_ids and not comments_addressed:
            return {
                "total_comments": 0,
                "addressed_comments": [],
                "unaddressed_comments": [],
                "action_status": {}
            }
        
        # Extract all comment IDs that were included in the prompt
        all_comment_ids = set()
        comment_id_to_annotation = {}
        
        # Build mapping from comment IDs to annotation metadata
        if used_annotation_ids:
            # We need to reconstruct comment IDs from annotation IDs
            # This is a simplified version - in practice, we'd query the database
            # For now, we'll use the comments_addressed list as the source of truth
            pass
        
        # Use comments_addressed as primary source if available
        addressed_comment_ids = set(comments_addressed) if comments_addressed else set()
        
        # Build action status for each comment
        action_status = {}
        
        # For comments that were included in prompt but not reported as addressed
        if used_annotation_ids:
            # We would need to query the database to get comment IDs from annotation IDs
            # For now, we'll focus on comments_addressed
            pass
        
        # Mark comments as addressed if they're in comments_addressed
        for comment_id in addressed_comment_ids:
            action_status[comment_id] = {
                "status": "addressed",
                "confidence": "high",  # LLM self-reported
                "source": "llm_self_report"
            }
        
        # If we have survey_diff, we can validate that changes actually occurred
        if survey_diff and addressed_comment_ids:
            # Validate that addressed comments have corresponding changes
            validated_status = self._validate_against_diff(
                addressed_comment_ids,
                survey_diff
            )
            
            # Update confidence based on validation
            for comment_id, validation_result in validated_status.items():
                if comment_id in action_status:
                    if validation_result["has_changes"]:
                        action_status[comment_id]["confidence"] = "high"
                        action_status[comment_id]["validation"] = "confirmed"
                    else:
                        action_status[comment_id]["confidence"] = "medium"
                        action_status[comment_id]["validation"] = "unconfirmed"
                        action_status[comment_id]["warning"] = "LLM reported addressing but no changes detected"
        
        # Build lists
        addressed_comments = [
            {
                "comment_id": comment_id,
                **status
            }
            for comment_id, status in action_status.items()
            if status["status"] == "addressed"
        ]
        
        return {
            "total_comments": len(addressed_comment_ids),
            "addressed_comments": addressed_comments,
            "unaddressed_comments": [],  # Would need full list of comments to compute
            "action_status": action_status,
            "summary": {
                "addressed_count": len(addressed_comments),
                "high_confidence": len([c for c in addressed_comments if c.get("confidence") == "high"]),
                "medium_confidence": len([c for c in addressed_comments if c.get("confidence") == "medium"]),
                "low_confidence": len([c for c in addressed_comments if c.get("confidence") == "low"])
            }
        }

    def _validate_against_diff(
        self,
        comment_ids: Set[str],
        survey_diff: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Validate that comments reported as addressed actually have corresponding changes.
        
        Args:
            comment_ids: Set of comment IDs to validate
            survey_diff: Survey diff showing actual changes
            
        Returns:
            Dict mapping comment_id to validation result
        """
        validation_results = {}
        
        # Extract question and section changes from diff
        question_changes = {}
        section_changes = {}
        
        if "questions" in survey_diff:
            for q_change in survey_diff["questions"].get("modified", []):
                question_id = q_change.get("question_id")
                if question_id:
                    question_changes[question_id] = q_change
        
        if "sections" in survey_diff:
            for s_change in survey_diff["sections"].get("modified", []):
                section_id = s_change.get("section_id")
                if section_id:
                    section_changes[section_id] = s_change
        
        # Validate each comment ID
        for comment_id in comment_ids:
            has_changes = False
            
            # Parse comment ID format: COMMENT-Q{question_id}-V{version} or COMMENT-S{section_id}-V{version}
            if comment_id.startswith("COMMENT-Q"):
                # Extract question ID
                try:
                    # Format: COMMENT-Q123-V2
                    parts = comment_id.split("-")
                    if len(parts) >= 2:
                        question_id = parts[1].replace("Q", "")
                        if question_id in question_changes:
                            has_changes = True
                except Exception as e:
                    logger.warning(f"⚠️ [CommentActionAnalyzer] Failed to parse question comment ID {comment_id}: {e}")
            
            elif comment_id.startswith("COMMENT-S"):
                # Extract section ID
                try:
                    # Format: COMMENT-S3-V1
                    parts = comment_id.split("-")
                    if len(parts) >= 2:
                        section_id_str = parts[1].replace("S", "")
                        # Try to match section ID (could be int or string)
                        section_id = int(section_id_str) if section_id_str.isdigit() else section_id_str
                        if section_id in section_changes or str(section_id) in section_changes:
                            has_changes = True
                except Exception as e:
                    logger.warning(f"⚠️ [CommentActionAnalyzer] Failed to parse section comment ID {comment_id}: {e}")
            
            elif comment_id.startswith("COMMENT-SURVEY"):
                # Survey-level comments - check if any changes occurred
                has_changes = (
                    survey_diff.get("summary", {}).get("questions_added", 0) > 0 or
                    survey_diff.get("summary", {}).get("questions_modified", 0) > 0 or
                    survey_diff.get("summary", {}).get("questions_removed", 0) > 0
                )
            
            validation_results[comment_id] = {
                "has_changes": has_changes,
                "comment_id": comment_id
            }
        
        return validation_results

    def compute_comment_action_status(
        self,
        used_annotation_ids: Optional[Dict[str, List[int]]],
        comments_addressed: Optional[List[str]],
        survey_diff: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Compute action status for each comment (addressed/unaddressed/unknown).
        
        Returns:
            Dict mapping comment_id to status ("addressed", "unaddressed", "unknown")
        """
        analysis = self.analyze_comment_actions(
            used_annotation_ids,
            comments_addressed,
            survey_diff
        )
        
        # Build simple status mapping
        status_map = {}
        for comment in analysis.get("addressed_comments", []):
            comment_id = comment.get("comment_id")
            if comment_id:
                status_map[comment_id] = "addressed"
        
        return status_map

