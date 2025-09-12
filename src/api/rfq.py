from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db, RFQ, Survey
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4
import logging
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rfq", tags=["RFQ"])


class RFQSubmissionRequest(BaseModel):
    title: Optional[str] = None
    description: str
    product_category: Optional[str] = None
    target_segment: Optional[str] = None
    research_goal: Optional[str] = None


class RFQSubmissionResponse(BaseModel):
    workflow_id: str
    survey_id: str
    status: str


@router.post("/", response_model=RFQSubmissionResponse)
async def submit_rfq(
    request: RFQSubmissionRequest,
    db: Session = Depends(get_db)
) -> RFQSubmissionResponse:
    """
    Submit new RFQ for survey generation
    Returns: workflow_id, survey_id, status (async processing)
    """
    logger.info(f"🚀 [RFQ API] Received RFQ submission: title='{request.title}', description_length={len(request.description)}, product_category='{request.product_category}'")
    
    try:
        # Generate unique IDs
        workflow_id = f"survey-gen-{str(uuid4())}"
        survey_id = f"survey-{str(uuid4())}"
        
        logger.info(f"📋 [RFQ API] Generated workflow_id={workflow_id}, survey_id={survey_id}")
        
        # Create RFQ record
        logger.info("💾 [RFQ API] Creating RFQ database record")
        rfq = RFQ(
            title=request.title,
            description=request.description,
            product_category=request.product_category,
            target_segment=request.target_segment,
            research_goal=request.research_goal
        )
        db.add(rfq)
        db.commit()
        db.refresh(rfq)
        logger.info(f"✅ [RFQ API] RFQ record created with ID: {rfq.id}")
        
        # Create initial survey record
        logger.info("💾 [RFQ API] Creating initial Survey database record")
        survey = Survey(
            rfq_id=rfq.id,
            status="started",
            model_version="gpt-4o-mini"  # Default model
        )
        db.add(survey)
        db.commit()
        db.refresh(survey)
        logger.info(f"✅ [RFQ API] Survey record created with ID: {survey.id}")
        
        # Process RFQ directly through workflow (consolidated approach)
        logger.info(f"🔄 [RFQ API] Starting direct workflow processing: workflow_id={workflow_id}")
        
        try:
            from src.services.workflow_service import WorkflowService
            from src.main import manager  # Import the connection manager
            
            # Initialize workflow service with connection manager
            workflow_service = WorkflowService(db, manager)
            
            # Start workflow processing in background with a small delay to ensure WebSocket connection
            asyncio.create_task(process_rfq_workflow_async(
                workflow_service=workflow_service,
                title=request.title,
                description=request.description,
                product_category=request.product_category,
                target_segment=request.target_segment,
                research_goal=request.research_goal,
                workflow_id=workflow_id,
                survey_id=str(survey.id)
            ))
            
            logger.info(f"✅ [RFQ API] Workflow processing started in background: workflow_id={workflow_id}")
            
        except Exception as e:
            logger.error(f"❌ [RFQ API] Failed to start workflow processing: {str(e)}")
            # Mark survey as pending if workflow fails to start
            survey.status = "pending"
            db.commit()
        
        # Return immediate response
        response = RFQSubmissionResponse(
            workflow_id=workflow_id,
            survey_id=str(survey.id),
            status="started"
        )
        
        logger.info(f"🎉 [RFQ API] Returning async response: {response.model_dump()}")
        return response
        
    except Exception as e:
        logger.error(f"❌ [RFQ API] Failed to process RFQ: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process RFQ: {str(e)}")


async def process_rfq_workflow_async(
    workflow_service,
    title: str,
    description: str,
    product_category: str,
    target_segment: str,
    research_goal: str,
    workflow_id: str,
    survey_id: str
):
    """
    Process RFQ workflow asynchronously with detailed logging
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"🚀 [Async Workflow] Starting RFQ processing: title='{title}', workflow_id={workflow_id}")
        
        # Add a small delay to ensure WebSocket connection is established
        logger.info("⏳ [Async Workflow] Waiting 2 seconds for WebSocket connection to establish...")
        await asyncio.sleep(2)
        
        # Process through workflow with detailed logging
        result = await workflow_service.process_rfq(
            title=title,
            description=description,
            product_category=product_category,
            target_segment=target_segment,
            research_goal=research_goal,
            workflow_id=workflow_id,
            survey_id=survey_id
        )
        
        logger.info(f"✅ [Async Workflow] Workflow completed successfully: {result.status}")
        
    except Exception as e:
        logger.error(f"❌ [Async Workflow] Workflow failed: {str(e)}", exc_info=True)