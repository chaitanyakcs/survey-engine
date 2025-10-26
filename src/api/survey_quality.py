"""
Survey Quality Analysis API

Composite endpoint that returns non-AI evaluation (always) and AI evaluation (if enabled).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

from src.database.connection import get_db
from src.database.models import Survey
from src.services.settings_service import SettingsService
from src.services.golden_similarity_analysis_service import GoldenSimilarityAnalysisService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/surveys", tags=["survey-quality"])


class GoldenSimilarityAnalysis(BaseModel):
    """Golden similarity analysis results"""
    overall_average: float
    best_match: Optional[Dict[str, Any]] = None
    best_industry_match: Optional[Dict[str, Any]] = None
    best_methodology_match: Optional[Dict[str, Any]] = None
    best_combined_match: Optional[Dict[str, Any]] = None
    individual_similarities: list = []
    methodology_alignment: Dict[str, Any] = {}
    industry_alignment: Dict[str, Any] = {}
    total_golden_examples_analyzed: int = 0


class PillarEvaluation(BaseModel):
    """Pillar evaluation results (AI)"""
    overall_grade: str
    weighted_score: float
    total_score: float
    pillar_breakdown: list = []
    recommendations: list = []
    summary: Optional[str] = None


class QualityAnalysisResponse(BaseModel):
    """Comprehensive quality analysis response"""
    survey_id: str
    evaluation_mode: str  # "ai" | "non_ai"
    timestamp: str
    golden_similarity_analysis: GoldenSimilarityAnalysis
    pillar_evaluation: Optional[PillarEvaluation] = None
    legacy_evaluation: Optional[Dict[str, Any]] = None


@router.get("/{survey_id}/quality-analysis", response_model=QualityAnalysisResponse)
async def get_quality_analysis(
    survey_id: UUID,
    force_refresh: bool = False,
    db: Session = Depends(get_db)
) -> QualityAnalysisResponse:
    """
    Get comprehensive quality analysis including:
    - Golden similarity analysis (non-AI, always runs)
    - Pillar evaluation (AI, if enabled in settings)
    - Legacy evaluation (fallback)
    
    Args:
        survey_id: Survey ID to analyze
        force_refresh: Force recalculation of analysis
        db: Database session
        
    Returns:
        QualityAnalysisResponse with evaluation results
    """
    try:
        logger.info(f"🔍 [SurveyQualityAPI] Getting quality analysis for survey {survey_id}")
        
        # Get survey from database
        survey = db.query(Survey).filter(Survey.id == survey_id).first()
        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found")
        
        # Check if we already have pillar_scores with golden_similarity_analysis
        has_existing_analysis = (
            survey.pillar_scores and 
            isinstance(survey.pillar_scores, dict) and
            "golden_similarity_analysis" in survey.pillar_scores and
            not force_refresh
        )
        
        # Get evaluation settings
        settings_service = SettingsService(db)
        evaluation_settings = settings_service.get_evaluation_settings()
        enable_llm_evaluation = evaluation_settings.get('enable_llm_evaluation', True)
        
        evaluation_mode = "ai" if enable_llm_evaluation else "non_ai"
        
        # Get golden similarity analysis
        if has_existing_analysis:
            golden_similarity_analysis = survey.pillar_scores.get("golden_similarity_analysis", {})
            logger.info("✅ [SurveyQualityAPI] Using existing golden similarity analysis")
        else:
            # For older surveys, use available data gracefully
            logger.info("ℹ️ [SurveyQualityAPI] No detailed similarity analysis available, using legacy data")
            
            # Try to get basic similarity from golden_similarity_score
            avg_similarity = survey.golden_similarity_score or 0.0
            
            # Extract any metadata from pillar_scores if available
            used_golden_examples = survey.used_golden_examples or []
            num_golden_examples = len(used_golden_examples) if used_golden_examples else 0
            
            # Fetch golden example metadata from database
            individual_similarities = []
            if num_golden_examples > 0:
                try:
                    from src.database.models import GoldenRFQSurveyPair
                    golden_pairs = db.query(GoldenRFQSurveyPair).filter(
                        GoldenRFQSurveyPair.id.in_(used_golden_examples[:10])  # Limit to 10
                    ).all()
                    
                    for pair in golden_pairs:
                        individual_similarities.append({
                            "golden_id": str(pair.id),
                            "similarity": float(avg_similarity),  # Use overall average for legacy data
                            "title": pair.title or "Untitled Golden Example",
                            "methodology_tags": pair.methodology_tags or [],
                            "industry_category": pair.industry_category
                        })
                except Exception as e:
                    logger.warning(f"⚠️ [SurveyQualityAPI] Failed to fetch golden example metadata: {e}")
                    # Fallback to just IDs
                    for golden_id in used_golden_examples[:3]:
                        individual_similarities.append({
                            "golden_id": str(golden_id),
                            "similarity": float(avg_similarity),
                            "title": "Golden Example",
                            "methodology_tags": [],
                            "industry_category": None
                        })
            
            golden_similarity_analysis = {
                "overall_average": float(avg_similarity),
                "best_match": {
                    "golden_id": str(used_golden_examples[0]) if used_golden_examples else None,
                    "title": individual_similarities[0]["title"] if individual_similarities else "Legacy Golden Example",
                    "similarity": float(avg_similarity),
                    "match_type": "overall",
                    "match_reason": "Based on legacy similarity calculation"
                } if num_golden_examples > 0 and avg_similarity > 0 else None,
                "best_industry_match": None,
                "best_methodology_match": None,
                "best_combined_match": None,
                "individual_similarities": individual_similarities,
                "methodology_alignment": {"score": 0.0},
                "industry_alignment": {"score": 0.0},
                "total_golden_examples_analyzed": num_golden_examples,
                "note": "Legacy analysis - detailed breakdown not available for older surveys"
            }
        
        # Extract pillar evaluation if AI evaluation was run
        pillar_evaluation = None
        legacy_evaluation = None
        
        if survey.pillar_scores:
            pillar_data = survey.pillar_scores
            
            # Check if this is AI evaluation (has weighted_score)
            # Note: pillar_breakdown might be empty array for legacy surveys
            if isinstance(pillar_data, dict) and "weighted_score" in pillar_data:
                # Check if pillar_breakdown exists and has data
                pillar_breakdown = pillar_data.get("pillar_breakdown", [])
                has_pillar_data = bool(pillar_breakdown and len(pillar_breakdown) > 0)
                
                # For older surveys, we might only have the weighted_score without breakdown
                # Still show it but note that detailed data is missing
                pillar_evaluation = PillarEvaluation(
                    overall_grade=pillar_data.get("overall_grade", "N/A"),
                    weighted_score=pillar_data.get("weighted_score", 0.0),
                    total_score=pillar_data.get("total_score", 0.0),
                    pillar_breakdown=pillar_breakdown if has_pillar_data else [],
                    recommendations=pillar_data.get("recommendations", []) if has_pillar_data else [],
                    summary=pillar_data.get("summary")
                )
            
            # Check if this is legacy evaluation (fallback)
            elif isinstance(pillar_data, dict) and not pillar_evaluation:
                legacy_evaluation = pillar_data
        
        # Ensure golden_similarity_analysis has all required fields
        if not isinstance(golden_similarity_analysis, dict):
            golden_similarity_analysis = {}
        
        golden_analysis = GoldenSimilarityAnalysis(
            overall_average=golden_similarity_analysis.get("overall_average", 0.0),
            best_match=golden_similarity_analysis.get("best_match"),
            best_industry_match=golden_similarity_analysis.get("best_industry_match"),
            best_methodology_match=golden_similarity_analysis.get("best_methodology_match"),
            best_combined_match=golden_similarity_analysis.get("best_combined_match"),
            individual_similarities=golden_similarity_analysis.get("individual_similarities", []),
            methodology_alignment=golden_similarity_analysis.get("methodology_alignment", {}),
            industry_alignment=golden_similarity_analysis.get("industry_alignment", {}),
            total_golden_examples_analyzed=golden_similarity_analysis.get("total_golden_examples_analyzed", 0)
        )
        
        response = QualityAnalysisResponse(
            survey_id=str(survey_id),
            evaluation_mode=evaluation_mode,
            timestamp=datetime.now().isoformat(),
            golden_similarity_analysis=golden_analysis,
            pillar_evaluation=pillar_evaluation,
            legacy_evaluation=legacy_evaluation
        )
        
        logger.info(f"✅ [SurveyQualityAPI] Returning quality analysis for survey {survey_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [SurveyQualityAPI] Failed to get quality analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get quality analysis: {str(e)}")

