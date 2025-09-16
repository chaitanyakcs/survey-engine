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
eval_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'evaluations')
if eval_path not in sys.path:
    sys.path.append(eval_path)

try:
    from evaluations.modules.pillar_based_evaluator import PillarBasedEvaluator
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

async def _evaluate_with_advanced_system(survey_data: Dict[str, Any], rfq_text: str, db: Session) -> OverallPillarScoreResponse:
    """
    Evaluate survey using the advanced pillar-based evaluator system
    """
    logger.info("🚀 Using advanced pillar evaluators with chain-of-thought reasoning")
    
    try:
        # Initialize advanced evaluator
        evaluator = PillarBasedEvaluator(llm_client=None, db_session=db)
        
        # Run advanced evaluation
        result = await evaluator.evaluate_survey(survey_data, rfq_text)
        
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
        
        weights = evaluator.PILLAR_WEIGHTS
        
        for pillar_name, display_name in pillar_mapping.items():
            score = getattr(result.pillar_scores, pillar_name)
            weight = weights[pillar_name]
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
        if result.overall_score >= 0.9:
            overall_grade = "A"
        elif result.overall_score >= 0.8:
            overall_grade = "B" 
        elif result.overall_score >= 0.7:
            overall_grade = "C"
        elif result.overall_score >= 0.6:
            overall_grade = "D"
        else:
            overall_grade = "F"
        
        # Create enhanced summary with advanced evaluation info
        advanced_info = f"Advanced Chain-of-Thought Analysis (v{result.evaluation_metadata.get('evaluation_version', '2.0')})"
        if result.evaluation_metadata.get('advanced_evaluators_used'):
            confidence_info = f"Content Validity Confidence: {result.evaluation_metadata.get('content_validity_confidence', 0):.0%}, " \
                           f"Methodological Rigor Confidence: {result.evaluation_metadata.get('methodological_rigor_confidence', 0):.0%}"
            advanced_summary = f"{advanced_info} | {confidence_info} | {result.evaluation_metadata.get('objectives_extracted', 0)} objectives extracted, {result.evaluation_metadata.get('biases_detected', 0)} biases detected"
        else:
            advanced_summary = f"{advanced_info} | Fallback mode active"
        
        return OverallPillarScoreResponse(
            overall_grade=overall_grade,
            weighted_score=result.overall_score,
            total_score=result.overall_score,  # For advanced system, these are the same
            summary=advanced_summary,
            pillar_breakdown=pillar_breakdown,
            recommendations=result.recommendations
        )
        
    except Exception as e:
        logger.error(f"❌ Advanced pillar evaluation failed: {e}")
        raise

@router.get("/{survey_id}", response_model=OverallPillarScoreResponse)
async def get_pillar_scores(
    survey_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get pillar adherence scores for a specific survey
    """
    logger.info(f"🏛️ [Pillar Scores API] Getting pillar scores for survey: {survey_id}")
    
    try:
        # Get survey from database
        survey = db.query(Survey).filter(Survey.id == survey_id).first()
        
        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found")
        
        if not survey.final_output:
            raise HTTPException(status_code=400, detail="Survey has not been generated yet")
        
        # Use advanced evaluators if available, otherwise fallback to basic
        if ADVANCED_EVALUATORS_AVAILABLE:
            # Extract RFQ text for advanced evaluation (fallback if not available)
            rfq_text = getattr(survey, 'original_rfq', survey.metadata.get('rfq', '')) if survey.metadata else ''
            if not rfq_text:
                rfq_text = f"Survey: {survey.final_output.get('title', 'Unnamed Survey')}"
            
            logger.info("🚀 Using advanced pillar evaluation system")
            response = await _evaluate_with_advanced_system(survey.final_output, rfq_text, db)
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
            response = await _evaluate_with_advanced_system(survey_data, rfq_text, db)
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
