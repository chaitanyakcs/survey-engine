import httpx
import logging
from typing import Dict, Any, Optional
from src.config import settings

logger = logging.getLogger(__name__)

class WebSocketNotificationService:
    """
    Service to communicate with the WebSocket server for real-time updates
    """
    
    def __init__(self, websocket_server_url: str = "http://127.0.0.1:8001"):
        self.websocket_server_url = websocket_server_url
        logger.info(f"🔗 [WebSocket Client] Initialized with server URL: {websocket_server_url}")
    
    async def send_progress_update(self, workflow_id: str, message: Dict[str, Any]) -> bool:
        """
        Send progress update to WebSocket server to broadcast to connected clients
        """
        try:
            logger.info(f"📤 [WebSocket Client] Sending progress update for workflow_id={workflow_id}: {message.get('type', 'unknown')}")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.websocket_server_url}/internal/broadcast/{workflow_id}",
                    json=message,
                    timeout=2.0  # Reduced timeout
                )
                
                if response.status_code == 200:
                    logger.debug(f"✅ [WebSocket Client] Progress update sent successfully for workflow_id={workflow_id}")
                    return True
                else:
                    logger.warning(f"⚠️ [WebSocket Client] WebSocket server not available. Status: {response.status_code} - continuing without real-time updates")
                    return False
                    
        except Exception as e:
            logger.warning(f"⚠️ [WebSocket Client] WebSocket server not available for workflow_id={workflow_id}: {str(e)} - continuing without real-time updates")
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