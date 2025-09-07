from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api import rfq_router, survey_router, golden_router, analytics_router
from src.config import settings

app = FastAPI(
    title="Survey Generation Engine",
    description="Transform RFQs into researcher-ready surveys using AI with golden standards",
    version="0.1.0",
    debug=settings.debug
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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