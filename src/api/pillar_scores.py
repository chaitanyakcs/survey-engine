#!/usr/bin/env python3
"""
Pillar Scores API
Endpoints for retrieving and managing pillar adherence scores
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from src.database import get_db, Survey
from src.services.pillar_scoring_service import PillarScoringService
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from uuid import UUID
import logging
import asyncio
import sys
import os
import threading
from datetime import datetime

# Add evaluations directory to path for advanced evaluators
# Find project root by looking for the evaluations directory
current_dir = os.path.dirname(__file__)
project_root = current_dir
while project_root != '/' and project_root != '':
    eval_path = os.path.join(project_root, 'evaluations')
    if os.path.exists(eval_path):
        break
    project_root = os.path.dirname(project_root)

if not os.path.exists(eval_path):
    # Fallback: use current working directory
    project_root = os.getcwd()
    eval_path = os.path.join(project_root, 'evaluations')

eval_path = os.path.abspath(eval_path)  # Convert to absolute path
if eval_path not in sys.path:
    sys.path.insert(0, eval_path)  # Insert at beginning for higher priority

try:
    from evaluations.modules.single_call_evaluator import SingleCallEvaluator
    ADVANCED_EVALUATORS_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("🚀 Advanced pillar evaluators loaded successfully")
except ImportError as e:
    ADVANCED_EVALUATORS_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(f"⚠️  Advanced pillar evaluators not available: {e}")

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pillar-scores", tags=["Pillar Scores"])

# Global lock to prevent concurrent evaluations of the same survey
_evaluation_locks = {}
_lock_cleanup_lock = threading.Lock()

# Pydantic models
class PillarScoreResponse(BaseModel):
    pillar_name: str
    display_name: str
    score: float
    weighted_score: float
    weight: float
    criteria_met: int
    total_criteria: int
    grade: str

class OverallPillarScoreResponse(BaseModel):
    overall_grade: str
    weighted_score: float
    total_score: float
    summary: str
    pillar_breakdown: List[PillarScoreResponse]
    recommendations: List[str]

class EvaluationStatusResponse(BaseModel):
    status: str
    data: Optional[OverallPillarScoreResponse] = None
    message: Optional[str] = None

# Removed _get_evaluation_mode_cached() and _get_evaluation_mode() functions
# Evaluation mode is now retrieved directly from SettingsService using database session
# This avoids HTTP timeouts and improves performance

def _get_evaluation_lock(survey_id: str) -> threading.Lock:
    """Get or create a lock for a specific survey to prevent concurrent evaluations"""
    with _lock_cleanup_lock:
        if survey_id not in _evaluation_locks:
            _evaluation_locks[survey_id] = threading.Lock()
        return _evaluation_locks[survey_id]

def _cleanup_evaluation_lock(survey_id: str):
    """Clean up evaluation lock for a survey (call after evaluation completes)"""
    with _lock_cleanup_lock:
        if survey_id in _evaluation_locks:
            del _evaluation_locks[survey_id]

async def _evaluate_with_advanced_system(survey_data: Dict[str, Any], rfq_text: str, db: Session, survey_id: str = None, rfq_id: str = None) -> OverallPillarScoreResponse:
    """
    Evaluate survey using SingleCallEvaluator
    """
    logger.info(f"🚀 Starting survey evaluation")
    
    try:
        # Initialize LLM client for evaluator
        from evaluations.llm_client import create_evaluation_llm_client
        llm_client = create_evaluation_llm_client(db_session=db)
        
        # Use single-call evaluator
        evaluator = SingleCallEvaluator(llm_client=llm_client, db_session=db)
        result = await evaluator.evaluate_survey(survey_data, rfq_text, survey_id, rfq_id)
        
        # Generate AI annotations if result has annotation data
        logger.info(f"🔍 [Pillar Scores] Result type: {type(result)}")
        logger.info(f"🔍 [Pillar Scores] Has question_annotations: {hasattr(result, 'question_annotations')}")
        logger.info(f"🔍 [Pillar Scores] Has section_annotations: {hasattr(result, 'section_annotations')}")
        
        # Generate AI annotations if result has annotation data
        if hasattr(result, 'question_annotations') and hasattr(result, 'section_annotations'):
            logger.info(f"🔍 [Pillar Scores] Question annotations count: {len(result.question_annotations)}")
            logger.info(f"🔍 [Pillar Scores] Section annotations count: {len(result.section_annotations)}")
            
            try:
                from src.services.ai_annotation_service import AIAnnotationService
                ai_service = AIAnnotationService(db)
                
                # Create AI annotations from evaluation result
                annotation_result = await ai_service.create_annotations_from_evaluation(
                    result, survey_id, "ai_system"
                )
                
                logger.info(f"🤖 Generated {annotation_result['total_created']} AI annotations for survey {survey_id}")
                
                # Add annotation info to evaluation metadata
                if hasattr(result, 'evaluation_metadata'):
                    result.evaluation_metadata['ai_annotations_created'] = annotation_result['total_created']
                    result.evaluation_metadata['annotation_errors'] = len(annotation_result['errors'])
                
            except Exception as e:
                logger.error(f"❌ Failed to generate AI annotations: {str(e)}")
                # Don't fail the evaluation, just log the error
        
        # Convert advanced results to API format
        pillar_breakdown = []
        
        # Map pillar scores to API format
        pillar_mapping = {
            'content_validity': 'Content Validity',
            'methodological_rigor': 'Methodological Rigor',
            'clarity_comprehensibility': 'Clarity & Comprehensibility',
            'structural_coherence': 'Structural Coherence',
            'deployment_readiness': 'Deployment Readiness'
        }
        
        # SingleCallEvaluator result handling
        pillar_scores = result.pillar_scores if hasattr(result, 'pillar_scores') and isinstance(result.pillar_scores, dict) else {}
        weights = {
            'content_validity': 0.20,
            'methodological_rigor': 0.25,
            'clarity_comprehensibility': 0.25,
            'structural_coherence': 0.20,
            'deployment_readiness': 0.10
        }
        
        for pillar_name, display_name in pillar_mapping.items():
            score = pillar_scores.get(pillar_name, 0.5)
            weight = weights.get(pillar_name, 0.2)
            weighted_score = score * weight
            
            # Convert score to criteria format (simulate criteria met/total for UI compatibility)
            criteria_met = int(score * 10)  # Scale to 0-10 for display
            total_criteria = 10
            
            # Calculate grade
            if score >= 0.9:
                grade = "A"
            elif score >= 0.8:
                grade = "B"
            elif score >= 0.7:
                grade = "C"
            elif score >= 0.6:
                grade = "D"
            else:
                grade = "F"
                
            pillar_breakdown.append(PillarScoreResponse(
                pillar_name=pillar_name,
                display_name=display_name,
                score=score,
                weighted_score=weighted_score,
                weight=weight,
                criteria_met=criteria_met,
                total_criteria=total_criteria,
                grade=grade
            ))
        
        # Calculate overall grade
        overall_score = getattr(result, 'weighted_score', getattr(result, 'overall_score', 0.5))
        if overall_score >= 0.9:
            overall_grade = "A"
        elif overall_score >= 0.8:
            overall_grade = "B" 
        elif overall_score >= 0.7:
            overall_grade = "C"
        elif overall_score >= 0.6:
            overall_grade = "D"
        else:
            overall_grade = "F"
        
        # Create enhanced summary with evaluation info
        advanced_info = "Single-Call Comprehensive Analysis"
        
        # Get recommendations
        recommendations = []
        if hasattr(result, 'overall_recommendations'):
            recommendations = result.overall_recommendations
        elif hasattr(result, 'recommendations'):
            recommendations = result.recommendations
        elif hasattr(result, 'detailed_analysis'):
            # Extract recommendations from detailed analysis
            for pillar_data in result.detailed_analysis.values():
                if isinstance(pillar_data, dict) and 'recommendations' in pillar_data:
                    recommendations.extend(pillar_data['recommendations'])
        
        # Update cost metrics (non-blocking)
        try:
            import requests
            cost_per_evaluation = 0.24  # Approximate cost per evaluation
            requests.post(
                "http://localhost:8000/api/v1/settings/cost-metrics/update",
                params={
                    "cost_per_evaluation": cost_per_evaluation
                },
                timeout=5  # Add timeout to prevent hanging
            )
        except Exception as e:
            logger.warning(f"⚠️ Failed to update cost metrics: {e}")
        
        return OverallPillarScoreResponse(
            overall_grade=overall_grade,
            weighted_score=overall_score,
            total_score=overall_score,
            summary=advanced_info,
            pillar_breakdown=pillar_breakdown,
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"❌ Advanced pillar evaluation failed: {e}")
        raise

@router.get("/{survey_id}", response_model=OverallPillarScoreResponse)
async def get_pillar_scores(
    survey_id: UUID,
    force: bool = False,
    db: Session = Depends(get_db)
):
    """
    Get pillar adherence scores for a specific survey
    Args:
        survey_id: UUID of the survey
        force: If True, re-evaluate even if scores exist (default: False)
    """
    
    try:
        # Get survey from database
        survey = db.query(Survey).filter(Survey.id == survey_id).first()
        
        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found")
        
        if not survey.final_output:
            raise HTTPException(status_code=400, detail="Survey has not been generated yet")
        
        # Check if pillar scores already exist in the survey object (unless forced to re-evaluate)
        if not force and survey.pillar_scores:
            # Convert stored scores to response format
            stored_scores = survey.pillar_scores
            
            # Validate that the stored scores have the expected structure
            if (stored_scores.get('overall_grade') and 
                stored_scores.get('weighted_score') is not None and
                stored_scores.get('pillar_breakdown')):
                
                pillar_breakdown = [
                    PillarScoreResponse(
                        pillar_name=pillar.get('pillar_name', ''),
                        display_name=pillar.get('display_name', ''),
                        score=pillar.get('score', 0.0),
                        weighted_score=pillar.get('weighted_score', 0.0),
                        weight=pillar.get('weight', 0.0),
                        criteria_met=pillar.get('criteria_met', 0),
                        total_criteria=pillar.get('total_criteria', 0),
                        grade=pillar.get('grade', 'F')
                    )
                    for pillar in stored_scores.get('pillar_breakdown', [])
                ]
                
                return OverallPillarScoreResponse(
                    overall_grade=stored_scores.get('overall_grade', 'F'),
                    weighted_score=stored_scores.get('weighted_score', 0.0),
                    total_score=stored_scores.get('total_score', 0.0),
                    summary=stored_scores.get('summary', 'Cached evaluation results'),
                    pillar_breakdown=pillar_breakdown,
                    recommendations=stored_scores.get('recommendations', [])
                )
            else:
                # Re-evaluate if scores are incomplete
                pass
        
        # Use advanced evaluators if available, otherwise fallback to basic
        if ADVANCED_EVALUATORS_AVAILABLE:
            # Get lock for this survey to prevent concurrent evaluations
            survey_id_str = str(survey.id)
            evaluation_lock = _get_evaluation_lock(survey_id_str)
            
            # Try to acquire lock with timeout to prevent hanging
            if not evaluation_lock.acquire(blocking=False):
                # If we can't get the lock, check if there are cached scores
                if survey.pillar_scores:
                    stored_scores = survey.pillar_scores
                    pillar_breakdown = [
                        PillarScoreResponse(
                            pillar_name=pillar.get('pillar_name', ''),
                            display_name=pillar.get('display_name', ''),
                            score=pillar.get('score', 0.0),
                            weighted_score=pillar.get('weighted_score', 0.0),
                            weight=pillar.get('weight', 0.0),
                            criteria_met=pillar.get('criteria_met', 0),
                            total_criteria=pillar.get('total_criteria', 0),
                            grade=pillar.get('grade', 'F')
                        )
                        for pillar in stored_scores.get('pillar_breakdown', [])
                    ]
                    return OverallPillarScoreResponse(
                        overall_grade=stored_scores.get('overall_grade', 'F'),
                        weighted_score=stored_scores.get('weighted_score', 0.0),
                        total_score=stored_scores.get('total_score', 0.0),
                        summary=stored_scores.get('summary', 'Evaluation in progress'),
                        pillar_breakdown=pillar_breakdown,
                        recommendations=stored_scores.get('recommendations', [])
                    )
                else:
                    # No cached scores and evaluation is in progress - return a "pending" response
                    # instead of waiting or triggering another evaluation
                    return OverallPillarScoreResponse(
                        overall_grade="Pending",
                        weighted_score=0.0,
                        total_score=0.0,
                        summary="Evaluation in progress, please check back in a few moments",
                        pillar_breakdown=[],
                        recommendations=[]
                    )
            
            try:
                # Extract RFQ text for advanced evaluation (fallback if not available)
                rfq_text = getattr(survey, 'original_rfq', survey.rfq.description if survey.rfq else '')
                if not rfq_text:
                    rfq_text = f"Survey: {survey.final_output.get('title', 'Unnamed Survey')}"


                # Run evaluation using SingleCallEvaluator
                response = await _evaluate_with_advanced_system(survey.final_output, rfq_text, db, str(survey.id), str(survey.rfq_id) if survey.rfq_id else None)
                
                # Update survey record with pillar scores
                if response:
                    try:
                        # Convert response to dict format for storage
                        pillar_scores_data = {
                            "overall_grade": response.overall_grade,
                            "weighted_score": response.weighted_score,
                            "total_score": response.total_score,
                            "summary": response.summary,
                            "pillar_breakdown": [
                                {
                                    "pillar_name": pillar.pillar_name,
                                    "display_name": pillar.display_name,
                                    "score": pillar.score,
                                    "weighted_score": pillar.weighted_score,
                                    "weight": pillar.weight,
                                    "criteria_met": pillar.criteria_met,
                                    "total_criteria": pillar.total_criteria,
                                    "grade": pillar.grade
                                }
                                for pillar in response.pillar_breakdown
                            ],
                            "recommendations": response.recommendations,
                            "evaluation_timestamp": datetime.now().isoformat()
                        }
                        
                        # Update survey record
                        survey.pillar_scores = pillar_scores_data
                        db.commit()
                        
                        logger.info(f"✅ [Pillar Scores API] Updated survey {survey_id} with pillar scores: {response.overall_grade} ({response.weighted_score:.2f})")
                        
                    except Exception as e:
                        logger.error(f"❌ [Pillar Scores API] Failed to update survey with pillar scores: {str(e)}")
                        # Don't fail the request, just log the error
                
                return response
            finally:
                # Always release the lock and clean up
                evaluation_lock.release()
                _cleanup_evaluation_lock(survey_id_str)
        else:
            # Fallback to legacy system
            pillar_scoring_service = PillarScoringService(db)
            pillar_scores = pillar_scoring_service.evaluate_survey_pillars(survey.final_output)
        
        # Convert to response format
        pillar_breakdown = [
            PillarScoreResponse(
                pillar_name=score.pillar_name,
                display_name=score.pillar_name.replace('_', ' ').title().replace('Comprehensibility', '& Comprehensibility'),
                score=score.score,
                weighted_score=score.weighted_score,
                weight=score.weight,
                criteria_met=score.criteria_met,
                total_criteria=score.total_criteria,
                grade=pillar_scoring_service._calculate_grade(score.score)
            )
            for score in pillar_scores.pillar_scores
        ]
        
        # Compile recommendations
        recommendations = []
        for score in pillar_scores.pillar_scores:
            recommendations.extend(score.recommendations)
        
        # Remove duplicates
        unique_recommendations = list(dict.fromkeys(recommendations))
        
        response = OverallPillarScoreResponse(
            overall_grade=pillar_scores.overall_grade,
            weighted_score=pillar_scores.weighted_score,
            total_score=pillar_scores.total_score,
            summary=pillar_scores.summary,
            pillar_breakdown=pillar_breakdown,
            recommendations=unique_recommendations
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [Pillar Scores API] Error getting pillar scores for survey {survey_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get pillar scores: {str(e)}")

@router.post("/evaluate", response_model=OverallPillarScoreResponse)
async def evaluate_survey_pillars(
    survey_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Evaluate a survey JSON against pillar rules (for testing/validation)
    """
    
    try:
        # Use advanced evaluators if available, otherwise fallback to basic
        if ADVANCED_EVALUATORS_AVAILABLE:
            # For testing endpoint, use the survey title/description as RFQ if available
            rfq_text = survey_data.get('description', survey_data.get('title', 'Test survey evaluation'))
            
            response = await _evaluate_with_advanced_system(survey_data, rfq_text, db, "test_survey", None)
            return response
        else:
            # Fallback to legacy system
            pillar_scoring_service = PillarScoringService(db)
            pillar_scores = pillar_scoring_service.evaluate_survey_pillars(survey_data)
        
        # Convert to response format
        pillar_breakdown = [
            PillarScoreResponse(
                pillar_name=score.pillar_name,
                display_name=score.pillar_name.replace('_', ' ').title().replace('Comprehensibility', '& Comprehensibility'),
                score=score.score,
                weighted_score=score.weighted_score,
                weight=score.weight,
                criteria_met=score.criteria_met,
                total_criteria=score.total_criteria,
                grade=pillar_scoring_service._calculate_grade(score.score)
            )
            for score in pillar_scores.pillar_scores
        ]
        
        # Compile recommendations
        recommendations = []
        for score in pillar_scores.pillar_scores:
            recommendations.extend(score.recommendations)
        
        # Remove duplicates
        unique_recommendations = list(dict.fromkeys(recommendations))
        
        response = OverallPillarScoreResponse(
            overall_grade=pillar_scores.overall_grade,
            weighted_score=pillar_scores.weighted_score,
            total_score=pillar_scores.total_score,
            summary=pillar_scores.summary,
            pillar_breakdown=pillar_breakdown,
            recommendations=unique_recommendations
        )
        
        return response
        
    except Exception as e:
        logger.error(f"❌ [Pillar Scores API] Error evaluating survey: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to evaluate survey: {str(e)}")

