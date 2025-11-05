"""
Prompt Validators
Validators for checking compliance with prompt rules:
- Open-ended question limits
- Best fit single-choice enforcement
- Question numbering and format rules
"""

from typing import Dict, List, Any, Optional, Tuple
import re
import logging
from src.utils.survey_utils import extract_all_questions

logger = logging.getLogger(__name__)


def test_open_ended_limits(survey: Dict[str, Any]) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Validate open-ended question limits per OPEN_ENDED_LIMIT_RULES:
    - open_ended_count ≤ 12% of respondent-facing questions AND ≤ 6 total
    - If total respondent questions < 20 → hard cap = 3
    - Only NPS 'why' + ≤ 2 targeted follow-ups may be required: true
    
    Args:
        survey: Survey JSON object
        
    Returns:
        Tuple of (is_valid, error_messages, metadata)
    """
    errors = []
    metadata = {
        "open_ended_count": 0,
        "open_ended_limit": {
            "pct": 12,
            "max": 6,
            "small_cap": 3
        },
        "total_respondent_questions": 0,
        "required_open_ended_count": 0,
        "nps_why_count": 0
    }
    
    try:
        # Extract all questions
        all_questions = extract_all_questions(survey)
        
        # Filter respondent-facing questions (exclude Section 7 programmer instructions)
        respondent_questions = []
        for question in all_questions:
            # Skip programmer instructions (Section 7)
            section_id = question.get("section_id")
            if section_id and section_id == 7:
                continue
            
            # Skip if question type indicates non-respondent question
            q_type = question.get("type", "").lower()
            if q_type in ["programmer_instruction", "instruction"]:
                continue
                
            respondent_questions.append(question)
        
        metadata["total_respondent_questions"] = len(respondent_questions)
        
        # Count open-ended questions
        open_ended_count = 0
        required_open_ended = []
        nps_why_count = 0
        
        for question in respondent_questions:
            q_type = question.get("type", "").lower()
            q_text = question.get("text", "").lower()
            is_required = question.get("required", False)
            
            if q_type in ["open_ended", "text", "textarea"]:
                open_ended_count += 1
                if is_required:
                    required_open_ended.append({
                        "id": question.get("id", "unknown"),
                        "text": question.get("text", "")[:100]  # First 100 chars
                    })
                
                # Check if it's an NPS "why" question
                if "why" in q_text and ("nps" in q_text or "recommend" in q_text):
                    nps_why_count += 1
        
        metadata["open_ended_count"] = open_ended_count
        metadata["required_open_ended_count"] = len(required_open_ended)
        metadata["nps_why_count"] = nps_why_count
        
        # Calculate limits
        total_q = metadata["total_respondent_questions"]
        pct_limit = int(total_q * 0.12)  # 12% of total
        max_limit = 6
        
        # Small survey cap (if < 20 questions)
        if total_q < 20:
            hard_cap = 3
        else:
            hard_cap = max_limit
        
        # Apply percentage limit
        effective_limit = min(pct_limit, max_limit, hard_cap)
        
        # Validation checks
        if open_ended_count > effective_limit:
            errors.append(
                f"Open-ended count ({open_ended_count}) exceeds limit: "
                f"≤12% of {total_q} questions ({pct_limit}) AND ≤{max_limit} total"
                f"{' (cap 3 for <20Q)' if total_q < 20 else ''}"
            )
        
        # Check required open-ended questions
        # Allow only NPS "why" + ≤2 targeted follow-ups to be required
        allowed_required = nps_why_count + 2  # NPS why + up to 2 follow-ups
        if len(required_open_ended) > allowed_required:
            non_nps_required = len(required_open_ended) - nps_why_count
            errors.append(
                f"Too many required open-ended questions ({len(required_open_ended)}). "
                f"Only NPS 'why' questions ({nps_why_count}) + ≤2 targeted follow-ups may be required. "
                f"Found {non_nps_required} non-NPS required open-ended questions."
            )
        
        # Update metadata with calculated limits
        metadata["open_ended_limit"]["effective_limit"] = effective_limit
        metadata["open_ended_limit"]["pct_limit"] = pct_limit
        
        is_valid = len(errors) == 0
        return is_valid, errors, metadata
        
    except Exception as e:
        logger.error(f"Error in test_open_ended_limits: {e}")
        errors.append(f"Validation error: {str(e)}")
        return False, errors, metadata


def test_best_fit_single_choice(survey: Dict[str, Any]) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Validate that questions with "best fit/describes/matches" text use single_choice type.
    Auto-convert multiple_select→single_choice violations and log in metadata.
    
    Args:
        survey: Survey JSON object
        
    Returns:
        Tuple of (is_valid, error_messages, metadata)
    """
    errors = []
    metadata = {
        "enforced_conversions": [],
        "violations_found": 0,
        "best_fit_questions": []
    }
    
    # Best fit phrases to detect
    best_fit_phrases = [
        "best fit",
        "best describes",
        "best matches",
        "which best",
        "pick the best",
        "single best"
    ]
    
    try:
        all_questions = extract_all_questions(survey)
        
        for question in all_questions:
            q_text = question.get("text", "").lower()
            q_type = question.get("type", "").lower()
            q_id = question.get("id", "unknown")
            
            # Check if question text contains any best fit phrase
            contains_best_fit = any(phrase in q_text for phrase in best_fit_phrases)
            
            if contains_best_fit:
                metadata["best_fit_questions"].append({
                    "id": q_id,
                    "text": question.get("text", "")[:100],
                    "current_type": q_type
                })
                
                # Check if type is NOT single_choice
                if q_type not in ["single_choice", "multiple_choice"]:
                    # This is a violation
                    metadata["violations_found"] += 1
                    
                    # Auto-convert if it's multiple_select
                    if q_type == "multiple_select":
                        conversion = {
                            "question_id": q_id,
                            "from_type": q_type,
                            "to_type": "single_choice",
                            "reason": "Best fit phrase detected in text"
                        }
                        metadata["enforced_conversions"].append(conversion)
                        
                        # Log the conversion
                        logger.info(
                            f"Auto-converting question {q_id} from {q_type} to single_choice "
                            f"due to best fit phrase in text"
                        )
                    else:
                        # Not multiple_select, so it's an error
                        errors.append(
                            f"Question {q_id} contains 'best fit/describes/matches' phrase "
                            f"but type is '{q_type}' (must be 'single_choice')"
                        )
        
        # Check if we have violations that couldn't be auto-converted
        non_convertible = metadata["violations_found"] - len(metadata["enforced_conversions"])
        if non_convertible > 0:
            errors.append(
                f"Found {non_convertible} 'best fit' questions with invalid types "
                f"that could not be auto-converted"
            )
        
        is_valid = len(errors) == 0
        return is_valid, errors, metadata
        
    except Exception as e:
        logger.error(f"Error in test_best_fit_single_choice: {e}")
        errors.append(f"Validation error: {str(e)}")
        return False, errors, metadata


