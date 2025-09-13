"""API endpoints for intelligent field extraction during golden example creation."""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging
import uuid

from ..database import get_db
from ..services.field_extraction_service import field_extraction_service
from ..services.progress_service import progress_service
from ..services.websocket_client import WebSocketClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/field-extraction", tags=["Field Extraction"])

class FieldExtractionRequest(BaseModel):
    rfq_text: str
    survey_json: Dict[str, Any]
    session_id: Optional[str] = None

class FieldExtractionResponse(BaseModel):
    methodology_tags: List[str]
    industry_category: str
    research_goal: str
    quality_score: float
    suggested_title: str
    confidence_level: float
    reasoning: Dict[str, str]

@router.post("/extract", response_model=FieldExtractionResponse)
async def extract_fields(
    request: FieldExtractionRequest,
    db: Session = Depends(get_db)
):
    """
    Extract golden example fields from RFQ and Survey content with real-time progress.
    """
    session_id = request.session_id or str(uuid.uuid4())
    
    logger.info(f"🔍 [Field Extraction API] Starting field extraction for session: {session_id}")
    logger.info(f"📝 [Field Extraction API] RFQ length: {len(request.rfq_text)} chars")
    logger.info(f"📊 [Field Extraction API] Survey keys: {list(request.survey_json.keys())}")
    
    try:
        # Initialize progress service with WebSocket client
        ws_client = WebSocketClient()
        progress_service.ws_client = ws_client
        
        # Send initial progress
        await progress_service.send_field_extraction_progress(
            session_id=session_id,
            step="analyzing_rfq",
            message="Starting field extraction..."
        )
        
        # Extract fields with progress updates
        extracted_fields = await field_extraction_service.extract_fields(
            rfq_text=request.rfq_text,
            survey_json=request.survey_json
        )
        
        # Send completion progress
        await progress_service.send_field_extraction_progress(
            session_id=session_id,
            step="completed",
            message="Field extraction completed!",
            extracted_data=extracted_fields
        )
        
        logger.info(f"✅ [Field Extraction API] Field extraction completed for session: {session_id}")
        logger.info(f"📊 [Field Extraction API] Extracted fields: {extracted_fields}")
        
        return FieldExtractionResponse(**extracted_fields)
        
    except Exception as e:
        logger.error(f"❌ [Field Extraction API] Field extraction failed for session {session_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Field extraction failed: {str(e)}")

@router.websocket("/progress/{session_id}")
async def progress_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time progress updates during field extraction.
    """
    await websocket.accept()
    logger.info(f"🔌 [Field Extraction API] WebSocket connected for session: {session_id}")
    
    try:
        while True:
            # Keep connection alive and handle any incoming messages
            data = await websocket.receive_text()
            logger.debug(f"📨 [Field Extraction API] Received WebSocket message: {data}")
            
    except WebSocketDisconnect:
        logger.info(f"🔌 [Field Extraction API] WebSocket disconnected for session: {session_id}")
    except Exception as e:
        logger.error(f"❌ [Field Extraction API] WebSocket error for session {session_id}: {str(e)}")
        await websocket.close()
