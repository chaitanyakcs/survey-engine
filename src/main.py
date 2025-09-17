from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from src.api import rfq_router, survey_router, golden_router, analytics_router, rules_router, utils_router, field_extraction_router, pillar_scores_router, annotations, system_prompt_audit, settings as settings_router
from src.config import settings
import logging
import asyncio
import json
from typing import Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Survey Generation Engine",
    description="Transform RFQs into researcher-ready surveys using AI with golden standards",
    version="0.1.0",
    debug=settings.debug
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, workflow_id: str):
        await websocket.accept()
        if workflow_id not in self.active_connections:
            self.active_connections[workflow_id] = []
        self.active_connections[workflow_id].append(websocket)
        logger.info(f"🔌 [WebSocket] Connection established for workflow_id={workflow_id}. Total active: {len(self.active_connections[workflow_id])}")

    def disconnect(self, websocket: WebSocket, workflow_id: str):
        if workflow_id in self.active_connections:
            self.active_connections[workflow_id].remove(websocket)
            if not self.active_connections[workflow_id]:
                del self.active_connections[workflow_id]
        logger.info(f"🔌 [WebSocket] Connection closed for workflow_id={workflow_id}")

    async def send_progress(self, workflow_id: str, message: dict):
        if workflow_id in self.active_connections:
            for connection in self.active_connections[workflow_id]:
                try:
                    await connection.send_text(json.dumps(message))
                    logger.debug(f"📤 [WebSocket] Sent message to workflow_id={workflow_id}: {message.get('type', 'unknown')}")
                except Exception as e:
                    logger.warning(f"⚠️ [WebSocket] Failed to send message to workflow_id={workflow_id}: {str(e)}")

    async def broadcast_to_workflow(self, workflow_id: str, message: dict):
        """Alias for send_progress for compatibility with workflow service"""
        await self.send_progress(workflow_id, message)

manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 [FastAPI] Starting Survey Generation Engine...")
    
    # Note: Models are preloaded by start.sh before FastAPI starts
    # This avoids double-loading and reduces startup time
    logger.info("✅ [FastAPI] Models already preloaded by startup script")
    logger.info("🎉 [FastAPI] Startup completed successfully - server is ready to accept requests")

app.include_router(rfq_router, prefix="/api/v1")
app.include_router(survey_router, prefix="/api/v1")
app.include_router(golden_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(rules_router, prefix="/api/v1")
app.include_router(utils_router, prefix="/api/v1")
app.include_router(field_extraction_router, prefix="/api/v1")
app.include_router(pillar_scores_router, prefix="/api/v1")
app.include_router(annotations.router, prefix="/api/v1")
app.include_router(system_prompt_audit.router)
app.include_router(settings_router.router, prefix="/api/v1")


@app.websocket("/ws/survey/{workflow_id}")
async def websocket_endpoint(websocket: WebSocket, workflow_id: str):
    """
    WebSocket endpoint for real-time survey generation progress
    """
    await manager.connect(websocket, workflow_id)
    try:
        while True:
            # Keep connection alive and handle any incoming messages
            data = await websocket.receive_text()
            logger.debug(f"📨 [WebSocket] Received message from workflow_id={workflow_id}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket, workflow_id)

@app.get("/")
async def root():
    """Root endpoint - should be served by nginx, but fallback here"""
    return {"message": "Survey Generation Engine API", "status": "running", "version": "0.1.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=settings.debug
    )