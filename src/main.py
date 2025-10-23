from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from src.api import rfq_router, survey_router, golden_router, golden_content_router, analytics_router, rules_router, utils_router, field_extraction_router, pillar_scores_router, human_reviews_router, annotation_insights_router, annotations, settings as settings_router, llm_audit, export, admin, retrieval_weights
from src.config import settings
import logging
import asyncio
import json
from typing import Dict, List, Any

# Configure logging with timestamps
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Suppress SQLAlchemy engine logs
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.dialects').setLevel(logging.WARNING)

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
    def __init__(self) -> None:
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, workflow_id: str) -> None:
        await websocket.accept()
        if workflow_id not in self.active_connections:
            self.active_connections[workflow_id] = []
        self.active_connections[workflow_id].append(websocket)
        logger.info(f"🔌 [WebSocket] Connection established for workflow_id={workflow_id}. Total active: {len(self.active_connections[workflow_id])}")

    def disconnect(self, websocket: WebSocket, workflow_id: str) -> None:
        if workflow_id in self.active_connections:
            self.active_connections[workflow_id].remove(websocket)
            if not self.active_connections[workflow_id]:
                del self.active_connections[workflow_id]
        logger.info(f"🔌 [WebSocket] Connection closed for workflow_id={workflow_id}")

    async def send_progress(self, workflow_id: str, message: Dict[str, Any]) -> None:
        if workflow_id in self.active_connections:
            for connection in self.active_connections[workflow_id]:
                try:
                    await connection.send_text(json.dumps(message))
                    logger.debug(f"📤 [WebSocket] Sent message to workflow_id={workflow_id}: {message.get('type', 'unknown')}")
                except Exception as e:
                    logger.warning(f"⚠️ [WebSocket] Failed to send message to workflow_id={workflow_id}: {str(e)}")

    async def broadcast_to_workflow(self, workflow_id: str, message: Dict[str, Any]) -> None:
        """Alias for send_progress for compatibility with workflow service"""
        await self.send_progress(workflow_id, message)

manager = ConnectionManager()

@app.on_event("startup")
async def startup_event() -> None:
    logger.info("🚀 [FastAPI] Starting Survey Generation Engine...")
    
    # Start background model loading
    from src.services.model_loader import BackgroundModelLoader
    logger.info("🔄 [FastAPI] Starting background model loading...")
    
    # Launch model loading task (non-blocking)
    model_loading_task = await BackgroundModelLoader.load_models_async()
    
    logger.info("✅ [FastAPI] Server ready - models loading in background")
    logger.info("🎉 [FastAPI] Startup completed successfully - server is ready to accept requests")

app.include_router(rfq_router, prefix="/api/v1")
app.include_router(survey_router, prefix="/api/v1")
app.include_router(golden_router, prefix="/api/v1")
app.include_router(golden_content_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(rules_router, prefix="/api/v1")
app.include_router(utils_router, prefix="/api/v1")
app.include_router(field_extraction_router, prefix="/api/v1")
app.include_router(pillar_scores_router, prefix="/api/v1")
app.include_router(human_reviews_router, prefix="/api/v1")
app.include_router(annotation_insights_router, prefix="/api/v1")
app.include_router(annotations.router, prefix="/api/v1")
app.include_router(llm_audit.router, prefix="/api/v1")
app.include_router(settings_router.router, prefix="/api/v1")
app.include_router(export.router, prefix="/api/v1")
app.include_router(retrieval_weights.router)
app.include_router(admin.router)


@app.websocket("/ws/survey/{workflow_id}")
async def websocket_endpoint(websocket: WebSocket, workflow_id: str) -> None:
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


@app.websocket("/ws/rfq-parsing/{session_id}")
async def rfq_parsing_websocket(websocket: WebSocket, session_id: str) -> None:
    """
    WebSocket endpoint for real-time progress updates during RFQ document parsing.
    """
    logger.info(f"🔌 [RFQ Parsing WebSocket] New connection attempt for session_id={session_id}")

    # Import the RFQ parsing manager
    from src.api.field_extraction import rfq_parsing_manager

    await rfq_parsing_manager.connect(websocket, session_id)
    logger.info(f"✅ [RFQ Parsing WebSocket] Connection established for session_id={session_id}")

    try:
        while True:
            # Keep connection alive and handle any incoming messages
            data = await websocket.receive_text()
            logger.debug(f"📨 [RFQ Parsing WebSocket] Received WebSocket message: {data}")

    except WebSocketDisconnect:
        logger.info(f"🔌 [RFQ Parsing WebSocket] Client disconnected for session_id={session_id}")
        rfq_parsing_manager.disconnect(websocket, session_id)
    except Exception as e:
        logger.error(f"❌ [RFQ Parsing WebSocket] WebSocket error for session {session_id}: {str(e)}", exc_info=True)
        rfq_parsing_manager.disconnect(websocket, session_id)
        await websocket.close()


@app.websocket("/ws/init/{client_id}")
async def model_init_websocket(websocket: WebSocket, client_id: str) -> None:
    """
    WebSocket endpoint for real-time model loading progress updates
    """
    await manager.connect(websocket, f"init_{client_id}")
    logger.info(f"🔌 [Model Init WebSocket] Connection established for client_id={client_id}")
    
    try:
        from src.services.model_loader import BackgroundModelLoader
        
        # Stream progress updates every 1 second while loading
        while BackgroundModelLoader.is_loading():
            status = BackgroundModelLoader.get_status()
            await manager.send_progress(f"init_{client_id}", {
                "type": "model_loading",
                "progress": status["progress"],  # 0-100
                "estimated_seconds": status["estimated_seconds"],
                "phase": status["phase"],  # "connecting" | "loading" | "finalizing"
                "message": status["message"]
            })
            await asyncio.sleep(1)
        
        # Send ready notification
        await manager.send_progress(f"init_{client_id}", {
            "type": "models_ready",
            "message": "All systems ready!",
            "ready": True
        })
        
        # Keep connection alive for a bit to ensure message is sent
        await asyncio.sleep(2)
        
    except WebSocketDisconnect:
        logger.info(f"🔌 [Model Init WebSocket] Client disconnected for client_id={client_id}")
        manager.disconnect(websocket, f"init_{client_id}")
    except Exception as e:
        logger.error(f"❌ [Model Init WebSocket] WebSocket error for client {client_id}: {str(e)}", exc_info=True)
        manager.disconnect(websocket, f"init_{client_id}")
        await websocket.close()


@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint - should be served by nginx, but fallback here"""
    return {"message": "Survey Generation Engine API", "status": "running", "version": "0.1.0"}

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    return {"status": "healthy", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=settings.debug
    )