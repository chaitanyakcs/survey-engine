from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src.services.workflow_service import WorkflowService
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/rfq", tags=["RFQ"])


class RFQSubmissionRequest(BaseModel):
    title: Optional[str] = None
    description: str
    product_category: Optional[str] = None
    target_segment: Optional[str] = None
    research_goal: Optional[str] = None


class RFQSubmissionResponse(BaseModel):
    survey_id: str
    estimated_completion_time: int
    golden_examples_used: int
    status: str


@router.post("/", response_model=RFQSubmissionResponse)
async def submit_rfq(
    request: RFQSubmissionRequest,
    db: Session = Depends(get_db)
) -> RFQSubmissionResponse:
    """
    Submit new RFQ for survey generation
    Returns: survey_id, estimated_completion_time, golden_examples_used
    """
    try:
        workflow_service = WorkflowService(db)
        result = await workflow_service.process_rfq(
            title=request.title,
            description=request.description,
            product_category=request.product_category,
            target_segment=request.target_segment,
            research_goal=request.research_goal
        )
        
        return RFQSubmissionResponse(
            survey_id=str(result.survey_id),
            estimated_completion_time=result.estimated_completion_time,
            golden_examples_used=result.golden_examples_used,
            status=result.status
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process RFQ: {str(e)}")