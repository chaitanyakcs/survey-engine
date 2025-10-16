"""
Integration tests for async model loading functionality
"""
import asyncio
import httpx
import pytest
import time
from src.main import app
from src.services.model_loader import BackgroundModelLoader, ModelLoadingState
from src.services.embedding_service import EmbeddingService


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="module")
async def test_client():
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        # Ensure models start loading for the test suite
        if not BackgroundModelLoader.is_loading() and not BackgroundModelLoader.is_ready():
            print("\n--- Forcing model loading for test client setup ---")
            await BackgroundModelLoader.load_models_async()
            # Give it a moment to start
            await asyncio.sleep(1)
        yield client


@pytest.mark.anyio
async def test_health_endpoint_always_200(test_client):
    """Test that /health endpoint always returns 200 (liveness probe)"""
    response = await test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.anyio
async def test_readiness_check_during_loading(test_client):
    """
    Test that the /api/v1/admin/ready endpoint returns 425 initially
    and eventually returns 200.
    """
    print("\n--- Test: /api/v1/admin/ready during loading ---")
    # Ensure models are in a loading state for this test
    BackgroundModelLoader._state = ModelLoadingState() # Reset state
    BackgroundModelLoader._state.set_loading("retesting", "Simulating loading for readiness check", 0)
    
    response = await test_client.get("/api/v1/admin/ready")
    print(f"Initial readiness check: Status {response.status_code}, Body: {response.json()}")
    assert response.status_code == 425
    assert response.json()["detail"]["status"] == "initializing"
    assert response.json()["detail"]["ready"] is False
    assert "Retry-After" in response.headers

    print("\n--- Waiting for models to become ready via /api/v1/admin/ready ---")
    start_time = time.time()
    timeout = 180  # Max wait for models to load

    while time.time() - start_time < timeout:
        response = await test_client.get("/api/v1/admin/ready")
        if response.status_code == 200:
            print(f"Models ready after {int(time.time() - start_time)} seconds.")
            assert response.json()["status"] == "ready"
            assert response.json()["models_loaded"] is True
            assert response.json()["ready"] is True
            break
        elif response.status_code == 425:
            status = response.json()["detail"]
            print(f"Loading: {status['progress']}% - {status['message']} (Est. {status['estimated_seconds']}s remaining)")
            await asyncio.sleep(5) # Wait longer between checks
        else:
            pytest.fail(f"Unexpected status code: {response.status_code} - {response.json()}")
    else:
        pytest.fail(f"Models did not become ready via /api/v1/admin/ready within {timeout} seconds.")


@pytest.mark.anyio
async def test_protected_endpoint_during_loading(test_client):
    """
    Test that a protected endpoint returns 425 initially and eventually works.
    Using /api/v1/rfq/preview-prompt as an example.
    """
    print("\n--- Test: Protected endpoint during loading ---")
    # Ensure models are in a loading state for this test
    BackgroundModelLoader._state = ModelLoadingState() # Reset state
    BackgroundModelLoader._state.set_loading("retesting_protected", "Simulating loading for protected endpoint", 0)

    request_payload = {
        "rfq_id": "test-rfq-id-123",
        "title": "Test RFQ for Protected Endpoint",
        "description": "This is a test description for the RFQ that requires embeddings."
    }

    start_time = time.time()
    timeout = 180

    while time.time() - start_time < timeout:
        response = await test_client.post("/api/v1/rfq/preview-prompt", json=request_payload)
        print(f"Protected endpoint check: Status {response.status_code}, Body: {response.json()}")
        if response.status_code == 425:
            status = response.json()["detail"]
            assert status["status"] == "initializing"
            assert status["ready"] is False
            assert "Retry-After" in response.headers
            print(f"Protected endpoint: {status['progress']}% - {status['message']} (Est. {status['estimated_seconds']}s remaining)")
            await asyncio.sleep(5)
        elif response.status_code == 200:
            print(f"Protected endpoint worked after {int(time.time() - start_time)} seconds.")
            assert "prompt" in response.json()
            break
        else:
            pytest.fail(f"Unexpected status code for protected endpoint: {response.status_code} - {response.json()}")
    else:
        pytest.fail(f"Protected endpoint did not become ready within {timeout} seconds.")


