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
    similarity_breakdown: Optional[Dict[str, Any]] = None  # Detailed breakdown with methodology, question match, etc.


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
        
        # Check if we already have pillar_scores with golden_similarity_analysis AND breakdown
        has_existing_analysis = (
            survey.pillar_scores and 
            isinstance(survey.pillar_scores, dict) and
            "golden_similarity_analysis" in survey.pillar_scores and
            "similarity_breakdown" in survey.pillar_scores.get("golden_similarity_analysis", {}) and
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
            logger.info("✅ [SurveyQualityAPI] Using existing golden similarity analysis with breakdown")
        else:
            # For older surveys, recalculate using new SOTA comparison
            if force_refresh:
                logger.info("🔄 [SurveyQualityAPI] Force refresh requested, recalculating similarity breakdown")
            else:
                logger.info("ℹ️ [SurveyQualityAPI] No detailed similarity breakdown available, recalculating with SOTA approach")
            
            # Get golden examples used during generation
            used_golden_examples = survey.used_golden_examples or []
            num_golden_examples = len(used_golden_examples) if used_golden_examples else 0
            
            # Try to recalculate using new comparison function
            individual_similarities = []
            avg_similarity = 0.0
            
            if num_golden_examples > 0 and survey.final_output:
                try:
                    from src.database.models import GoldenRFQSurveyPair
                    from src.utils.survey_comparison import compare_surveys
                    
                    golden_pairs = db.query(GoldenRFQSurveyPair).filter(
                        GoldenRFQSurveyPair.id.in_(used_golden_examples[:10])  # Limit to 10
                    ).all()
                    
                    logger.info(f"🔄 [SurveyQualityAPI] Recalculating similarity for {len(golden_pairs)} golden examples")
                    
                    for pair in golden_pairs:
                        if pair.survey_json:
                            # Extract actual survey from nested structures if needed
                            golden_survey = pair.survey_json
                            if isinstance(golden_survey, dict) and "final_output" in golden_survey:
                                golden_survey = golden_survey["final_output"]
                            elif isinstance(golden_survey, dict) and "survey_json" in golden_survey:
                                golden_survey = golden_survey["survey_json"]
                            
                            # Ensure methodology_tags from database are available for comparison
                            if isinstance(golden_survey, dict) and pair.methodology_tags:
                                if "metadata" not in golden_survey:
                                    golden_survey["metadata"] = {}
                                # Use database methodology_tags if survey JSON doesn't have them
                                if not golden_survey["metadata"].get("methodology_tags"):
                                    golden_survey["metadata"]["methodology_tags"] = pair.methodology_tags
                                # Also ensure industry_category is set
                                if pair.industry_category and not golden_survey["metadata"].get("industry_category"):
                                    golden_survey["metadata"]["industry_category"] = pair.industry_category
                            
                            # Use new SOTA comparison function
                            similarity = compare_surveys(survey.final_output, golden_survey)
                            
                            # Extract the best title: prefer final_output title (most accurate), then survey_json title, then extract from RFQ
                            survey_title = None
                            if isinstance(pair.survey_json, dict):
                                # First try final_output title (most accurate survey title)
                                final_output = pair.survey_json.get('final_output', {})
                                if isinstance(final_output, dict):
                                    survey_title = final_output.get('title', '').strip()
                                
                                # If no final_output title, try top-level title
                                if not survey_title:
                                    survey_title = pair.survey_json.get('title', '').strip()
                            
                            # Check if title looks like concatenated methodology tags
                            def is_tag_concatenated(title):
                                if not title or len(title) < 10:
                                    return False
                                # If title contains 3+ methodology keywords, it's likely concatenated
                                keywords = ['van westendorp', 'conjoint', 'nps', 'pricing study', 'concept testing', 
                                          'market research', 'satisfaction', 'brand tracking', 'attitude']
                                keyword_count = sum(1 for kw in keywords if kw.lower() in title.lower())
                                return keyword_count >= 3
                            
                            # If title looks concatenated, try to extract from RFQ
                            if survey_title and is_tag_concatenated(survey_title):
                                # Extract meaningful title from RFQ
                                rfq_lines = pair.rfq_text.split('\n')[:5]
                                for line in rfq_lines:
                                    line = line.strip()
                                    if line and not line.startswith('RFQ') and not line.startswith('REQUEST'):
                                        # Use first meaningful line from RFQ as title
                                        if len(line) > 10 and len(line) < 100:
                                            survey_title = line
                                            break
                            
                            # Use survey title if available and meaningful, otherwise fall back to pair.title
                            display_title = survey_title if survey_title else (pair.title or "Untitled Golden Example")
                            
                            individual_similarities.append({
                                "golden_id": str(pair.id),
                                "similarity": float(similarity),
                                "title": display_title,
                                "methodology_tags": pair.methodology_tags or [],
                                "industry_category": pair.industry_category
                            })
                    
                    # Calculate average from individual similarities
                    if individual_similarities:
                        avg_similarity = sum(s['similarity'] for s in individual_similarities) / len(individual_similarities)
                    
                    # Store the recalculated analysis for future use
                    # Also include detailed similarity breakdown for UI
                    # Compute detailed on best match if available, else on first
                    similarity_breakdown = None
                    try:
                        from src.utils.survey_comparison import compare_surveys_detailed, compute_question_match_across_all_golden_pairs
                        if individual_similarities:
                            # Identify best match index
                            best_idx = max(range(len(individual_similarities)), key=lambda k: individual_similarities[k]["similarity"])
                            best_pair = golden_pairs[best_idx]
                            best_survey = best_pair.survey_json
                            if isinstance(best_survey, dict) and "final_output" in best_survey:
                                best_survey = best_survey["final_output"]
                            elif isinstance(best_survey, dict) and "survey_json" in best_survey:
                                best_survey = best_survey["survey_json"]
                            
                            # Ensure metadata from DB is available
                            if isinstance(best_survey, dict) and best_pair.methodology_tags:
                                if "metadata" not in best_survey:
                                    best_survey["metadata"] = {}
                                if not best_survey["metadata"].get("methodology_tags"):
                                    best_survey["metadata"]["methodology_tags"] = best_pair.methodology_tags
                                if best_pair.industry_category and not best_survey["metadata"].get("industry_category"):
                                    best_survey["metadata"]["industry_category"] = best_pair.industry_category
                            
                            logger.info(f"🔄 [SurveyQualityAPI] Computing detailed breakdown for best match (index {best_idx})")
                            similarity_breakdown = compare_surveys_detailed(survey.final_output, best_survey)
                            
                            # Override question_match with cross-all-golden-pairs matching (more accurate)
                            # Match against ALL golden pairs, not just used ones (better coverage)
                            try:
                                from src.database.models import GoldenRFQSurveyPair
                                # Get ALL golden pairs for comprehensive question matching
                                all_golden_pairs = db.query(GoldenRFQSurveyPair).all()
                                
                                all_golden_surveys = []
                                for pair in all_golden_pairs:
                                    if not pair.survey_json:
                                        continue
                                    gs = pair.survey_json
                                    if isinstance(gs, dict) and "final_output" in gs:
                                        gs = gs["final_output"]
                                    elif isinstance(gs, dict) and "survey_json" in gs:
                                        gs = gs["survey_json"]
                                    
                                    if not isinstance(gs, dict):
                                        continue
                                    
                                    # Ensure metadata
                                    if pair.methodology_tags:
                                        if "metadata" not in gs:
                                            gs["metadata"] = {}
                                        if not gs["metadata"].get("methodology_tags"):
                                            gs["metadata"]["methodology_tags"] = pair.methodology_tags
                                        if pair.industry_category and not gs["metadata"].get("industry_category"):
                                            gs["metadata"]["industry_category"] = pair.industry_category
                                    
                                    all_golden_surveys.append(gs)
                                
                                logger.info(f"🔍 [SurveyQualityAPI] Matching against {len(all_golden_surveys)} golden surveys")
                                question_match_all = compute_question_match_across_all_golden_pairs(
                                    survey.final_output,
                                    all_golden_surveys
                                )
                                logger.info(f"🔍 [SurveyQualityAPI] Found {len(question_match_all.get('matched_pairs', []))} question matches")
                                similarity_breakdown["question_match"] = question_match_all
                                
                                logger.info(f"✅ [SurveyQualityAPI] Breakdown computed: methodology={similarity_breakdown.get('methodology_similarity', 0):.2%}, question_match={similarity_breakdown.get('question_match', {}).get('match_rate', 0):.2%} (across {len(all_golden_surveys)} golden pairs, {len(question_match_all.get('matched_pairs', []))} matches)")
                            except Exception as qm_error:
                                logger.warning(f"⚠️ [SurveyQualityAPI] Failed to compute cross-all-golden-pairs question matching, using single-survey match: {qm_error}", exc_info=True)
                                # Keep the question_match from compare_surveys_detailed (single survey match)
                                logger.info(f"✅ [SurveyQualityAPI] Breakdown computed: methodology={similarity_breakdown.get('methodology_similarity', 0):.2%}, question_match={similarity_breakdown.get('question_match', {}).get('match_rate', 0):.2%} (single survey match)")
                    except Exception as e:
                        logger.error(f"❌ [SurveyQualityAPI] Failed to compute similarity breakdown: {e}", exc_info=True)
                        similarity_breakdown = None

                    golden_similarity_analysis = {
                        "overall_average": float(avg_similarity),
                        "best_match": {
                            "golden_id": str(individual_similarities[0]["golden_id"]) if individual_similarities else None,
                            "title": individual_similarities[0]["title"] if individual_similarities else None,
                            "similarity": float(individual_similarities[0]["similarity"]) if individual_similarities else 0.0,
                            "match_type": "overall",
                            "match_reason": "Recalculated using SOTA hybrid comparison (TF-IDF + structural + metadata)"
                        } if individual_similarities else None,
                        "best_industry_match": None,
                        "best_methodology_match": None,
                        "best_combined_match": None,
                        "individual_similarities": individual_similarities,
                        "methodology_alignment": {"score": 0.0},
                        "industry_alignment": {"score": 0.0},
                        "total_golden_examples_analyzed": len(individual_similarities),
                        "similarity_breakdown": similarity_breakdown,
                        "note": "Recalculated using SOTA hybrid approach - improved accuracy over legacy method"
                    }
                    
                    # Store in pillar_scores for future use
                    if survey.pillar_scores is None:
                        survey.pillar_scores = {}
                    survey.pillar_scores["golden_similarity_analysis"] = golden_similarity_analysis
                    db.commit()
                    
                    logger.info(f"✅ [SurveyQualityAPI] Recalculated similarity: {avg_similarity:.2%} average")
                    
                except Exception as e:
                    logger.error(f"⚠️ [SurveyQualityAPI] Failed to recalculate similarity: {e}", exc_info=True)
                    # Fallback to legacy approach
                    avg_similarity = survey.golden_similarity_score or 0.0
                    individual_similarities = []
                    if used_golden_examples:
                        from src.database.models import GoldenRFQSurveyPair
                        golden_pairs = db.query(GoldenRFQSurveyPair).filter(
                            GoldenRFQSurveyPair.id.in_(used_golden_examples[:3])
                        ).all()
                        for pair in golden_pairs:
                            individual_similarities.append({
                                "golden_id": str(pair.id),
                                "similarity": float(avg_similarity),
                                "title": pair.title or "Untitled",
                                "methodology_tags": pair.methodology_tags or [],
                                "industry_category": pair.industry_category
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
                        "note": "Legacy analysis - detailed breakdown not available"
                    }
            else:
                # No golden examples or final output
                avg_similarity = survey.golden_similarity_score or 0.0
                golden_similarity_analysis = {
                    "overall_average": float(avg_similarity),
                    "best_match": None,
                    "best_industry_match": None,
                    "best_methodology_match": None,
                    "best_combined_match": None,
                    "individual_similarities": [],
                    "methodology_alignment": {"score": 0.0},
                    "industry_alignment": {"score": 0.0},
                    "total_golden_examples_analyzed": 0,
                    "note": "No golden examples available for comparison"
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
            total_golden_examples_analyzed=golden_similarity_analysis.get("total_golden_examples_analyzed", 0),
            similarity_breakdown=golden_similarity_analysis.get("similarity_breakdown")
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

