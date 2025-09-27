#!/usr/bin/env python3
"""
Async Pillar Evaluation Service
Handles asynchronous pillar evaluation with WebSocket progress updates
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from uuid import UUID
from src.services.websocket_client import WebSocketNotificationService
from src.services.progress_tracker import get_progress_tracker
from src.services.pillar_scoring_service import PillarScoringService
from src.database import Survey
import sys
import os

# Add evaluations directory to path for advanced evaluators
current_dir = os.path.dirname(__file__)
project_root = current_dir
while project_root != '/' and project_root != '':
    eval_path = os.path.join(project_root, 'evaluations')
    if os.path.exists(eval_path):
        break
    project_root = os.path.dirname(project_root)

if not os.path.exists(eval_path):
    project_root = os.getcwd()
    eval_path = os.path.join(project_root, 'evaluations')

eval_path = os.path.abspath(eval_path)
if eval_path not in sys.path:
    sys.path.insert(0, eval_path)

try:
    from evaluations.modules.pillar_based_evaluator import PillarBasedEvaluator
    from evaluations.modules.single_call_evaluator import SingleCallEvaluator
    ADVANCED_EVALUATORS_AVAILABLE = True
except ImportError as e:
    ADVANCED_EVALUATORS_AVAILABLE = False

logger = logging.getLogger(__name__)


class AsyncPillarEvaluationService:
    """
    Service for asynchronous pillar evaluation with progress updates
    """
    
    def __init__(self, db: Session, connection_manager=None):
        self.db = db
        self.connection_manager = connection_manager
        self.ws_client = WebSocketNotificationService(connection_manager)
        self.active_evaluations = set()  # Track active evaluations
        
    async def evaluate_survey_pillars_async(
        self, 
        survey_id: str, 
        workflow_id: Optional[str] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluate survey pillars asynchronously with progress updates
        """
        if survey_id in self.active_evaluations:
            logger.warning(f"⚠️ [AsyncPillarEvaluation] Evaluation already in progress for survey {survey_id}")
            return {"status": "already_in_progress"}
            
        self.active_evaluations.add(survey_id)
        
        try:
            logger.info(f"🏛️ [AsyncPillarEvaluation] Starting async pillar evaluation for survey {survey_id}")
            
            # Send initial progress update
            if workflow_id:
                await self.ws_client.send_progress_update(workflow_id, {
                    "type": "pillar_evaluation_started",
                    "survey_id": survey_id,
                    "message": "Starting pillar evaluation..."
                })
            
            # Get survey from database
            survey = self.db.query(Survey).filter(Survey.id == survey_id).first()
            if not survey:
                raise ValueError(f"Survey {survey_id} not found")
            
            if not survey.final_output:
                raise ValueError(f"Survey {survey_id} has no final output")
            
            # Check if we already have pillar scores (unless forced)
            if not force and survey.pillar_scores:
                logger.info(f"📋 [AsyncPillarEvaluation] Returning cached pillar scores for survey {survey_id}")
                return {
                    "status": "completed",
                    "pillar_scores": survey.pillar_scores,
                    "cached": True
                }
            
            # Send progress update
            if workflow_id:
                progress_tracker = get_progress_tracker(workflow_id)
                progress_data = progress_tracker.get_progress_data("evaluating_pillars")
                progress_data.update({
                    "type": "pillar_evaluation_progress",
                    "survey_id": survey_id
                })
                await self.ws_client.send_progress_update(workflow_id, progress_data)
            
            # Run evaluation in background task
            evaluation_result = await self._run_evaluation_async(survey, workflow_id)
            
            # Update survey with results
            survey.pillar_scores = evaluation_result
            self.db.commit()
            
            # Send completion update
            if workflow_id:
                await self.ws_client.send_progress_update(workflow_id, {
                    "type": "pillar_evaluation_completed",
                    "survey_id": survey_id,
                    "pillar_scores": evaluation_result,
                    "message": "Pillar evaluation completed successfully"
                })
            
            logger.info(f"✅ [AsyncPillarEvaluation] Pillar evaluation completed for survey {survey_id}")
            return {
                "status": "completed",
                "pillar_scores": evaluation_result,
                "cached": False
            }
            
        except Exception as e:
            logger.error(f"❌ [AsyncPillarEvaluation] Pillar evaluation failed for survey {survey_id}: {str(e)}")
            
            # Send error update
            if workflow_id:
                await self.ws_client.send_progress_update(workflow_id, {
                    "type": "pillar_evaluation_error",
                    "survey_id": survey_id,
                    "error": str(e),
                    "message": "Pillar evaluation failed"
                })
            
            return {
                "status": "error",
                "error": str(e)
            }
        finally:
            self.active_evaluations.discard(survey_id)
    
    async def _run_evaluation_async(self, survey: Survey, workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Run the actual pillar evaluation
        """
        try:
            if ADVANCED_EVALUATORS_AVAILABLE:
                logger.info("🚀 [AsyncPillarEvaluation] Using advanced pillar evaluation system")
                
                # Send progress update
                if workflow_id:
                    progress_data = get_progress_tracker(workflow_id).get_progress_data("evaluating_pillars")
                    progress_data["survey_id"] = str(survey.id)
                    progress_data["message"] = "Running advanced pillar evaluation..."
                    await self.ws_client.send_progress_update(workflow_id, progress_data)
                
                # Use advanced evaluators
                evaluator = PillarBasedEvaluator(self.db)
                result = await evaluator.evaluate_survey(
                    survey_data=survey.final_output,
                    rfq_text=getattr(survey, 'original_rfq', survey.rfq.description if survey.rfq else ''),
                    survey_id=str(survey.id),
                    rfq_id=str(survey.rfq_id) if survey.rfq_id else None
                )
                
                return result
            else:
                logger.info("⚠️ [AsyncPillarEvaluation] Using legacy pillar scoring system")
                
                # Send progress update
                if workflow_id:
                    progress_data = get_progress_tracker(workflow_id).get_progress_data("evaluating_pillars")
                    progress_data["survey_id"] = str(survey.id)
                    progress_data["message"] = "Running legacy pillar evaluation..."
                    await self.ws_client.send_progress_update(workflow_id, progress_data)
                
                # Use legacy system
                pillar_scoring_service = PillarScoringService(self.db)
                pillar_scores = pillar_scoring_service.evaluate_survey_pillars(survey.final_output)
                
                # Convert to dict format
                return {
                    "overall_grade": pillar_scores.overall_grade,
                    "weighted_score": pillar_scores.weighted_score,
                    "total_score": pillar_scores.total_score,
                    "summary": pillar_scores.summary,
                    "pillar_breakdown": [
                        {
                            "pillar_name": score.pillar_name,
                            "display_name": score.pillar_name.replace('_', ' ').title().replace('Comprehensibility', '& Comprehensibility'),
                            "score": score.score,
                            "weighted_score": score.weighted_score,
                            "weight": score.weight,
                            "criteria_met": score.criteria_met,
                            "total_criteria": score.total_criteria,
                            "grade": pillar_scoring_service._calculate_grade(score.score)
                        }
                        for score in pillar_scores.pillar_scores
                    ],
                    "recommendations": list(set([
                        rec for score in pillar_scores.pillar_scores 
                        for rec in score.recommendations
                    ]))
                }
                
        except Exception as e:
            logger.error(f"❌ [AsyncPillarEvaluation] Evaluation failed: {str(e)}")
            raise
    
    def is_evaluation_in_progress(self, survey_id: str) -> bool:
        """Check if an evaluation is currently in progress for a survey"""
        return survey_id in self.active_evaluations

