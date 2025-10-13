"""Pydantic models for survey data structures."""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class QuestionType(str, Enum):
    """Enumeration of question types."""
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT = "text"
    SCALE = "scale"
    RATING = "rating"
    YES_NO = "yes_no"
    DROPDOWN = "dropdown"
    MATRIX = "matrix"
    RANKING = "ranking"
    NUMERIC = "numeric"
    DATE = "date"
    BOOLEAN = "boolean"
    FILE_UPLOAD = "file_upload"
    # Methodology-specific types
    VAN_WESTENDORP = "van_westendorp"
    GABOR_GRANGER = "gabor_granger"
    CONJOINT = "conjoint"
    MAXDIFF = "maxdiff"
    UNKNOWN = "unknown"


class Question(BaseModel):
    """Pydantic model for survey questions."""
    id: str = Field(..., description="Unique identifier for the question")
    text: str = Field(..., description="Question text")
    type: QuestionType = Field(..., description="Type of question")
    options: Optional[List[str]] = Field(default_factory=list, description="Available options for choice questions")
    required: bool = Field(True, description="Whether the question is required")
    order: Optional[int] = Field(None, description="Order of the question in the survey")
    description: Optional[str] = Field(None, description="Additional description or help text")
    validation: Optional[str] = Field(None, description="Validation rules as string")
    methodology: Optional[str] = Field(None, description="Survey methodology")
    routing: Optional[Dict[str, Any]] = Field(None, description="Question routing logic")
    conditional_logic: Optional[Dict[str, Any]] = Field(None, description="Conditional display logic")


class SurveyCreate(BaseModel):
    """Pydantic model for creating a survey."""
    title: str = Field(..., description="Survey title")
    description: Optional[str] = Field(None, description="Survey description")
    questions: List[Question] = Field(..., description="List of survey questions")
    settings: Optional[Dict[str, Any]] = Field(None, description="Survey settings")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True


class SurveyUpdate(BaseModel):
    """Pydantic model for updating a survey."""
    title: Optional[str] = Field(None, description="Survey title")
    description: Optional[str] = Field(None, description="Survey description")
    questions: Optional[List[Question]] = Field(None, description="List of survey questions")
    settings: Optional[Dict[str, Any]] = Field(None, description="Survey settings")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True


class SurveyResponse(BaseModel):
    """Pydantic model for survey responses."""
    id: str = Field(..., description="Unique identifier for the response")
    survey_id: str = Field(..., description="ID of the survey")
    answers: Dict[str, Any] = Field(..., description="User answers")
    submitted_at: Optional[str] = Field(None, description="Submission timestamp")
    user_id: Optional[str] = Field(None, description="User identifier")
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True
