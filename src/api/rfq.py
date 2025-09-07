from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src.services.workflow_service import WorkflowService
from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)

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
    logger.info(f"🚀 [RFQ API] Received RFQ submission: title='{request.title}', description_length={len(request.description)}, product_category='{request.product_category}'")
    
    try:
        logger.info("📋 [RFQ API] Creating WorkflowService instance")
        workflow_service = WorkflowService(db)
        
        logger.info("⚙️ [RFQ API] Starting workflow processing...")
        result = await workflow_service.process_rfq(
            title=request.title,
            description=request.description,
            product_category=request.product_category,
            target_segment=request.target_segment,
            research_goal=request.research_goal
        )
        
        logger.info(f"✅ [RFQ API] Workflow completed successfully: survey_id={result.survey_id}, status={result.status}, golden_examples_used={result.golden_examples_used}")
        
        response = RFQSubmissionResponse(
            survey_id=str(result.survey_id),
            estimated_completion_time=result.estimated_completion_time,
            golden_examples_used=result.golden_examples_used,
            status=result.status
        )
        
        logger.info(f"🎉 [RFQ API] Returning response: {response.model_dump()}")
        return response
        
    except Exception as e:
        logger.error(f"❌ [RFQ API] Failed to process RFQ: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process RFQ: {str(e)}")