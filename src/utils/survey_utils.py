"""
Survey utility functions for handling both legacy and sectioned survey formats
"""
from typing import Dict, List, Any, Optional, Union

def extract_all_questions(survey: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract all questions from both legacy and sectioned survey formats

    Args:
        survey: Survey object that may have questions in legacy format
               (survey['questions']) or sectioned format (survey['sections'][].questions)

    Returns:
        List of all question objects regardless of format
    """
    if not survey:
        return []

    # Legacy format: questions are directly in survey['questions']
    if survey.get("questions"):
        return survey["questions"]

    # Sectioned format: questions are in survey['sections'][].questions
    if survey.get("sections"):
        all_questions = []
        for section in survey["sections"]:
            all_questions.extend(section.get("questions", []))
        return all_questions

    return []


def get_questions_count(survey: Optional[Dict[str, Any]]) -> int:
    """
    Get the total number of questions in a survey regardless of format

    Args:
        survey: Survey object in either legacy or sectioned format

    Returns:
        int: Total number of questions
    """
    return len(extract_all_questions(survey))