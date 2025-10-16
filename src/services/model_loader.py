"""
Background model loading service with progress tracking
"""
import asyncio
import threading
import time
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class LoadingPhase(Enum):
    """Model loading phases"""
    CONNECTING = "connecting"
    LOADING = "loading"
    FINALIZING = "finalizing"
    READY = "ready"
    ERROR = "error"


class ModelLoadingState:
    """Thread-safe model loading state tracker"""
    
    def __init__(self):
        self._loading = False
        self._ready = False
        self._error: Optional[str] = None
        self._started_at: Optional[datetime] = None
        self._completed_at: Optional[datetime] = None
        self._current_phase = LoadingPhase.CONNECTING
        self._lock = threading.Lock()
    
    @property
    def loading(self) -> bool:
        with self._lock:
            return self._loading
    
    @property
    def ready(self) -> bool:
        with self._lock:
            return self._ready
    
    @property
    def error(self) -> Optional[str]:
        with self._lock:
            return self._error
    
    @property
    def started_at(self) -> Optional[datetime]:
        with self._lock:
            return self._started_at
    
    @property
    def completed_at(self) -> Optional[datetime]:
        with self._lock:
            return self._completed_at
    
    @property
    def current_phase(self) -> LoadingPhase:
        with self._lock:
            return self._current_phase
    
    def set_loading(self, loading: bool) -> None:
        with self._lock:
            self._loading = loading
            if loading and self._started_at is None:
                self._started_at = datetime.now()
                self._current_phase = LoadingPhase.CONNECTING
    
    def set_ready(self, ready: bool) -> None:
        with self._lock:
            self._ready = ready
            if ready:
                self._loading = False
                self._completed_at = datetime.now()
                self._current_phase = LoadingPhase.READY
    
    def set_error(self, error: str) -> None:
        with self._lock:
            self._error = error
            self._loading = False
            self._current_phase = LoadingPhase.ERROR
    
    def set_phase(self, phase: LoadingPhase) -> None:
        with self._lock:
            self._current_phase = phase


