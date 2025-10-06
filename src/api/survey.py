from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from src.database import get_db, Survey
from src.services.survey_service import SurveyService
from src.utils.survey_utils import get_questions_count
from pydantic import BaseModel
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/survey", tags=["Survey"])


class SurveyResponse(BaseModel):
    id: str
    status: str
    raw_output: Optional[Dict[Any, Any]]
    final_output: Optional[Dict[Any, Any]]
    golden_similarity_score: Optional[float]
    validation_results: Optional[Dict[str, Any]]
    edit_suggestions: Optional[Dict[str, Any]]
    pillar_scores: Optional[Dict[str, Any]]


class EditRequest(BaseModel):
    edit_type: str
    edit_reason: str
    before_text: str
    after_text: str


class SurveyListItem(BaseModel):
    id: str
    title: str
    description: str
    status: str
    created_at: str
    methodology_tags: list
    quality_score: Optional[float]
    estimated_time: Optional[int]
    question_count: int
    annotation: Optional[Dict[str, Any]] = None


class ValidationRequest(BaseModel):
    methodology_strict_mode: Optional[bool] = None
    golden_similarity_threshold: Optional[float] = None


@router.get("/list", response_model=list[SurveyListItem])
async def list_surveys(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get list of all generated surveys"""
    try:
        surveys = db.query(Survey).order_by(Survey.created_at.desc()).offset(skip).limit(limit).all()
        
        survey_list = []
        for survey in surveys:
            # Extract survey data
            survey_data = survey.final_output or survey.raw_output or {}
            metadata = survey_data.get('metadata', {})
            
            # Ensure methodology_tags is always a list
            methodology_tags = metadata.get('methodology_tags', [])
            if not isinstance(methodology_tags, list):
                methodology_tags = []
            
            # Use pillar scores if available, fallback to metadata quality_score
            quality_score = None
            if survey.pillar_scores and isinstance(survey.pillar_scores, dict):
                quality_score = survey.pillar_scores.get('weighted_score')
            elif metadata.get('quality_score'):
                quality_score = metadata.get('quality_score')
            
            survey_list.append(SurveyListItem(
                id=str(survey.id),
                title=survey_data.get('title', 'Untitled Survey'),
                description=survey_data.get('description', 'No description available'),
                status=survey.status,
                created_at=survey.created_at.isoformat() if survey.created_at else '',
                methodology_tags=methodology_tags,
                quality_score=quality_score,
                estimated_time=metadata.get('estimated_time'),
                question_count=get_questions_count(survey_data),
                annotation=None  # Survey model doesn't have annotation field
            ))
        
        return survey_list
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list surveys: {str(e)}")


@router.get("/{survey_id}", response_model=SurveyResponse)
async def get_survey(
    survey_id: UUID,
    db: Session = Depends(get_db)
) -> SurveyResponse:
    """
    Retrieve generated survey
    Include: golden_similarity_score, validation_results, edit_suggestions
    """
    logger.info(f"🔍 [Survey API] Retrieving survey: survey_id={survey_id}")
    logger.info(f"🔍 [Survey API] Request received at: {datetime.now()}")
    
    try:
        survey_service = SurveyService(db)
        logger.info("📋 [Survey API] Created SurveyService, querying database")
        
        logger.info(f"🔍 [Survey API] About to call survey_service.get_survey({survey_id})")
        survey = survey_service.get_survey(survey_id)
        logger.info(f"🔍 [Survey API] get_survey returned: {survey is not None}")
        
        if not survey:
            logger.warning(f"❌ [Survey API] Survey not found in database: survey_id={survey_id}")
            raise HTTPException(status_code=404, detail="Survey not found")
        
        logger.info(f"✅ [Survey API] Survey found: id={survey.id}, status={survey.status}")
        logger.info(f"🔍 [Survey API] Survey data keys: {list(survey.__dict__.keys()) if survey else 'None'}")
        
        logger.info(f"🔍 [Survey API] Getting validation results for survey_id={survey_id}")
        validation_results = survey_service.get_validation_results(survey_id)
        logger.info(f"🔍 [Survey API] Validation results: {validation_results is not None}")
        
        logger.info(f"🔍 [Survey API] Getting edit suggestions for survey_id={survey_id}")
        edit_suggestions = survey_service.get_edit_suggestions(survey_id)
        logger.info(f"🔍 [Survey API] Edit suggestions: {edit_suggestions is not None}")
        
        logger.info(f"🔍 [Survey API] Building response object...")
        response = SurveyResponse(
            id=str(survey.id),
            status=survey.status,  # type: ignore
            raw_output=survey.raw_output,  # type: ignore
            final_output=survey.final_output,  # type: ignore
            golden_similarity_score=float(survey.golden_similarity_score) if survey.golden_similarity_score else None,  # type: ignore
            validation_results=validation_results,
            edit_suggestions=edit_suggestions,
            pillar_scores=survey.pillar_scores  # type: ignore
        )
        
        logger.info(f"🎉 [Survey API] Returning survey response: status={response.status}")
        logger.info(f"🔍 [Survey API] Response data size: {len(str(response))} characters")
        logger.info(f"🔍 [Survey API] Response has final_output: {response.final_output is not None}")
        if response.final_output:
            logger.info(f"🔍 [Survey API] Final output keys: {list(response.final_output.keys())}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [Survey API] Unexpected error retrieving survey {survey_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put("/{survey_id}/edit")
async def submit_edit(
    survey_id: UUID,
    edit: EditRequest,
    db: Session = Depends(get_db)
) -> dict[str, str]:
    """
    Submit human edits
    Granularity: Based on EDIT_GRANULARITY_LEVEL setting
    Required fields: edit_type, edit_reason, before_text, after_text
    """
    try:
        survey_service = SurveyService(db)
        result = survey_service.submit_edit(
            survey_id=survey_id,
            edit_type=edit.edit_type,
            edit_reason=edit.edit_reason,
            before_text=edit.before_text,
            after_text=edit.after_text,
            annotation=edit.annotation
        )
        
        return {"status": "success", "edit_id": str(result.edit_id)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit edit: {str(e)}")


@router.post("/{survey_id}/validate")
async def revalidate_survey(
    survey_id: UUID,
    validation_request: ValidationRequest,
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    """
    Re-run validation with different parameters
    Parameters: methodology_strict_mode, golden_similarity_threshold
    """
    try:
        survey_service = SurveyService(db)
        result = survey_service.revalidate(
            survey_id=survey_id,
            methodology_strict_mode=validation_request.methodology_strict_mode,
            golden_similarity_threshold=validation_request.golden_similarity_threshold
        )
        
        return {"status": "success", "validation_results": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to revalidate: {str(e)}")


@router.delete("/{survey_id}")
async def delete_survey(
    survey_id: str,
    db: Session = Depends(get_db)
):
    """Delete a survey and clean up related records"""
    try:
        survey = db.query(Survey).filter(Survey.id == survey_id).first()
        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found")
        
        # Delete related human review records first
        from src.database.models import HumanReview
        db.query(HumanReview).filter(HumanReview.survey_id == survey_id).delete()
        
        # Delete the survey
        db.delete(survey)
        db.commit()
        
        logger.info(f"🗑️ [Survey API] Survey {survey_id} and related records deleted successfully")
        return {"status": "success", "message": "Survey deleted successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ [Survey API] Failed to delete survey {survey_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete survey: {str(e)}")


@router.post("/{survey_id}/reparse")
async def reparse_survey(
    survey_id: UUID,
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    """
    Reparse survey LLM output using raw response from LLM audit
    This fixes surveys generated with outdated validation rules
    """
    logger.info(f"🔄 [Survey API] Starting reparse for survey: {survey_id}")
    
    try:
        # Get the survey
        survey = db.query(Survey).filter(Survey.id == survey_id).first()
        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found")
        
        # Get the raw LLM response from audit system
        from src.database.models import LLMAudit
        from src.services.generation_service import GenerationService
        
        # Find the LLM audit record for this survey
        audit_record = db.query(LLMAudit).filter(
            LLMAudit.parent_survey_id == str(survey_id),
            LLMAudit.purpose == "survey_generation"
        ).order_by(LLMAudit.created_at.desc()).first()
        
        if not audit_record:
            raise HTTPException(status_code=400, detail="No LLM audit record found for this survey")
        
        if not audit_record.raw_response:
            raise HTTPException(status_code=400, detail="No raw response found in LLM audit record")
        
        logger.info(f"📊 [Survey API] Raw response found, starting reparse process")
        logger.info(f"🔍 [Survey API] Raw response length: {len(audit_record.raw_response)} characters")
        
        # Extract survey data using enhanced parsing logic
        generation_service = GenerationService(db)
        
        if isinstance(audit_record.raw_response, dict):
            # If raw_response is already parsed, extract the json_output field
            if 'json_output' in audit_record.raw_response:
                logger.info(f"🔍 [Survey API] Found json_output in raw_response, applying enhanced parsing")
                # Use enhanced parsing even for pre-parsed data to ensure proper structure
                json_output = audit_record.raw_response['json_output']
                if isinstance(json_output, dict):
                    # Apply enhanced validation and structure fixing
                    generation_service._validate_and_fix_survey_structure(json_output)
                    reparsed_survey = json_output
                else:
                    # If json_output is a string, parse it with enhanced logic
                    reparsed_survey = generation_service._extract_survey_json(str(json_output))
            else:
                # Fallback to the original raw_response if no json_output field
                logger.info(f"🔍 [Survey API] No json_output found, using raw_response directly")
                reparsed_survey = audit_record.raw_response
        else:
            # If raw_response is still a string, use the enhanced generation service
            logger.info(f"🔍 [Survey API] Raw response is string, using enhanced parsing")
            reparsed_survey = generation_service._extract_survey_json(audit_record.raw_response)
        
        if not reparsed_survey:
            raise HTTPException(status_code=500, detail="Failed to extract survey from raw response")
        
        logger.info(f"✅ [Survey API] Successfully extracted survey from raw response")
        
        # Count questions before updating
        question_count = get_questions_count(reparsed_survey)
        sections_count = len(reparsed_survey.get('sections', []))
        logger.info(f"📊 [Survey API] Reparsed survey contains {question_count} questions across {sections_count} sections")
        
        # Update the survey with reparsed data
        logger.info(f"💾 [Survey API] Updating survey final_output with reparsed data")
        logger.info(f"🔍 [Survey API] Reparsed survey keys: {list(reparsed_survey.keys())}")
        
        # Show sample of questions before saving
        if 'sections' in reparsed_survey and reparsed_survey['sections']:
            first_section = reparsed_survey['sections'][0]
            if 'questions' in first_section and first_section['questions']:
                first_question = first_section['questions'][0]
                logger.info(f"🔍 [Survey API] Sample question: '{first_question.get('text', 'No text')}'")
        
        # Log detailed section breakdown
        for i, section in enumerate(reparsed_survey.get('sections', [])):
            section_questions = len(section.get('questions', []))
            logger.info(f"📋 [Survey API] Section {i+1}: '{section.get('title', 'Unknown')}' - {section_questions} questions")
        
        survey.final_output = reparsed_survey
        survey.status = "reparsed"
        
        # Also update the raw_output to reflect the new processing
        survey.raw_output = reparsed_survey
        
        # Update the LLM audit record with the new processed output
        logger.info(f"📝 [Survey API] Updating LLM audit record with reparsed output")
        reparsed_output_json = json.dumps(reparsed_survey, indent=2)
        audit_record.output_content = reparsed_output_json
        audit_record.output_tokens = len(reparsed_output_json.split()) if reparsed_output_json else 0
        
        logger.info(f"💾 [Survey API] Committing changes to database")
        db.commit()
        
        logger.info(f"✅ [Survey API] Successfully reparsed survey: {survey_id}")
        
        return {
            "status": "success",
            "message": "Survey reparsed successfully using enhanced JSON parsing",
            "survey_id": str(survey_id),
            "question_count": question_count,
            "sections_count": sections_count,
            "raw_response_length": len(str(audit_record.raw_response)),
            "reparsed_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [Survey API] Failed to reparse survey {survey_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to reparse survey: {str(e)}")


@router.post("/workflow/{workflow_id}/cleanup")
async def cleanup_workflow(
    workflow_id: str,
    db: Session = Depends(get_db)
):
    """Clean up progress tracker and related resources for a workflow"""
    try:
        from src.services.progress_tracker import cleanup_progress_tracker
        
        # Clean up progress tracker
        cleanup_progress_tracker(workflow_id)
        
        logger.info(f"🧹 [Survey API] Cleaned up resources for workflow: {workflow_id}")
        return {"status": "success", "message": "Workflow cleanup completed"}
        
    except Exception as e:
        logger.error(f"❌ [Survey API] Failed to cleanup workflow {workflow_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup workflow: {str(e)}")