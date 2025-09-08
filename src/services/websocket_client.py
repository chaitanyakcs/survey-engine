import logging
from typing import Dict, Any, Optional
from src.config import settings

logger = logging.getLogger(__name__)

class WebSocketNotificationService:
    """
    Service to communicate with the WebSocket server for real-time updates
    """
    
    def __init__(self, connection_manager=None):
        self.connection_manager = connection_manager
        logger.info(f"🔗 [WebSocket Client] Initialized with connection manager: {connection_manager is not None}")
    
    async def send_progress_update(self, workflow_id: str, message: Dict[str, Any]) -> bool:
        """
        Send progress update via WebSocket connection manager
        """
        try:
            logger.info(f"📤 [WebSocket Client] Sending progress update for workflow_id={workflow_id}: {message.get('type', 'unknown')}")
            
            if self.connection_manager:
                await self.connection_manager.broadcast_to_workflow(workflow_id, message)
                logger.debug(f"✅ [WebSocket Client] Progress update sent successfully for workflow_id={workflow_id}")
                return True
            else:
                logger.warning(f"⚠️ [WebSocket Client] No connection manager available - continuing without real-time updates")
                return False
                    
        except Exception as e:
            logger.warning(f"⚠️ [WebSocket Client] Failed to send progress update for workflow_id={workflow_id}: {str(e)} - continuing without real-time updates")
            return False
    
    async def notify_workflow_completion(self, workflow_id: str, survey_id: str, status: str) -> bool:
        """
        Notify WebSocket server that workflow is completed
        """
        message = {
            "type": "completed",
            "survey_id": survey_id,
            "status": status
        }
        return await self.send_progress_update(workflow_id, message)
    
    async def notify_workflow_error(self, workflow_id: str, error_message: str) -> bool:
        """
        Notify WebSocket server that workflow failed
        """
        message = {
            "type": "error",
            "message": f"Generation failed: {error_message}"
        }
        return await self.send_progress_update(workflow_id, message)