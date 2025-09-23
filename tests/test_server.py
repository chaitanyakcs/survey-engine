#!/usr/bin/env python3
"""
Simple test server for Survey Engine - runs without dependencies
"""
from fastapi import FastAPI
import uvicorn

app = FastAPI(
    title="Survey Generation Engine - Test Mode",
    description="Minimal test version to verify Replicate integration",
    version="0.1.0"
)

@app.get("/")
async def root():
    return {"message": "Survey Engine Test Server", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0", "mode": "test"}

@app.post("/api/v1/test-rfq/")
async def test_rfq_submission(rfq_data: dict):
    """
    Test endpoint that simulates RFQ processing without external dependencies
    """
    return {
        "message": "RFQ received in test mode",
        "rfq_data": rfq_data,
        "mock_survey_id": "test-survey-123",
        "status": "success",
        "note": "This is a test endpoint. Full functionality requires Replicate API setup."
    }

@app.get("/api/v1/test-replicate/")
async def test_replicate():
    """
    Test Replicate connectivity
    """
    try:
        import replicate
        return {
            "replicate_available": True,
            "message": "Replicate library imported successfully",
            "status": "ready"
        }
    except ImportError:
        return {
            "replicate_available": False,
            "message": "Replicate library not installed",
            "status": "missing_dependency"
        }

if __name__ == "__main__":
    print("🚀 Starting Survey Engine Test Server")
    print("📊 API Docs: http://localhost:8000/docs")
    print("🏥 Health Check: http://localhost:8000/health")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)