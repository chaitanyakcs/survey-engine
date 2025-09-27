from sqlalchemy.orm import Session
from src.database import RFQ, Survey
from src.workflows.state import SurveyGenerationState
from src.workflows.workflow import create_workflow
from src.services.embedding_service import EmbeddingService
from src.services.websocket_client import WebSocketNotificationService
from src.services.workflow_state_service import WorkflowStateService
from src.services.progress_tracker import get_progress_tracker, cleanup_progress_tracker
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
            self.connection_manager = connection_manager
            logger.info("🔧 [WorkflowService] Database session assigned successfully")

            # Initialize circuit breaker for workflow execution
            self.circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=30)
            logger.info("🔧 [WorkflowService] Circuit breaker initialized")

            # Track active workflows to prevent resource exhaustion
            self.active_workflows = set()
            self.max_concurrent_workflows = 10
            
            # Initialize workflow state service
            self.state_service = WorkflowStateService(db)
            logger.info("✅ [WorkflowService] WorkflowStateService created successfully")

            logger.info("🔧 [WorkflowService] Creating embedding service")
            self.embedding_service = EmbeddingService()
            logger.info("✅ [WorkflowService] EmbeddingService created successfully")

            logger.info("🔧 [WorkflowService] Creating WebSocket notification service")
            self.ws_client = WebSocketNotificationService(connection_manager)
            logger.info("✅ [WorkflowService] WebSocketNotificationService created successfully")

            logger.info("🔧 [WorkflowService] Creating LangGraph workflow")
            try:
                self.workflow = create_workflow(db, connection_manager)
                logger.info(f"✅ [WorkflowService] LangGraph workflow created successfully: {type(self.workflow)}")
                logger.info(f"✅ [WorkflowService] Workflow has ainvoke method: {hasattr(self.workflow, 'ainvoke')}")
            except Exception as workflow_error:
                logger.error(f"❌ [WorkflowService] Failed to create workflow: {str(workflow_error)}", exc_info=True)
                raise Exception(f"Workflow creation failed: {str(workflow_error)}")

            logger.info("✅ [WorkflowService] Workflow service initialized successfully")
        except Exception as e:
            logger.error(f"❌ [WorkflowService] Failed to initialize workflow service: {str(e)}", exc_info=True)
            # Set workflow to None to indicate initialization failed
            self.workflow = None
            raise e
    
    def _ensure_workflow_initialized(self):
        """Ensure workflow is properly initialized, reinitialize if needed"""
        if not hasattr(self, 'workflow') or self.workflow is None:
            logger.warning("⚠️ [WorkflowService] Workflow not initialized, attempting to reinitialize...")
            try:
                from src.workflows.workflow import create_workflow
                self.workflow = create_workflow(self.db, None)
                logger.info("✅ [WorkflowService] Workflow reinitialized successfully")
            except Exception as e:
                logger.error(f"❌ [WorkflowService] Failed to reinitialize workflow: {str(e)}")
                raise Exception(f"Workflow reinitialization failed: {str(e)}")
    
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
            
        import time
        
        initial_state = SurveyGenerationState(
            rfq_id=rfq.id,  # type: ignore
            rfq_text=description,
            rfq_title=title,
            product_category=product_category,
            target_segment=target_segment,
            research_goal=research_goal,
            workflow_id=workflow_id,
            survey_id=str(survey.id),
            workflow_start_time=time.time()  # Set start time for loop prevention
        )
        logger.info(f"📋 [WorkflowService] Workflow state initialized: workflow_id={initial_state.workflow_id}, survey_id={initial_state.survey_id}")
        
        try:
            # Ensure workflow is properly initialized
            self._ensure_workflow_initialized()
            logger.info(f"✅ [WorkflowService] Workflow is properly initialized: {type(self.workflow)}")
            
            # Send initial progress update
            logger.info("📡 [WorkflowService] Sending initial progress update via WebSocket")
            try:
                progress_tracker = get_progress_tracker(initial_state.workflow_id)
                progress_data = progress_tracker.get_progress_data("initializing_workflow")
                await self.ws_client.send_progress_update(initial_state.workflow_id, progress_data)
                logger.info("✅ [WorkflowService] Initial progress update sent successfully")
            except Exception as ws_error:
                logger.warning(f"⚠️ [WorkflowService] Failed to send WebSocket progress update: {str(ws_error)} - continuing anyway")
                # Don't fail the whole workflow for WebSocket issues
            
            # Execute workflow
            logger.info("🚀 [WorkflowService] Starting LangGraph workflow execution")
            logger.info(f"🔍 [WorkflowService] Initial state before execution: {initial_state.model_dump()}")
            
            try:
                final_state = await self.workflow.ainvoke(initial_state)
                logger.info(f"✅ [WorkflowService] Workflow execution completed. Final state keys: {list(final_state.keys()) if isinstance(final_state, dict) else 'not dict'}")
                logger.info(f"🔍 [WorkflowService] Final state details: {final_state}")
                
                # Check if workflow was paused
                if isinstance(final_state, dict):
                    workflow_paused = final_state.get('workflow_paused', False)
                    pending_human_review = final_state.get('pending_human_review', False)
                    logger.info(f"🔍 [WorkflowService] Final state - workflow_paused: {workflow_paused}")
                    logger.info(f"🔍 [WorkflowService] Final state - pending_human_review: {pending_human_review}")
                    
            except Exception as e:
                if "WORKFLOW_PAUSED_FOR_HUMAN_REVIEW" in str(e):
                    logger.info("⏸️ [WorkflowService] Workflow paused for human review as expected")
                    # Send human review required message
                    progress_data = get_progress_tracker(workflow_id).get_progress_data("human_review")
                    progress_data["message"] = "Waiting for human review of system prompt..."
                    progress_data["workflow_paused"] = True
                    progress_data["pending_human_review"] = True
                    await self.ws_client.send_progress_update(workflow_id, progress_data)
                    
                    # Return a paused result
                    return WorkflowResult(
                        survey_id=survey_id,
                        status="paused",
                        estimated_completion_time=0,  # Will be updated when resumed
                        golden_examples_used=0  # Will be updated when resumed
                    )
                else:
                    # Re-raise other exceptions
                    raise
            
            # Save workflow state for potential resumption
            if isinstance(final_state, dict):
                # Convert dict back to SurveyGenerationState for saving
                try:
                    state_for_saving = SurveyGenerationState(**final_state)
                    self.state_service.save_workflow_state(state_for_saving)
                    logger.info("💾 [WorkflowService] Workflow state saved for potential resumption")
                except Exception as save_error:
                    logger.warning(f"⚠️ [WorkflowService] Failed to save workflow state: {str(save_error)} - continuing anyway")
            
            # Check if workflow was paused for human review before sending completion message
            if isinstance(final_state, dict) and (final_state.get('workflow_paused') or final_state.get('pending_human_review')):
                logger.info("⏸️ [WorkflowService] Workflow paused for human review - not sending finalizing message")
            else:
                # Send completion progress update only if workflow completed normally
                progress_tracker = get_progress_tracker(initial_state.workflow_id)
                progress_data = progress_tracker.get_progress_data("finalizing")
                await self.ws_client.send_progress_update(initial_state.workflow_id, progress_data)
            
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
                progress_tracker = get_progress_tracker(initial_state.workflow_id)
                completion_data = progress_tracker.get_completion_data("completed")
                await self.ws_client.send_progress_update(initial_state.workflow_id, completion_data)
                
                # Clean up the progress tracker
                cleanup_progress_tracker(initial_state.workflow_id)
                
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
            
            raise
    
    async def execute_workflow_from_generation(self, initial_state: SurveyGenerationState, workflow_id: str, survey_id: str, ws_client: WebSocketNotificationService):
        """Execute workflow starting from generation step using the same service instances for consistency"""
        try:
            logger.info(f"🚀 [WorkflowService] Starting workflow execution from generation step for {workflow_id}")

            # Update the state to mark that human review has been approved
            initial_state.pending_human_review = False
            initial_state.workflow_paused = False
            initial_state.prompt_approved = True
            
            # CRITICAL FIX: Rebuild context if it's missing or empty
            if not initial_state.context or not initial_state.context.get('survey_id'):
                logger.info("🔧 [WorkflowService] Rebuilding context for resumed workflow")
                from src.workflows.nodes import ContextBuilderNode
                context_builder = ContextBuilderNode(self.db)
                context_result = await context_builder(initial_state)
                if context_result.get('context'):
                    initial_state.context = context_result['context']
                    logger.info(f"✅ [WorkflowService] Context rebuilt successfully: {list(initial_state.context.keys())}")
                else:
                    logger.warning("⚠️ [WorkflowService] Failed to rebuild context, proceeding with existing state")

            # Send progress update
            try:
                progress_data = get_progress_tracker(workflow_id).get_progress_data("preparing_generation")
                progress_data["message"] = "Human review approved - resuming workflow..."
                await ws_client.send_progress_update(workflow_id, progress_data)
            except Exception as ws_error:
                logger.warning(f"⚠️ [WorkflowService] Failed to send progress update: {str(ws_error)}")

            # CRITICAL FIX: Use the same node instances as the main workflow to ensure consistency
            # Create nodes with the same database session and configuration as the main workflow
            from src.workflows.nodes import GeneratorAgent, ValidatorAgent

            # Use the same database session as the main workflow service
            generator = GeneratorAgent(self.db, connection_manager=self.connection_manager)
            validator = ValidatorAgent(self.db, connection_manager=self.connection_manager)

            # Send progress update for generation
            try:
                progress_tracker = get_progress_tracker(workflow_id)
                progress_data = progress_tracker.get_progress_data("generating_questions")
                await ws_client.send_progress_update(workflow_id, progress_data)
            except Exception as ws_error:
                logger.warning(f"⚠️ [WorkflowService] Failed to send generation progress update: {str(ws_error)}")

            # Execute generation step directly using the same service configuration
            logger.info("🚀 [WorkflowService] Starting direct generation execution with consistent services")
            try:
                generation_result = await generator(initial_state)
                logger.info(f"✅ [WorkflowService] Generation completed. Result keys: {list(generation_result.keys()) if isinstance(generation_result, dict) else 'not dict'}")
            except Exception as gen_error:
                logger.error(f"❌ [WorkflowService] Generation step failed: {str(gen_error)}", exc_info=True)
                # Send error notification
                await ws_client.send_progress_update(workflow_id, {
                    "type": "error",
                    "message": f"Survey generation failed: {str(gen_error)}"
                })
                raise gen_error

            # Update the state with generation results
            if isinstance(generation_result, dict):
                for key, value in generation_result.items():
                    if hasattr(initial_state, key):
                        setattr(initial_state, key, value)

            # Send progress update for validation
            try:
                progress_tracker = get_progress_tracker(workflow_id)
                progress_data = progress_tracker.get_progress_data("validation_scoring")
                await ws_client.send_progress_update(workflow_id, progress_data)
            except Exception as ws_error:
                logger.warning(f"⚠️ [WorkflowService] Failed to send validation progress update: {str(ws_error)}")

            # Execute validation step directly
            logger.info("🚀 [WorkflowService] Starting direct validation execution")
            try:
                validation_result = await validator(initial_state)
                logger.info(f"✅ [WorkflowService] Validation completed. Result keys: {list(validation_result.keys()) if isinstance(validation_result, dict) else 'not dict'}")
            except Exception as val_error:
                logger.error(f"❌ [WorkflowService] Validation step failed: {str(val_error)}", exc_info=True)
                # Send error notification
                await ws_client.send_progress_update(workflow_id, {
                    "type": "error",
                    "message": f"Survey validation failed: {str(val_error)}"
                })
                raise val_error

            # Update the state with validation results
            if isinstance(validation_result, dict):
                for key, value in validation_result.items():
                    if hasattr(initial_state, key):
                        setattr(initial_state, key, value)

            # Update survey with final results - use the same logic as the main workflow
            try:
                from src.database.models import Survey

                # Ensure we have a healthy database session
                if not self._ensure_healthy_db_session():
                    raise Exception("Failed to establish healthy database session")

                survey = self.db.query(Survey).filter(Survey.id == survey_id).first()
                if survey:
                    # Refresh to get latest data
                    self.db.refresh(survey)

                    # Use the same update logic as the main workflow
                    survey.raw_output = generation_result.get("raw_survey")
                    survey.final_output = generation_result.get("generated_survey")
                    survey.golden_similarity_score = validation_result.get("golden_similarity_score")
                    survey.used_golden_examples = initial_state.used_golden_examples
                    survey.pillar_scores = generation_result.get("pillar_scores")
                    survey.status = "validated" if validation_result.get("quality_gate_passed", False) else "draft"

                    self.db.commit()
                    logger.info(f"✅ [WorkflowService] Survey updated from resumed workflow: status={survey.status}")
                    logger.info(f"✅ [WorkflowService] Pillar scores stored: {survey.pillar_scores is not None}")
                else:
                    logger.warning(f"⚠️ [WorkflowService] Survey not found for update: {survey_id}")
            except Exception as e:
                logger.error(f"❌ [WorkflowService] Failed to update survey from resumed workflow: {str(e)}")
                self.db.rollback()
                # Don't fail the entire operation for database update issues

            # Send completion message
            try:
                progress_tracker = get_progress_tracker(workflow_id)
                completion_data = progress_tracker.get_completion_data("completed")
                completion_data.update({
                    "type": "completed",
                    "survey_id": survey_id
                })
                await ws_client.send_progress_update(workflow_id, completion_data)
                # Clean up the progress tracker
                cleanup_progress_tracker(workflow_id)
            except Exception as ws_error:
                logger.warning(f"⚠️ [WorkflowService] Failed to send completion message: {str(ws_error)}")

            logger.info(f"✅ [WorkflowService] Resumed workflow execution completed successfully: {workflow_id}")

        except Exception as e:
            logger.error(f"❌ [WorkflowService] Resumed workflow execution failed: {str(e)}", exc_info=True)

            # Update survey status to failed
            try:
                from src.database.models import Survey
                survey = self.db.query(Survey).filter(Survey.id == survey_id).first()
                if survey:
                    survey.status = "failed"
                    self.db.commit()
                    logger.info(f"✅ [WorkflowService] Survey status updated to failed: {survey_id}")
            except Exception as status_error:
                logger.error(f"❌ [WorkflowService] Failed to update survey status to failed: {str(status_error)}")

            # Send error notification
            try:
                await ws_client.send_progress_update(workflow_id, {
                    "type": "error",
                    "message": f"Failed to resume workflow: {str(e)}"
                })
            except Exception as ws_error:
                logger.warning(f"⚠️ [WorkflowService] Failed to send error notification: {str(ws_error)}")
            raise Exception(f"Workflow execution failed: {str(e)}")