from sqlalchemy.orm import Session
from src.database import RFQ, Survey
from src.workflows import create_workflow, SurveyGenerationState
from src.services.embedding_service import EmbeddingService
from src.config import settings
from typing import Optional
from uuid import uuid4
from pydantic import BaseModel


class WorkflowResult(BaseModel):
    survey_id: str
    estimated_completion_time: int
    golden_examples_used: int
    status: str


class WorkflowService:
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService()
        self.workflow = create_workflow(db)
    
    async def process_rfq(
        self,
        title: Optional[str],
        description: str,
        product_category: Optional[str],
        target_segment: Optional[str],
        research_goal: Optional[str]
    ) -> WorkflowResult:
        """
        Process RFQ through the complete LangGraph workflow
        """
        # Create RFQ record
        rfq = RFQ(
            title=title,
            description=description,
            product_category=product_category,
            target_segment=target_segment,
            research_goal=research_goal
        )
        self.db.add(rfq)
        self.db.commit()
        self.db.refresh(rfq)
        
        # Create initial survey record
        survey = Survey(
            rfq_id=rfq.id,
            status="draft",
            model_version=settings.generation_model
        )
        self.db.add(survey)
        self.db.commit()
        self.db.refresh(survey)
        
        # Initialize workflow state
        initial_state = SurveyGenerationState(
            rfq_id=rfq.id,  # type: ignore
            rfq_text=description,
            rfq_title=title,
            product_category=product_category,
            target_segment=target_segment,
            research_goal=research_goal
        )
        
        try:
            # Execute workflow
            final_state = await self.workflow.ainvoke(initial_state)
            
            # Update survey with results (final_state is a dict from LangGraph)
            survey.raw_output = final_state.get("raw_survey")
            survey.final_output = final_state.get("generated_survey")
            survey.golden_similarity_score = final_state.get("golden_similarity_score")
            survey.used_golden_examples = final_state.get("used_golden_examples", [])
            survey.status = "validated" if final_state.get("quality_gate_passed", False) else "draft"
            
            self.db.commit()
            
            return WorkflowResult(
                survey_id=str(survey.id),
                estimated_completion_time=30,  # TODO: Calculate based on complexity
                golden_examples_used=len(final_state.get("used_golden_examples", [])),
                status=survey.status
            )
            
        except Exception as e:
            # Update survey with error
            survey.status = "draft"  # type: ignore
            self.db.commit()
            
            raise Exception(f"Workflow execution failed: {str(e)}")