async def _run_evaluation_background(survey_id: str):
    """
    Background task to run evaluation for a survey
    """
    evaluation_lock = None
    try:
        logger.info(f"🚀 [Background Evaluation] Starting evaluation for survey {survey_id}")
        
        # Get a fresh database session for the background task
        from src.database import get_db
        fresh_db = next(get_db())
        
        try:
            # Get survey
            survey = fresh_db.query(Survey).filter(Survey.id == UUID(survey_id)).first()
            if not survey:
                logger.error(f"❌ [Background Evaluation] Survey {survey_id} not found")
                return
            
            if not survey.final_output:
                logger.error(f"❌ [Background Evaluation] Survey {survey_id} has no final_output")
                return
            
            # Extract RFQ text
            rfq_text = getattr(survey, 'original_rfq', survey.rfq.description if survey.rfq else '')
            if not rfq_text:
                rfq_text = f"Survey: {survey.final_output.get('title', 'Unnamed Survey')}"
            
            # Run evaluation using SingleCallEvaluator
            response = await _evaluate_with_advanced_system(
                survey.final_output, rfq_text, fresh_db,
                str(survey.id), str(survey.rfq_id) if survey.rfq_id else None
            )
            
            # Update survey record with pillar scores
            if response:
                pillar_scores_data = {
                    "overall_grade": response.overall_grade,
                    "weighted_score": response.weighted_score,
                    "total_score": response.total_score,
                    "summary": response.summary,
                    "pillar_breakdown": [
                        {
                            "pillar_name": pillar.pillar_name,
                            "display_name": pillar.display_name,
                            "score": pillar.score,
                            "weighted_score": pillar.weighted_score,
                            "weight": pillar.weight,
                            "criteria_met": pillar.criteria_met,
                            "total_criteria": pillar.total_criteria,
                            "grade": pillar.grade
                        }
                        for pillar in response.pillar_breakdown
                    ],
                    "recommendations": response.recommendations,
                    "evaluation_timestamp": datetime.now().isoformat()
                }
                
                survey.pillar_scores = pillar_scores_data
                fresh_db.commit()
                logger.info(f"✅ [Background Evaluation] Updated survey {survey_id} with pillar scores: {response.overall_grade} ({response.weighted_score:.2f})")
            
        finally:
            fresh_db.close()
            
    except Exception as e:
        logger.error(f"❌ [Background Evaluation] Error evaluating survey {survey_id}: {str(e)}", exc_info=True)
    finally:
        # Always release the lock
        try:
            evaluation_lock = _get_evaluation_lock(survey_id)
            if evaluation_lock.locked():
                evaluation_lock.release()
            _cleanup_evaluation_lock(survey_id)
            logger.info(f"🔓 [Background Evaluation] Released evaluation lock for survey {survey_id}")
        except Exception as e:
            logger.warning(f"⚠️ [Background Evaluation] Error releasing lock: {e}")

