"""
User-friendly error messages and error handling utilities
"""
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class UserFriendlyError(Exception):
    """Custom exception for user-friendly error messages"""
    def __init__(self, message: str, technical_details: Optional[str] = None, action_required: Optional[str] = None):
        self.message = message
        self.technical_details = technical_details
        self.action_required = action_required
        super().__init__(message)

def get_api_configuration_error() -> Dict[str, Any]:
    """Get user-friendly API configuration error message"""
    return {
        "title": "AI Service Configuration Required",
        "message": "The AI service needs to be configured to generate surveys.",
        "details": [
            "This application uses AI to automatically generate surveys from your documents.",
            "To enable this feature, you need to configure an AI service provider."
        ],
        "solutions": [
            {
                "title": "Option 1: Use Replicate (Recommended)",
                "steps": [
                    "1. Visit https://replicate.com and create a free account",
                    "2. Go to your account settings and generate an API token",
                    "3. Contact your administrator to add the token to the system",
                    "4. The token will be securely stored and used for AI generation"
                ],
                "note": "Replicate offers free credits and is easy to set up"
            },
            {
                "title": "Option 2: Use OpenAI (Alternative)",
                "steps": [
                    "1. Visit https://platform.openai.com and create an account",
                    "2. Generate an API key from your dashboard",
                    "3. Contact your administrator to configure the system",
                    "4. OpenAI provides high-quality AI models for survey generation"
                ],
                "note": "OpenAI requires a paid account but offers excellent results"
            }
        ],
        "contact_support": "If you need help setting up AI services, please contact your system administrator or support team."
    }

def get_document_parsing_error() -> Dict[str, Any]:
    """Get user-friendly document parsing error message"""
    return {
        "title": "Document Could Not Be Processed",
        "message": "We couldn't convert your document into a survey. This usually happens for a few common reasons.",
        "common_causes": [
            {
                "issue": "Unsupported File Format",
                "description": "The file you uploaded isn't in a supported format",
                "solution": "Please upload a .docx (Word document) file"
            },
            {
                "issue": "AI Service Not Available",
                "description": "The AI service needed to process your document isn't configured",
                "solution": "Contact your administrator to set up AI services"
            },
            {
                "issue": "Document Content Issues",
                "description": "The document might be corrupted or contain unsupported content",
                "solution": "Try opening the document in Word and saving it again, then re-upload"
            },
            {
                "issue": "Network Connection",
                "description": "There might be a temporary connection issue",
                "solution": "Check your internet connection and try again"
            }
        ],
        "next_steps": [
            "Try uploading a different document",
            "Make sure the file is a .docx format",
            "Contact support if the problem continues"
        ]
    }

def get_survey_generation_error() -> Dict[str, Any]:
    """Get user-friendly survey generation error message"""
    return {
        "title": "Survey Generation Failed",
        "message": "We couldn't generate a survey from your request. This might be due to configuration or content issues.",
        "possible_causes": [
            "AI service is not properly configured",
            "The request content is too complex or unclear",
            "Temporary service unavailability",
            "Content doesn't contain enough information for survey generation"
        ],
        "solutions": [
            "Try simplifying your request or providing more details",
            "Check if AI services are properly configured",
            "Contact support if the issue persists"
        ]
    }

def format_technical_error(error: Exception, context: str = "") -> Dict[str, Any]:
    """Format a technical error into a user-friendly message"""
    error_type = type(error).__name__
    
    # Log the technical error for debugging
    logger.error(f"Technical error in {context}: {error_type}: {str(error)}")
    
    # Map common technical errors to user-friendly messages
    if "REPLICATE_API_TOKEN" in str(error):
        return get_api_configuration_error()
    elif "document" in str(error).lower() or "docx" in str(error).lower():
        return get_document_parsing_error()
    elif "survey" in str(error).lower() or "generation" in str(error).lower():
        return get_survey_generation_error()
    else:
        return {
            "title": "Something Went Wrong",
            "message": "An unexpected error occurred while processing your request.",
            "details": [
                "We're sorry for the inconvenience. Our team has been notified of this issue.",
                "Please try again in a few moments, or contact support if the problem continues."
            ],
            "technical_info": f"Error type: {error_type}",
            "contact_support": "If this problem persists, please contact support with the error details above."
        }

def create_error_response(error: Exception, context: str = "") -> Dict[str, Any]:
    """Create a complete error response with user-friendly messaging"""
    if isinstance(error, UserFriendlyError):
        return {
            "error": True,
            "user_message": error.message,
            "technical_details": error.technical_details,
            "action_required": error.action_required
        }
    else:
        formatted_error = format_technical_error(error, context)
        return {
            "error": True,
            "user_message": formatted_error["message"],
            "title": formatted_error["title"],
            "details": formatted_error.get("details", []),
            "solutions": formatted_error.get("solutions", []),
            "contact_support": formatted_error.get("contact_support", "")
        }

