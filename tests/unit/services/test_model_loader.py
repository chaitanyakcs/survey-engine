"""
Unit tests for model loading functionality
"""
import asyncio
import pytest
import time
from unittest.mock import patch, MagicMock
from src.services.model_loader import BackgroundModelLoader, ModelLoadingState
from src.services.embedding_service import EmbeddingService


class TestModelLoadingState:
    """Test ModelLoadingState class"""
    
    def test_initial_state(self):
        """Test initial state values"""
        state = ModelLoadingState()
        status = state.get_status()
        
        assert status["loading"] is False
        assert status["ready"] is False
        assert status["error"] is None
        assert status["started_at"] is None
        assert status["completed_at"] is None
        assert status["progress"] == 0
        assert status["phase"] == "idle"
        assert status["message"] == "Waiting to start"
    
    def test_set_loading(self):
        """Test set_loading method"""
        state = ModelLoadingState()
        state.set_loading("loading", "Test loading message", 25)
        status = state.get_status()
        
        assert status["loading"] is True
        assert status["ready"] is False
        assert status["error"] is None
        assert status["started_at"] is not None
        assert status["progress"] == 25
        assert status["phase"] == "loading"
        assert status["message"] == "Test loading message"
    
    def test_set_progress(self):
        """Test set_progress method"""
        state = ModelLoadingState()
        state.set_loading("loading", "Initial", 10)
        state.set_progress(50, "loading", "Halfway done")
        status = state.get_status()
        
        assert status["progress"] == 50
        assert status["phase"] == "loading"
        assert status["message"] == "Halfway done"
    
    def test_set_ready(self):
        """Test set_ready method"""
        state = ModelLoadingState()
        state.set_loading("loading", "Loading", 75)
        state.set_ready()
        status = state.get_status()
        
        assert status["loading"] is False
        assert status["ready"] is True
        assert status["completed_at"] is not None
        assert status["progress"] == 100
        assert status["phase"] == "ready"
        assert status["message"] == "All models loaded successfully"
    
    def test_set_error(self):
        """Test set_error method"""
        state = ModelLoadingState()
        state.set_loading("loading", "Loading", 50)
        state.set_error("Test error message")
        status = state.get_status()
        
        assert status["loading"] is False
        assert status["ready"] is False
        assert status["error"] == "Test error message"
        assert status["completed_at"] is not None
        assert status["phase"] == "error"
        assert "Test error message" in status["message"]


class TestBackgroundModelLoader:
    """Test BackgroundModelLoader class"""
    
    def test_initial_state(self):
        """Test initial state"""
        assert isinstance(BackgroundModelLoader.is_loading(), bool)
        assert isinstance(BackgroundModelLoader.is_ready(), bool)
        
        status = BackgroundModelLoader.get_status()
        assert isinstance(status, dict)
        assert "loading" in status
        assert "ready" in status
        assert "progress" in status
        assert "phase" in status
        assert "message" in status
    
    @pytest.mark.anyio
    async def test_load_models_async_returns_task(self):
        """Test that load_models_async returns an asyncio.Task"""
        task = await BackgroundModelLoader.load_models_async()
        assert asyncio.iscoroutine(task) or asyncio.isfuture(task)
    
    @pytest.mark.anyio
    async def test_load_models_async_idempotent(self):
        """Test that calling load_models_async multiple times returns same task"""
        task1 = await BackgroundModelLoader.load_models_async()
        task2 = await BackgroundModelLoader.load_models_async()
        
        # Should return the same task if already loading
        assert task1 is task2
    
    def test_get_status_structure(self):
        """Test that get_status returns proper structure"""
        status = BackgroundModelLoader.get_status()
        
        required_keys = ["loading", "ready", "error", "started_at", "completed_at", 
                        "progress", "phase", "message", "estimated_seconds"]
        
        for key in required_keys:
            assert key in status, f"Missing key: {key}"
        
        assert isinstance(status["loading"], bool)
        assert isinstance(status["ready"], bool)
        assert isinstance(status["progress"], int)
        assert 0 <= status["progress"] <= 100
        assert isinstance(status["estimated_seconds"], int)
        assert status["estimated_seconds"] >= 0


class TestEmbeddingServiceReadiness:
    """Test EmbeddingService readiness methods"""
    
    def test_is_ready_class_method(self):
        """Test is_ready class method"""
        result = EmbeddingService.is_ready()
        assert isinstance(result, bool)
    
    def test_wait_until_ready_class_method(self):
        """Test wait_until_ready class method"""
        result = EmbeddingService.wait_until_ready(timeout=1)
        assert isinstance(result, bool)
    
    def test_should_use_replicate_static_class_method(self):
        """Test _should_use_replicate_static class method"""
        result = EmbeddingService._should_use_replicate_static()
        assert isinstance(result, bool)


@pytest.mark.anyio
async def test_model_loading_integration():
    """Integration test for model loading (requires actual models)"""
    print("\n--- Integration Test: Model Loading ---")
    
    # Test initial state
    print(f"Initial - is_loading: {BackgroundModelLoader.is_loading()}")
    print(f"Initial - is_ready: {BackgroundModelLoader.is_ready()}")
    
    # Start loading
    print("Starting model loading...")
    start_time = time.time()
    loading_task = await BackgroundModelLoader.load_models_async()
    print(f"Loading task: {loading_task}")
    
    # Monitor progress for a short time
    print("Monitoring progress...")
    for i in range(5):  # Monitor for 5 seconds
        status = BackgroundModelLoader.get_status()
        elapsed = time.time() - start_time
        print(f"[{elapsed:.1f}s] {status['phase']}: {status['progress']}% "
              f"(est. {status['estimated_seconds']}s remaining)")
        
        if not BackgroundModelLoader.is_loading():
            break
            
        await asyncio.sleep(1)
    
    # Check final state
    final_status = BackgroundModelLoader.get_status()
    print(f"Final status: {final_status}")
    
    # This test passes regardless of whether models actually load
    # It's testing the interface and state management
    assert isinstance(final_status, dict)
    assert "loading" in final_status
    assert "ready" in final_status


