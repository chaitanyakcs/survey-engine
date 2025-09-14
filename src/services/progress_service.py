"""Real-time progress service for golden example creation."""

import logging
from typing import Dict, Any, Optional
from ..services.websocket_client import WebSocketNotificationService

logger = logging.getLogger(__name__)

class ProgressService:
    """Service for managing real-time progress updates during golden example creation."""
    
    def __init__(self, ws_client: Optional[WebSocketNotificationService] = None):
        self.ws_client = ws_client
    
    async def send_progress_update(self, session_id: str, step: str, percent: int, message: str, details: Optional[Dict[str, Any]] = None):
        """Send a progress update via WebSocket."""
        if not self.ws_client:
            logger.warning(f"⚠️ [ProgressService] No WebSocket client available, skipping progress update")
            return
        
        progress_data = {
            "type": "golden_example_progress",
            "session_id": session_id,
            "step": step,
            "percent": percent,
            "message": message,
            "details": details or {}
        }
        
        try:
            logger.info(f"📡 [ProgressService] Sending progress update: {step} ({percent}%)")
            await self.ws_client.send_progress_update(session_id, progress_data)
            logger.info(f"✅ [ProgressService] Progress update sent successfully")
        except Exception as e:
            logger.error(f"❌ [ProgressService] Failed to send progress update: {str(e)}")
    
    async def send_field_extraction_progress(self, session_id: str, step: str, message: str, extracted_data: Optional[Dict[str, Any]] = None):
        """Send field extraction progress update."""
        progress_mapping = {
            "analyzing_rfq": {"percent": 10, "message": "Analyzing RFQ content..."},
            "analyzing_survey": {"percent": 20, "message": "Analyzing survey structure..."},
            "extracting_methodologies": {"percent": 30, "message": "Identifying methodologies..."},
            "classifying_industry": {"percent": 40, "message": "Classifying industry category..."},
            "determining_goals": {"percent": 50, "message": "Determining research goals..."},
            "assessing_quality": {"percent": 60, "message": "Assessing survey quality..."},
            "generating_title": {"percent": 70, "message": "Generating suggested title..."},
            "validating_fields": {"percent": 80, "message": "Validating extracted fields..."},
            "completed": {"percent": 100, "message": "Field extraction completed!"}
        }
        
        step_info = progress_mapping.get(step, {"percent": 0, "message": message})
        
        await self.send_progress_update(
            session_id=session_id,
            step=step,
            percent=step_info["percent"],
            message=step_info["message"],
            details={
                "extracted_data": extracted_data,
                "step_details": step
            }
        )

# Global instance
progress_service = ProgressService()
