from sqlalchemy.orm import Session
from src.database import RFQ, Survey
from src.workflows.state import SurveyGenerationState
from src.workflows.workflow import create_workflow
from src.services.embedding_service import EmbeddingService
from src.services.websocket_client import WebSocketNotificationService
from src.services.workflow_state_service import WorkflowStateService
from src.services.progress_tracker import get_progress_tracker, cleanup_progress_tracker
from src.config import settings
from typing import Optional, List
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
        survey_id: Optional[str] = None,
        custom_prompt: Optional[str] = None
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
                        research_goal, workflow_id, survey_id, custom_prompt
                    ),
                    timeout=900.0  # 15 minute timeout
                )
            except asyncio.TimeoutError:
                logger.error(f"❌ [WorkflowService] Workflow {workflow_id} timed out after 15 minutes")
                # Send failure notification
                try:
                    await self.ws_client.send_progress_update(workflow_id, {
                        "type": "error",
                        "message": "Workflow timed out after 15 minutes",
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
        survey_id: Optional[str] = None,
        custom_prompt: Optional[str] = None
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
                        legacy_research_goal, workflow_id, survey_id, custom_prompt
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
        survey_id: Optional[str],
        custom_prompt: Optional[str] = None
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
            # Custom prompt for survey generation
            system_prompt=custom_prompt,
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
        
        if custom_prompt:
            logger.info(f"🎨 [WorkflowService] Using custom prompt for survey generation ({len(custom_prompt)} chars)")

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
        survey_id: Optional[str],
        custom_prompt: Optional[str] = None,
        initial_state: Optional[SurveyGenerationState] = None
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
        if initial_state:
            # Use provided initial_state (e.g., from regeneration)
            logger.info("🔄 [WorkflowService] Using provided initial_state (regeneration mode)")
            # Update override fields to ensure consistency
            initial_state.workflow_id = workflow_id
            initial_state.survey_id = str(survey.id)
            logger.info(f"📋 [WorkflowService] Regeneration state: regeneration_mode={initial_state.regeneration_mode}, parent_survey_id={initial_state.parent_survey_id}")
        else:
            # Create new state for normal generation
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
                system_prompt=custom_prompt,  # Custom prompt for survey generation
                workflow_start_time=time.time()  # Set start time for loop prevention
            )
        
        if custom_prompt:
            logger.info(f"🎨 [WorkflowService] Using custom prompt for basic RFQ ({len(custom_prompt)} chars)")
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
            logger.info(f"🔍 [WorkflowService] Initial state before execution: {str(initial_state.model_dump())[:200]}...")
            
            try:
                final_state = await self.workflow.ainvoke(initial_state)
                logger.info(f"✅ [WorkflowService] Workflow execution completed. Final state keys: {list(final_state.keys()) if isinstance(final_state, dict) else 'not dict'}")
                logger.info(f"🔍 [WorkflowService] Final state: {str(final_state)[:200]}...")
                
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
                from uuid import UUID
                # Convert string IDs to UUIDs for used_golden_examples
                used_examples = final_state.get("used_golden_examples", [])
                survey.used_golden_examples = [UUID(ex) if isinstance(ex, str) else ex for ex in used_examples] if used_examples else []
                
                # Convert string IDs to UUIDs for used_golden_questions  
                used_questions = final_state.get("used_golden_questions", [])
                survey.used_golden_questions = [UUID(q) if isinstance(q, str) else q for q in used_questions] if used_questions else []
                
                # Convert string IDs to UUIDs for used_golden_sections
                used_sections = final_state.get("used_golden_sections", [])
                survey.used_golden_sections = [UUID(s) if isinstance(s, str) else s for s in used_sections] if used_sections else []
                
                # Track feedback questions (questions with comments used in digest)
                # Combine both similarity-matched and feedback digest questions for tracking
                feedback_questions = final_state.get("used_feedback_questions", [])
                if feedback_questions:
                    all_question_ids = list(survey.used_golden_questions) if survey.used_golden_questions else []
                    feedback_question_ids = [UUID(q) if isinstance(q, str) else q for q in feedback_questions]
                    # Merge but avoid duplicates
                    all_question_ids.extend([qid for qid in feedback_question_ids if qid not in all_question_ids])
                    survey.used_golden_questions = all_question_ids
                    logger.info(f"✅ [WorkflowService] Tracking {len(feedback_question_ids)} feedback questions in addition to {len(used_questions)} similarity-matched questions")

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
                
                # Persist feedback_digest if available
                feedback_digest = final_state.get("feedback_digest")
                if feedback_digest:
                    survey.feedback_digest = feedback_digest
                    logger.info(f"✅ [WorkflowService] Stored feedback digest for survey {survey.id}")

                self.db.commit()
                logger.info(f"✅ [WorkflowService] Survey record updated: status={survey.status}, golden_examples_used={len(survey.used_golden_examples)}")
                
                # Track golden content usage (non-blocking, won't fail survey generation)
                # This includes both similarity-matched questions AND feedback digest questions
                try:
                    from src.services.golden_content_tracking_service import GoldenContentTrackingService
                    tracking_service = GoldenContentTrackingService(self.db)
                    # survey.used_golden_questions now includes both types after merging above
                    await tracking_service.track_golden_content_usage(
                        survey_id=survey.id,
                        question_ids=survey.used_golden_questions if survey.used_golden_questions else [],
                        section_ids=survey.used_golden_sections if survey.used_golden_sections else []
                    )
                except Exception as track_error:
                    logger.warning(f"⚠️ [WorkflowService] Golden content tracking failed (non-critical): {str(track_error)}")
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
                        from uuid import UUID
                        # Convert string IDs to UUIDs for used_golden_examples
                        used_examples = final_state.get("used_golden_examples", [])
                        survey.used_golden_examples = [UUID(ex) if isinstance(ex, str) else ex for ex in used_examples] if used_examples else []
                        
                        # Convert string IDs to UUIDs for used_golden_questions  
                        used_questions = final_state.get("used_golden_questions", [])
                        survey.used_golden_questions = [UUID(q) if isinstance(q, str) else q for q in used_questions] if used_questions else []
                        
                        # Convert string IDs to UUIDs for used_golden_sections
                        used_sections = final_state.get("used_golden_sections", [])
                        survey.used_golden_sections = [UUID(s) if isinstance(s, str) else s for s in used_sections] if used_sections else []
                        
                        # Track feedback questions (combine with similarity-matched questions)
                        feedback_questions = final_state.get("used_feedback_questions", [])
                        if feedback_questions:
                            all_question_ids = list(survey.used_golden_questions) if survey.used_golden_questions else []
                            feedback_question_ids = [UUID(q) if isinstance(q, str) else q for q in feedback_questions]
                            # Merge but avoid duplicates
                            all_question_ids.extend([qid for qid in feedback_question_ids if qid not in all_question_ids])
                            survey.used_golden_questions = all_question_ids

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
                        
                        # Persist feedback_digest if available
                        feedback_digest = final_state.get("feedback_digest")
                        if feedback_digest:
                            survey.feedback_digest = feedback_digest
                            logger.info(f"✅ [WorkflowService] Stored feedback digest for survey {survey.id} (retry)")
                        
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
    
    async def regenerate_survey(
        self,
        parent_survey_id: str,
        include_annotations: bool = True,
        version_notes: Optional[str] = None,
        target_sections: Optional[List[str]] = None,
        focus_on_annotated_areas: bool = True,
        regeneration_mode: str = "surgical"
    ) -> WorkflowResult:
        """
        Regenerate a survey with annotation feedback from all previous versions
        
        Args:
            parent_survey_id: The survey ID to regenerate from
            include_annotations: Whether to include annotation feedback
            version_notes: Optional notes about this version
            target_sections: Optional list of section IDs to regenerate (for section-specific regeneration)
            focus_on_annotated_areas: Whether to prioritize annotated areas
            
        Returns:
            WorkflowResult with new survey_id and workflow_id
        """
        from uuid import UUID
        from src.services.version_service import VersionService
        from src.services.annotation_feedback_service import AnnotationFeedbackService
        from src.services.survey_encoder_service import SurveyEncoderService
        
        logger.info(f"🔄 [WorkflowService] Starting survey regeneration for parent_survey_id={parent_survey_id}")
        
        # Load parent survey
        parent_survey = self.db.query(Survey).filter(Survey.id == UUID(parent_survey_id)).first()
        if not parent_survey:
            raise ValueError(f"Parent survey not found: {parent_survey_id}")
        
        # Get RFQ
        rfq = self.db.query(RFQ).filter(RFQ.id == parent_survey.rfq_id).first()
        if not rfq:
            raise ValueError(f"RFQ not found for survey: {parent_survey_id}")
        
        # Get version service
        version_service = VersionService(self.db)
        
        # Get next version number
        next_version = version_service.increment_version(rfq.id)
        
        # Mark previous current version as not current
        current_version = version_service.get_current_version(rfq.id)
        if current_version:
            current_version.is_current = False
            self.db.commit()
        
        # Create new survey record
        new_survey = Survey(
            rfq_id=rfq.id,
            status="draft",
            version=next_version,
            parent_survey_id=UUID(str(parent_survey.id)),
            is_current=True,
            version_notes=version_notes
        )
        self.db.add(new_survey)
        self.db.commit()
        self.db.refresh(new_survey)
        
        logger.info(f"✅ [WorkflowService] Created new survey version {next_version}: {new_survey.id}")
        
        # Generate workflow_id (final) - now we can send progress updates
        workflow_id = f"survey-regenerate-{new_survey.id}"
        
        # Initialize progress tracker and WebSocket client for regeneration prep updates
        from src.services.progress_tracker import get_progress_tracker
        from src.services.websocket_client import WebSocketNotificationService
        
        progress_tracker = get_progress_tracker(workflow_id)
        ws_client = None
        if self.connection_manager:
            ws_client = WebSocketNotificationService(self.connection_manager)
        
        # Send initial progress update: Preparing regeneration
        try:
            if ws_client:
                progress_data = progress_tracker.get_progress_data("preparing_regeneration")
                logger.info(f"📡 [WorkflowService] Sending progress update: preparing_regeneration for workflow_id={workflow_id}")
                await ws_client.send_progress_update(workflow_id, progress_data)
                logger.info(f"✅ [WorkflowService] Progress update sent: preparing_regeneration")
        except Exception as e:
            logger.warning(f"⚠️ [WorkflowService] Failed to send preparing_regeneration progress update: {str(e)}")
        
        # Send progress update: Collecting feedback
        try:
            if ws_client:
                progress_data = progress_tracker.get_progress_data("collecting_feedback")
                logger.info(f"📡 [WorkflowService] Sending progress update: collecting_feedback")
                await ws_client.send_progress_update(workflow_id, progress_data)
                logger.info(f"✅ [WorkflowService] Progress update sent: collecting_feedback")
        except Exception as e:
            logger.warning(f"⚠️ [WorkflowService] Failed to send collecting_feedback progress update: {str(e)}")
        
        # Collect annotation feedback if requested
        annotation_feedback = None
        if include_annotations:
            annotation_service = AnnotationFeedbackService(self.db)
            annotation_feedback = await annotation_service.build_feedback_digest(
                rfq_id=rfq.id,
                section_ids=target_sections,
                prioritize_annotated=focus_on_annotated_areas
            )
            logger.info(f"📝 [WorkflowService] Collected annotation feedback: {annotation_feedback.get('question_feedback', {}).get('total_count', 0)} questions, {annotation_feedback.get('section_feedback', {}).get('total_count', 0)} sections")
            
            # Log detailed feedback for debugging
            if annotation_feedback.get('section_feedback', {}).get('sections_with_feedback'):
                logger.info(f"📝 [WorkflowService] Section feedback details:")
                for sf in annotation_feedback['section_feedback']['sections_with_feedback'][:5]:
                    logger.info(f"  - Section {sf.get('section_id')}: {len(sf.get('comments', []))} comments")
                    for comment in sf.get('comments', [])[:2]:
                        logger.info(f"    - v{comment.get('version')}: {comment.get('comment', '')[:100]}")
            
            logger.info(f"📝 [WorkflowService] Combined digest preview: {annotation_feedback.get('combined_digest', '')[:500]}")
        
        # Analyze feedback for surgical mode (determine which sections need regeneration)
        from src.workflows.state import RegenerationMode
        
        regeneration_mode_enum = RegenerationMode.SURGICAL if regeneration_mode == "surgical" else (
            RegenerationMode.TARGETED if regeneration_mode == "targeted" else RegenerationMode.FULL
        )
        
        surgical_analysis = None
        if regeneration_mode_enum == RegenerationMode.SURGICAL and annotation_feedback and parent_survey.final_output:
            # Send progress update: Analyzing feedback (surgical mode only)
            try:
                if ws_client:
                    progress_data = progress_tracker.get_progress_data("analyzing_feedback")
                    logger.info(f"📡 [WorkflowService] Sending progress update: analyzing_feedback")
                    await ws_client.send_progress_update(workflow_id, progress_data)
                    logger.info(f"✅ [WorkflowService] Progress update sent: analyzing_feedback")
            except Exception as e:
                logger.warning(f"⚠️ [WorkflowService] Failed to send analyzing_feedback progress update: {str(e)}")
            
            from src.services.feedback_analyzer_service import FeedbackAnalyzerService
            
            analyzer = FeedbackAnalyzerService()
            surgical_analysis = analyzer.analyze_feedback_for_surgical_regeneration(
                annotation_feedback=annotation_feedback,
                previous_survey=parent_survey.final_output
            )
            
            logger.info(f"🔬 [WorkflowService] Surgical analysis complete:")
            logger.info(f"  - Total sections: {surgical_analysis['total_sections']}")
            logger.info(f"  - Sections to regenerate: {surgical_analysis['sections_to_regenerate']} ({surgical_analysis['regeneration_percentage']:.1f}%)")
            logger.info(f"  - Sections to preserve: {surgical_analysis['sections_to_preserve']} ({100-surgical_analysis['regeneration_percentage']:.1f}%)")
            
            # Update target_sections to only include sections that need regeneration
            if not target_sections:  # Only override if user didn't specify target sections
                target_sections = [str(sid) for sid in surgical_analysis['sections_to_regenerate']]
                logger.info(f"  - Updated target_sections for surgical mode: {target_sections}")
        
        elif regeneration_mode_enum == RegenerationMode.TARGETED and target_sections and parent_survey.final_output:
            # For targeted mode, create surgical_analysis from user-selected sections
            all_sections = parent_survey.final_output.get('sections', [])
            all_section_ids = {s.get('id') for s in all_sections if s.get('id') is not None}
            target_section_ids = [int(sid) if sid.isdigit() else sid for sid in target_sections]
            preserve_section_ids = sorted([sid for sid in all_section_ids if sid not in target_section_ids])
            
            surgical_analysis = {
                "sections_to_regenerate": sorted(target_section_ids),
                "sections_to_preserve": preserve_section_ids,
                "regeneration_rationale": {sid: ["User selected for regeneration"] for sid in target_section_ids},
                "total_sections": len(all_section_ids),
                "regeneration_percentage": (len(target_section_ids) / len(all_section_ids) * 100) if all_section_ids else 0
            }
            
            logger.info(f"🎯 [WorkflowService] Targeted mode: User selected {len(target_section_ids)} sections to regenerate")
            logger.info(f"  - Sections to regenerate: {surgical_analysis['sections_to_regenerate']}")
            logger.info(f"  - Sections to preserve: {surgical_analysis['sections_to_preserve']}")
        
        # Send progress update: Encoding previous survey
        try:
            if ws_client:
                progress_data = progress_tracker.get_progress_data("encoding_previous_survey")
                logger.info(f"📡 [WorkflowService] Sending progress update: encoding_previous_survey")
                await ws_client.send_progress_update(workflow_id, progress_data)
                logger.info(f"✅ [WorkflowService] Progress update sent: encoding_previous_survey")
        except Exception as e:
            logger.warning(f"⚠️ [WorkflowService] Failed to send encoding_previous_survey progress update: {str(e)}")
        
        # Encode previous survey structure
        # Include full questions for sections that have feedback
        previous_survey_encoded = None
        if parent_survey.final_output:
            encoder_service = SurveyEncoderService()
            
            # Identify sections with feedback to include full questions
            sections_with_feedback = []
            if annotation_feedback:
                for sf in annotation_feedback.get('section_feedback', {}).get('sections_with_feedback', []):
                    section_id = sf.get('section_id')
                    if section_id is not None:
                        # Convert to int if it's a number, keep as-is otherwise
                        try:
                            sections_with_feedback.append(int(section_id))
                        except (ValueError, TypeError):
                            sections_with_feedback.append(section_id)
            
            previous_survey_encoded = encoder_service.encode_survey_structure(
                parent_survey.final_output,
                include_full_questions_for_sections=sections_with_feedback if sections_with_feedback else None
            )
            logger.info(f"📦 [WorkflowService] Encoded previous survey structure: {len(str(previous_survey_encoded))} chars, full questions for {len(sections_with_feedback)} sections")
        
        # Initialize workflow state with regeneration mode
        import time
        initial_state = SurveyGenerationState(
            rfq_id=rfq.id,
            rfq_text=rfq.description or "",
            rfq_title=rfq.title,
            product_category=rfq.product_category,
            target_segment=rfq.target_segment,
            research_goal=rfq.research_goal,
            workflow_id=workflow_id,
            survey_id=str(new_survey.id),
            workflow_start_time=time.time(),
            # Regeneration mode fields
            parent_survey_id=UUID(parent_survey_id),
            regeneration_mode=True,
            regeneration_type="sections" if target_sections else "full",  # Deprecated, use regeneration_mode_type
            regeneration_mode_type=regeneration_mode_enum,  # New enum-based mode
            target_sections=target_sections,
            previous_survey_encoded=previous_survey_encoded,
            annotation_feedback_summary=annotation_feedback,
            focus_on_annotated_areas=focus_on_annotated_areas,
            surgical_analysis=surgical_analysis  # Analysis of which sections to regenerate
        )
        
        logger.info(f"🔄 [WorkflowService] Initialized regeneration state: workflow_id={workflow_id}, version={next_version}")
        
        # Execute workflow (reuse existing method) - pass initial_state to preserve regeneration fields
        return await self._execute_workflow_with_circuit_breaker(
            title=rfq.title,
            description=rfq.description or "",
            product_category=rfq.product_category,
            target_segment=rfq.target_segment,
            research_goal=rfq.research_goal,
            workflow_id=workflow_id,
            survey_id=str(new_survey.id),
            custom_prompt=None,
            initial_state=initial_state  # Pass the regeneration state we created
        )
    
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
            from src.workflows.nodes import GeneratorAgent

            # Use the same database session as the main workflow service
            generator = GeneratorAgent(self.db, connection_manager=self.connection_manager)

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

            # Save survey to database immediately after generation (before evaluation)
            # This ensures survey is available in UI even if evaluation fails later
            try:
                # Ensure we have a healthy database session
                if not self._ensure_healthy_db_session():
                    raise Exception("Failed to establish healthy database session")

                survey = self.db.query(Survey).filter(Survey.id == survey_id).first()
                if survey:
                    # Refresh to get latest data
                    self.db.refresh(survey)

                    # Save generation results immediately
                    # CRITICAL: Save truly raw response from LLM API (before any processing)
                    # This should work even when generation fails - raw_response may be in generation_metadata from error handling
                    raw_response = generation_result.get("generation_metadata", {}).get("raw_response")
                    if raw_response:
                        # Store raw response as pure text (may be string or already JSON string)
                        survey.raw_output = raw_response if isinstance(raw_response, str) else str(raw_response)
                        logger.info(f"💾 [WorkflowService] Saved raw LLM response to survey.raw_output (length: {len(survey.raw_output) if survey.raw_output else 0})")
                    else:
                        # Fallback: check if there's an error with raw_response attached
                        error_message = generation_result.get("error_message")
                        if error_message:
                            logger.warning(f"⚠️ [WorkflowService] Generation failed: {error_message}")
                            logger.warning("⚠️ [WorkflowService] No raw response found in generation_metadata - cannot save raw response")
                        else:
                            # Fallback: use parsed survey if raw response not available
                            survey.raw_output = generation_result.get("raw_survey")
                            logger.warning("⚠️ [WorkflowService] Raw response not found in generation_metadata, using parsed survey as fallback")
                    
                    # CRITICAL: Validate survey is not empty before saving
                    generated_survey = generation_result.get("generated_survey", {})
                    if not generated_survey:
                        logger.error(f"❌ [WorkflowService] CRITICAL: Cannot save empty survey - no survey data in generation_result")
                        raise ValueError("Cannot save survey: generation result contains no survey data")
                    
                    from src.utils.survey_utils import get_questions_count
                    question_count = get_questions_count(generated_survey)
                    if question_count == 0:
                        logger.error(f"❌ [WorkflowService] CRITICAL: Cannot save empty survey - 0 questions found")
                        logger.error(f"❌ [WorkflowService] Survey structure: sections={len(generated_survey.get('sections', []))}")
                        for i, section in enumerate(generated_survey.get("sections", [])):
                            section_questions = len(section.get("questions", []))
                            logger.error(f"❌ [WorkflowService] Section {i+1} ({section.get('title', 'No title')}): {section_questions} questions")
                        raise ValueError("Cannot save survey: generated survey is empty (0 questions). This indicates a generation failure.")
                    
                    logger.info(f"✅ [WorkflowService] Survey validation passed: {question_count} questions found")
                    
                    # Save parsed/processed survey as final_output
                    survey.final_output = generated_survey
                    # Convert state UUID lists to survey arrays
                    from uuid import UUID
                    survey.used_golden_examples = initial_state.used_golden_examples
                    # Combine feedback questions with similarity-matched questions
                    all_questions = list(initial_state.used_golden_questions) if initial_state.used_golden_questions else []
                    if initial_state.used_feedback_questions:
                        all_questions.extend([qid for qid in initial_state.used_feedback_questions if qid not in all_questions])
                    survey.used_golden_questions = all_questions
                    survey.used_golden_sections = initial_state.used_golden_sections
                    
                    # Check if this is a failed survey (minimal fallback due to LLM failure)
                    is_failed_survey = generated_survey.get('metadata', {}).get('generation_failed', False)

                    if is_failed_survey:
                        logger.warning(f"⚠️ [WorkflowService] Survey {survey.id} marked as draft due to generation failure")
                        survey.status = "draft"
                        survey.pillar_scores = None
                    else:
                        # Set status to draft initially - will be updated to validated after evaluation if it passes
                        survey.status = "draft"
                        survey.pillar_scores = None  # Will be set after evaluation

                    self.db.commit()
                    logger.info(f"✅ [WorkflowService] Survey saved immediately after generation: status={survey.status}, survey_id={survey_id}")
                else:
                    logger.warning(f"⚠️ [WorkflowService] Survey not found for immediate save: {survey_id}")
            except Exception as e:
                logger.error(f"❌ [WorkflowService] Failed to save survey after generation: {str(e)}", exc_info=True)
                self.db.rollback()
                # Don't fail the workflow for database update issues - continue to evaluation

            # Note: AI evaluation has been removed from the workflow
            # The workflow now goes directly from golden_validation to completion_handler
            # Users can trigger evaluation manually from SurveyPreview/SurveyInsights if needed
            
            # Send progress update - generation completed, workflow continues with golden validation
            try:
                progress_tracker = get_progress_tracker(workflow_id)
                # Complete generation step
                progress_data = progress_tracker.get_completion_data("generating_questions")
                progress_data["message"] = "Generation completed - proceeding to validation..."
                await ws_client.send_progress_update(workflow_id, progress_data)
            except Exception as ws_error:
                logger.warning(f"⚠️ [WorkflowService] Failed to send progress update: {str(ws_error)}")

            # Update survey with final results - use the same logic as the main workflow
            try:

                # Ensure we have a healthy database session
                if not self._ensure_healthy_db_session():
                    raise Exception("Failed to establish healthy database session")

                survey = self.db.query(Survey).filter(Survey.id == survey_id).first()
                if survey:
                    # Refresh to get latest data
                    self.db.refresh(survey)

                    # CRITICAL: Validate survey is not empty before saving (second save point)
                    final_survey = generation_result.get("generated_survey", {})
                    if not final_survey:
                        logger.error(f"❌ [WorkflowService] CRITICAL: Cannot save empty survey at final update - no survey data")
                        raise ValueError("Cannot save survey: generation result contains no survey data")
                    
                    from src.utils.survey_utils import get_questions_count
                    final_question_count = get_questions_count(final_survey)
                    if final_question_count == 0:
                        logger.error(f"❌ [WorkflowService] CRITICAL: Cannot save empty survey at final update - 0 questions")
                        raise ValueError("Cannot save survey: generated survey is empty (0 questions). This indicates a generation failure.")
                    
                    # Use the same update logic as the main workflow
                    survey.raw_output = generation_result.get("raw_survey")
                    survey.final_output = final_survey
                    survey.golden_similarity_score = validation_result.get("golden_similarity_score")
                    # Convert state UUID lists to survey arrays
                    from uuid import UUID
                    survey.used_golden_examples = initial_state.used_golden_examples
                    # Combine feedback questions with similarity-matched questions
                    all_questions = list(initial_state.used_golden_questions) if initial_state.used_golden_questions else []
                    if initial_state.used_feedback_questions:
                        all_questions.extend([qid for qid in initial_state.used_feedback_questions if qid not in all_questions])
                    survey.used_golden_questions = all_questions
                    survey.used_golden_sections = initial_state.used_golden_sections

                    # Check if this is a failed survey (minimal fallback due to LLM failure)
                    generated_survey = generation_result.get("generated_survey", {})
                    is_failed_survey = generated_survey.get('metadata', {}).get('generation_failed', False)

                    # Check if evaluation failed
                    evaluation_failed = validation_result.get("evaluation_failed", False)

                    if is_failed_survey:
                        logger.warning(f"⚠️ [WorkflowService] Survey {survey.id} marked as draft due to generation failure (prompt review path)")
                        survey.status = "draft"  # Changed from "failed" to "draft" - survey is still available
                        survey.pillar_scores = None  # Don't store pillar scores for failed surveys
                    elif evaluation_failed:
                        # Evaluation failed but generation succeeded - keep survey as draft
                        logger.warning(f"⚠️ [WorkflowService] Survey {survey.id} evaluation failed but survey is available")
                        survey.status = "draft"  # Keep as draft since evaluation failed
                        survey.pillar_scores = None  # Don't store pillar scores since evaluation failed
                    else:
                        # Both generation and evaluation succeeded
                        survey.pillar_scores = validation_result.get("pillar_scores") or generation_result.get("pillar_scores")
                        survey.status = "validated" if validation_result.get("quality_gate_passed", False) else "draft"
                    
                    # Persist feedback_digest if available
                    feedback_digest = initial_state.feedback_digest if hasattr(initial_state, 'feedback_digest') else None
                    if feedback_digest:
                        survey.feedback_digest = feedback_digest
                        logger.info(f"✅ [WorkflowService] Stored feedback digest for survey {survey.id} (prompt review path)")

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