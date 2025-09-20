#!/usr/bin/env python3
"""
Pillar Scores API
Endpoints for retrieving and managing pillar adherence scores
"""

from fastapi import APIRouter, Depends, HTTPException
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
    from evaluations.modules.pillar_based_evaluator import PillarBasedEvaluator
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

async def _get_evaluation_mode() -> str:
    """Get current evaluation mode from settings"""
    try:
        import requests
        response = requests.get("http://localhost:8000/api/v1/settings/evaluation-mode")
        if response.status_code == 200:
            data = response.json()
            return data.get("evaluation_mode", "single_call")
    except Exception as e:
        logger.warning(f"⚠️ Failed to get evaluation mode from settings: {e}")
    
    # Default to single_call if settings unavailable
    return "single_call"

async def _evaluate_with_advanced_system(survey_data: Dict[str, Any], rfq_text: str, db: Session, survey_id: str = None, rfq_id: str = None) -> OverallPillarScoreResponse:
    """
    Evaluate survey using the appropriate evaluator based on settings
    """
    # Get evaluation mode from settings
    evaluation_mode = await _get_evaluation_mode()
    logger.info(f"🚀 Using {evaluation_mode} evaluation mode")
    
    try:
        # Initialize LLM client for advanced evaluator
        from evaluations.llm_client import create_evaluation_llm_client
        llm_client = create_evaluation_llm_client(db_session=db)
        
        # Choose evaluator based on settings
        if evaluation_mode == "single_call":
            # Use single-call evaluator for cost efficiency
            evaluator = SingleCallEvaluator(llm_client=llm_client, db_session=db)
            result = await evaluator.evaluate_survey(survey_data, rfq_text, survey_id, rfq_id)
        elif evaluation_mode == "multiple_calls":
            # Use multiple-call evaluator for detailed analysis
            evaluator = PillarBasedEvaluator(llm_client=llm_client, db_session=db)
            result = await evaluator.evaluate_survey(survey_data, rfq_text, survey_id, rfq_id)
        else:  # hybrid
            # Use single-call for now (can implement hybrid later)
            evaluator = SingleCallEvaluator(llm_client=llm_client, db_session=db)
            result = await evaluator.evaluate_survey(survey_data, rfq_text, survey_id, rfq_id)
        
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
        
        # Handle different result types
        if hasattr(result, 'pillar_scores') and isinstance(result.pillar_scores, dict):
            # SingleCallEvaluator result
            pillar_scores = result.pillar_scores
            weights = {
                'content_validity': 0.20,
                'methodological_rigor': 0.25,
                'clarity_comprehensibility': 0.25,
                'structural_coherence': 0.20,
                'deployment_readiness': 0.10
            }
        else:
            # PillarBasedEvaluator result
            pillar_scores = {
                'content_validity': getattr(result.pillar_scores, 'content_validity', 0.5),
                'methodological_rigor': getattr(result.pillar_scores, 'methodological_rigor', 0.5),
                'clarity_comprehensibility': getattr(result.pillar_scores, 'clarity_comprehensibility', 0.5),
                'structural_coherence': getattr(result.pillar_scores, 'structural_coherence', 0.5),
                'deployment_readiness': getattr(result.pillar_scores, 'deployment_readiness', 0.5)
            }
            weights = getattr(evaluator, 'PILLAR_WEIGHTS', {
                'content_validity': 0.20,
                'methodological_rigor': 0.25,
                'clarity_comprehensibility': 0.25,
                'structural_coherence': 0.20,
                'deployment_readiness': 0.10
            })
        
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
        evaluation_mode = await _get_evaluation_mode()
        cost_savings = getattr(result, 'cost_savings', {})
        
        if evaluation_mode == "single_call":
            cost_info = f"Cost Savings: {cost_savings.get('cost_reduction_percent', 0):.0f}% (${cost_savings.get('estimated_cost_saved', 0):.2f} saved)"
            advanced_info = f"Single-Call Comprehensive Analysis | {cost_info}"
        else:
            advanced_info = f"Multiple-Call Detailed Analysis (v{result.evaluation_metadata.get('evaluation_version', '2.0')})"
        
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
        
        # Update cost metrics
        try:
            import requests
            cost_per_evaluation = 0.24 if evaluation_mode == "single_call" else 1.21  # Approximate costs
            requests.post(
                "http://localhost:8000/api/v1/settings/cost-metrics/update",
                params={
                    "evaluation_mode": evaluation_mode,
                    "cost_per_evaluation": cost_per_evaluation
                }
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
    logger.info(f"🏛️ [Pillar Scores API] Getting pillar scores for survey: {survey_id} (force={force})")
    
    try:
        # Get survey from database
        survey = db.query(Survey).filter(Survey.id == survey_id).first()
        
        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found")
        
        if not survey.final_output:
            raise HTTPException(status_code=400, detail="Survey has not been generated yet")
        
        # Check if pillar scores already exist in the survey object (unless forced to re-evaluate)
        if not force and survey.pillar_scores:
            logger.info("📋 [Pillar Scores API] Returning cached pillar scores from survey object")
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
                logger.warning("⚠️ [Pillar Scores API] Stored pillar scores are incomplete, re-evaluating")
        
        # Use advanced evaluators if available, otherwise fallback to basic
        if ADVANCED_EVALUATORS_AVAILABLE:
            # Extract RFQ text for advanced evaluation (fallback if not available)
            rfq_text = getattr(survey, 'original_rfq', survey.rfq.description if survey.rfq else '')
            if not rfq_text:
                rfq_text = f"Survey: {survey.final_output.get('title', 'Unnamed Survey')}"
            
            logger.info("🚀 Using advanced pillar evaluation system")
            response = await _evaluate_with_advanced_system(survey.final_output, rfq_text, db, str(survey.id), str(survey.rfq_id) if survey.rfq_id else None)
            return response
        else:
            logger.info("⚠️  Using legacy pillar scoring system")
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
        
        logger.info(f"✅ [Pillar Scores API] Successfully retrieved pillar scores: {pillar_scores.overall_grade} ({pillar_scores.weighted_score:.1%})")
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
    logger.info("🏛️ [Pillar Scores API] Evaluating survey data against pillar rules")
    
    try:
        # Use advanced evaluators if available, otherwise fallback to basic
        if ADVANCED_EVALUATORS_AVAILABLE:
            # For testing endpoint, use the survey title/description as RFQ if available
            rfq_text = survey_data.get('description', survey_data.get('title', 'Test survey evaluation'))
            
            logger.info("🚀 Using advanced pillar evaluation system for testing")
            response = await _evaluate_with_advanced_system(survey_data, rfq_text, db, "test_survey", None)
            return response
        else:
            logger.info("⚠️  Using legacy pillar scoring system for testing")
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
        
        logger.info(f"✅ [Pillar Scores API] Successfully evaluated survey: {pillar_scores.overall_grade} ({pillar_scores.weighted_score:.1%})")
        return response
        
    except Exception as e:
        logger.error(f"❌ [Pillar Scores API] Error evaluating survey: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to evaluate survey: {str(e)}")

@router.get("/rules/summary")
async def get_pillar_rules_summary(db: Session = Depends(get_db)):
    """
    Get a summary of all pillar rules for reference
    """
    logger.info("🏛️ [Pillar Scores API] Getting pillar rules summary")
    
    try:
        from src.database.models import SurveyRule
        
        # Get all pillar rules
        rules = db.query(SurveyRule).filter(
            SurveyRule.rule_type == 'pillar',
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
