from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from src.api import rfq_router, survey_router, golden_router, analytics_router
from src.config import settings
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add global exception handler
import sys
import traceback

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.critical("💥 [FastAPI] Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

app = FastAPI(
    title="Survey Generation Engine",
    description="Transform RFQs into researcher-ready surveys using AI with golden standards",
    version="0.1.0",
    debug=settings.debug
)

# Request logging middleware - simplified to avoid crashes
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"🔍 [FastAPI] {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"✅ [FastAPI] {request.method} {request.url.path} completed in {process_time:.3f}s with status {response.status_code}")
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"❌ [FastAPI] {request.method} {request.url.path} failed in {process_time:.3f}s: {str(e)}", exc_info=True)
        raise

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 [FastAPI] Starting Survey Generation Engine...")
    logger.info(f"🔧 [FastAPI] Python version: {sys.version}")
    logger.info(f"🔧 [FastAPI] Debug mode: {settings.debug}")
    logger.info(f"🔧 [FastAPI] Database URL: {settings.database_url}")
    
    # Test environment variables
    import os
    logger.info(f"🔧 [FastAPI] Environment check - REPLICATE_API_TOKEN present: {'REPLICATE_API_TOKEN' in os.environ}")
    
    logger.info("📝 [FastAPI] Testing database connection...")
    try:
        from src.database import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        result = db.execute(text("SELECT version()")).fetchone()
        db.close()
        logger.info(f"✅ [FastAPI] Database connection successful - PostgreSQL version: {result[0] if result else 'Unknown'}")
    except Exception as e:
        logger.error(f"❌ [FastAPI] Database connection failed: {str(e)}")
        # Don't raise - let the server start and handle DB errors per request
    
    logger.info("📝 [FastAPI] Testing import of critical services...")
    try:
        from src.services.workflow_service import WorkflowService
        from src.services.embedding_service import EmbeddingService
        from src.services.websocket_client import WebSocketNotificationService
        logger.info("✅ [FastAPI] All critical services imported successfully")
    except Exception as e:
        logger.error(f"❌ [FastAPI] Critical service import failed: {str(e)}")
        # Don't raise - let the server start and handle import errors per request
        
    logger.info("🎉 [FastAPI] Startup completed successfully - server is ready to accept requests")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 [FastAPI] Shutting down Survey Generation Engine...")

app.include_router(rfq_router, prefix="/api/v1")
app.include_router(survey_router, prefix="/api/v1")
app.include_router(golden_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=settings.debug
    )