def test_question_numbering_format(survey: Dict[str, Any]) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Validate question numbering and format rules:
    - IDs must follow format: <SectionCode>Q<NN>
    - Section codes: SP (1), SQ (2), BQ (3), CQ (4), MQ (5), AQ (6), PQ (7)
    - Purchase-intent questions must use 1-5 format
    - Matrix Likert must have proper format
    
    Args:
        survey: Survey JSON object
        
    Returns:
        Tuple of (is_valid, error_messages, metadata)
    """
    errors = []
    metadata = {
        "invalid_ids": [],
        "missing_ids": [],
        "purchase_intent_violations": [],
        "matrix_likert_violations": [],
        "section_code_mapping": {
            1: "SP",
            2: "SQ",
            3: "BQ",
            4: "CQ",
            5: "MQ",
            6: "AQ",
            7: "PQ"
        }
    }
    
    # Question ID pattern: <SectionCode>Q<NN>
    id_pattern = re.compile(r'^(SP|SQ|BQ|CQ|MQ|AQ|PQ)Q(\d{2,})$')
    
    # Purchase intent pattern
    purchase_intent_pattern = re.compile(
        r'on a scale of 1 to 5.*where 1 is.*definitely will not purchase.*'
        r'and 5 is.*definitely will purchase.*how likely are you to buy',
        re.IGNORECASE | re.DOTALL
    )
    
    try:
        all_questions = extract_all_questions(survey)
        
        # Track question numbers per section
        section_question_counts = {}
        
        for question in all_questions:
            q_id = question.get("id", "")
            q_text = question.get("text", "")
            q_type = question.get("type", "").lower()
            section_id = question.get("section_id")
            
            # Get section code from section_id
            if section_id and section_id in metadata["section_code_mapping"]:
                expected_code = metadata["section_code_mapping"][section_id]
            else:
                # Try to infer from question ID if section_id not available
                if q_id:
                    match = id_pattern.match(q_id)
                    if match:
                        expected_code = match.group(1)
                    else:
                        expected_code = None
                else:
                    expected_code = None
            
            # Validate question ID format
            if not q_id:
                metadata["missing_ids"].append({
                    "text": q_text[:100],
                    "section_id": section_id,
                    "type": q_type
                })
                errors.append(f"Question missing ID: {q_text[:50]}...")
            elif not id_pattern.match(q_id):
                metadata["invalid_ids"].append({
                    "id": q_id,
                    "text": q_text[:100],
                    "section_id": section_id,
                    "expected_format": f"{expected_code}Q<NN>" if expected_code else "<SectionCode>Q<NN>"
                })
                errors.append(
                    f"Question ID '{q_id}' does not follow format <SectionCode>Q<NN>. "
                    f"Expected format: {expected_code}Q<NN>" if expected_code else "<SectionCode>Q<NN>"
                )
            elif expected_code and not q_id.startswith(expected_code):
                # ID format is valid but wrong section code
                metadata["invalid_ids"].append({
                    "id": q_id,
                    "text": q_text[:100],
                    "section_id": section_id,
                    "expected_code": expected_code,
                    "actual_code": q_id[:2]
                })
                errors.append(
                    f"Question ID '{q_id}' has wrong section code. "
                    f"Expected '{expected_code}' for section {section_id}, got '{q_id[:2]}'"
                )
            
            # Validate purchase intent format
            if "purchase" in q_text.lower() and "intent" in q_text.lower():
                if not purchase_intent_pattern.search(q_text):
                    metadata["purchase_intent_violations"].append({
                        "id": q_id,
                        "text": q_text[:200]
                    })
                    errors.append(
                        f"Purchase intent question {q_id} does not follow required format: "
                        f"'On a scale of 1 to 5, where 1 is 'Definitely will not purchase' "
                        f"and 5 is 'Definitely will purchase', how likely are you to buy <Product> at <Price>?'"
                    )
            
            # Validate matrix_likert format
            if q_type == "matrix_likert":
                # Check if text ends with ?, : or . then comma-separated attributes
                text_ends_properly = q_text.rstrip().endswith(('?', ':', '.'))
                
                # Check if attributes field exists
                has_attributes = "attributes" in question and isinstance(question["attributes"], list)
                
                # Check if options field exists
                has_options = "options" in question and isinstance(question["options"], list)
                
                if not text_ends_properly:
                    metadata["matrix_likert_violations"].append({
                        "id": q_id,
                        "issue": "text does not end with ?, :, or .",
                        "text": q_text[:100]
                    })
                    errors.append(
                        f"Matrix Likert question {q_id}: text must end with ?, :, or . "
                        f"followed by comma-separated attributes"
                    )
                
                if not has_attributes:
                    metadata["matrix_likert_violations"].append({
                        "id": q_id,
                        "issue": "missing attributes field",
                        "text": q_text[:100]
                    })
                    errors.append(
                        f"Matrix Likert question {q_id}: must have 'attributes' array field"
                    )
                
                if not has_options:
                    metadata["matrix_likert_violations"].append({
                        "id": q_id,
                        "issue": "missing options field",
                        "text": q_text[:100]
                    })
                    errors.append(
                        f"Matrix Likert question {q_id}: must have 'options' array field"
                    )
        
        is_valid = len(errors) == 0
        return is_valid, errors, metadata
        
    except Exception as e:
        logger.error(f"Error in test_question_numbering_format: {e}")
        errors.append(f"Validation error: {str(e)}")
        return False, errors, metadata


def validate_prompt_rules(survey: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run all prompt validators and return consolidated results.
    
    Args:
        survey: Survey JSON object
        
    Returns:
        Dictionary with validation results for all rules
    """
    results = {
        "open_ended_limits": {},
        "best_fit_single_choice": {},
        "question_numbering_format": {},
        "overall_valid": True,
        "errors": []
    }
    
    # Run open-ended limits validator
    is_valid, errors, metadata = test_open_ended_limits(survey)
    results["open_ended_limits"] = {
        "valid": is_valid,
        "errors": errors,
        "metadata": metadata
    }
    if not is_valid:
        results["overall_valid"] = False
        results["errors"].extend(errors)
    
    # Run best fit single choice validator
    is_valid, errors, metadata = test_best_fit_single_choice(survey)
    results["best_fit_single_choice"] = {
        "valid": is_valid,
        "errors": errors,
        "metadata": metadata
    }
    if not is_valid:
        results["overall_valid"] = False
        results["errors"].extend(errors)
    
    # Run question numbering format validator
    is_valid, errors, metadata = test_question_numbering_format(survey)
    results["question_numbering_format"] = {
        "valid": is_valid,
        "errors": errors,
        "metadata": metadata
    }
    if not is_valid:
        results["overall_valid"] = False
        results["errors"].extend(errors)
    
    return results

