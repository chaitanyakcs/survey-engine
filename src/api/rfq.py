from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db, RFQ, Survey
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4
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
        
        # Send to WebSocket server for async processing with retry
        logger.info(f"🔄 [RFQ API] Sending to WebSocket server for async processing: workflow_id={workflow_id}")
        
        import httpx
        import asyncio
        
        max_retries = 10  # Increased retries
        retry_delay = 3.0  # Increased initial delay
        
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:  # Increased timeout
                    ws_response = await client.post(
                        "http://localhost:8001/api/v1/rfq/",
                        json={
                            "title": request.title,
                            "description": request.description,
                            "product_category": request.product_category,
                            "target_segment": request.target_segment,
                            "research_goal": request.research_goal,
                            "workflow_id": workflow_id,
                            "survey_id": str(survey.id),
                            "rfq_id": str(rfq.id)
                        }
                    )
                    ws_response.raise_for_status()
                    logger.info(f"✅ [RFQ API] WebSocket server accepted request: {ws_response.status_code}")
                    break  # Success, exit retry loop
                    
            except Exception as ws_error:
                logger.warning(f"⚠️ [RFQ API] Attempt {attempt + 1}/{max_retries} failed to connect to WebSocket server: {str(ws_error)}")
                
                if attempt == max_retries - 1:
                    # Final attempt failed - but don't fail the request, just log and continue
                    logger.error(f"❌ [RFQ API] All {max_retries} attempts failed to connect to WebSocket server")
                    logger.warning("⚠️ [RFQ API] Continuing without async processing - survey will be marked as pending")
                    # Don't fail the request, just mark survey as pending
                    survey.status = "pending"
                    db.commit()
                    # Return success but with pending status
                    response = RFQSubmissionResponse(
                        workflow_id=workflow_id,
                        survey_id=str(survey.id),
                        status="pending"
                    )
                    logger.info(f"🎉 [RFQ API] Returning pending response: {response.model_dump()}")
                    return response
                else:
                    # Wait before retry
                    logger.info(f"⏳ [RFQ API] Waiting {retry_delay}s before retry...")
                    await asyncio.sleep(retry_delay)
                    retry_delay = min(retry_delay * 1.2, 10.0)  # Gradual backoff, max 10s
        
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