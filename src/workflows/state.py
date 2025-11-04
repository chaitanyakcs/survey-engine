from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from uuid import UUID


class SurveyGenerationState(BaseModel):
    # Basic RFQ fields
    rfq_id: Optional[UUID] = None
    survey_id: Optional[str] = None
    workflow_id: Optional[str] = None
    rfq_text: str
    rfq_title: Optional[str] = None
    title: Optional[str] = None  # Alias for rfq_title for compatibility
    description: Optional[str] = None  # Alias for rfq_text for compatibility
    product_category: Optional[str] = None
    target_segment: Optional[str] = None
    research_goal: Optional[str] = None
    rfq_embedding: Optional[List[float]] = None

    # Enhanced RFQ fields
    enhanced_rfq_data: Optional[Dict[str, Any]] = None
    unmapped_context: Optional[str] = None

    # Workflow tracking fields
    current_step: Optional[str] = None
    survey_output: Optional[Dict[str, Any]] = None
    estimated_completion_time: Optional[int] = None
    golden_examples_used: int = 0
    messages: List[str] = []
    embedding: Optional[List[float]] = None
    start_time: Optional[float] = None
    progress_tracking: Optional[Dict[str, Any]] = None
    
    golden_examples: List[Dict[str, Any]] = []
    methodology_blocks: List[Dict[str, Any]] = []
    template_questions: List[Dict[str, Any]] = []
    # Multi-level RAG
    golden_sections: List[Dict[str, Any]] = []
    golden_questions: List[Dict[str, Any]] = []
    feedback_digest: Optional[Dict[str, Any]] = None  # Feedback digest from questions with comments
    
    context: Dict[str, Any] = {}
    
    raw_survey: Optional[Dict[str, Any]] = None
    generated_survey: Optional[Dict[str, Any]] = None
    pillar_scores: Optional[Dict[str, Any]] = None
    
    validation_results: Dict[str, Any] = {}
    quality_gate_passed: bool = False
    
    golden_similarity_score: Optional[float] = None
    used_golden_examples: List[UUID] = []
    used_golden_questions: List[UUID] = []  # Questions retrieved via similarity matching
    used_golden_sections: List[UUID] = []
    used_feedback_questions: List[UUID] = []  # Questions with comments from feedback digest
    
    retry_count: int = 0
    max_retries: int = 1  # Reduced to prevent long loops
    
    # Workflow timing for loop prevention
    workflow_start_time: Optional[float] = None
    
    # Human review state
    pending_human_review: bool = False
    workflow_paused: bool = False
    prompt_approved: bool = False
    system_prompt: Optional[str] = None
    review_id: Optional[int] = None

    error_message: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True