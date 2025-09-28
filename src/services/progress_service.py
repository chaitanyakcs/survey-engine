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
        # Import progress tracker
        from .progress_tracker import get_progress_tracker
        tracker = get_progress_tracker(session_id or "field_extraction")

        # Use progress tracker instead of hardcoded percentages
        if step == "completed":
            step_info = tracker.get_completion_data("extraction_complete")
        else:
            step_info = tracker.get_progress_data(step)

        # Override message if provided
        if message:
            step_info["message"] = message
        
        # Send via field extraction WebSocket if available
        if hasattr(self, 'field_extraction_manager') and self.field_extraction_manager:
            message_data = {
                "type": "golden_example_progress",
                "step": step,
                "percent": step_info["percent"],
                "message": step_info["message"],
                "extracted_data": extracted_data
            }
            await self.field_extraction_manager.send_progress(session_id, message_data)
            logger.info(f"📤 [ProgressService] Field extraction progress sent via WebSocket for session {session_id}: {step}")
        else:
            # Fallback to regular progress update
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
