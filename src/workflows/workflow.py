try:
    from langgraph.graph import StateGraph
except ImportError:
    # Fallback for different langgraph versions
    from langgraph import StateGraph
from sqlalchemy.orm import Session
from typing import Any, Dict
from .state import SurveyGenerationState
from .nodes import (
    RFQNode,
    GoldenRetrieverNode,
    ContextBuilderNode,
    GeneratorAgent,
    GoldenValidatorNode,
    ValidatorAgent,
    HumanPromptReviewNode,
    LabelDetectionNode
)
from src.services.progress_tracker import get_progress_tracker
import logging

logger = logging.getLogger(__name__)


def create_workflow(db: Session, connection_manager=None) -> Any:
    """
    Create the LangGraph workflow for survey generation
    """
    workflow = StateGraph(SurveyGenerationState)
    
    # Initialize nodes
    rfq_node = RFQNode(db)
    golden_retriever = GoldenRetrieverNode(db)
    context_builder = ContextBuilderNode(db)
    prompt_reviewer = HumanPromptReviewNode(db)
    generator = GeneratorAgent(db, connection_manager=connection_manager)
    label_detector = LabelDetectionNode(db, connection_manager=connection_manager)
    validator = ValidatorAgent(db, connection_manager=connection_manager)
    
    # Initialize WebSocket client for progress updates
    try:
        from src.services.websocket_client import WebSocketNotificationService
        ws_client = WebSocketNotificationService(connection_manager)
    except Exception:
        # Graceful fallback if settings/config not available during tests
        class _NoopWS:
            async def send_progress_update(self, *args, **kwargs):
                return None
        ws_client = _NoopWS()
    
    # Create wrapper functions that send progress updates
    async def initialize_workflow_with_progress(state: SurveyGenerationState) -> Dict[str, Any]:
        """Send initializing workflow progress update"""
        progress_tracker = get_progress_tracker(state.workflow_id)
        
        try:
            progress_data = progress_tracker.get_progress_data("initializing_workflow")
            logger.info(f"📡 [Workflow] Sending progress update: initializing_workflow for workflow_id={state.workflow_id}")
            await ws_client.send_progress_update(state.workflow_id, progress_data)
            logger.info(f"✅ [Workflow] Progress update sent: initializing_workflow")
        except Exception as e:
            logger.error(f"❌ [Workflow] Failed to send progress update: {str(e)}")
        
        return {}
    
    async def parse_rfq_with_progress(state: SurveyGenerationState) -> Dict[str, Any]:
        """Parse RFQ with progress update"""
        progress_tracker = get_progress_tracker(state.workflow_id)
        
        try:
            progress_data = progress_tracker.get_progress_data("building_context", "parsing_rfq")
            logger.info(f"📡 [Workflow] Sending progress update: parsing_rfq for workflow_id={state.workflow_id}")
            await ws_client.send_progress_update(state.workflow_id, progress_data)
            logger.info(f"✅ [Workflow] Progress update sent successfully: parsing_rfq")
        except Exception as e:
            logger.error(f"❌ [Workflow] Failed to send progress update: {str(e)}")
        
        # Send additional progress update for embedding generation
        try:
            progress_data = progress_tracker.get_progress_data("building_context", "generating_embeddings")
            logger.info(f"📡 [Workflow] Sending progress update: generating_embeddings for workflow_id={state.workflow_id}")
            await ws_client.send_progress_update(state.workflow_id, progress_data)
            logger.info(f"✅ [Workflow] Progress update sent successfully: generating_embeddings")
        except Exception as e:
            logger.error(f"❌ [Workflow] Failed to send embedding progress update: {str(e)}")
        
        result = await rfq_node(state)
        
        # Send completion progress update
        try:
            completion_data = progress_tracker.get_completion_data("building_context", "rfq_parsed")
            logger.info(f"📡 [Workflow] Sending progress update: rfq_parsed for workflow_id={state.workflow_id}")
            await ws_client.send_progress_update(state.workflow_id, completion_data)
            logger.info(f"✅ [Workflow] Progress update sent successfully: rfq_parsed")
        except Exception as e:
            logger.error(f"❌ [Workflow] Failed to send RFQ completion progress update: {str(e)}")
        
        return result
    
    async def retrieve_golden_with_progress(state: SurveyGenerationState) -> Dict[str, Any]:
        """Retrieve golden examples with progress update"""
        progress_tracker = get_progress_tracker(state.workflow_id)
        
        try:
            logger.info(f"📡 [Workflow] Sending progress update: matching_golden_examples for workflow_id={state.workflow_id}")
            progress_data = progress_tracker.get_progress_data("building_context", "matching_golden_examples")
            progress_data["message"] = "Finding templates and matching relevant examples..."
            await ws_client.send_progress_update(state.workflow_id, progress_data)
            logger.info(f"✅ [Workflow] Progress update sent successfully: matching_golden_examples")
        except Exception as e:
            logger.error(f"❌ [Workflow] Failed to send progress update: {str(e)}")
        
        # Add detailed logging for golden pairs retrieval
        logger.info(f"🔍 [Workflow] Starting golden pairs retrieval for RFQ: '{state.rfq_text[:100]}...'")
        logger.info(f"🔍 [Workflow] RFQ details - Category: {state.product_category}, Segment: {state.target_segment}, Goal: {state.research_goal}")
        
        try:
            result = await golden_retriever(state)
            logger.info(f"✅ [Workflow] Golden pairs retrieval completed. Found {len(result.get('golden_examples', []))} examples")
            if result.get('golden_examples'):
                for i, example in enumerate(result['golden_examples'][:3]):  # Log first 3 examples
                    rfq_text = example.get('rfq_text', 'No text')
                    text_preview = rfq_text[:50] if rfq_text is not None else '<null>'
                    logger.info(f"📋 [Workflow] Example {i+1}: {text_preview}... (Score: {example.get('similarity_score', 'N/A')})")
            return result
        except Exception as e:
            logger.error(f"❌ [Workflow] Golden pairs retrieval failed: {str(e)}", exc_info=True)
            raise
    
    async def build_context_with_progress(state: SurveyGenerationState) -> Dict[str, Any]:
        """Build context with progress update"""
        progress_tracker = get_progress_tracker(state.workflow_id)
        
        try:
            logger.info(f"📡 [Workflow] Sending progress update: planning_methodologies for workflow_id={state.workflow_id}")
            progress_data = progress_tracker.get_progress_data("building_context", "planning_methodologies")
            await ws_client.send_progress_update(state.workflow_id, progress_data)
            logger.info(f"✅ [Workflow] Progress update sent successfully: planning_methodologies")
        except Exception as e:
            logger.error(f"❌ [Workflow] Failed to send progress update: {str(e)}")
        
        result = await context_builder(state)
        
        # Send build context completion progress
        try:
            logger.info(f"📡 [Workflow] Sending progress update: build_context for workflow_id={state.workflow_id}")
            progress_data = progress_tracker.get_progress_data("building_context", "build_context")
            progress_data["message"] = "Finalizing context and templates..."
            await ws_client.send_progress_update(state.workflow_id, progress_data)
            logger.info(f"✅ [Workflow] Progress update sent successfully: build_context")
        except Exception as e:
            logger.error(f"❌ [Workflow] Failed to send progress update: {str(e)}")
        
        return result
    
    async def prompt_review_with_progress(state: SurveyGenerationState) -> Dict[str, Any]:
        """Human prompt review with progress update"""
        progress_tracker = get_progress_tracker(state.workflow_id)
        
        logger.info(f"🔍 [Workflow] prompt_review_with_progress called for workflow: {state.workflow_id}")
        logger.info(f"🔍 [Workflow] Input state pending_human_review: {getattr(state, 'pending_human_review', False)}")
        logger.info(f"🔍 [Workflow] Input state workflow_paused: {getattr(state, 'workflow_paused', False)}")

        # Check if human review is enabled before doing anything
        enable_prompt_review = False
        try:
            from src.services.settings_service import SettingsService
            from src.database import get_db

            fresh_db = next(get_db())
            settings_service = SettingsService(fresh_db)
            settings = settings_service.get_evaluation_settings()

            enable_prompt_review = settings.get('enable_prompt_review', False)
            prompt_review_mode = settings.get('prompt_review_mode', 'disabled')
            logger.info(f"🔍 [Workflow] Human review settings: enable={enable_prompt_review}, mode={prompt_review_mode}")

            fresh_db.close()
        except Exception as e:
            logger.warning(f"⚠️ [Workflow] Settings fetch failed: {e}, defaulting to disabled")
            enable_prompt_review = False

        # If human review is disabled, skip entirely and send appropriate progress
        if not enable_prompt_review:
            logger.info(f"⏭️ [Workflow] Human review disabled, skipping review step")
            try:
                progress_data = progress_tracker.get_progress_data("preparing_generation")
                progress_data["message"] = "Preparing survey generation..."
                await ws_client.send_progress_update(state.workflow_id, progress_data)
                logger.info(f"✅ [Workflow] Progress update sent: skipping human review")
            except Exception as e:
                logger.error(f"❌ [Workflow] Failed to send progress update: {str(e)}")

            # Return result as if review was approved and continue
            return {
                "prompt_approved": True,
                "pending_human_review": False,
                "workflow_paused": False,
                "error_message": None
            }

        # Human review is enabled, proceed with normal flow
        try:
            progress_tracker = get_progress_tracker(state.workflow_id)
            progress_data = progress_tracker.get_progress_data("human_review")
            logger.info(f"📡 [Workflow] Sending progress update: human_review for workflow_id={state.workflow_id}")
            await ws_client.send_progress_update(state.workflow_id, progress_data)
            logger.info(f"✅ [Workflow] Progress update sent successfully: human_review")
        except Exception as e:
            logger.error(f"❌ [Workflow] Failed to send progress update: {str(e)}")

        logger.info(f"🚀 [Workflow] About to call HumanPromptReviewNode...")
        result = await prompt_reviewer(state)
        logger.info(f"📊 [Workflow] HumanPromptReviewNode result: {result}")
        logger.info(f"📊 [Workflow] Pending human review: {result.get('pending_human_review', False)}")
        logger.info(f"📊 [Workflow] Workflow paused: {result.get('workflow_paused', False)}")
        logger.info(f"📊 [Workflow] Review ID: {result.get('review_id', None)}")
        
        # Update the state with the result
        if 'pending_human_review' in result:
            state.pending_human_review = result['pending_human_review']
        if 'workflow_paused' in result:
            state.workflow_paused = result['workflow_paused']
        if 'review_id' in result:
            state.review_id = result['review_id']
            
        logger.info(f"🔍 [Workflow] Updated state - pending_human_review: {state.pending_human_review}")
        logger.info(f"🔍 [Workflow] Updated state - workflow_paused: {state.workflow_paused}")
        logger.info(f"🔍 [Workflow] Updated state - review_id: {state.review_id}")
        
        # If blocking review is pending, send special WebSocket message
        if result.get('pending_human_review'):
            # Check if we already sent a human review required message to prevent duplicates
            if not state.workflow_paused:
                try:
                    progress_tracker = get_progress_tracker(state.workflow_id)
                    progress_data = progress_tracker.get_progress_data("human_review", "waiting_for_review")
                    progress_data.update({
                        "type": "human_review_required",
                        "message": "Waiting for human review of system prompt...",
                        "review_id": result.get('review_id'),
                        "workflow_paused": True
                    })
                    logger.info(f"🛑 [Workflow] Sending human review required message for workflow_id={state.workflow_id}")
                    await ws_client.send_progress_update(state.workflow_id, progress_data)
                    logger.info(f"✅ [Workflow] Human review required message sent successfully")
                except Exception as e:
                    logger.error(f"❌ [Workflow] Failed to send human review required message: {str(e)}")
            else:
                logger.info(f"🔄 [Workflow] Human review already in progress, skipping duplicate message")
        else:
            logger.info(f"ℹ️ [Workflow] No human review required, continuing workflow")
        
        return result
    
    async def generate_with_progress(state: SurveyGenerationState) -> Dict[str, Any]:
        """Generate survey with progress update"""
        progress_tracker = get_progress_tracker(state.workflow_id)

        # Step 1: Preparing generation
        try:
            progress_data = progress_tracker.get_progress_data("preparing_generation")
            logger.info(f"📡 [Workflow] Sending progress update: preparing_generation for workflow_id={state.workflow_id}")
            await ws_client.send_progress_update(state.workflow_id, progress_data)
            logger.info(f"✅ [Workflow] Progress update sent successfully: preparing_generation")
        except Exception as e:
            logger.error(f"❌ [Workflow] Failed to send progress update: {str(e)}")

        # Step 2: LLM Processing - let GenerationService handle detailed progress
        logger.info("🚀 [Workflow] About to call GeneratorAgent...")
        logger.info(f"📊 [Workflow] State before generation - context: {bool(state.context)}, golden_examples: {len(state.golden_examples) if state.golden_examples else 0}")

        result = await generator(state)

        # Step 3: Parsing Output
        try:
            progress_data = progress_tracker.get_progress_data("parsing_output")
            logger.info(f"📡 [Workflow] Sending progress update: parsing_output for workflow_id={state.workflow_id}")
            await ws_client.send_progress_update(state.workflow_id, progress_data)
            logger.info(f"✅ [Workflow] Progress update sent successfully: parsing_output")
        except Exception as e:
            logger.error(f"❌ [Workflow] Failed to send parsing progress update: {str(e)}")
        
        logger.info(f"📊 [Workflow] GeneratorAgent result keys: {list(result.keys()) if result else 'None'}")
        logger.info(f"📊 [Workflow] GeneratorAgent error_message: {result.get('error_message', 'None') if result else 'None'}")
        
        # CRITICAL: If generation failed, we need to ensure the error is properly set in the state
        # LangGraph will merge the result into the state, but we need to make sure error_message is included
        if result and result.get('error_message'):
            logger.error(f"❌ [Workflow] Generation failed, error will be propagated to state: {result['error_message']}")
            # The error_message will be automatically merged into the state by LangGraph
            # No need to manually set it here
        
        return result
    
    async def detect_labels_with_progress(state: SurveyGenerationState) -> Dict[str, Any]:
        """Detect and assign labels to questions with progress update"""
        progress_tracker = get_progress_tracker(state.workflow_id)
        
        try:
            logger.info(f"📡 [Workflow] Sending progress update: detecting_labels for workflow_id={state.workflow_id}")
            progress_data = progress_tracker.get_progress_data("detecting_labels")
            progress_data["message"] = "Automatically detecting and assigning question labels..."
            await ws_client.send_progress_update(state.workflow_id, progress_data)
            logger.info(f"✅ [Workflow] Progress update sent successfully: detecting_labels")
        except Exception as e:
            logger.error(f"❌ [Workflow] Failed to send progress update: {str(e)}")
        
        result = await label_detector(state)
        
        # Send completion progress update
        try:
            logger.info(f"📡 [Workflow] Sending progress update: labels_detected for workflow_id={state.workflow_id}")
            progress_data = progress_tracker.get_progress_data("labels_detected")
            progress_data["message"] = "Question labels detected and assigned successfully!"
            await ws_client.send_progress_update(state.workflow_id, progress_data)
            logger.info(f"✅ [Workflow] Progress update sent successfully: labels_detected")
        except Exception as e:
            logger.error(f"❌ [Workflow] Failed to send label detection completion progress update: {str(e)}")
        
        return result
    
    async def validate_with_progress(state: SurveyGenerationState) -> Dict[str, Any]:
        """Validate survey with progress update"""
        progress_tracker = get_progress_tracker(state.workflow_id)
        
        try:
            logger.info(f"📡 [Workflow] Sending progress update: validation_scoring for workflow_id={state.workflow_id}")
            progress_data = progress_tracker.get_progress_data("validation_scoring")
            progress_data["message"] = "Running comprehensive evaluations and quality assessments..."
            await ws_client.send_progress_update(state.workflow_id, progress_data)
            logger.info(f"✅ [Workflow] Progress update sent successfully: validation_scoring")
        except Exception as e:
            logger.error(f"❌ [Workflow] Failed to send progress update: {str(e)}")
        
        # Send evaluating pillars progress
        try:
            progress_data = progress_tracker.get_progress_data("evaluating_pillars")
            progress_data["message"] = "Analyzing quality across all pillars..."
            await ws_client.send_progress_update(state.workflow_id, progress_data)
        except Exception as e:
            logger.error(f"❌ [Workflow] Failed to send progress update: {str(e)}")
        
        result = await validator(state)
        
        # Send finalizing progress
        try:
            logger.info(f"📡 [Workflow] Sending progress update: finalizing for workflow_id={state.workflow_id}")
            progress_data = progress_tracker.get_progress_data("finalizing")
            progress_data["message"] = "Finalizing survey generation..."
            await ws_client.send_progress_update(state.workflow_id, progress_data)
            logger.info(f"✅ [Workflow] Progress update sent successfully: finalizing")
        except Exception as e:
            logger.error(f"❌ [Workflow] Failed to send progress update: {str(e)}")
        
        return result
    
    
    # Add nodes to workflow
    workflow.add_node("initialize_workflow", initialize_workflow_with_progress)
    workflow.add_node("parse_rfq", parse_rfq_with_progress)
    workflow.add_node("retrieve_golden", retrieve_golden_with_progress)
    workflow.add_node("build_context", build_context_with_progress)
    workflow.add_node("prompt_review", prompt_review_with_progress)
    workflow.add_node("generate", generate_with_progress)
    workflow.add_node("detect_labels", detect_labels_with_progress)
    workflow.add_node("validate", validate_with_progress)
    
    # Set entry point to initialization
    workflow.set_entry_point("initialize_workflow")
    
    # Add sequential edges
    workflow.add_edge("initialize_workflow", "parse_rfq")
    workflow.add_edge("parse_rfq", "retrieve_golden")
    workflow.add_edge("retrieve_golden", "build_context")
    workflow.add_edge("build_context", "prompt_review")
    workflow.add_edge("generate", "detect_labels")  # Always run label detection after generation
    workflow.add_edge("detect_labels", "validate")
    
    # Conditional edge to check if LLM validation should be skipped
    def should_run_llm_validation(state: SurveyGenerationState) -> str:
        """
        Check if LLM-based validation should be run based on settings or generation errors
        """
        try:
            logger.info(f"🔍 [Workflow] should_run_llm_validation called - error_message: {state.error_message}, generated_survey: {bool(state.generated_survey)}")
            
            # First check if generation failed - if so, skip validation
            if state.error_message:
                logger.info(f"🔍 [Workflow] Generation failed with error: {state.error_message}, skipping validation")
                return "completion_handler"
            
            # Check if no survey was generated - if so, skip validation
            if not state.generated_survey:
                logger.info("🔍 [Workflow] No survey generated, skipping validation")
                return "completion_handler"
            
            from src.services.settings_service import SettingsService
            from src.database import get_db
            
            # Get evaluation settings
            db = next(get_db())
            settings_service = SettingsService(db)
            evaluation_settings = settings_service.get_evaluation_settings()
            
            enable_llm_evaluation = evaluation_settings.get('enable_llm_evaluation', True)
            
            if not enable_llm_evaluation:
                logger.info(f"⏭️ [Workflow] LLM evaluation disabled, running basic validation only")
                return "validate"  # Still run validation but with basic mode
            else:
                logger.info(f"✅ [Workflow] LLM evaluation enabled, running full validation")
                return "validate"
        except Exception as e:
            logger.error(f"❌ [Workflow] Error checking evaluation settings: {e}")
            # Default to validation if there's an error
            return "validate"

    # Add conditional edge to check if validation should be skipped
    workflow.add_conditional_edges(
        "detect_labels",
        should_run_llm_validation,
        {
            "validate": "validate",
            "completion_handler": "completion_handler"
        }
    )
    
    # Add a pause node for human review
    async def pause_for_review(state: SurveyGenerationState) -> Dict[str, Any]:
        """Pause point for human review - workflow will be resumed externally"""
        logger.info(f"⏸️ [Workflow] pause_for_review called for workflow: {state.workflow_id}")
        logger.info(f"⏸️ [Workflow] State pending_human_review: {getattr(state, 'pending_human_review', False)}")
        logger.info(f"⏸️ [Workflow] State workflow_paused: {getattr(state, 'workflow_paused', False)}")
        logger.info(f"⏸️ [Workflow] State review_id: {getattr(state, 'review_id', None)}")
        
        # Update the state to reflect that the workflow is paused
        state.workflow_paused = True
        state.pending_human_review = True
        
        result = {
            "workflow_paused": True,
            "pending_human_review": True,
            "pause_reason": "human_review_required",
            "error_message": None
        }
        
        logger.info(f"⏸️ [Workflow] pause_for_review returning: {result}")
        logger.info(f"⏸️ [Workflow] Workflow paused at human review step - waiting for external resume")
        
        # CRITICAL: This is where the workflow should actually pause
        # The workflow will be resumed externally when human review is completed
        # We need to raise an exception to actually stop execution
        raise Exception("WORKFLOW_PAUSED_FOR_HUMAN_REVIEW")
    
    workflow.add_node("pause_for_review", pause_for_review)
    
    # Conditional edge for prompt review - determines if workflow should pause or continue
    def should_continue_after_review(state: SurveyGenerationState) -> str:
        """
        Determine if workflow should continue to generation or pause for human review
        """
        logger.info(f"🔍 [Workflow] should_continue_after_review called for workflow: {getattr(state, 'workflow_id', 'unknown')}")
        logger.info(f"🔍 [Workflow] State error_message: {getattr(state, 'error_message', None)}")
        logger.info(f"🔍 [Workflow] State pending_human_review: {getattr(state, 'pending_human_review', False)}")
        logger.info(f"🔍 [Workflow] State workflow_paused: {getattr(state, 'workflow_paused', False)}")
        logger.info(f"🔍 [Workflow] State prompt_approved: {getattr(state, 'prompt_approved', False)}")
        logger.info(f"🔍 [Workflow] State review_id: {getattr(state, 'review_id', None)}")

        if state.error_message:
            logger.info(f"🔄 [Workflow] Error detected, routing to completion_handler")
            return "completion_handler"  # Error occurred, send to completion

        # Check if prompt has been explicitly approved (resume from human review)
        if getattr(state, 'prompt_approved', False):
            logger.info(f"✅ [Workflow] Prompt approved, routing to generate")
            return "generate"  # Continue to generation

        # Check if human review is pending (blocking mode)
        if getattr(state, 'pending_human_review', False):
            logger.info(f"⏸️ [Workflow] Human review pending, routing to pause_for_review")
            # In blocking mode, workflow should pause here
            # The workflow will be resumed externally when review is completed
            return "pause_for_review"  # Pause workflow

        # Non-blocking mode or review disabled - continue to generation
        logger.info(f"🚀 [Workflow] No human review needed, routing to generate")
        return "generate"
    
    # Add conditional edge for prompt review
    workflow.add_conditional_edges(
        "prompt_review",
        should_continue_after_review,
        {
            "generate": "generate",
            "completion_handler": "completion_handler",
            "pause_for_review": "pause_for_review"
        }
    )
    
    # Conditional edge for validation with retry logic
    def should_retry(state: SurveyGenerationState) -> str:
        """
        Determine if we should retry generation or proceed to completion
        RETRIES DISABLED: Always route to completion_handler
        """
        logger.info(f"🔄 [Workflow] should_retry called - retry_count: {state.retry_count}, max_retries: {state.max_retries}, quality_gate_passed: {state.quality_gate_passed}")
        
        # RETRIES DISABLED: Always route to completion_handler
        logger.info(f"🚫 [Workflow] Retries disabled - routing to completion_handler")
        return "completion_handler"
    
    workflow.add_conditional_edges(
        "validate",
        should_retry,
        {
            "generate": "generate",
            "completion_handler": "completion_handler"
        }
    )

    # Completion handler to send proper WebSocket messages
    async def completion_handler(state: SurveyGenerationState) -> Dict[str, Any]:
        """Handle workflow completion and send appropriate WebSocket messages"""
        progress_tracker = get_progress_tracker(state.workflow_id)
        
        try:
            from src.services.websocket_client import WebSocketNotificationService
            ws_client = WebSocketNotificationService()

            # Check if workflow was paused (human review required)
            if state.workflow_paused or state.pending_human_review:
                logger.info(f"⏸️ [Workflow] Workflow paused for human review: {state.workflow_id}")
                # The pause message was already sent by prompt_review_with_progress
                return {"workflow_completed": False, "workflow_paused": True}
            elif state.error_message:
                # Workflow completed with error
                logger.error(f"❌ [Workflow] Workflow completed with error: {state.workflow_id} - {state.error_message}")
                progress_data = progress_tracker.get_completion_data("completed")
                progress_data["message"] = f"Survey generation failed: {state.error_message}"
                progress_data["error"] = True
                await ws_client.send_progress_update(state.workflow_id, progress_data)
                return {"workflow_completed": True, "workflow_paused": False, "error": True}
            else:
                # Workflow completed normally
                logger.info(f"✅ [Workflow] Workflow completed successfully: {state.workflow_id}")
                progress_data = progress_tracker.get_completion_data("completed")
                progress_data["message"] = "Survey generation completed successfully!"
                await ws_client.send_progress_update(state.workflow_id, progress_data)
                return {"workflow_completed": True, "workflow_paused": False}
        except Exception as e:
            logger.error(f"❌ [Workflow] Error in completion handler: {str(e)}")
            return {"workflow_completed": True, "workflow_paused": False, "error": True}

    workflow.add_node("completion_handler", completion_handler)

    # pause_for_review should not have outgoing edges - workflow pauses here
    # The workflow will be resumed externally when human review is completed

    # Note: generate -> validate is already defined above (line 285)

    # Set end points - both completion_handler and pause_for_review are valid end points
    workflow.set_finish_point("completion_handler")
    workflow.set_finish_point("pause_for_review")
    
    return workflow.compile()