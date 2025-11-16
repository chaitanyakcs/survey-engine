"""
Unit tests for survey diff service.
Tests the fix for section diff detection when questions change but count stays same.
"""
import pytest
from src.services.survey_diff_service import SurveyDiffService


class TestSurveyDiffService:
    """Test suite for survey diff service"""
    
    def test_section_modified_when_questions_change_same_count(self):
        """
        Test that sections are marked as modified when questions change,
        even if the question count remains the same.
        
        This is the fix for the bug where versions 1 and 5 showed as different
        but the diff didn't show the differences.
        """
        survey1 = {
            "title": "Test Survey",
            "sections": [
                {
                    "id": 1,
                    "title": "Section 1",
                    "questions": [
                        {"id": "q1", "text": "Question 1 - Original", "type": "rating"},
                        {"id": "q2", "text": "Question 2 - Original", "type": "multiple_choice", "options": ["A", "B"]}
                    ]
                },
                {
                    "id": 2,
                    "title": "Section 2",
                    "questions": [
                        {"id": "q3", "text": "Question 3 - Same", "type": "text"}
                    ]
                }
            ]
        }
        
        survey2 = {
            "title": "Test Survey",
            "sections": [
                {
                    "id": 1,
                    "title": "Section 1",
                    "questions": [
                        {"id": "q1", "text": "Question 1 - Modified", "type": "rating"},
                        {"id": "q2", "text": "Question 2 - Modified", "type": "multiple_choice", "options": ["C", "D"]}
                    ]
                },
                {
                    "id": 2,
                    "title": "Section 2",
                    "questions": [
                        {"id": "q3", "text": "Question 3 - Same", "type": "text"}
                    ]
                }
            ]
        }
        
        diff_service = SurveyDiffService()
        diff_result = diff_service.compute_diff(survey1, survey2)
        
        # Find Section 1 in the diff
        section1_diff = next((s for s in diff_result["sections"] if s["id"] == 1), None)
        assert section1_diff is not None, "Section 1 should be in diff"
        
        # Section 1 should be marked as modified (not preserved) because questions changed
        assert section1_diff["status"] == "modified", \
            f"Section 1 should be 'modified' but got '{section1_diff['status']}'"
        
        # Section 1 should have questions_changed > 0
        assert section1_diff["questions_changed"] > 0, \
            f"Section 1 should have questions_changed > 0 but got {section1_diff['questions_changed']}"
        
        # Section 2 should be preserved (no changes)
        section2_diff = next((s for s in diff_result["sections"] if s["id"] == 2), None)
        assert section2_diff is not None, "Section 2 should be in diff"
        assert section2_diff["status"] == "preserved", \
            f"Section 2 should be 'preserved' but got '{section2_diff['status']}'"
        
        # Check that questions changed (could be modified, added, or removed)
        # When text changes significantly, questions might be added/removed instead of modified
        changed_questions = [
            q for q in diff_result["questions"] 
            if q["status"] in ["modified", "added", "removed"]
        ]
        assert len(changed_questions) >= 2, \
            f"Should have at least 2 changed questions (modified/added/removed), got {len(changed_questions)}"
        
        # Verify summary reflects changes (added + modified + removed)
        total_changes = (
            diff_result["summary"]["questions_modified"] +
            diff_result["summary"]["questions_added"] +
            diff_result["summary"]["questions_removed"]
        )
        assert total_changes >= 2, \
            f"Summary should show at least 2 total question changes, got {total_changes}"
        assert diff_result["summary"]["sections_changed"] >= 1, \
            f"Summary should show at least 1 changed section, got {diff_result['summary']['sections_changed']}"
    
    def test_question_modified_when_text_changes_high_similarity(self):
        """
        Test that questions are marked as modified when actual changes are detected,
        even if similarity score is high (>= 0.9).
        
        This is the fix for questions being marked as preserved when they actually changed.
        """
        survey1 = {
            "title": "Test Survey",
            "sections": [
                {
                    "id": 1,
                    "title": "Section 1",
                    "questions": [
                        {"id": "q1", "text": "How satisfied are you with our product?", "type": "rating"}
                    ]
                }
            ]
        }
        
        survey2 = {
            "title": "Test Survey",
            "sections": [
                {
                    "id": 1,
                    "title": "Section 1",
                    "questions": [
                        {"id": "q1", "text": "How satisfied are you with our service?", "type": "rating"}
                    ]
                }
            ]
        }
        
        diff_service = SurveyDiffService()
        diff_result = diff_service.compute_diff(survey1, survey2)
        
        # Find the question in the diff
        question_diff = next((q for q in diff_result["questions"] if q.get("id") == "q1"), None)
        assert question_diff is not None, "Question q1 should be in diff"
        
        # Question should be marked as modified (not preserved) because text changed
        assert question_diff["status"] == "modified", \
            f"Question should be 'modified' but got '{question_diff['status']}'"
        
        # Should have "text" in changes
        assert "text" in question_diff["changes"], \
            f"Question changes should include 'text', got {question_diff['changes']}"
        
        # Section should also be marked as modified
        section1_diff = next((s for s in diff_result["sections"] if s["id"] == 1), None)
        assert section1_diff is not None, "Section 1 should be in diff"
        assert section1_diff["status"] == "modified", \
            f"Section 1 should be 'modified' because question changed, but got '{section1_diff['status']}'"
    
    def test_question_modified_when_options_change(self):
        """Test that questions are marked as modified when options change"""
        survey1 = {
            "title": "Test Survey",
            "sections": [
                {
                    "id": 1,
                    "title": "Section 1",
                    "questions": [
                        {"id": "q1", "text": "Choose an option", "type": "multiple_choice", "options": ["A", "B", "C"]}
                    ]
                }
            ]
        }
        
        survey2 = {
            "title": "Test Survey",
            "sections": [
                {
                    "id": 1,
                    "title": "Section 1",
                    "questions": [
                        {"id": "q1", "text": "Choose an option", "type": "multiple_choice", "options": ["X", "Y", "Z"]}
                    ]
                }
            ]
        }
        
        diff_service = SurveyDiffService()
        diff_result = diff_service.compute_diff(survey1, survey2)
        
        question_diff = next((q for q in diff_result["questions"] if q.get("id") == "q1"), None)
        assert question_diff is not None, "Question q1 should be in diff"
        assert question_diff["status"] == "modified", \
            f"Question should be 'modified' when options change, got '{question_diff['status']}'"
        assert "options" in question_diff["changes"], \
            f"Question changes should include 'options', got {question_diff['changes']}"
    
    def test_question_modified_when_type_changes(self):
        """Test that questions are marked as modified when type changes"""
        survey1 = {
            "title": "Test Survey",
            "sections": [
                {
                    "id": 1,
                    "title": "Section 1",
                    "questions": [
                        {"id": "q1", "text": "Rate this", "type": "rating"}
                    ]
                }
            ]
        }
        
        survey2 = {
            "title": "Test Survey",
            "sections": [
                {
                    "id": 1,
                    "title": "Section 1",
                    "questions": [
                        {"id": "q1", "text": "Rate this", "type": "multiple_choice", "options": ["1", "2", "3"]}
                    ]
                }
            ]
        }
        
        diff_service = SurveyDiffService()
        diff_result = diff_service.compute_diff(survey1, survey2)
        
        question_diff = next((q for q in diff_result["questions"] if q.get("id") == "q1"), None)
        assert question_diff is not None, "Question q1 should be in diff"
        assert question_diff["status"] == "modified", \
            f"Question should be 'modified' when type changes, got '{question_diff['status']}'"
        assert "type" in question_diff["changes"], \
            f"Question changes should include 'type', got {question_diff['changes']}"
    
    def test_section_preserved_when_no_changes(self):
        """Test that sections are preserved when no questions change"""
        survey1 = {
            "title": "Test Survey",
            "sections": [
                {
                    "id": 1,
                    "title": "Section 1",
                    "questions": [
                        {"id": "q1", "text": "Question 1", "type": "rating"},
                        {"id": "q2", "text": "Question 2", "type": "text"}
                    ]
                }
            ]
        }
        
        survey2 = {
            "title": "Test Survey",
            "sections": [
                {
                    "id": 1,
                    "title": "Section 1",
                    "questions": [
                        {"id": "q1", "text": "Question 1", "type": "rating"},
                        {"id": "q2", "text": "Question 2", "type": "text"}
                    ]
                }
            ]
        }
        
        diff_service = SurveyDiffService()
        diff_result = diff_service.compute_diff(survey1, survey2)
        
        section1_diff = next((s for s in diff_result["sections"] if s["id"] == 1), None)
        assert section1_diff is not None, "Section 1 should be in diff"
        assert section1_diff["status"] == "preserved", \
            f"Section 1 should be 'preserved' when no changes, got '{section1_diff['status']}'"
        
        # All questions should be preserved
        preserved_questions = [q for q in diff_result["questions"] if q["status"] == "preserved"]
        assert len(preserved_questions) == 2, \
            f"Should have 2 preserved questions, got {len(preserved_questions)}"

