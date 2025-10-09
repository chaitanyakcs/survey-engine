"""
Dedicated Survey Evaluation Service

Handles all quality assessment and pillar scoring for generated surveys.
Separated from GenerationService for clean architecture and proper progress tracking.
"""

import logging
import uuid
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from src.config import settings
from src.services.pillar_scoring_service import PillarScoringService
from src.utils.llm_audit_decorator import LLMAuditContext
from src.services.llm_audit_service import LLMAuditService

logger = logging.getLogger(__name__)

class EvaluatorService:
    """
    Dedicated service for survey quality evaluation and pillar scoring.
    Provides multiple evaluation strategies with proper progress tracking.
    """

    def __init__(self, db_session: Optional[Session] = None, workflow_id: Optional[str] = None, connection_manager=None):
        self.db_session = db_session
        self.workflow_id = workflow_id
        self.connection_manager = connection_manager

        # Initialize WebSocket client for progress updates
        if connection_manager and workflow_id:
            from src.services.websocket_client import WebSocketNotificationService
            self.ws_client = WebSocketNotificationService(connection_manager)
        else:
            self.ws_client = None

        # Initialize pillar scoring service
        self.pillar_scoring_service = PillarScoringService(db_session=db_session)

        # Initialize advanced evaluator if available
        self.advanced_evaluator = None
        try:
            import sys
            import os
            current_dir = os.path.dirname(__file__)
            project_root = current_dir
            while project_root != '/' and project_root != '':
                eval_path = os.path.join(project_root, 'evaluations')
                if os.path.exists(eval_path):
                    break
                project_root = os.path.dirname(project_root)

            if os.path.exists(eval_path):
                sys.path.insert(0, eval_path)
                from modules.pillar_based_evaluator import PillarBasedEvaluator
                from llm_client import create_evaluation_llm_client

                llm_client = create_evaluation_llm_client(db_session=db_session)
                self.advanced_evaluator = PillarBasedEvaluator(llm_client=llm_client, db_session=db_session)
                logger.info("✅ [EvaluatorService] Advanced evaluator initialized")
        except Exception as e:
            logger.warning(f"⚠️ [EvaluatorService] Advanced evaluator not available: {e}")

    async def evaluate_survey(self, survey_data: Dict[str, Any], rfq_text: str) -> Dict[str, Any]:
        """
        Main evaluation method with comprehensive fallback chain and progress tracking.

        Args:
            survey_data: Generated survey JSON
            rfq_text: Original RFQ text for context

        Returns:
            Dictionary with evaluation results in consistent format
        """
        logger.info("🏛️ [EvaluatorService] Starting comprehensive survey evaluation...")

        # Get evaluation lock to prevent duplicate evaluations
        evaluation_lock = None
        if hasattr(self, 'survey_id') and self.survey_id:
            try:
                from src.api.pillar_scores import _get_evaluation_lock, _cleanup_evaluation_lock
                evaluation_lock = _get_evaluation_lock(self.survey_id)
                
                # Try to acquire lock with timeout
                if not evaluation_lock.acquire(blocking=True, timeout=30):
                    logger.warning(f"⚠️ [EvaluatorService] Could not acquire evaluation lock for survey {self.survey_id}, evaluation may already be in progress")
                    # Continue without lock - the API endpoint will handle the race condition
                else:
                    logger.info(f"🔓 [EvaluatorService] Acquired evaluation lock for survey {self.survey_id}")
            except Exception as e:
                logger.warning(f"⚠️ [EvaluatorService] Could not get evaluation lock: {e}")

        # Send initial progress update using ProgressTracker
        if self.workflow_id:
            from src.services.progress_tracker import get_progress_tracker
            progress_tracker = get_progress_tracker(self.workflow_id)
            progress_data = progress_tracker.get_progress_data("validation_scoring")
            progress_data["message"] = "Starting comprehensive quality evaluation..."
            await self._send_progress_update_with_data(progress_data)

        try:
            # Try evaluation methods in order of preference
            result = await self._try_evaluation_chain(survey_data, rfq_text)

            # Send completion progress using ProgressTracker
            if self.workflow_id:
                from src.services.progress_tracker import get_progress_tracker
                progress_tracker = get_progress_tracker(self.workflow_id)
                progress_data = progress_tracker.get_progress_data("validation_scoring")
                progress_data["message"] = "Quality evaluation completed successfully!"
                await self._send_progress_update_with_data(progress_data)

            logger.info(f"✅ [EvaluatorService] Evaluation completed: {result.get('overall_grade', 'N/A')} ({result.get('weighted_score', 0):.1%})")
            return result

        except Exception as e:
            logger.error(f"❌ [EvaluatorService] Evaluation failed: {str(e)}")
            if self.workflow_id:
                from src.services.progress_tracker import get_progress_tracker
                progress_tracker = get_progress_tracker(self.workflow_id)
                progress_data = progress_tracker.get_progress_data("validation_scoring")
                progress_data["message"] = "Evaluation encountered issues, survey will be generated without quality scores..."
                await self._send_progress_update_with_data(progress_data)

            # Return empty scores with evaluation failure message
            return {
                "overall_grade": "N/A",
                "weighted_score": 0.0,
                "total_score": 0.0,
                "pillar_breakdown": [],
                "evaluation_failed": True,
                "evaluation_error": str(e),
                "message": "Quality evaluation could not be completed. Survey generated successfully but without quality scores."
            }
        
        finally:
            # Release evaluation lock if we acquired it
            if evaluation_lock and evaluation_lock.locked():
                try:
                    from src.api.pillar_scores import _cleanup_evaluation_lock
                    evaluation_lock.release()
                    if hasattr(self, 'survey_id') and self.survey_id:
                        _cleanup_evaluation_lock(self.survey_id)
                    logger.info(f"🔓 [EvaluatorService] Released evaluation lock for survey {getattr(self, 'survey_id', 'unknown')}")
                except Exception as e:
                    logger.warning(f"⚠️ [EvaluatorService] Error releasing evaluation lock: {e}")

    async def _try_evaluation_chain(self, survey_data: Dict[str, Any], rfq_text: str) -> Dict[str, Any]:
        """Try evaluation methods in order: single-call → legacy → basic (no multi-call)."""

        # Force single-call mode regardless of DB settings to avoid multiple LLM calls
        evaluation_mode = "single_call"

        # Try 1: Single-call evaluation (cost efficient)
        if evaluation_mode == "single_call":
            try:
                if self.workflow_id:
                    from src.services.progress_tracker import get_progress_tracker
                    progress_tracker = get_progress_tracker(self.workflow_id)
                    progress_data = progress_tracker.get_progress_data("evaluating_pillars", "single_call_evaluator")
                    progress_data["message"] = "Running AI-powered comprehensive quality assessment"
                    await self._send_progress_update_with_data(progress_data)
                result = await self._evaluate_with_single_call(survey_data, rfq_text)
                if result:
                    # Send pillar scores analysis progress
                    if self.workflow_id:
                        from src.services.progress_tracker import get_progress_tracker
                        progress_tracker = get_progress_tracker(self.workflow_id)
                        progress_data = progress_tracker.get_progress_data("evaluating_pillars", "pillar_scores_analysis")
                        progress_data["message"] = "Analyzing pillar scores and methodological rigor"
                        await self._send_progress_update_with_data(progress_data)
                    return result
            except Exception as e:
                logger.warning(f"⚠️ [EvaluatorService] Single-call evaluation failed: {e}")
                # Send advanced evaluation progress for fallback
                if self.workflow_id:
                    from src.services.progress_tracker import get_progress_tracker
                    progress_tracker = get_progress_tracker(self.workflow_id)
                    progress_data = progress_tracker.get_progress_data("evaluating_pillars", "advanced_evaluation")
                    progress_data["message"] = "Running advanced quality assessment"
                    await self._send_progress_update_with_data(progress_data)

        # Skip advanced multi-call and API-based evaluations to prevent 5 separate LLM calls

        # Try 2: Legacy evaluation system (local, non-LLM)
        try:
            if self.workflow_id:
                from src.services.progress_tracker import get_progress_tracker
                progress_tracker = get_progress_tracker(self.workflow_id)
                progress_data = progress_tracker.get_progress_data("evaluating_pillars", "legacy_evaluation")
                progress_data["message"] = "Using legacy evaluation methods"
                await self._send_progress_update_with_data(progress_data)
            result = await self._evaluate_with_legacy(survey_data, rfq_text)
            if result:
                return result
        except Exception as e:
            logger.warning(f"⚠️ [EvaluatorService] Legacy evaluation failed: {e}")

        # Fallback: No scores, just message
        logger.warning("🚨 [EvaluatorService] All evaluation methods failed, survey will be generated without quality scores")
        if self.workflow_id:
            from src.services.progress_tracker import get_progress_tracker
            progress_tracker = get_progress_tracker(self.workflow_id)
            progress_data = progress_tracker.get_progress_data("evaluating_pillars", "fallback_evaluation")
            progress_data["message"] = "Evaluation could not be completed, survey will be generated without quality scores"
            await self._send_progress_update_with_data(progress_data)
        
        # Return empty scores with evaluation failure message
        return {
            "overall_grade": "N/A",
            "weighted_score": 0.0,
            "total_score": 0.0,
            "pillar_breakdown": [],
            "evaluation_failed": True,
            "evaluation_error": "All evaluation methods failed",
            "message": "Quality evaluation could not be completed. Survey generated successfully but without quality scores."
        }

    async def _evaluate_with_single_call(self, survey_data: Dict[str, Any], rfq_text: str) -> Optional[Dict[str, Any]]:
        """Single-call comprehensive evaluation using SingleCallEvaluator"""
        try:
            from evaluations.modules.single_call_evaluator import SingleCallEvaluator
            from evaluations.llm_client import create_evaluation_llm_client

            llm_client = create_evaluation_llm_client(db_session=self.db_session)
            evaluator = SingleCallEvaluator(llm_client=llm_client, db_session=self.db_session)

            # Run single-call evaluation
            survey_id = getattr(self, 'survey_id', None)
            rfq_id = getattr(self, 'rfq_id', None)
            result = await evaluator.evaluate_survey(survey_data, rfq_text, survey_id=survey_id, rfq_id=rfq_id)

            # Convert to standard format
            return self._format_single_call_result(result)

        except ImportError as e:
            logger.warning(f"⚠️ [EvaluatorService] Single-call evaluator not available: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ [EvaluatorService] Single-call evaluation error: {e}")
            return None

    async def _evaluate_with_advanced_system(self, survey_data: Dict[str, Any], rfq_text: str) -> Optional[Dict[str, Any]]:
        """Advanced multi-call evaluation using PillarBasedEvaluator"""
        if not self.advanced_evaluator:
            return None

        try:
            survey_id = getattr(self, 'survey_id', None)
            rfq_id = getattr(self, 'rfq_id', None)
            result = await self.advanced_evaluator.evaluate_survey(survey_data, rfq_text, survey_id=survey_id, rfq_id=rfq_id)
            return self._format_advanced_result(result)
        except Exception as e:
            logger.error(f"❌ [EvaluatorService] Advanced evaluation error: {e}")
            return None

    async def _evaluate_with_api(self, survey_data: Dict[str, Any], rfq_text: str) -> Optional[Dict[str, Any]]:
        """Evaluation using pillar-scores API"""
        try:
            from src.api.pillar_scores import _evaluate_with_advanced_system
            # Prevent circular fallback by disabling aira_v1
            survey_id = getattr(self, 'survey_id', None)
            rfq_id = getattr(self, 'rfq_id', None)
            result = await _evaluate_with_advanced_system(survey_data, rfq_text, self.db_session, survey_id=survey_id, rfq_id=rfq_id, allow_aira_v1=False)
            return self._format_api_result(result)
        except Exception as e:
            logger.error(f"❌ [EvaluatorService] API evaluation error: {e}")
            return None

    async def _evaluate_with_legacy(self, survey_data: Dict[str, Any], rfq_text: str) -> Optional[Dict[str, Any]]:
        """Legacy evaluation using PillarScoringService"""
        try:
            result = self.pillar_scoring_service.evaluate_survey_pillars(survey_data)
            return self._format_legacy_result(result)
        except Exception as e:
            logger.error(f"❌ [EvaluatorService] Legacy evaluation error: {e}")
            return None

    def _format_single_call_result(self, result) -> Dict[str, Any]:
        """Format SingleCallEvaluationResult to standard format"""
        pillar_breakdown = []
        pillar_mapping = {
            'content_validity': 'Content Validity',
            'methodological_rigor': 'Methodological Rigor',
            'clarity_comprehensibility': 'Clarity & Comprehensibility',
            'structural_coherence': 'Structural Coherence',
            'deployment_readiness': 'Deployment Readiness'
        }

        weights = {
            'content_validity': 0.20,
            'methodological_rigor': 0.25,
            'clarity_comprehensibility': 0.25,
            'structural_coherence': 0.20,
            'deployment_readiness': 0.10
        }

        for pillar_name, display_name in pillar_mapping.items():
            score = result.pillar_scores.get(pillar_name, 0.5)
            weight = weights[pillar_name]
            weighted_score = score * weight

            # Convert score to criteria format for compatibility
            criteria_met = int(score * 10)
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

            pillar_breakdown.append({
                "pillar_name": pillar_name,
                "display_name": display_name,
                "score": score,
                "weighted_score": weighted_score,
                "weight": weight,
                "criteria_met": criteria_met,
                "total_criteria": total_criteria,
                "grade": grade
            })

        return {
            "overall_grade": result.overall_grade,
            "weighted_score": result.weighted_score,
            "total_score": result.weighted_score,
            "summary": f"Single-Call Comprehensive Analysis | Overall Score: {result.weighted_score:.1%} (Grade {result.overall_grade})",
            "pillar_breakdown": pillar_breakdown,
            "recommendations": result.overall_recommendations or []
        }

    def _format_advanced_result(self, result) -> Dict[str, Any]:
        """Format PillarBasedEvaluator result to standard format"""
        pillar_breakdown = []
        pillar_mapping = {
            'content_validity': 'Content Validity',
            'methodological_rigor': 'Methodological Rigor',
            'clarity_comprehensibility': 'Clarity & Comprehensibility',
            'structural_coherence': 'Structural Coherence',
            'deployment_readiness': 'Deployment Readiness'
        }

        weights = self.advanced_evaluator.PILLAR_WEIGHTS

        for pillar_name, display_name in pillar_mapping.items():
            score = getattr(result.pillar_scores, pillar_name)
            weight = weights[pillar_name]
            weighted_score = score * weight

            criteria_met = int(score * 10)
            total_criteria = 10

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

            pillar_breakdown.append({
                "pillar_name": pillar_name,
                "display_name": display_name,
                "score": score,
                "weighted_score": weighted_score,
                "weight": weight,
                "criteria_met": criteria_met,
                "total_criteria": total_criteria,
                "grade": grade
            })

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

        return {
            "overall_grade": overall_grade,
            "weighted_score": result.overall_score,
            "total_score": result.overall_score,
            "summary": f"Advanced Chain-of-Thought Analysis | Overall Score: {result.overall_score:.1%} (Grade {overall_grade})",
            "pillar_breakdown": pillar_breakdown,
            "recommendations": result.recommendations or []
        }

    def _format_api_result(self, result) -> Dict[str, Any]:
        """Format API result to standard format"""
        return {
            "overall_grade": result.overall_grade,
            "weighted_score": result.weighted_score,
            "total_score": result.total_score,
            "summary": result.summary,
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
                for pillar in result.pillar_breakdown
            ],
            "recommendations": result.recommendations
        }

    def _format_legacy_result(self, result) -> Dict[str, Any]:
        """Format legacy result to standard format"""
        return {
            "overall_grade": result.overall_grade,
            "weighted_score": result.weighted_score,
            "total_score": result.total_score,
            "summary": f"Legacy Evaluation - {result.summary}",
            "pillar_breakdown": [
                {
                    "pillar_name": score.pillar_name,
                    "display_name": score.pillar_name.replace('_', ' ').title().replace('Comprehensibility', '& Comprehensibility'),
                    "score": score.score,
                    "weighted_score": score.weighted_score,
                    "weight": score.weight,
                    "criteria_met": score.criteria_met,
                    "total_criteria": score.total_criteria,
                    "grade": self._calculate_pillar_grade(score.score)
                }
                for score in result.pillar_scores
            ],
            "recommendations": self._compile_recommendations(result.pillar_scores)
        }

    def _create_fallback_scores(self, survey_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create basic fallback scores when all evaluation methods fail"""
        from src.utils.survey_utils import get_questions_count

        question_count = get_questions_count(survey_data)

        # Basic heuristic scoring
        content_validity = min(0.8, question_count / 10)
        methodological_rigor = 0.7
        clarity = 0.75
        structure = 0.8
        deployment = 0.9

        weighted_score = (
            content_validity * 0.20 +
            methodological_rigor * 0.25 +
            clarity * 0.25 +
            structure * 0.20 +
            deployment * 0.10
        )

        if weighted_score >= 0.9:
            grade = "A"
        elif weighted_score >= 0.8:
            grade = "B"
        elif weighted_score >= 0.7:
            grade = "C"
        elif weighted_score >= 0.6:
            grade = "D"
        else:
            grade = "F"

        return {
            "overall_grade": grade,
            "weighted_score": weighted_score,
            "total_score": weighted_score,
            "summary": f"Basic Fallback Evaluation | {question_count} questions | Score: {weighted_score:.1%} (Grade {grade})",
            "pillar_breakdown": [
                {
                    "pillar_name": "content_validity",
                    "display_name": "Content Validity",
                    "score": content_validity,
                    "weighted_score": content_validity * 0.20,
                    "weight": 0.20,
                    "criteria_met": int(content_validity * 10),
                    "total_criteria": 10,
                    "grade": self._calculate_pillar_grade(content_validity)
                },
                {
                    "pillar_name": "methodological_rigor",
                    "display_name": "Methodological Rigor",
                    "score": methodological_rigor,
                    "weighted_score": methodological_rigor * 0.25,
                    "weight": 0.25,
                    "criteria_met": int(methodological_rigor * 10),
                    "total_criteria": 10,
                    "grade": self._calculate_pillar_grade(methodological_rigor)
                },
                {
                    "pillar_name": "clarity_comprehensibility",
                    "display_name": "Clarity & Comprehensibility",
                    "score": clarity,
                    "weighted_score": clarity * 0.25,
                    "weight": 0.25,
                    "criteria_met": int(clarity * 10),
                    "total_criteria": 10,
                    "grade": self._calculate_pillar_grade(clarity)
                },
                {
                    "pillar_name": "structural_coherence",
                    "display_name": "Structural Coherence",
                    "score": structure,
                    "weighted_score": structure * 0.20,
                    "weight": 0.20,
                    "criteria_met": int(structure * 10),
                    "total_criteria": 10,
                    "grade": self._calculate_pillar_grade(structure)
                },
                {
                    "pillar_name": "deployment_readiness",
                    "display_name": "Deployment Readiness",
                    "score": deployment,
                    "weighted_score": deployment * 0.10,
                    "weight": 0.10,
                    "criteria_met": int(deployment * 10),
                    "total_criteria": 10,
                    "grade": self._calculate_pillar_grade(deployment)
                }
            ],
            "recommendations": [
                "Basic evaluation used - advanced evaluation was unavailable",
                "Quality scoring systems were offline - manual review recommended",
                "All survey functionality remains available despite scoring limitations"
            ]
        }

    async def _send_progress_update(self, percent: int, message: str, substep: str = "validation_scoring"):
        """Send progress update via WebSocket with specific substep"""
        if self.ws_client and self.workflow_id:
            try:
                await self.ws_client.send_progress_update(self.workflow_id, {
                    "type": "progress",
                    "step": substep,
                    "percent": percent,
                    "message": message
                })
            except Exception as e:
                logger.warning(f"⚠️ [EvaluatorService] Failed to send progress update: {e}")

    async def _send_progress_update_with_data(self, progress_data: dict):
        """Send progress update using complete progress data from ProgressTracker"""
        if self.ws_client and self.workflow_id:
            try:
                await self.ws_client.send_progress_update(self.workflow_id, progress_data)
            except Exception as e:
                logger.warning(f"⚠️ [EvaluatorService] Failed to send progress update: {e}")

    def _calculate_pillar_grade(self, score: float) -> str:
        """Calculate letter grade from score"""
        if score >= 0.9:
            return "A"
        elif score >= 0.8:
            return "B"
        elif score >= 0.7:
            return "C"
        elif score >= 0.6:
            return "D"
        else:
            return "F"

    def _compile_recommendations(self, pillar_scores) -> List[str]:
        """Compile recommendations from pillar scores"""
        all_recommendations = []
        for score in pillar_scores:
            if hasattr(score, 'recommendations'):
                all_recommendations.extend(score.recommendations)

        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in all_recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)

        return unique_recommendations or ["Evaluation completed using legacy system"]