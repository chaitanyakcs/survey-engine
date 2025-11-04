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
        return list(survey["questions"])  # Ensure we return a new list

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


def get_questions_and_instructions_count(survey: Optional[Dict[str, Any]]) -> tuple[int, int]:
    """
    Get the count of questions and instructions separately in a survey
    
    Args:
        survey: Survey object in either legacy or sectioned format
    
    Returns:
        tuple: (question_count, instruction_count)
    """
    if not survey:
        return 0, 0
    
    question_count = 0
    instruction_count = 0
    
    # Check sections format
    if survey.get("sections"):
        for section in survey.get("sections", []):
            # Count questions vs instructions in section questions
            for question in section.get("questions", []):
                if question.get("type") == "instruction":
                    instruction_count += 1
                else:
                    question_count += 1
            
            # Count instructions in introText
            intro_text = section.get("introText")
            if intro_text and intro_text.get("type") == "instruction":
                instruction_count += 1
            
            # Count instructions in closingText
            closing_text = section.get("closingText")
            if closing_text and closing_text.get("type") == "instruction":
                instruction_count += 1
            
            # Count instructions in textBlocks
            text_blocks = section.get("textBlocks", [])
            for text_block in text_blocks:
                if text_block.get("type") == "instruction":
                    instruction_count += 1
    
    # Check legacy format
    elif survey.get("questions"):
        for question in survey.get("questions", []):
            if question.get("type") == "instruction":
                instruction_count += 1
            else:
                question_count += 1
    
    return question_count, instruction_count


def validate_survey_json(survey: Optional[Dict[str, Any]]) -> tuple[bool, List[str]]:
    """
    Validate a survey JSON structure

    Args:
        survey: Survey object to validate

    Returns:
        tuple: (is_valid, list_of_errors)
    """
    errors = []
    
    if not survey:
        return False, ["Survey is None or empty"]
    
    # Check required fields
    if not isinstance(survey, dict):
        return False, ["Survey must be a dictionary"]
    
    # Check for title
    if not survey.get("title"):
        errors.append("Survey must have a title")
    
    # Check for questions or sections
    if not survey.get("questions") and not survey.get("sections"):
        errors.append("Survey must have either 'questions' or 'sections'")
    
    # If sections format, validate structure
    if survey.get("sections"):
        if not isinstance(survey["sections"], list):
            errors.append("Sections must be a list")
        else:
            for i, section in enumerate(survey["sections"]):
                if not isinstance(section, dict):
                    errors.append(f"Section {i} must be a dictionary")
                    continue
                
                if not section.get("id"):
                    errors.append(f"Section {i} must have an id")
                
                if not section.get("title"):
                    errors.append(f"Section {i} must have a title")
                
                # Check questions in section
                questions = section.get("questions", [])
                if not isinstance(questions, list):
                    errors.append(f"Section {i} questions must be a list")
                else:
                    for j, question in enumerate(questions):
                        if not isinstance(question, dict):
                            errors.append(f"Section {i}, Question {j} must be a dictionary")
                            continue
                        
                        if not question.get("id"):
                            errors.append(f"Section {i}, Question {j} must have an id")
                        
                        if not question.get("text"):
                            errors.append(f"Section {i}, Question {j} must have text")
    
    # If legacy format, validate questions
    elif survey.get("questions"):
        questions = survey["questions"]
        if not isinstance(questions, list):
            errors.append("Questions must be a list")
        else:
            for i, question in enumerate(questions):
                if not isinstance(question, dict):
                    errors.append(f"Question {i} must be a dictionary")
                    continue
                
                if not question.get("id"):
                    errors.append(f"Question {i} must have an id")
                
                if not question.get("text"):
                    errors.append(f"Question {i} must have text")
    
    return len(errors) == 0, errors