"""
Human Reviews API endpoints for managing prompt review workflows
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime, timedelta
import logging
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from ..models.human_review import HumanReviewCreate, HumanReviewUpdate, HumanReviewResponse, ReviewDecision, PendingReviewsSummary, ReviewStatus
from ..database import get_db, HumanReview

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reviews", tags=["human-reviews"])


@router.post("/", response_model=HumanReviewResponse)
def create_review(
    review_data: HumanReviewCreate,
    db: Session = Depends(get_db)
):
    """Create a new human review record"""
    try:
        # Set default deadline if not provided
        deadline = review_data.review_deadline
        if deadline is None:
            deadline = datetime.utcnow() + timedelta(hours=24)
        
        # Create new review record
        db_review = HumanReview(
            workflow_id=review_data.workflow_id,
            survey_id=review_data.survey_id,
            prompt_data=review_data.prompt_data,
            original_rfq=review_data.original_rfq,
            reviewer_id=review_data.reviewer_id,
            review_deadline=deadline,
            review_status="pending"
        )
        
        db.add(db_review)
        db.commit()
        db.refresh(db_review)
        
        # Convert to response model
        return convert_to_response(db_review)
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create review: {str(e)}")
        if "duplicate key" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Review already exists for workflow_id: {review_data.workflow_id}"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create review"
        )


@router.get("/pending", response_model=PendingReviewsSummary)
def get_pending_reviews(
    limit: int = 50,
    skip: int = 0,
    db: Session = Depends(get_db)
):
    """Get all pending reviews with summary statistics"""
    try:
        # Get counts by status
        pending_count = db.query(HumanReview).filter(HumanReview.review_status == "pending").count()
        in_progress_count = db.query(HumanReview).filter(HumanReview.review_status == "in_progress").count()
        
        # Count expired reviews (past deadline)
        now = datetime.utcnow()
        expired_count = db.query(HumanReview).filter(
            and_(
                HumanReview.review_status.in_(["pending", "in_progress"]),
                HumanReview.review_deadline < now
            )
        ).count()
        
        # Get oldest pending review date
        oldest_pending = db.query(HumanReview).filter(
            HumanReview.review_status == "pending"
        ).order_by(HumanReview.created_at).first()
        
        oldest_pending_date = oldest_pending.created_at if oldest_pending else None
        
        # Get recent reviews (pending, in_progress, or recently completed)
        reviews = db.query(HumanReview).filter(
            HumanReview.review_status.in_(["pending", "in_progress", "approved", "rejected"])
        ).order_by(desc(HumanReview.created_at)).offset(skip).limit(limit).all()
        
        # Convert to response models
        review_responses = [convert_to_response(review) for review in reviews]
        
        return PendingReviewsSummary(
            total_pending=pending_count,
            total_in_progress=in_progress_count,
            total_expired=expired_count,
            oldest_pending=oldest_pending_date,
            reviews=review_responses
        )
        
    except Exception as e:
        logger.error(f"Failed to get pending reviews: {str(e)}")
        # If table doesn't exist or other DB errors, return empty result instead of 500
        # This prevents 404/500 errors when the table hasn't been created yet
        if "does not exist" in str(e).lower() or "relation" in str(e).lower():
            logger.warning("HumanReview table does not exist yet, returning empty results")
            return PendingReviewsSummary(
                total_pending=0,
                total_in_progress=0,
                total_expired=0,
                oldest_pending=None,
                reviews=[]
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pending reviews"
        )


@router.get("/workflow/{workflow_id}", response_model=HumanReviewResponse)
def get_review_by_workflow(
    workflow_id: str,
    db: Session = Depends(get_db)
):
    """Get review by workflow ID"""
    try:
        review = db.query(HumanReview).filter(HumanReview.workflow_id == workflow_id).first()
        
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No review found for workflow_id: {workflow_id}"
            )
        
        return convert_to_response(review)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get review by workflow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve review"
        )


@router.post("/{review_id}/decision")
async def submit_review_decision(
    review_id: int,
    decision: ReviewDecision,
    db: Session = Depends(get_db)
):
    """Submit a review decision (approve/reject)"""
    try:
        review = db.query(HumanReview).filter(HumanReview.id == review_id).first()
        
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Review not found: {review_id}"
            )
        
        if review.review_status not in ["pending", "in_progress"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Review is already {review.review_status}"
            )
        
        # Update review based on decision
        if decision.decision == "approve":
            review.review_status = "approved"
            review.approval_reason = decision.reason or "Approved by reviewer"

            # Resume workflow if it was paused for this review
            await resume_paused_workflow(review.workflow_id, db)

        else:
            review.review_status = "rejected"
            review.rejection_reason = decision.reason or "Rejected by reviewer"

            # Cancel workflow if rejected
            await cancel_paused_workflow(review.workflow_id, db, decision.reason)

        review.reviewer_notes = decision.notes
        review.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(review)

        return convert_to_response(review)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to submit review decision: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit review decision"
        )


@router.put("/{review_id}/resume")
def resume_review(
    review_id: int,
    db: Session = Depends(get_db)
):
    """Resume a review (mark as in_progress)"""
    try:
        review = db.query(HumanReview).filter(HumanReview.id == review_id).first()
        
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Review not found: {review_id}"
            )
        
        if review.review_status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Review is already {review.review_status}"
            )
        
        review.review_status = "in_progress"
        review.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(review)
        
        return convert_to_response(review)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to resume review: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resume review"
        )


def _validate_workflow_resume(workflow_id: str, db: Session) -> bool:
    """Validate that a workflow can be safely resumed"""
    try:
        from src.database.models import Survey, RFQ, HumanReview
        
        # Check if workflow_id format is valid
        if not workflow_id.startswith('survey-gen-'):
            logger.error(f"❌ [HumanReview] Invalid workflow_id format: {workflow_id}")
            return False
        
        # First, find the human review to get the survey_id
        review = db.query(HumanReview).filter(HumanReview.workflow_id == workflow_id).first()
        if not review:
            logger.error(f"❌ [HumanReview] No human review found for workflow {workflow_id}")
            return False
        
        if review.review_status != 'approved':
            logger.error(f"❌ [HumanReview] Human review is not approved: {review.review_status}")
            return False
        
        # Use the survey_id from the review record instead of extracting from workflow_id
        if not review.survey_id:
            logger.error(f"❌ [HumanReview] No survey_id in review record for workflow {workflow_id}")
            return False
        
        # Convert survey_id string to UUID for database lookup
        import uuid
        try:
            survey_uuid_obj = uuid.UUID(review.survey_id)
            survey = db.query(Survey).filter(Survey.id == survey_uuid_obj).first()
        except ValueError:
            logger.error(f"❌ [HumanReview] Invalid survey_id format in review: {review.survey_id}")
            return False
        
        if not survey:
            logger.error(f"❌ [HumanReview] No survey found with ID {review.survey_id} for workflow {workflow_id}")
            return False
        
        # Check if survey is in a resumable state
        if survey.status not in ['draft', 'pending', 'started']:
            logger.error(f"❌ [HumanReview] Survey {survey.id} is in non-resumable state: {survey.status}")
            return False
        
        # Check if RFQ exists
        rfq = db.query(RFQ).filter(RFQ.id == survey.rfq_id).first()
        if not rfq:
            logger.error(f"❌ [HumanReview] No RFQ found for survey {survey.id}")
            return False
        
        logger.info(f"✅ [HumanReview] Workflow validation passed for {workflow_id} (survey: {survey.id})")
        return True
        
    except Exception as e:
        logger.error(f"❌ [HumanReview] Workflow validation failed: {str(e)}")
        return False


async def resume_paused_workflow(workflow_id: str, db: Session):
    """Resume a paused workflow after human review approval"""
    try:
        logger.info(f"🔄 [HumanReview] Resuming workflow: {workflow_id}")
        
        # Validate workflow can be resumed
        if not _validate_workflow_resume(workflow_id, db):
            raise Exception("Workflow validation failed - cannot resume")

        # Import workflow service to resume the workflow
        from src.services.workflow_service import WorkflowService
        from src.workflows.state import SurveyGenerationState
        from src.database.models import Survey, RFQ
        from src.services.websocket_client import WebSocketNotificationService

        # Find the survey associated with this workflow using the review record
        if workflow_id.startswith('survey-gen-'):
            # Get the review record to find the survey_id
            review = db.query(HumanReview).filter(HumanReview.workflow_id == workflow_id).first()
            if not review or not review.survey_id:
                logger.error(f"❌ [HumanReview] No review or survey_id found for workflow {workflow_id}")
                return
            
            # Convert survey_id string to UUID for database lookup
            import uuid
            try:
                survey_uuid_obj = uuid.UUID(review.survey_id)
                survey = db.query(Survey).filter(Survey.id == survey_uuid_obj).first()
            except ValueError:
                logger.error(f"❌ [HumanReview] Invalid survey_id format in review: {review.survey_id}")
                return

            if survey:
                logger.info(f"📊 [HumanReview] Found survey {survey.id} for workflow {workflow_id}")

                # Get the RFQ data
                rfq = db.query(RFQ).filter(RFQ.id == survey.rfq_id).first()
                if not rfq:
                    logger.error(f"❌ [HumanReview] No RFQ found for survey {survey.id}")
                    return

                # Send notification that workflow is resuming
                from src.main import manager  # Import the connection manager
                ws_client = WebSocketNotificationService(manager)
                await ws_client.send_progress_update(workflow_id, {
                    "type": "progress",
                    "step": "resuming_generation",
                    "percent": 60,
                    "message": "Human review approved - resuming survey generation..."
                })

                # Try to load saved workflow state first
                from src.services.workflow_state_service import WorkflowStateService
                state_service = WorkflowStateService(db)
                saved_state = state_service.load_workflow_state(workflow_id)
                
                if saved_state:
                    logger.info(f"📂 [HumanReview] Loaded saved workflow state for {workflow_id}")
                    # Update the saved state to skip human review and continue from generation
                    saved_state.pending_human_review = False
                    saved_state.workflow_paused = False
                    # Mark that human review is already completed
                    saved_state.review_id = None
                    initial_state = saved_state
                else:
                    logger.info(f"📝 [HumanReview] No saved state found, creating new state for {workflow_id}")
                    # Create a new workflow state that will skip human review
                    initial_state = SurveyGenerationState(
                        workflow_id=workflow_id,
                        survey_id=str(survey.id),
                        rfq_id=str(survey.rfq_id),
                        rfq_text=rfq.description,
                        rfq_title=rfq.title,
                        product_category=rfq.product_category,
                        target_segment=rfq.target_segment,
                        research_goal=rfq.research_goal,
                        # Mark that human review is already approved - this will skip human review
                        pending_human_review=False,
                        workflow_paused=False,
                        review_id=None
                    )

                # Instead of restarting the entire workflow, directly execute the remaining steps
                # This avoids going through the human review step again
                try:
                    # Use the workflow service to execute from generation step
                    from src.services.workflow_service import WorkflowService
                    workflow_service = WorkflowService(db, manager)
                    
                    # Send notification that workflow is about to resume
                    await ws_client.send_progress_update(workflow_id, {
                        "type": "workflow_resuming",
                        "step": "resuming_generation",
                        "percent": 60,
                        "message": "Human review approved - resuming survey generation...",
                        "workflow_paused": False,
                        "pending_human_review": False
                    })

                    # Execute the remaining workflow steps directly
                    asyncio.create_task(
                        workflow_service.execute_workflow_from_generation(
                            initial_state, 
                            workflow_id, 
                            str(survey.id),
                            ws_client
                        )
                    )

                    logger.info(f"✅ [HumanReview] Workflow {workflow_id} resumed successfully")
                    
                except Exception as workflow_error:
                    logger.error(f"❌ [HumanReview] Failed to create workflow service: {str(workflow_error)}")
                    
                    # Send error notification
                    await ws_client.send_progress_update(workflow_id, {
                        "type": "error",
                        "message": f"Failed to resume workflow: {str(workflow_error)}"
                    })
                    
                    # Update survey status to failed
                    survey.status = "failed"
                    db.commit()
                    
                    raise Exception(f"Workflow resume failed: {str(workflow_error)}")
            else:
                logger.warning(f"⚠️ [HumanReview] No survey found for workflow {workflow_id}")
        else:
            logger.warning(f"⚠️ [HumanReview] Invalid workflow_id format: {workflow_id}")

    except Exception as e:
        logger.error(f"❌ [HumanReview] Failed to resume workflow {workflow_id}: {str(e)}")


# Removed duplicate _execute_workflow_from_generation function - now using workflow_service.execute_workflow_from_generation


async def _execute_workflow_with_error_handling(workflow_service, initial_state, workflow_id: str, survey_id: str, ws_client, db):
    """Execute workflow with comprehensive error handling and recovery"""
    try:
        logger.info(f"🚀 [HumanReview] Starting workflow execution with error handling for {workflow_id}")
        
        # Execute the workflow
        result = await workflow_service._execute_workflow_with_circuit_breaker(
            title=initial_state.rfq_title,
            description=initial_state.rfq_text,
            product_category=initial_state.product_category,
            target_segment=initial_state.target_segment,
            research_goal=initial_state.research_goal,
            workflow_id=workflow_id,
            survey_id=survey_id
        )
        
        logger.info(f"✅ [HumanReview] Workflow execution completed successfully for {workflow_id}")
        return result
        
    except Exception as e:
        logger.error(f"❌ [HumanReview] Workflow execution failed for {workflow_id}: {str(e)}")
        
        # Send error notification to frontend
        try:
            await ws_client.send_progress_update(workflow_id, {
                "type": "error",
                "message": f"Survey generation failed: {str(e)}"
            })
        except Exception as ws_error:
            logger.error(f"❌ [HumanReview] Failed to send error notification: {str(ws_error)}")
        
        # Update survey status to failed
        try:
            from src.database.models import Survey
            survey = db.query(Survey).filter(Survey.id == survey_id).first()
            if survey:
                survey.status = "failed"
                db.commit()
                logger.info(f"📊 [HumanReview] Updated survey {survey_id} status to failed")
        except Exception as db_error:
            logger.error(f"❌ [HumanReview] Failed to update survey status: {str(db_error)}")
        
        # Re-raise the original exception
        raise e


async def cancel_paused_workflow(workflow_id: str, db: Session, reason: Optional[str] = None):
    """Cancel a paused workflow after human review rejection"""
    try:
        logger.info(f"🛑 [HumanReview] Cancelling workflow: {workflow_id}, reason: {reason}")

        # Mark associated survey as failed
        from src.database.models import Survey

        if workflow_id.startswith('survey-gen-'):
            # Get the review record to find the survey_id
            review = db.query(HumanReview).filter(HumanReview.workflow_id == workflow_id).first()
            if not review or not review.survey_id:
                logger.error(f"❌ [HumanReview] No review or survey_id found for workflow {workflow_id}")
                return
            
            # Convert survey_id string to UUID for database lookup
            import uuid
            try:
                survey_uuid_obj = uuid.UUID(review.survey_id)
                survey = db.query(Survey).filter(Survey.id == survey_uuid_obj).first()
            except ValueError:
                logger.error(f"❌ [HumanReview] Invalid survey_id format in review: {review.survey_id}")
                return

            if survey:
                survey.status = "failed"
                db.commit()
                logger.info(f"📊 [HumanReview] Survey {survey.id} marked as failed due to review rejection")

                # Send failure notification via WebSocket
                from src.services.websocket_client import WebSocketNotificationService
                ws_client = WebSocketNotificationService()
                await ws_client.notify_workflow_error(
                    workflow_id,
                    f"Workflow cancelled due to human review rejection: {reason or 'No reason provided'}"
                )

                logger.info(f"✅ [HumanReview] Workflow {workflow_id} cancelled successfully")
            else:
                logger.warning(f"⚠️ [HumanReview] No survey found for workflow {workflow_id}")

    except Exception as e:
        logger.error(f"❌ [HumanReview] Failed to cancel workflow {workflow_id}: {str(e)}")


def convert_to_response(review: HumanReview) -> HumanReviewResponse:
    """Convert SQLAlchemy model to Pydantic response model"""
    # Calculate expiration status
    is_expired = False
    time_remaining_hours = None
    
    if review.review_deadline:
        now = datetime.utcnow()
        is_expired = now > review.review_deadline
        if not is_expired:
            time_diff = review.review_deadline - now
            time_remaining_hours = time_diff.total_seconds() / 3600
        else:
            time_remaining_hours = 0
    
    return HumanReviewResponse(
        id=review.id,
        workflow_id=review.workflow_id,
        survey_id=review.survey_id,
        review_status=ReviewStatus(review.review_status),
        prompt_data=review.prompt_data,
        original_rfq=review.original_rfq,
        reviewer_id=review.reviewer_id,
        review_deadline=review.review_deadline,
        reviewer_notes=review.reviewer_notes,
        approval_reason=review.approval_reason,
        rejection_reason=review.rejection_reason,
        created_at=review.created_at,
        updated_at=review.updated_at,
        is_expired=is_expired,
        time_remaining_hours=time_remaining_hours
    )