@router.post("/{survey_id}/run-evaluation", response_model=EvaluationStatusResponse)
async def run_evaluation(
    survey_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Trigger async evaluation for a survey. Returns immediately with status.
    Evaluation runs in background and results are saved to survey.pillar_scores.
    """
    try:
        survey_id_str = str(survey_id)
        
        # Get survey
        survey = db.query(Survey).filter(Survey.id == survey_id).first()
        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found")
        
        if not survey.final_output:
            raise HTTPException(status_code=400, detail="Survey has not been generated yet")
        
        # Check if evaluation is already in progress
        evaluation_lock = _get_evaluation_lock(survey_id_str)
        
        # Try to acquire lock (non-blocking)
        if evaluation_lock.locked():
            logger.info(f"⏳ [Run Evaluation] Evaluation already in progress for survey {survey_id_str}")
            return EvaluationStatusResponse(
                status="in_progress",
                message="Evaluation is already running. Please check back in a few moments."
            )
        
        # Check if we already have valid pillar scores
        if survey.pillar_scores and isinstance(survey.pillar_scores, dict):
            weighted_score = survey.pillar_scores.get('weighted_score', 0)
            summary = survey.pillar_scores.get('summary', '')
            
            # Check if it's a valid completed evaluation (not in-progress)
            if weighted_score > 0 and "in progress" not in summary.lower():
                logger.info(f"✅ [Run Evaluation] Survey {survey_id_str} already has evaluation results")
                # Return existing results
                try:
                    existing_response = OverallPillarScoreResponse(
                        overall_grade=survey.pillar_scores.get('overall_grade', 'N/A'),
                        weighted_score=survey.pillar_scores.get('weighted_score', 0.0),
                        total_score=survey.pillar_scores.get('total_score', 0.0),
                        summary=survey.pillar_scores.get('summary', ''),
                        pillar_breakdown=[
                            PillarScoreResponse(
                                pillar_name=p.get('pillar_name', ''),
                                display_name=p.get('display_name', ''),
                                score=p.get('score', 0.0),
                                weighted_score=p.get('weighted_score', 0.0),
                                weight=p.get('weight', 0.0),
                                criteria_met=p.get('criteria_met', 0),
                                total_criteria=p.get('total_criteria', 0),
                                grade=p.get('grade', 'F')
                            )
                            for p in survey.pillar_scores.get('pillar_breakdown', [])
                        ],
                        recommendations=survey.pillar_scores.get('recommendations', [])
                    )
                    return EvaluationStatusResponse(
                        status="completed",
                        data=existing_response,
                        message="Evaluation already completed"
                    )
                except Exception as e:
                    logger.warning(f"⚠️ [Run Evaluation] Error parsing existing scores: {e}")
                    # Continue to trigger new evaluation
        
        # Acquire lock
        evaluation_lock.acquire()
        logger.info(f"🔓 [Run Evaluation] Acquired evaluation lock for survey {survey_id_str}")
        
        # Set initial "in progress" state
        survey.pillar_scores = {
            "overall_grade": "Pending",
            "weighted_score": 0.0,
            "total_score": 0.0,
            "summary": "Evaluation in progress, please check back in a few moments",
            "pillar_breakdown": [],
            "recommendations": [],
            "evaluation_status": "in_progress",
            "evaluation_timestamp": datetime.now().isoformat()
        }
        db.commit()
        
        # Trigger background evaluation
        background_tasks.add_task(_run_evaluation_background, survey_id_str)
        
        logger.info(f"🚀 [Run Evaluation] Triggered background evaluation for survey {survey_id_str}")
        
        return EvaluationStatusResponse(
            status="in_progress",
            message="Evaluation started. Results will be available shortly."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [Run Evaluation] Error triggering evaluation for survey {survey_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger evaluation: {str(e)}")

@router.get("/{survey_id}/ai-annotations")
async def get_ai_annotations(
    survey_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get AI-generated annotations for a specific survey
    """
    try:
        from src.services.ai_annotation_service import AIAnnotationService
        ai_service = AIAnnotationService(db)
        
        annotations = ai_service.get_ai_annotations_for_survey(str(survey_id))
        
        return {
            "survey_id": str(survey_id),
            "question_annotations": annotations["question_annotations"],
            "section_annotations": annotations["section_annotations"],
            "total_annotations": len(annotations["question_annotations"]) + len(annotations["section_annotations"])
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting AI annotations: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get AI annotations: {str(e)}"
        )

class VerifyAnnotationRequest(BaseModel):
    annotation_id: int
    annotation_type: str

@router.post("/{survey_id}/verify-annotation")
async def verify_ai_annotation(
    survey_id: UUID,
    request_data: VerifyAnnotationRequest,
    db: Session = Depends(get_db)
):
    """
    Mark an AI-generated annotation as human verified
    """
    try:
        from src.services.ai_annotation_service import AIAnnotationService
        ai_service = AIAnnotationService(db)
        
        success = await ai_service.mark_annotation_as_verified(request_data.annotation_id, request_data.annotation_type)
        
        if success:
            return {"status": "success", "message": "Annotation marked as verified"}
        else:
            raise HTTPException(
                status_code=404,
                detail="Annotation not found or verification failed"
            )
        
    except Exception as e:
        logger.error(f"❌ Error verifying annotation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to verify annotation: {str(e)}"
        )

@router.get("/rules/summary")
async def get_pillar_rules_summary(db: Session = Depends(get_db)):
    """
    Get a summary of all pillar rules for reference
    """
    
    try:
        from src.database.models import SurveyRule
        
        # Get all pillar rules (both pillar and generation types)
        rules = db.query(SurveyRule).filter(
            SurveyRule.rule_type.in_(['pillar', 'generation']),
            SurveyRule.is_active == True
        ).all()
        
        # Group by pillar
        pillar_summary = {}
        for rule in rules:
            pillar = rule.category
            if pillar not in pillar_summary:
                pillar_summary[pillar] = {
                    'pillar_name': pillar.replace('_', ' ').title().replace('Comprehensibility', '& Comprehensibility'),
                    'rule_count': 0,
                    'rules': []
                }
            
            pillar_summary[pillar]['rule_count'] += 1
            pillar_summary[pillar]['rules'].append({
                'id': str(rule.id),
                'description': rule.rule_description,
                'priority': rule.rule_content.get('priority', 'medium') if rule.rule_content else 'medium'
            })
        
        return {
            'total_pillars': len(pillar_summary),
            'total_rules': len(rules),
            'pillars': list(pillar_summary.values())
        }
        
    except Exception as e:
        logger.error(f"❌ [Pillar Scores API] Error getting pillar rules summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get pillar rules summary: {str(e)}")

