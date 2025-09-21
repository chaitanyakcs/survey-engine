from langgraph.graph import StateGraph
from sqlalchemy.orm import Session
from typing import Any, Dict
from .state import SurveyGenerationState
from .nodes import (
    RFQNode,
    GoldenRetrieverNode,
    ContextBuilderNode,
    GeneratorAgent,
    GoldenValidatorNode,
    HumanPromptReviewNode
)
from src.services.websocket_client import WebSocketNotificationService
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
    generator = GeneratorAgent(db)
    validator = GoldenValidatorNode(db)
    
    # Initialize WebSocket client for progress updates
    ws_client = WebSocketNotificationService(connection_manager)
    
    # Create wrapper functions that send progress updates
    async def parse_rfq_with_progress(state: SurveyGenerationState) -> Dict[str, Any]:
        """Parse RFQ with progress update"""
        try:
            logger.info(f"📡 [Workflow] Sending progress update: parsing_rfq for workflow_id={state.workflow_id}")
            await ws_client.send_progress_update(state.workflow_id, {
                "type": "progress",
                "step": "parsing_rfq",
                "percent": 10,
                "message": "Parsing RFQ and analyzing requirements..."
            })
            logger.info(f"✅ [Workflow] Progress update sent successfully: parsing_rfq")
        except Exception as e:
            logger.error(f"❌ [Workflow] Failed to send progress update: {str(e)}")
        
        # Send additional progress update for embedding generation
        try:
            logger.info(f"📡 [Workflow] Sending progress update: generating_embeddings for workflow_id={state.workflow_id}")
            await ws_client.send_progress_update(state.workflow_id, {
                "type": "progress",
                "step": "generating_embeddings",
                "percent": 15,
                "message": "Generating embeddings for semantic search..."
            })
            logger.info(f"✅ [Workflow] Progress update sent successfully: generating_embeddings")
        except Exception as e:
            logger.error(f"❌ [Workflow] Failed to send embedding progress update: {str(e)}")
        
        result = await rfq_node(state)
        
        # Send completion progress update
        try:
            logger.info(f"📡 [Workflow] Sending progress update: rfq_parsed for workflow_id={state.workflow_id}")
            await ws_client.send_progress_update(state.workflow_id, {
                "type": "progress",
                "step": "rfq_parsed",
                "percent": 20,
                "message": "RFQ analysis completed, starting golden example retrieval..."
            })
            logger.info(f"✅ [Workflow] Progress update sent successfully: rfq_parsed")
        except Exception as e:
            logger.error(f"❌ [Workflow] Failed to send RFQ completion progress update: {str(e)}")
        
        return result
    
    async def retrieve_golden_with_progress(state: SurveyGenerationState) -> Dict[str, Any]:
        """Retrieve golden examples with progress update"""
        try:
            logger.info(f"📡 [Workflow] Sending progress update: matching_golden_examples for workflow_id={state.workflow_id}")
            await ws_client.send_progress_update(state.workflow_id, {
                "type": "progress",
                "step": "matching_golden_examples",
                "percent": 25,
                "message": "Finding templates and matching relevant examples..."
            })
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
                    logger.info(f"📋 [Workflow] Example {i+1}: {example.get('rfq_text', 'No text')[:50]}... (Score: {example.get('similarity_score', 'N/A')})")
            return result
        except Exception as e:
            logger.error(f"❌ [Workflow] Golden pairs retrieval failed: {str(e)}", exc_info=True)
            raise
    
    async def build_context_with_progress(state: SurveyGenerationState) -> Dict[str, Any]:
        """Build context with progress update"""
        try:
            logger.info(f"📡 [Workflow] Sending progress update: planning_methodologies for workflow_id={state.workflow_id}")
            await ws_client.send_progress_update(state.workflow_id, {
                "type": "progress",
                "step": "planning_methodologies",
                "percent": 40,
                "message": "Planning methods and selecting research approaches..."
            })
            logger.info(f"✅ [Workflow] Progress update sent successfully: planning_methodologies")
        except Exception as e:
            logger.error(f"❌ [Workflow] Failed to send progress update: {str(e)}")
        
        return await context_builder(state)
    
    async def prompt_review_with_progress(state: SurveyGenerationState) -> Dict[str, Any]:
        """Human prompt review with progress update"""
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
                await ws_client.send_progress_update(state.workflow_id, {
                    "type": "progress",
                    "step": "preparing_generation",
                    "percent": 50,
                    "message": "Preparing survey generation..."
                })
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
            logger.info(f"📡 [Workflow] Sending progress update: human_review for workflow_id={state.workflow_id}")
            await ws_client.send_progress_update(state.workflow_id, {
                "type": "progress",
                "step": "human_review",
                "percent": 50,
                "message": "Reviewing AI-generated system prompt..."
            })
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
                    logger.info(f"🛑 [Workflow] Sending human review required message for workflow_id={state.workflow_id}")
                    await ws_client.send_progress_update(state.workflow_id, {
                        "type": "human_review_required",
                        "step": "human_review",
                        "percent": 50,
                        "message": "Waiting for human review of system prompt...",
                        "review_id": result.get('review_id'),
                        "workflow_paused": True
                    })
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
        try:
            logger.info(f"📡 [Workflow] Sending progress update: generating_questions for workflow_id={state.workflow_id}")
            await ws_client.send_progress_update(state.workflow_id, {
                "type": "progress",
                "step": "generating_questions",
                "percent": 60,
                "message": "Creating questions and generating survey content..."
            })
            logger.info(f"✅ [Workflow] Progress update sent successfully: generating_questions")
        except Exception as e:
            logger.error(f"❌ [Workflow] Failed to send progress update: {str(e)}")
        
        logger.info("🚀 [Workflow] About to call GeneratorAgent...")
        logger.info(f"📊 [Workflow] State before generation - context: {bool(state.context)}, golden_examples: {len(state.golden_examples) if state.golden_examples else 0}")
        
        result = await generator(state)
        
        logger.info(f"📊 [Workflow] GeneratorAgent result keys: {list(result.keys()) if result else 'None'}")
        logger.info(f"📊 [Workflow] GeneratorAgent error_message: {result.get('error_message', 'None') if result else 'None'}")
        
        return result
    
    async def validate_with_progress(state: SurveyGenerationState) -> Dict[str, Any]:
        """Validate survey with progress update"""
        try:
            logger.info(f"📡 [Workflow] Sending progress update: validation_scoring for workflow_id={state.workflow_id}")
            await ws_client.send_progress_update(state.workflow_id, {
                "type": "progress",
                "step": "validation_scoring",
                "percent": 80,
                "message": "Running comprehensive evaluations and quality assessments..."
            })
            logger.info(f"✅ [Workflow] Progress update sent successfully: validation_scoring")
        except Exception as e:
            logger.error(f"❌ [Workflow] Failed to send progress update: {str(e)}")
        
        return await validator(state)
    
    
    # Add nodes to workflow
    workflow.add_node("parse_rfq", parse_rfq_with_progress)
    workflow.add_node("retrieve_golden", retrieve_golden_with_progress)
    workflow.add_node("build_context", build_context_with_progress)
    workflow.add_node("prompt_review", prompt_review_with_progress)
    workflow.add_node("generate", generate_with_progress)
    workflow.add_node("validate", validate_with_progress)
    
    # Set entry point
    workflow.set_entry_point("parse_rfq")
    
    # Add sequential edges
    workflow.add_edge("parse_rfq", "retrieve_golden")
    workflow.add_edge("retrieve_golden", "build_context")
    workflow.add_edge("build_context", "prompt_review")
    workflow.add_edge("generate", "validate")
    
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
        """
        import time
        
        logger.info(f"🔄 [Workflow] should_retry called - retry_count: {state.retry_count}, max_retries: {state.max_retries}, quality_gate_passed: {state.quality_gate_passed}")
        
        # CRITICAL SAFEGUARD: Prevent infinite loops
        # If we've been retrying for more than 5 minutes, force completion
        if hasattr(state, 'workflow_start_time'):
            elapsed_time = time.time() - state.workflow_start_time
            if elapsed_time > 300:  # 5 minutes
                logger.error(f"❌ [Workflow] SAFEGUARD TRIGGERED: Workflow running for {elapsed_time:.1f}s, forcing completion to prevent infinite loop")
                return "completion_handler"
        
        if state.error_message:
            logger.info(f"🔄 [Workflow] Error detected, routing to completion_handler")
            return "completion_handler"  # Send to completion on error
            
        if not state.quality_gate_passed:
            if state.retry_count < state.max_retries:
                logger.info(f"🔄 [Workflow] Quality gate failed, retrying generation (attempt {state.retry_count + 1}/{state.max_retries})")
                return "generate"  # Retry generation
            else:
                logger.warning(f"⚠️ [Workflow] Max retries ({state.max_retries}) reached, completing workflow")
                return "completion_handler"  # Max retries reached, complete workflow
        
        logger.info(f"✅ [Workflow] Quality gate passed, routing to completion_handler")
        return "completion_handler"  # Quality gate passed, ready for completion
    
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
        try:
            from src.services.websocket_client import WebSocketNotificationService
            ws_client = WebSocketNotificationService()

            # Check if workflow was paused (human review required)
            if state.workflow_paused or state.pending_human_review:
                logger.info(f"⏸️ [Workflow] Workflow paused for human review: {state.workflow_id}")
                # The pause message was already sent by prompt_review_with_progress
                return {"workflow_completed": False, "workflow_paused": True}
            else:
                # Workflow completed normally
                logger.info(f"✅ [Workflow] Workflow completed successfully: {state.workflow_id}")
                await ws_client.send_progress_update(state.workflow_id, {
                    "type": "progress",
                    "step": "completed",
                    "percent": 100,
                    "message": "Survey generation completed successfully!"
                })
                return {"workflow_completed": True, "workflow_paused": False}
        except Exception as e:
            logger.error(f"❌ [Workflow] Error in completion handler: {str(e)}")
            return {"workflow_completed": True, "workflow_paused": False, "error_message": str(e)}

    workflow.add_node("completion_handler", completion_handler)

    # pause_for_review should not have outgoing edges - workflow pauses here
    # The workflow will be resumed externally when human review is completed

    # Route from generate to completion_handler
    workflow.add_edge("generate", "completion_handler")

    # Set end points - both completion_handler and pause_for_review are valid end points
    workflow.set_finish_point("completion_handler")
    workflow.set_finish_point("pause_for_review")
    
    return workflow.compile()