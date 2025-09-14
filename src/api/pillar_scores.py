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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pillar-scores", tags=["Pillar Scores"])

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
        
        # Initialize pillar scoring service
        pillar_scoring_service = PillarScoringService(db)
        
        # Evaluate survey against pillar rules
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
        # Initialize pillar scoring service
        pillar_scoring_service = PillarScoringService(db)
        
        # Evaluate survey against pillar rules
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
