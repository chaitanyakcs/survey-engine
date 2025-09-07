from sqlalchemy.orm import Session
from src.database import RFQ, Survey
from src.workflows import create_workflow, SurveyGenerationState
from src.services.embedding_service import EmbeddingService
from src.services.websocket_client import WebSocketNotificationService
from src.config import settings
from typing import Optional
from uuid import uuid4
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class WorkflowResult(BaseModel):
    survey_id: str
    estimated_completion_time: int
    golden_examples_used: int
    status: str


class WorkflowService:
    def __init__(self, db: Session):
        logger.info("🔧 [WorkflowService] Initializing workflow service")
        try:
            self.db = db
            logger.info("🔧 [WorkflowService] Database session assigned successfully")
            
            logger.info("🔧 [WorkflowService] Creating embedding service")
            self.embedding_service = EmbeddingService()
            logger.info("✅ [WorkflowService] EmbeddingService created successfully")
            
            logger.info("🔧 [WorkflowService] Creating WebSocket notification service")
            self.ws_client = WebSocketNotificationService()
            logger.info("✅ [WorkflowService] WebSocketNotificationService created successfully")
            
            logger.info("🔧 [WorkflowService] Creating LangGraph workflow")
            self.workflow = create_workflow(db)
            logger.info("✅ [WorkflowService] LangGraph workflow created successfully")
            
            logger.info("✅ [WorkflowService] Workflow service initialized successfully")
        except Exception as e:
            logger.error(f"❌ [WorkflowService] Failed to initialize workflow service: {str(e)}", exc_info=True)
            raise Exception(f"WorkflowService initialization failed: {str(e)}")
    
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
        logger.info(f"📝 [WorkflowService] Starting RFQ processing: title='{title}', description_length={len(description)}")
        
        # Create RFQ record
        logger.info("💾 [WorkflowService] Creating RFQ database record")
        try:
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
            logger.info(f"✅ [WorkflowService] RFQ record created with ID: {rfq.id}")
        except Exception as e:
            logger.error(f"❌ [WorkflowService] Failed to create RFQ record: {str(e)}", exc_info=True)
            raise Exception(f"Database error while creating RFQ: {str(e)}")
        
        # Create initial survey record
        logger.info("💾 [WorkflowService] Creating initial Survey database record")
        try:
            survey = Survey(
                rfq_id=rfq.id,
                status="started",
                model_version=settings.generation_model
            )
            self.db.add(survey)
            self.db.commit()
            self.db.refresh(survey)
            logger.info(f"✅ [WorkflowService] Survey record created with ID: {survey.id}")
        except Exception as e:
            logger.error(f"❌ [WorkflowService] Failed to create Survey record: {str(e)}", exc_info=True)
            raise Exception(f"Database error while creating Survey: {str(e)}")
        
        # Initialize workflow state
        logger.info("🔄 [WorkflowService] Initializing workflow state")
        initial_state = SurveyGenerationState(
            rfq_id=rfq.id,  # type: ignore
            rfq_text=description,
            rfq_title=title,
            product_category=product_category,
            target_segment=target_segment,
            research_goal=research_goal,
            workflow_id=f"survey-gen-{survey.id}",
            survey_id=str(survey.id)
        )
        logger.info(f"📋 [WorkflowService] Workflow state initialized: workflow_id={initial_state.workflow_id}, survey_id={initial_state.survey_id}")
        
        try:
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
            survey.raw_output = final_state.get("raw_survey")
            survey.final_output = final_state.get("generated_survey")
            survey.golden_similarity_score = final_state.get("golden_similarity_score")
            survey.used_golden_examples = final_state.get("used_golden_examples", [])
            survey.status = "validated" if final_state.get("quality_gate_passed", False) else "draft"
            
            self.db.commit()
            logger.info(f"✅ [WorkflowService] Survey record updated: status={survey.status}, golden_examples_used={len(survey.used_golden_examples)}")
            
            result = WorkflowResult(
                survey_id=str(survey.id),
                estimated_completion_time=30,  # TODO: Calculate based on complexity
                golden_examples_used=len(final_state.get("used_golden_examples", [])),
                status=survey.status
            )
            
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