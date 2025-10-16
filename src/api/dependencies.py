from fastapi import HTTPException, Depends
from src.services.embedding_service import EmbeddingService
from src.services.model_loader import BackgroundModelLoader
import logging

logger = logging.getLogger(__name__)

async def require_models_ready():
    """
    FastAPI dependency that checks if embedding models are ready.
    If not, it raises an HTTPException with status code 425 (Too Early)
    and provides model loading progress details.
    """
    if not EmbeddingService.is_ready() or not BackgroundModelLoader.is_ready():
        status = BackgroundModelLoader.get_status()
        raise HTTPException(
            status_code=425,  # Too Early
            detail={
                "status": "initializing",
                "message": "AI models are still loading",
                "ready": False,
                "progress": status["progress"],
                "estimated_seconds": status["estimated_seconds"],
                "phase": status["phase"],
                "type": "initialization"  # Distinguish from errors
            },
            headers={"Retry-After": str(max(status["estimated_seconds"], 30))}
        )
    return True # Models are ready


