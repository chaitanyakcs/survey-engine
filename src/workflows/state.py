from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from uuid import UUID


class SurveyGenerationState(BaseModel):
    rfq_id: Optional[UUID] = None
    survey_id: Optional[str] = None
    workflow_id: Optional[str] = None
    rfq_text: str
    rfq_title: Optional[str] = None
    product_category: Optional[str] = None
    target_segment: Optional[str] = None
    research_goal: Optional[str] = None
    rfq_embedding: Optional[List[float]] = None
    
    golden_examples: List[Dict[str, Any]] = []
    methodology_blocks: List[Dict[str, Any]] = []
    template_questions: List[Dict[str, Any]] = []
    
    context: Dict[str, Any] = {}
    
    raw_survey: Optional[Dict[str, Any]] = None
    generated_survey: Optional[Dict[str, Any]] = None
    pillar_scores: Optional[Dict[str, Any]] = None
    
    validation_results: Dict[str, Any] = {}
    quality_gate_passed: bool = False
    
    golden_similarity_score: Optional[float] = None
    used_golden_examples: List[UUID] = []
    
    retry_count: int = 0
    max_retries: int = 2
    
    # Human review state
    pending_human_review: bool = False
    system_prompt: Optional[str] = None
    review_id: Optional[int] = None
    
    error_message: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True