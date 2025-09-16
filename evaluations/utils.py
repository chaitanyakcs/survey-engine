"""
Utility functions for survey evaluation modules
"""


def extract_all_questions(survey):
    """
    Extract all questions from both legacy and sectioned survey formats
    
    Args:
        survey: Survey object that may have questions in legacy format 
               (survey.questions) or sectioned format (survey.sections[].questions)
    
    Returns:
        List of all question objects regardless of format
    """
    if not survey:
        return []
    
    # Legacy format: questions are directly in survey.questions
    if survey.get("questions"):
        return survey["questions"]
    
    # Sectioned format: questions are in survey.sections[].questions
    if survey.get("sections"):
        all_questions = []
        for section in survey["sections"]:
            all_questions.extend(section.get("questions", []))
        return all_questions
    
    return []