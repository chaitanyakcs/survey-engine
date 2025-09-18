from sqlalchemy.orm import Session
from src.database import RFQ, Survey
from src.workflows.state import SurveyGenerationState
from src.workflows.workflow import create_workflow
from src.services.embedding_service import EmbeddingService
from src.services.websocket_client import WebSocketNotificationService
from src.config import settings
from typing import Optional
from uuid import uuid4
from pydantic import BaseModel
import logging
import asyncio
import time
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Simple circuit breaker to prevent cascading failures"""
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half-open

    def call(self, func, *args, **kwargs):
        if self.state == 'open':
            if time.time() - self.last_failure_time > self.timeout:
                self.state = 'half-open'
            else:
                raise Exception("Circuit breaker is open")

        try:
            result = func(*args, **kwargs)
            if self.state == 'half-open':
                self.state = 'closed'
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = 'open'
            raise


class WorkflowResult(BaseModel):
    survey_id: str
    estimated_completion_time: int
    golden_examples_used: int
    status: str


class WorkflowService:
    def __init__(self, db: Session, connection_manager=None):
        logger.info("🔧 [WorkflowService] Initializing workflow service")
        try:
            self.db = db
            logger.info("🔧 [WorkflowService] Database session assigned successfully")

            # Initialize circuit breaker for workflow execution
            self.circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=30)
            logger.info("🔧 [WorkflowService] Circuit breaker initialized")

            # Track active workflows to prevent resource exhaustion
            self.active_workflows = set()
            self.max_concurrent_workflows = 10

            logger.info("🔧 [WorkflowService] Creating embedding service")
            self.embedding_service = EmbeddingService()
            logger.info("✅ [WorkflowService] EmbeddingService created successfully")

            logger.info("🔧 [WorkflowService] Creating WebSocket notification service")
            self.ws_client = WebSocketNotificationService(connection_manager)
            logger.info("✅ [WorkflowService] WebSocketNotificationService created successfully")

            logger.info("🔧 [WorkflowService] Creating LangGraph workflow")
            try:
                self.workflow = create_workflow(db, connection_manager)
                logger.info("✅ [WorkflowService] LangGraph workflow created successfully")
            except Exception as workflow_error:
                logger.error(f"❌ [WorkflowService] Failed to create workflow: {str(workflow_error)}", exc_info=True)
                raise Exception(f"Workflow creation failed: {str(workflow_error)}")

            logger.info("✅ [WorkflowService] Workflow service initialized successfully")
        except Exception as e:
            logger.error(f"❌ [WorkflowService] Failed to initialize workflow service: {str(e)}", exc_info=True)
    
    def _ensure_healthy_db_session(self):
        """Ensure we have a healthy database session after any transaction errors"""
        try:
            # Test the current session with a simple query
            from sqlalchemy import text
            self.db.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.warning(f"⚠️ [WorkflowService] Current DB session is unhealthy: {str(e)}")
            try:
                # Rollback the current session to clear any failed transaction
                self.db.rollback()
                logger.info("🔄 [WorkflowService] Rolled back failed transaction")
                
                # Test if the session is now healthy
                self.db.execute(text("SELECT 1"))
                logger.info("✅ [WorkflowService] Session recovered after rollback")
                return True
            except Exception as rollback_error:
                logger.warning(f"⚠️ [WorkflowService] Rollback failed: {str(rollback_error)}")
                try:
                    # Create a completely new session
                    from src.database import get_db
                    self.db = next(get_db())
                    logger.info("✅ [WorkflowService] Created new healthy DB session")
                    return True
                except Exception as new_session_error:
                    logger.error(f"❌ [WorkflowService] Failed to create new DB session: {str(new_session_error)}")
                    return False
    
    @asynccontextmanager
    async def _workflow_isolation(self, workflow_id: str):
        """Context manager for isolated workflow execution with resource limits"""
        # Check if we're at max capacity
        if len(self.active_workflows) >= self.max_concurrent_workflows:
            raise Exception(f"Maximum concurrent workflows ({self.max_concurrent_workflows}) reached")

        # Add to active workflows
        self.active_workflows.add(workflow_id)
        logger.info(f"🔄 [WorkflowService] Workflow {workflow_id} started. Active: {len(self.active_workflows)}")

        try:
            yield
        finally:
            # Always remove from active workflows
            self.active_workflows.discard(workflow_id)
            logger.info(f"🔄 [WorkflowService] Workflow {workflow_id} finished. Active: {len(self.active_workflows)}")

    async def process_rfq(
        self,
        title: Optional[str],
        description: str,
        product_category: Optional[str],
        target_segment: Optional[str],
        research_goal: Optional[str],
        workflow_id: Optional[str] = None,
        survey_id: Optional[str] = None
    ) -> WorkflowResult:
        """
        Process RFQ through the complete LangGraph workflow with robust isolation
        """
        if not workflow_id:
            workflow_id = f"workflow-{uuid4()}"

        logger.info(f"📝 [WorkflowService] Starting RFQ processing: title='{title}', description_length={len(description)}")

        # Use workflow isolation with timeout
        async with self._workflow_isolation(workflow_id):
            try:
                # Set overall timeout for workflow processing
                return await asyncio.wait_for(
                    self._execute_workflow_with_circuit_breaker(
                        title, description, product_category, target_segment,
                        research_goal, workflow_id, survey_id
                    ),
                    timeout=600.0  # 10 minute timeout
                )
            except asyncio.TimeoutError:
                logger.error(f"❌ [WorkflowService] Workflow {workflow_id} timed out after 10 minutes")
                # Send failure notification
                try:
                    await self.ws_client.send_progress_update(workflow_id, {
                        "type": "error",
                        "message": "Workflow timed out after 10 minutes",
                        "error": "timeout"
                    })
                except Exception:
                    pass
                raise Exception("Workflow execution timed out")
            except Exception as e:
                logger.error(f"❌ [WorkflowService] Workflow {workflow_id} failed: {str(e)}")
                # Send failure notification
                try:
                    await self.ws_client.send_progress_update(workflow_id, {
                        "type": "error",
                        "message": f"Workflow failed: {str(e)}",
                        "error": "execution_failed"
                    })
                except Exception:
                    pass
                raise

    async def _execute_workflow_with_circuit_breaker(
        self,
        title: Optional[str],
        description: str,
        product_category: Optional[str],
        target_segment: Optional[str],
        research_goal: Optional[str],
        workflow_id: str,
        survey_id: Optional[str]
    ) -> WorkflowResult:
        """Execute workflow with circuit breaker protection"""

        # Get existing survey record (created by RFQ API)
        if not survey_id:
            raise Exception("Survey ID is required for workflow processing")

        logger.info(f"🔍 [WorkflowService] Looking up existing survey: {survey_id}")
        try:
            survey = self.db.query(Survey).filter(Survey.id == survey_id).first()
            if not survey:
                raise Exception(f"Survey not found with ID: {survey_id}")

            # Get the associated RFQ
            rfq = self.db.query(RFQ).filter(RFQ.id == survey.rfq_id).first()
            if not rfq:
                raise Exception(f"RFQ not found for survey: {survey_id}")
                
            logger.info(f"✅ [WorkflowService] Found existing survey: {survey.id} and RFQ: {rfq.id}")
        except Exception as e:
            logger.error(f"❌ [WorkflowService] Failed to find existing survey: {str(e)}", exc_info=True)
            raise Exception(f"Database error while finding survey: {str(e)}")
        
        # Initialize workflow state
        logger.info("🔄 [WorkflowService] Initializing workflow state")
        # Use provided workflow_id or generate one if not provided
        if workflow_id is None:
            workflow_id = f"survey-gen-{survey.id}"
            logger.info(f"📋 [WorkflowService] Generated workflow_id: {workflow_id}")
        else:
            logger.info(f"📋 [WorkflowService] Using provided workflow_id: {workflow_id}")
            
        initial_state = SurveyGenerationState(
            rfq_id=rfq.id,  # type: ignore
            rfq_text=description,
            rfq_title=title,
            product_category=product_category,
            target_segment=target_segment,
            research_goal=research_goal,
            workflow_id=workflow_id,
            survey_id=str(survey.id)
        )
        logger.info(f"📋 [WorkflowService] Workflow state initialized: workflow_id={initial_state.workflow_id}, survey_id={initial_state.survey_id}")
        
        try:
            # Check if workflow is properly initialized
            if not hasattr(self, 'workflow') or self.workflow is None:
                raise Exception("Workflow not properly initialized - missing workflow attribute")
            
            # Send initial progress update
            logger.info("📡 [WorkflowService] Sending initial progress update via WebSocket")
            try:
                await self.ws_client.send_progress_update(initial_state.workflow_id, {
                    "type": "progress",
                    "step": "initializing_workflow",
                    "percent": 5,
                    "message": "Starting survey generation workflow..."
                })
                logger.info("✅ [WorkflowService] Initial progress update sent successfully")
            except Exception as ws_error:
                logger.warning(f"⚠️ [WorkflowService] Failed to send WebSocket progress update: {str(ws_error)} - continuing anyway")
                # Don't fail the whole workflow for WebSocket issues
            
            # Execute workflow
            logger.info("🚀 [WorkflowService] Starting LangGraph workflow execution")
            final_state = await self.workflow.ainvoke(initial_state)
            logger.info(f"✅ [WorkflowService] Workflow execution completed. Final state keys: {list(final_state.keys()) if isinstance(final_state, dict) else 'not dict'}")
            
            # Send completion progress update
            await self.ws_client.send_progress_update(initial_state.workflow_id, {
                "type": "progress", 
                "step": "finalizing",
                "percent": 95,
                "message": "Processing results and finalizing survey..."
            })
            
            # Update survey with results (final_state is a dict from LangGraph)
            logger.info("💾 [WorkflowService] Updating survey record with workflow results")
            logger.info(f"💾 [WorkflowService] Final state keys: {list(final_state.keys()) if final_state else 'None'}")
            logger.info(f"💾 [WorkflowService] Pillar scores in final_state: {final_state.get('pillar_scores') is not None}")
            
            try:
                # Ensure we have a healthy database session
                if not self._ensure_healthy_db_session():
                    raise Exception("Failed to establish healthy database session")
                
                # Refresh the survey object to ensure we have the latest data
                self.db.refresh(survey)
                
                survey.raw_output = final_state.get("raw_survey")
                survey.final_output = final_state.get("generated_survey")
                survey.golden_similarity_score = final_state.get("golden_similarity_score")
                survey.used_golden_examples = final_state.get("used_golden_examples", [])
                
                # Store pillar scores with detailed logging
                pillar_scores = final_state.get("pillar_scores")
                logger.info(f"💾 [WorkflowService] Pillar scores to store: {pillar_scores is not None}")
                if pillar_scores:
                    logger.info(f"💾 [WorkflowService] Pillar scores type: {type(pillar_scores)}")
                    logger.info(f"💾 [WorkflowService] Pillar scores keys: {list(pillar_scores.keys()) if isinstance(pillar_scores, dict) else 'Not a dict'}")
                    logger.info(f"💾 [WorkflowService] Overall grade: {pillar_scores.get('overall_grade', 'N/A')}")
                
                survey.pillar_scores = pillar_scores
                survey.status = "validated" if final_state.get("quality_gate_passed", False) else "draft"
                
                self.db.commit()
                logger.info(f"✅ [WorkflowService] Survey record updated: status={survey.status}, golden_examples_used={len(survey.used_golden_examples)}")
                logger.info(f"✅ [WorkflowService] Pillar scores stored: {survey.pillar_scores is not None}")
            except Exception as db_error:
                logger.error(f"❌ [WorkflowService] Database update failed: {str(db_error)}")
                self.db.rollback()
                # Try to create a new session and retry
                try:
                    from src.database import get_db
                    new_db = next(get_db())
                    survey = new_db.query(Survey).filter(Survey.id == survey.id).first()
                    if survey:
                        survey.raw_output = final_state.get("raw_survey")
                        survey.final_output = final_state.get("generated_survey")
                        survey.golden_similarity_score = final_state.get("golden_similarity_score")
                        survey.used_golden_examples = final_state.get("used_golden_examples", [])
                        survey.status = "validated" if final_state.get("quality_gate_passed", False) else "draft"
                        new_db.commit()
                        logger.info(f"✅ [WorkflowService] Survey record updated with new session: status={survey.status}")
                        # Update self.db to use the new session for subsequent operations
                        self.db = new_db
                    else:
                        new_db.close()
                        raise Exception("Survey not found in new session")
                except Exception as retry_error:
                    logger.error(f"❌ [WorkflowService] Retry also failed: {str(retry_error)}")
                    raise Exception(f"Database update failed: {str(db_error)}")
            
            result = WorkflowResult(
                survey_id=str(survey.id),
                estimated_completion_time=30,  # TODO: Calculate based on complexity
                golden_examples_used=len(final_state.get("used_golden_examples", [])),
                status=survey.status
            )
            
            # Check if workflow is paused for human review
            is_paused_for_review = final_state.get("pending_human_review", False) or final_state.get("workflow_paused", False)
            
            if is_paused_for_review:
                logger.info(f"⏸️ [WorkflowService] Workflow paused for human review - not sending completion message")
                logger.info(f"📊 [WorkflowService] Pending human review: {final_state.get('pending_human_review', False)}")
                logger.info(f"📊 [WorkflowService] Workflow paused: {final_state.get('workflow_paused', False)}")
            else:
                # Send 100% completion progress update
                await self.ws_client.send_progress_update(initial_state.workflow_id, {
                    "type": "progress",
                    "step": "completed",
                    "percent": 100,
                    "message": "Survey generation completed successfully!"
                })
                
                # Send completion notification
                await self.ws_client.notify_workflow_completion(
                    initial_state.workflow_id,
                    str(survey.id),
                    survey.status
                )
            
            logger.info(f"🎉 [WorkflowService] Workflow processing completed successfully: {result.model_dump()}")
            return result
            
        except Exception as e:
            # Update survey with error
            logger.error(f"❌ [WorkflowService] Workflow execution failed: {str(e)}", exc_info=True)
            survey.status = "failed"  # type: ignore
            self.db.commit()
            
            # Send error notification
            await self.ws_client.notify_workflow_error(initial_state.workflow_id, str(e))
            
            raise Exception(f"Workflow execution failed: {str(e)}")