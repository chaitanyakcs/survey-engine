"""
Settings API - Handle evaluation settings and cost tracking
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src.services.settings_service import SettingsService
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["Settings"])

class EvaluationSettings(BaseModel):
    evaluation_mode: str  # 'single_call', 'multiple_calls', 'hybrid'
    enable_cost_tracking: bool
    enable_parallel_processing: bool
    enable_ab_testing: bool
    cost_threshold_daily: float
    cost_threshold_monthly: float
    fallback_mode: str  # 'basic', 'multiple_calls', 'disabled'
    
    # Human Prompt Review Settings
    enable_prompt_review: bool = False
    prompt_review_mode: str = 'disabled'  # 'disabled', 'blocking', 'parallel'
    require_approval_for_generation: bool = False
    auto_approve_trusted_prompts: bool = False
    prompt_review_timeout_hours: int = 24

class CostMetrics(BaseModel):
    daily_cost: float
    monthly_cost: float
    evaluations_today: int
    evaluations_this_month: int
    average_cost_per_evaluation: float
    cost_savings_single_call: float
    cost_savings_percent: float

# In-memory cost metrics (in production, use database)
_cost_metrics: Dict[str, Any] = {
    "daily_cost": 0.0,
    "monthly_cost": 0.0,
    "evaluations_today": 0,
    "evaluations_this_month": 0,
    "average_cost_per_evaluation": 0.0,
    "cost_savings_single_call": 0.0,
    "cost_savings_percent": 0.0
}

@router.get("/evaluation", response_model=EvaluationSettings)
async def get_evaluation_settings(db: Session = Depends(get_db)):
    """Get current evaluation settings"""
    logger.info("🔧 [Settings API] Retrieving evaluation settings")
    try:
        settings_service = SettingsService(db)
        settings = settings_service.get_evaluation_settings()
        return EvaluationSettings(**settings)
    except Exception as e:
        logger.error(f"❌ [Settings API] Failed to retrieve settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.put("/evaluation", response_model=EvaluationSettings)
async def update_evaluation_settings(settings: EvaluationSettings, db: Session = Depends(get_db)):
    """Update evaluation settings"""
    logger.info(f"🔧 [Settings API] Updating evaluation settings: {settings.evaluation_mode}")
    try:
        # Validate settings
        if settings.evaluation_mode not in ['single_call', 'multiple_calls', 'hybrid']:
            raise HTTPException(status_code=400, detail="Invalid evaluation_mode")
        
        if settings.fallback_mode not in ['basic', 'multiple_calls', 'disabled']:
            raise HTTPException(status_code=400, detail="Invalid fallback_mode")
        
        if settings.cost_threshold_daily < 0 or settings.cost_threshold_monthly < 0:
            raise HTTPException(status_code=400, detail="Cost thresholds must be non-negative")
        
        # Validate prompt review settings
        if settings.prompt_review_mode not in ['disabled', 'blocking', 'parallel']:
            raise HTTPException(status_code=400, detail="Invalid prompt_review_mode")
        
        if settings.prompt_review_timeout_hours < 1 or settings.prompt_review_timeout_hours > 168:  # 1 hour to 1 week
            raise HTTPException(status_code=400, detail="Prompt review timeout must be between 1 and 168 hours")
        
        # Logical validation
        if settings.require_approval_for_generation and not settings.enable_prompt_review:
            raise HTTPException(status_code=400, detail="Cannot require approval without enabling prompt review")
        
        if settings.prompt_review_mode != 'disabled' and not settings.enable_prompt_review:
            raise HTTPException(status_code=400, detail="Cannot set review mode without enabling prompt review")
        
        # Update settings in database
        settings_service = SettingsService(db)
        success = settings_service.update_evaluation_settings(settings.dict())
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update settings in database")
        
        # Return updated settings
        updated_settings = settings_service.get_evaluation_settings()
        logger.info(f"✅ [Settings API] Settings updated successfully")
        return EvaluationSettings(**updated_settings)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [Settings API] Failed to update settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/cost-metrics", response_model=CostMetrics)
async def get_cost_metrics():
    """Get current cost metrics and savings"""
    logger.info("💰 [Settings API] Retrieving cost metrics")
    try:
        # In production, calculate from actual usage data
        # For now, return mock data
        return CostMetrics(**_cost_metrics)
    except Exception as e:
        logger.error(f"❌ [Settings API] Failed to retrieve cost metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/cost-metrics/update")
async def update_cost_metrics(
    evaluation_mode: str,
    cost_per_evaluation: float,
    db: Session = Depends(get_db)
):
    """Update cost metrics after an evaluation"""
    logger.info(f"💰 [Settings API] Updating cost metrics for {evaluation_mode} evaluation")
    try:
        # Calculate cost based on evaluation mode
        if evaluation_mode == "single_call":
            actual_cost = cost_per_evaluation
            saved_cost = cost_per_evaluation * 4  # 4 calls saved
        elif evaluation_mode == "multiple_calls":
            actual_cost = cost_per_evaluation
            saved_cost = 0
        else:  # hybrid
            actual_cost = cost_per_evaluation
            saved_cost = cost_per_evaluation * 2  # 2 calls saved
        
        # Update metrics
        _cost_metrics["daily_cost"] += actual_cost
        _cost_metrics["monthly_cost"] += actual_cost
        _cost_metrics["evaluations_today"] += 1
        _cost_metrics["evaluations_this_month"] += 1
        _cost_metrics["average_cost_per_evaluation"] = _cost_metrics["monthly_cost"] / max(_cost_metrics["evaluations_this_month"], 1)
        _cost_metrics["cost_savings_single_call"] += saved_cost
        
        # Calculate savings percentage
        if _cost_metrics["monthly_cost"] > 0:
            _cost_metrics["cost_savings_percent"] = (_cost_metrics["cost_savings_single_call"] / _cost_metrics["monthly_cost"]) * 100
        
        logger.info(f"✅ [Settings API] Cost metrics updated: ${actual_cost:.2f} spent, ${saved_cost:.2f} saved")
        return {"message": "Cost metrics updated successfully"}
        
    except Exception as e:
        logger.error(f"❌ [Settings API] Failed to update cost metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/evaluation-mode")
async def get_current_evaluation_mode(db: Session = Depends(get_db)):
    """Get current evaluation mode for use by other services"""
    logger.info("🔧 [Settings API] Retrieving current evaluation mode")
    try:
        settings_service = SettingsService(db)
        settings = settings_service.get_evaluation_settings()
        return {
            "evaluation_mode": settings["evaluation_mode"],
            "enable_parallel_processing": settings["enable_parallel_processing"],
            "fallback_mode": settings["fallback_mode"]
        }
    except Exception as e:
        logger.error(f"❌ [Settings API] Failed to retrieve evaluation mode: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/reset")
async def reset_settings(db: Session = Depends(get_db)):
    """Reset all settings to defaults"""
    logger.info("🔄 [Settings API] Resetting settings to defaults")
    try:
        settings_service = SettingsService(db)
        success = settings_service.reset_to_defaults()
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to reset settings in database")
        
        logger.info("✅ [Settings API] Settings reset to defaults")
        return {"message": "Settings reset to defaults successfully"}
        
    except Exception as e:
        logger.error(f"❌ [Settings API] Failed to reset settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
