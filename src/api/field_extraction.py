"""API endpoints for intelligent field extraction during golden example creation."""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging
import uuid
import json

from ..database import get_db
from ..services.field_extraction_service import field_extraction_service
from ..services.progress_service import progress_service
# from ..services.websocket_client import WebSocketNotificationService  # May be used later

logger = logging.getLogger(__name__)

# Field extraction connection manager
class FieldExtractionConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)
        logger.info(f"🔌 [Field Extraction WebSocket] Connection established for session_id={session_id}. Total active: {len(self.active_connections[session_id])}")

    def disconnect(self, websocket: WebSocket, session_id: str):
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        logger.info(f"🔌 [Field Extraction WebSocket] Connection closed for session_id={session_id}")

    async def send_progress(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_text(json.dumps(message))
                    logger.debug(f"📤 [Field Extraction WebSocket] Sent message to session_id={session_id}: {message.get('type', 'unknown')}")
                except Exception as e:
                    logger.warning(f"⚠️ [Field Extraction WebSocket] Failed to send message to session_id={session_id}: {str(e)}")

field_extraction_manager = FieldExtractionConnectionManager()

# RFQ parsing connection manager (reusing the same pattern)
class RFQParsingConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        logger.info(f"🔌 [RFQ Parsing WebSocket] Accepting connection for session_id={session_id}")
        await websocket.accept()
        logger.info(f"✅ [RFQ Parsing WebSocket] WebSocket accepted for session_id={session_id}")
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)
        logger.info(f"🔌 [RFQ Parsing WebSocket] Connection established for session_id={session_id}. Total active: {len(self.active_connections[session_id])}")

    def disconnect(self, websocket: WebSocket, session_id: str):
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        logger.info(f"🔌 [RFQ Parsing WebSocket] Connection closed for session_id={session_id}")

    async def send_progress(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_text(json.dumps(message))
                    logger.debug(f"📤 [RFQ Parsing WebSocket] Sent message to session_id={session_id}: {message.get('type', 'unknown')}")
                except Exception as e:
                    logger.warning(f"⚠️ [RFQ Parsing WebSocket] Failed to send message to session_id={session_id}: {str(e)}")

rfq_parsing_manager = RFQParsingConnectionManager()

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
        # Initialize progress service with field extraction manager
        progress_service.field_extraction_manager = field_extraction_manager
        
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
    await field_extraction_manager.connect(websocket, session_id)
    
    try:
        while True:
            # Keep connection alive and handle any incoming messages
            data = await websocket.receive_text()
            logger.debug(f"📨 [Field Extraction API] Received WebSocket message: {data}")
            
    except WebSocketDisconnect:
        field_extraction_manager.disconnect(websocket, session_id)
    except Exception as e:
        logger.error(f"❌ [Field Extraction API] WebSocket error for session {session_id}: {str(e)}")
        field_extraction_manager.disconnect(websocket, session_id)
        await websocket.close()

