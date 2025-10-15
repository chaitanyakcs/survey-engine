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

# Import enhanced RFQ models
try:
    from src.models.enhanced_rfq import EnhancedRFQRequest
except ImportError:
    # Fallback for testing or if models not available
    EnhancedRFQRequest = None

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

    async def process_enhanced_rfq(
        self,
        enhanced_rfq: 'EnhancedRFQRequest',
        legacy_title: Optional[str],
        legacy_description: str,
        legacy_product_category: Optional[str],
        legacy_target_segment: Optional[str],
        legacy_research_goal: Optional[str],
        workflow_id: Optional[str] = None,
        survey_id: Optional[str] = None
    ) -> WorkflowResult:
        """
        Process Enhanced RFQ through the complete LangGraph workflow with enriched context
        """
        if not workflow_id:
            workflow_id = f"enhanced-workflow-{uuid4()}"

        logger.info(f"📝 [WorkflowService] Starting Enhanced RFQ processing: title='{legacy_title}', workflow_id={workflow_id}")
        logger.info(f"📊 [WorkflowService] Enhanced data available: methodology={enhanced_rfq.methodology is not None}, business_context={enhanced_rfq.business_context is not None}")

        # Use workflow isolation with timeout
        async with self._workflow_isolation(workflow_id):
            try:
                # Set overall timeout for workflow processing
                return await asyncio.wait_for(
                    self._execute_enhanced_workflow_with_circuit_breaker(
                        enhanced_rfq, legacy_title, legacy_description,
                        legacy_product_category, legacy_target_segment,
                        legacy_research_goal, workflow_id, survey_id
                    ),
                    timeout=600.0  # 10 minute timeout
                )
            except asyncio.TimeoutError:
                logger.error(f"❌ [WorkflowService] Enhanced workflow {workflow_id} timed out after 10 minutes")
                # Send failure notification
                try:
                    await self.ws_client.send_progress_update(workflow_id, {
                        "type": "error",
                        "message": "Enhanced workflow timed out after 10 minutes",
                        "error": "timeout"
                    })
                except Exception:
                    pass
                raise Exception("Enhanced workflow execution timed out")
            except Exception as e:
                logger.error(f"❌ [WorkflowService] Enhanced workflow {workflow_id} failed: {str(e)}")
                # Send failure notification
                try:
                    await self.ws_client.send_progress_update(workflow_id, {
                        "type": "error",
                        "message": f"Enhanced workflow failed: {str(e)}",
                        "error": "execution_failed"
                    })
                except Exception:
                    pass
                raise

    async def _execute_enhanced_workflow_with_circuit_breaker(
        self,
        enhanced_rfq: 'EnhancedRFQRequest',
        legacy_title: Optional[str],
        legacy_description: str,
        legacy_product_category: Optional[str],
        legacy_target_segment: Optional[str],
        legacy_research_goal: Optional[str],
        workflow_id: str,
        survey_id: Optional[str]
    ) -> WorkflowResult:
        """Execute enhanced workflow with circuit breaker protection and enriched context"""

        # Get existing survey record (created by Enhanced RFQ API)
        if not survey_id:
            raise Exception("Survey ID is required for enhanced workflow processing")

        logger.info(f"🔍 [WorkflowService] Looking up existing survey for enhanced processing: {survey_id}")
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

        # Initialize enhanced workflow state with enriched context
        logger.info("🔄 [WorkflowService] Initializing enhanced workflow state")

        # Build enriched description from enhanced RFQ data
        enriched_description = self._build_enriched_description(enhanced_rfq, legacy_description)

        import time

        initial_state = SurveyGenerationState(
            # Use rfq_text as the primary field, with enriched description
            rfq_text=enriched_description,
            rfq_title=legacy_title,
            # Alias fields for compatibility
            title=legacy_title,
            description=enriched_description,
            # Standard RFQ fields
            product_category=legacy_product_category,
            target_segment=legacy_target_segment,
            research_goal=legacy_research_goal,
            # Enhanced workflow context
            enhanced_rfq_data=enhanced_rfq.model_dump() if enhanced_rfq else None,
            # Standard workflow fields
            current_step="initialize",
            workflow_id=workflow_id,
            survey_id=survey_id,
            survey_output=None,
            estimated_completion_time=None,
            golden_examples_used=0,
            messages=[],
            embedding=None,
            start_time=time.time(),
            progress_tracking=None
        )

        logger.info(f"✅ [WorkflowService] Enhanced workflow state initialized")
        logger.info(f"📊 [WorkflowService] Enriched description length: {len(enriched_description)} chars")

        # Create WebSocket client for progress updates
        ws_client = WebSocketNotificationService(self.connection_manager)

        try:
            # Execute the enhanced workflow
            logger.info(f"🚀 [WorkflowService] Starting enhanced workflow execution: {workflow_id}")
            result = await self.execute_enhanced_workflow_from_generation(initial_state, workflow_id, survey_id, ws_client)
            logger.info(f"✅ [WorkflowService] Enhanced workflow execution completed successfully")
            return result

        except Exception as e:
            logger.error(f"❌ [WorkflowService] Enhanced workflow execution failed: {str(e)}", exc_info=True)

            # Ensure database session health
            self._ensure_healthy_db_session()

            # Update survey status to failed
            try:
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
                    "message": f"Failed to execute enhanced workflow: {str(e)}"
                })
            except Exception as ws_error:
                logger.warning(f"⚠️ [WorkflowService] Failed to send error notification: {str(ws_error)}")
            raise Exception(f"Enhanced workflow execution failed: {str(e)}")

    def _build_enriched_description(self, enhanced_rfq: 'EnhancedRFQRequest', base_description: str) -> str:
        """Build enriched description from enhanced RFQ data for better survey generation"""

        # Import the converter utility
        try:
            from src.utils.enhanced_rfq_converter import createEnhancedDescriptionWithTextRequirements

            # Convert the enhanced RFQ to enriched text
            if enhanced_rfq:
                enriched_text = createEnhancedDescriptionWithTextRequirements(enhanced_rfq.model_dump())
                logger.info(f"📝 [WorkflowService] Created enriched description with {len(enriched_text)} characters")
                return enriched_text
            else:
                logger.warning("⚠️ [WorkflowService] No enhanced RFQ data available, using base description")
                return base_description
        except Exception as e:
            logger.warning(f"⚠️ [WorkflowService] Failed to build enriched description: {str(e)}")
            return base_description

    async def execute_enhanced_workflow_from_generation(
        self,
        initial_state: SurveyGenerationState,
        workflow_id: str,
        survey_id: str,
        ws_client: WebSocketNotificationService
    ) -> WorkflowResult:
        """Execute enhanced workflow with enriched context and text requirements"""

        logger.info(f"🚀 [WorkflowService] Starting enhanced workflow execution from generation: {workflow_id}")

        # For now, delegate to the standard workflow execution but with enhanced context
        # The enriched description will contain all the enhanced RFQ information
        return await self.execute_workflow_from_generation(initial_state, workflow_id, survey_id, ws_client)

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
            
            # Send initial progress update (only if not already started)
            logger.info("📡 [WorkflowService] Sending initial progress update via WebSocket")
            try:
                progress_tracker = get_progress_tracker(initial_state.workflow_id)

                # CRITICAL FIX: Only send initializing_workflow if we haven't progressed beyond it
                if progress_tracker.current_progress == 0 or progress_tracker.current_step is None:
                    progress_data = progress_tracker.get_progress_data("initializing_workflow")
                    await self.ws_client.send_progress_update(initial_state.workflow_id, progress_data)
                    logger.info("✅ [WorkflowService] Initial progress update sent successfully")
                else:
                    logger.info(f"⏭️ [WorkflowService] Skipping initial progress update - tracker already at {progress_tracker.current_progress}% (step: {progress_tracker.current_step})")

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

                # Check if this is a failed survey (minimal fallback due to LLM failure)
                generated_survey = final_state.get("generated_survey", {})
                is_failed_survey = generated_survey.get('metadata', {}).get('generation_failed', False)

                if is_failed_survey:
                    logger.warning(f"⚠️ [WorkflowService] Survey {survey.id} marked as draft due to generation failure")
                    survey.status = "draft"
                    survey.pillar_scores = None  # Don't store pillar scores for failed surveys
                else:
                    survey.pillar_scores = final_state.get("pillar_scores")
                    survey.status = "validated" if final_state.get("quality_gate_passed", False) else "draft"

                self.db.commit()
                logger.info(f"✅ [WorkflowService] Survey record updated: status={survey.status}, golden_examples_used={len(survey.used_golden_examples)}")
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

                        # Check if this is a failed survey (minimal fallback due to LLM failure)
                        generated_survey = final_state.get("generated_survey", {})
                        is_failed_survey = generated_survey.get('metadata', {}).get('generation_failed', False)

                        if is_failed_survey:
                            logger.warning(f"⚠️ [WorkflowService] Survey {survey.id} marked as failed due to generation failure (retry path)")
                            survey.status = "failed"
                            survey.pillar_scores = None  # Don't store pillar scores for failed surveys
                        else:
                            survey.pillar_scores = final_state.get("pillar_scores")
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

            # Send progress update - complete human review and start generation
            try:
                progress_tracker = get_progress_tracker(workflow_id)
                # Complete human review step first (30-35%)
                progress_data = progress_tracker.get_completion_data("human_review")
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

            # Send progress update for generation - continue from where human review ended
            try:
                progress_tracker = get_progress_tracker(workflow_id)
                progress_data = progress_tracker.get_progress_data("generating_questions")
                progress_data["message"] = "Starting survey generation..."
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

            # Send progress update for validation - continue from where generation ended
            try:
                progress_tracker = get_progress_tracker(workflow_id)
                # Complete generation step first
                progress_data = progress_tracker.get_completion_data("generating_questions")
                progress_data["message"] = "Generation completed - starting validation..."
                await ws_client.send_progress_update(workflow_id, progress_data)
                
                # Check if LLM evaluation is enabled before sending validation progress
                from src.services.settings_service import SettingsService
                settings_service = SettingsService(self.db)
                evaluation_settings = settings_service.get_evaluation_settings()
                enable_llm_evaluation = evaluation_settings.get('enable_llm_evaluation', True)
                
                if enable_llm_evaluation:
                    # Then start validation
                    progress_data = progress_tracker.get_progress_data("validation_scoring")
                    await ws_client.send_progress_update(workflow_id, progress_data)
                else:
                    # Skip validation and go directly to completion
                    progress_data = progress_tracker.get_progress_data("finalizing")
                    progress_data["message"] = "Skipping validation - LLM evaluation disabled"
                    await ws_client.send_progress_update(workflow_id, progress_data)
            except Exception as ws_error:
                logger.warning(f"⚠️ [WorkflowService] Failed to send validation progress update: {str(ws_error)}")

            # Use the same settings check from above
            
            if not enable_llm_evaluation:
                logger.info("⏭️ [WorkflowService] LLM evaluation disabled, skipping validation step")
                # Create a mock validation result to maintain workflow consistency
                validation_result = {
                    "pillar_scores": {},
                    "quality_gate_passed": True,  # Skip validation means pass
                    "validation_results": {"skipped": "LLM evaluation disabled"},
                    "retry_count": 0,
                    "workflow_should_continue": True,
                    "error_message": None
                }
                logger.info("✅ [WorkflowService] Validation skipped - LLM evaluation disabled")
            else:
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

                    # Check if this is a failed survey (minimal fallback due to LLM failure)
                    generated_survey = generation_result.get("generated_survey", {})
                    is_failed_survey = generated_survey.get('metadata', {}).get('generation_failed', False)

                    if is_failed_survey:
                        logger.warning(f"⚠️ [WorkflowService] Survey {survey.id} marked as failed due to generation failure (prompt review path)")
                        survey.status = "failed"
                        survey.pillar_scores = None  # Don't store pillar scores for failed surveys
                    else:
                        survey.pillar_scores = generation_result.get("pillar_scores")
                        survey.status = "validated" if validation_result.get("quality_gate_passed", False) else "draft"

                    self.db.commit()
                    logger.info(f"✅ [WorkflowService] Survey updated from resumed workflow: status={survey.status}")
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