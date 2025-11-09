"""
Shared utilities for formatting prompt content
Ensures consistency between prompt generation and API responses
"""

from typing import List, Dict, Any


def format_golden_questions_for_prompt(questions: List[Dict[str, Any]]) -> List[str]:
    """
    Format golden questions exactly as they appear in the prompt builder.
    This ensures the UI shows exactly what was sent to the LLM.
    
    Args:
        questions: List of question dictionaries with:
            - question_text: str
            - question_type: str
            - quality_score: float (optional)
            - human_verified: bool (optional)
            - annotation_comment: str (optional)
    
    Returns:
        List of formatted strings representing the questions in prompt format
    """
    formatted_lines = []
    
    for i, question in enumerate(questions[:8], 1):  # Limit to 8 as in prompt builder
        question_text = question.get('question_text', '')
        question_type = question.get('question_type', 'unknown')
        quality_score = question.get('quality_score', 0.0)
        human_verified = question.get('human_verified', False)
        annotation_comment = question.get('annotation_comment', '')
        
        # Format question example
        formatted_lines.append(f"**Example {i}:** \"{question_text}\"")
        formatted_lines.append(
            f"**Type:** {question_type} | **Quality:** {quality_score:.2f}/1.0 | "
            f"{'✅ Human Verified' if human_verified else '🤖 AI Generated'}"
        )
        
        # Add expert guidance if available (truncated to 200 chars as in prompt builder)
        if annotation_comment:
            max_comment_length = 200
            truncated_comment = (
                annotation_comment[:max_comment_length] + "..."
                if len(annotation_comment) > max_comment_length
                else annotation_comment
            )
            formatted_lines.append(f"**Expert Guidance:** {truncated_comment}")
            formatted_lines.append("")
        else:
            formatted_lines.append("")
    
    return formatted_lines

