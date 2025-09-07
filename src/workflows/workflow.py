from langgraph.graph import StateGraph
from sqlalchemy.orm import Session
from typing import Any
from .state import SurveyGenerationState
from .nodes import (
    RFQNode,
    GoldenRetrieverNode,
    ContextBuilderNode,
    GeneratorAgent,
    GoldenValidatorNode,
    ResearcherNode
)


def create_workflow(db: Session) -> Any:
    """
    Create the LangGraph workflow for survey generation
    """
    workflow = StateGraph(SurveyGenerationState)
    
    # Initialize nodes
    rfq_node = RFQNode(db)
    golden_retriever = GoldenRetrieverNode(db)
    context_builder = ContextBuilderNode(db)
    generator = GeneratorAgent(db)
    validator = GoldenValidatorNode(db)
    researcher = ResearcherNode(db)
    
    # Add nodes to workflow
    workflow.add_node("parse_rfq", rfq_node)
    workflow.add_node("retrieve_golden", golden_retriever)
    workflow.add_node("build_context", context_builder)
    workflow.add_node("generate", generator)
    workflow.add_node("validate", validator)
    workflow.add_node("human_review", researcher)
    
    # Set entry point
    workflow.set_entry_point("parse_rfq")
    
    # Add sequential edges
    workflow.add_edge("parse_rfq", "retrieve_golden")
    workflow.add_edge("retrieve_golden", "build_context")
    workflow.add_edge("build_context", "generate")
    workflow.add_edge("generate", "validate")
    
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
    
    # Set end point
    workflow.set_finish_point("human_review")
    
    return workflow.compile()