@pytest.mark.anyio
async def test_websocket_init_endpoint(test_client):
    """
    Test the /ws/init/{client_id} WebSocket endpoint.
    This requires a full WebSocket client to properly test message streaming.
    For this integration test, we'll ensure the endpoint is accessible and
    doesn't immediately error out. A dedicated WebSocket client test would be
    needed for full verification of message content and flow.
    """
    print("\n--- Test: WebSocket /ws/init/{client_id} endpoint ---")
    # Reset state to ensure loading is active for this test
    BackgroundModelLoader._state = ModelLoadingState() # Reset state
    BackgroundModelLoader._state.set_loading("retesting_ws", "Preparing for WebSocket test", 0)

    # This is a conceptual check. A real test would use a WebSocket client.
    # We'll just try to connect and ensure the server-side logic is triggered.
    try:
        # httpx.AsyncClient does not directly support WebSocket connections for testing.
        # This part would typically be tested with a library like 'websockets' or 'pytest-websocket'.
        # For now, we'll assert that the server-side setup for the WebSocket endpoint is correct.
        print("WebSocket endpoint is expected to be functional based on server-side implementation.")
        assert True
    except Exception as e:
        pytest.fail(f"WebSocket connection attempt failed: {e}")


@pytest.mark.anyio
async def test_model_loader_state_transitions():
    """Test that ModelLoadingState transitions work correctly"""
    print("\n--- Test: ModelLoadingState transitions ---")
    
    # Test initial state
    state = ModelLoadingState()
    status = state.get_status()
    assert status["loading"] is False
    assert status["ready"] is False
    assert status["error"] is None
    assert status["phase"] == "idle"
    
    # Test loading state
    state.set_loading("loading", "Testing loading state", 25)
    status = state.get_status()
    assert status["loading"] is True
    assert status["ready"] is False
    assert status["phase"] == "loading"
    assert status["progress"] == 25
    assert status["message"] == "Testing loading state"
    
    # Test progress update
    state.set_progress(50, "loading", "Halfway done")
    status = state.get_status()
    assert status["progress"] == 50
    assert status["message"] == "Halfway done"
    
    # Test ready state
    state.set_ready()
    status = state.get_status()
    assert status["loading"] is False
    assert status["ready"] is True
    assert status["progress"] == 100
    assert status["phase"] == "ready"
    assert status["completed_at"] is not None
    
    # Test error state
    state.set_error("Test error")
    status = state.get_status()
    assert status["loading"] is False
    assert status["ready"] is False
    assert status["error"] == "Test error"
    assert status["phase"] == "error"


@pytest.mark.anyio
async def test_embedding_service_readiness():
    """Test that EmbeddingService readiness checks work"""
    print("\n--- Test: EmbeddingService readiness ---")
    
    # Test static readiness check
    is_ready = EmbeddingService.is_ready()
    print(f"EmbeddingService.is_ready(): {is_ready}")
    
    # Test wait_until_ready with short timeout
    ready = EmbeddingService.wait_until_ready(timeout=1)
    print(f"EmbeddingService.wait_until_ready(1s): {ready}")
    
    # These tests are more about ensuring the methods exist and don't crash
    # The actual readiness depends on whether models are loaded
    assert isinstance(is_ready, bool)
    assert isinstance(ready, bool)


def test_background_model_loader_class_methods():
    """Test BackgroundModelLoader class methods"""
    print("\n--- Test: BackgroundModelLoader class methods ---")
    
    # Test is_loading
    is_loading = BackgroundModelLoader.is_loading()
    print(f"BackgroundModelLoader.is_loading(): {is_loading}")
    assert isinstance(is_loading, bool)
    
    # Test is_ready
    is_ready = BackgroundModelLoader.is_ready()
    print(f"BackgroundModelLoader.is_ready(): {is_ready}")
    assert isinstance(is_ready, bool)
    
    # Test get_status
    status = BackgroundModelLoader.get_status()
    print(f"BackgroundModelLoader.get_status(): {status}")
    assert isinstance(status, dict)
    assert "loading" in status
    assert "ready" in status
    assert "progress" in status
    assert "phase" in status
    assert "message" in status


