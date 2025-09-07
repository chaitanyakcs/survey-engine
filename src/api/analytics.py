from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src.services.analytics_service import AnalyticsService
from pydantic import BaseModel
from typing import Dict, Any, Optional

router = APIRouter(prefix="/analytics", tags=["Analytics"])


class TrainingDataStatusResponse(BaseModel):
    edits_collected: int
    min_edits_threshold: int
    golden_pairs_available: int
    min_golden_pairs_threshold: int
    ready_for_sft: bool


class QualityTrendsResponse(BaseModel):
    cleanup_time_trends: Dict[str, Any]
    edit_density_trends: Dict[str, Any]
    golden_similarity_trends: Dict[str, Any]


class ModelPerformanceRequest(BaseModel):
    model_a: str
    model_b: str
    test_rfqs: Optional[int] = 10


@router.get("/training-data/status", response_model=TrainingDataStatusResponse)
async def get_training_data_status(
    db: Session = Depends(get_db)
) -> TrainingDataStatusResponse:
    """
    Current collection status vs thresholds
    """
    analytics_service = AnalyticsService(db)
    status = analytics_service.get_training_data_status()
    
    return TrainingDataStatusResponse(
        edits_collected=status.edits_collected,
        min_edits_threshold=status.min_edits_threshold,
        golden_pairs_available=status.golden_pairs_available,
        min_golden_pairs_threshold=status.min_golden_pairs_threshold,
        ready_for_sft=status.ready_for_sft
    )


@router.get("/quality-trends", response_model=QualityTrendsResponse)
async def get_quality_trends(
    db: Session = Depends(get_db),
    days: int = 30
) -> QualityTrendsResponse:
    """
    Cleanup time, edit density trends
    """
    analytics_service = AnalyticsService(db)
    trends = analytics_service.get_quality_trends(days=days)
    
    return QualityTrendsResponse(
        cleanup_time_trends=trends.cleanup_time_trends,
        edit_density_trends=trends.edit_density_trends,
        golden_similarity_trends=trends.golden_similarity_trends
    )


@router.post("/model-performance")
async def test_model_performance(
    request: ModelPerformanceRequest,
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    """
    A/B test different model configurations
    """
    try:
        analytics_service = AnalyticsService(db)
        results = analytics_service.compare_model_performance(
            model_a=request.model_a,
            model_b=request.model_b,
            test_rfqs=request.test_rfqs or 10
        )
        
        return {"status": "success", "comparison_results": results}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run model comparison: {str(e)}")