class BackgroundModelLoader:
    """Async model loader with progress tracking"""
    
    _instance: Optional['BackgroundModelLoader'] = None
    _state = ModelLoadingState()
    _loading_task: Optional[asyncio.Task] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def is_loading(cls) -> bool:
        """Check if models are currently loading"""
        return cls._state.loading and not cls._state.ready
    
    @classmethod
    def is_ready(cls) -> bool:
        """Check if models are ready"""
        return cls._state.ready
    
    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        """Get current loading status for WebSocket streaming"""
        with cls._lock:
            return {
                "loading": cls._state.loading,
                "ready": cls._state.ready,
                "error": cls._state.error,
                "progress": cls._calculate_progress(),
                "estimated_seconds": cls._estimate_remaining_time(),
                "phase": cls._state.current_phase.value,
                "message": cls._get_phase_message(),
                "started_at": cls._state.started_at.isoformat() if cls._state.started_at else None,
                "completed_at": cls._state.completed_at.isoformat() if cls._state.completed_at else None
            }
    
    @classmethod
    def _calculate_progress(cls) -> int:
        """Calculate loading progress percentage"""
        if cls._state.ready:
            return 100
        
        if not cls._state.started_at:
            return 0
        
        # Based on elapsed time and typical load time (~120s)
        elapsed = (datetime.now() - cls._state.started_at).total_seconds()
        
        # Different phases have different time allocations
        phase_weights = {
            LoadingPhase.CONNECTING: 0.1,  # 10% of time
            LoadingPhase.LOADING: 0.8,     # 80% of time
            LoadingPhase.FINALIZING: 0.1   # 10% of time
        }
        
        current_phase = cls._state.current_phase
        if current_phase == LoadingPhase.READY:
            return 100
        elif current_phase == LoadingPhase.ERROR:
            return 0
        
        # Calculate progress based on phase
        phase_progress = phase_weights.get(current_phase, 0.5)
        base_progress = int(elapsed / 120 * 100)  # 120s total estimate
        
        # Adjust for current phase
        if current_phase == LoadingPhase.CONNECTING:
            return min(base_progress, 10)
        elif current_phase == LoadingPhase.LOADING:
            return min(10 + int((base_progress - 10) * 0.8), 90)
        elif current_phase == LoadingPhase.FINALIZING:
            return min(90 + int((base_progress - 90) * 0.1), 95)
        
        return min(base_progress, 95)  # Cap at 95% until done
    
    @classmethod
    def _estimate_remaining_time(cls) -> int:
        """Estimate remaining time in seconds"""
        if cls._state.ready:
            return 0
        
        if not cls._state.started_at:
            return 120  # Default estimate
        
        elapsed = (datetime.now() - cls._state.started_at).total_seconds()
        
        # Estimate based on typical load time
        if elapsed < 10:  # Still in connecting phase
            return max(120 - int(elapsed), 30)
        elif elapsed < 100:  # In loading phase
            remaining = 120 - int(elapsed)
            return max(remaining, 10)
        else:  # In finalizing phase
            return max(120 - int(elapsed), 5)
    
    @classmethod
    def _get_phase_message(cls) -> str:
        """Get user-friendly message for current phase"""
        phase_messages = {
            LoadingPhase.CONNECTING: "Connecting to AI services...",
            LoadingPhase.LOADING: "Loading AI models (this happens once per session)...",
            LoadingPhase.FINALIZING: "Finalizing AI capabilities...",
            LoadingPhase.READY: "All systems ready!",
            LoadingPhase.ERROR: "AI initialization failed"
        }
        return phase_messages.get(cls._state.current_phase, "Initializing...")
    
    @classmethod
    async def load_models_async(cls) -> asyncio.Task:
        """Start background model loading task"""
        if cls._loading_task is not None and not cls._loading_task.done():
            logger.info("Model loading already in progress")
            return cls._loading_task
        
        with cls._lock:
            if cls._loading_task is not None and not cls._loading_task.done():
                return cls._loading_task
            
            cls._state.set_loading(True)
            cls._state.set_phase(LoadingPhase.CONNECTING)
            cls._loading_task = asyncio.create_task(cls._load_models_worker())
            
        logger.info("🚀 [BackgroundModelLoader] Starting background model loading")
        return cls._loading_task
    
    @classmethod
    async def _load_models_worker(cls) -> None:
        """Background worker that loads models"""
        try:
            # Phase 1: Connecting
            logger.info("🔌 [BackgroundModelLoader] Phase 1: Connecting to AI services")
            cls._state.set_phase(LoadingPhase.CONNECTING)
            await asyncio.sleep(1)  # Simulate connection time
            
            # Phase 2: Loading models
            logger.info("🧠 [BackgroundModelLoader] Phase 2: Loading AI models")
            cls._state.set_phase(LoadingPhase.LOADING)
            
            # Import and initialize EmbeddingService
            from src.services.embedding_service import EmbeddingService
            
            # Load models in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, cls._load_embedding_models)
            
            # Phase 3: Finalizing
            logger.info("⚡ [BackgroundModelLoader] Phase 3: Finalizing AI capabilities")
            cls._state.set_phase(LoadingPhase.FINALIZING)
            await asyncio.sleep(1)  # Simulate finalization
            
            # Mark as ready
            cls._state.set_ready(True)
            logger.info("✅ [BackgroundModelLoader] Model loading completed successfully")
            
        except Exception as e:
            error_msg = f"Model loading failed: {str(e)}"
            logger.error(f"❌ [BackgroundModelLoader] {error_msg}", exc_info=True)
            cls._state.set_error(error_msg)
            raise
    
    @classmethod
    def _load_embedding_models(cls) -> None:
        """Load embedding models (runs in thread pool)"""
        try:
            from src.services.embedding_service import EmbeddingService
            
            # Initialize EmbeddingService to trigger model loading
            embedding_service = EmbeddingService()
            
            # Force model loading by calling _ensure_initialized
            embedding_service._ensure_initialized()
            
            # Test the model with a sample embedding
            if not embedding_service.use_replicate:
                # Only test if using local models
                test_embedding = embedding_service.model.encode("test")
                logger.info(f"✅ [BackgroundModelLoader] Model test successful, embedding dimension: {len(test_embedding)}")
            
        except Exception as e:
            logger.error(f"❌ [BackgroundModelLoader] Failed to load embedding models: {str(e)}")
            raise
    
    @classmethod
    async def wait_for_models(cls, timeout: int = 300) -> bool:
        """Wait for models to be ready with timeout"""
        if cls.is_ready():
            return True
        
        if cls._loading_task is None:
            # Start loading if not already started
            await cls.load_models_async()
        
        try:
            await asyncio.wait_for(cls._loading_task, timeout=timeout)
            return cls.is_ready()
        except asyncio.TimeoutError:
            logger.warning(f"⏰ [BackgroundModelLoader] Model loading timed out after {timeout}s")
            return False
        except Exception as e:
            logger.error(f"❌ [BackgroundModelLoader] Model loading failed: {str(e)}")
            return False


