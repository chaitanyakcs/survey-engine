"""Pydantic models for survey data structures."""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class QuestionType(str, Enum):
    """Enumeration of question types."""
    # Basic question types
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
    
    # Open-ended variants
    OPEN_TEXT = "open_text"
    OPEN_END = "open_end"
    OPEN_ENDED = "open_ended"
    SINGLE_OPEN = "single_open"
    MULTIPLE_OPEN = "multiple_open"
    
    # Numeric variants
    NUMERIC_OPEN = "numeric_open"
    NUMERIC_GRID = "numeric_grid"
    
    # Matrix/Grid variants
    MATRIX_LIKERT = "matrix_likert"
    CONSTANT_SUM = "constant_sum"
    
    # Specialized types
    LIKERT = "likert"
    
    # Display types
    INSTRUCTION = "instruction"
    DISPLAY_ONLY = "display_only"
    
    # Methodology-specific types
    VAN_WESTENDORP = "van_westendorp"
    GABOR_GRANGER = "gabor_granger"
    CONJOINT = "conjoint"
    MAXDIFF = "maxdiff"
    
    # Fallback
    UNKNOWN = "unknown"


class Question(BaseModel):
    """Pydantic model for survey questions."""
    id: str = Field(..., description="Unique identifier for the question")
    text: str = Field(..., description="Question text")
    type: QuestionType = Field(..., description="Type of question")
    options: Optional[List[str]] = Field(default_factory=list, description="Available options for choice questions")
    scale_labels: Optional[Dict[str, str]] = Field(None, description="Scale labels for scale questions")
    required: bool = Field(True, description="Whether the question is required")
    order: Optional[int] = Field(None, description="Order of the question in the survey")
    category: Optional[str] = Field(None, description="Question category")
    methodology: Optional[str] = Field(None, description="Survey methodology")
    ai_rationale: Optional[str] = Field(None, description="AI rationale for the question")
    label: Optional[str] = Field(None, description="Programming notes and labels")
    description: Optional[str] = Field(None, description="Additional description or help text")
    validation: Optional[str] = Field(None, description="Validation rules as string")
    routing: Optional[Dict[str, Any]] = Field(None, description="Question routing logic")
    conditional_logic: Optional[Dict[str, Any]] = Field(None, description="Conditional display logic")


class SurveySection(BaseModel):
    """Pydantic model for survey sections."""
    id: int = Field(..., description="Unique identifier for the section")
    title: str = Field(..., description="Section title")
    description: Optional[str] = Field(None, description="Section description")
    questions: List[Question] = Field(..., description="Questions in this section")
    order: Optional[int] = Field(None, description="Order of the section in the survey")
    introText: Optional[Dict[str, Any]] = Field(None, description="Introduction text for the section")
    textBlocks: Optional[List[Dict[str, Any]]] = Field(None, description="Additional text blocks for the section")
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True


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


class SurveyCreateWithSections(BaseModel):
    """Pydantic model for creating a survey with sections format."""
    title: str = Field(..., description="Survey title")
    description: Optional[str] = Field(None, description="Survey description")
    sections: List[SurveySection] = Field(..., description="List of survey sections")
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


class QuestionUpdate(BaseModel):
    """Pydantic model for updating individual questions."""
    text: Optional[str] = Field(None, description="Question text")
    type: Optional[QuestionType] = Field(None, description="Type of question")
    options: Optional[List[str]] = Field(None, description="Available options for choice questions")
    scale_labels: Optional[Dict[str, str]] = Field(None, description="Scale labels for scale questions")
    required: Optional[bool] = Field(None, description="Whether the question is required")
    category: Optional[str] = Field(None, description="Question category")
    methodology: Optional[str] = Field(None, description="Survey methodology")
    description: Optional[str] = Field(None, description="Additional description or help text")
    label: Optional[str] = Field(None, description="Programming notes and labels")
    validation: Optional[str] = Field(None, description="Validation rules as string")
    routing: Optional[Dict[str, Any]] = Field(None, description="Question routing logic")
    conditional_logic: Optional[Dict[str, Any]] = Field(None, description="Conditional display logic")
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True


class SectionUpdate(BaseModel):
    """Pydantic model for updating survey sections."""
    title: Optional[str] = Field(None, description="Section title")
    description: Optional[str] = Field(None, description="Section description")
    questions: Optional[List[Question]] = Field(None, description="Questions in this section")
    order: Optional[int] = Field(None, description="Order of the section in the survey")
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True
