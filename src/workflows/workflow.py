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
    ResearcherNode,
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
    researcher = ResearcherNode(db)
    
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
        
        # If blocking review is pending, send special WebSocket message
        if result.get('pending_human_review'):
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
    
    async def human_review_with_progress(state: SurveyGenerationState) -> Dict[str, Any]:
        """Human review with progress update"""
        try:
            logger.info(f"📡 [Workflow] Sending progress update: finalizing for workflow_id={state.workflow_id}")
            await ws_client.send_progress_update(state.workflow_id, {
                "type": "progress",
                "step": "finalizing",
                "percent": 95,
                "message": "Finalizing and preparing survey..."
            })
            logger.info(f"✅ [Workflow] Progress update sent successfully: finalizing")
        except Exception as e:
            logger.error(f"❌ [Workflow] Failed to send progress update: {str(e)}")
        
        return await researcher(state)
    
    # Add nodes to workflow
    workflow.add_node("parse_rfq", parse_rfq_with_progress)
    workflow.add_node("retrieve_golden", retrieve_golden_with_progress)
    workflow.add_node("build_context", build_context_with_progress)
    workflow.add_node("prompt_review", prompt_review_with_progress)
    workflow.add_node("generate", generate_with_progress)
    workflow.add_node("validate", validate_with_progress)
    workflow.add_node("human_review", human_review_with_progress)
    
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
        return {
            "workflow_paused": True,
            "pause_reason": "human_review_required",
            "error_message": None
        }
    
    workflow.add_node("pause_for_review", pause_for_review)
    
    # Conditional edge for prompt review - determines if workflow should pause or continue
    def should_continue_after_review(state: SurveyGenerationState) -> str:
        """
        Determine if workflow should continue to generation or pause for human review
        """
        if state.error_message:
            return "human_review"  # Error occurred, send to final human review
            
        # Check if human review is pending (blocking mode)
        if getattr(state, 'pending_human_review', False):
            # In blocking mode, workflow should pause here
            # The workflow will be resumed externally when review is completed
            return "pause_for_review"  # Pause workflow
        
        # Non-blocking mode or review disabled - continue to generation
        return "generate"
    
    # Add conditional edge for prompt review
    workflow.add_conditional_edges(
        "prompt_review",
        should_continue_after_review,
        {
            "generate": "generate",
            "human_review": "human_review",
            "pause_for_review": "pause_for_review"
        }
    )
    
    # Conditional edge for validation with retry logic
    def should_retry(state: SurveyGenerationState) -> str:
        """
        Determine if we should retry generation or proceed to human review
        """
        if state.error_message:
            return "human_review"  # Send to human review on error
            
        if not state.quality_gate_passed:
            if state.retry_count < state.max_retries:
                return "generate"  # Retry generation
            else:
                return "human_review"  # Max retries reached, send to human
        
        return "human_review"  # Quality gate passed, ready for human review
    
    workflow.add_conditional_edges(
        "validate",
        should_retry,
        {
            "generate": "generate",
            "human_review": "human_review"
        }
    )
    
    # Add edge from pause_for_review to end
    workflow.add_edge("pause_for_review", "human_review")
    
    # Set end point
    workflow.set_finish_point("human_review")
    
    return workflow.compile()