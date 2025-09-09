from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from src.database import get_db, Survey
from src.services.survey_service import SurveyService
from pydantic import BaseModel
from typing import Optional, Dict, Any
from uuid import UUID
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
            
            survey_list.append(SurveyListItem(
                id=str(survey.id),
                title=survey_data.get('title', 'Untitled Survey'),
                description=survey_data.get('description', 'No description available'),
                status=survey.status,
                created_at=survey.created_at.isoformat() if survey.created_at else '',
                methodology_tags=methodology_tags,
                quality_score=metadata.get('quality_score'),
                estimated_time=metadata.get('estimated_time'),
                question_count=len(survey_data.get('questions', [])),
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
    
    try:
        survey_service = SurveyService(db)
        logger.info("📋 [Survey API] Created SurveyService, querying database")
        
        survey = survey_service.get_survey(survey_id)
        
        if not survey:
            logger.warning(f"❌ [Survey API] Survey not found in database: survey_id={survey_id}")
            raise HTTPException(status_code=404, detail="Survey not found")
        
        logger.info(f"✅ [Survey API] Survey found: id={survey.id}, status={survey.status}")
        
        validation_results = survey_service.get_validation_results(survey_id)
        edit_suggestions = survey_service.get_edit_suggestions(survey_id)
        
        response = SurveyResponse(
            id=str(survey.id),
            status=survey.status,  # type: ignore
            raw_output=survey.raw_output,  # type: ignore
            final_output=survey.final_output,  # type: ignore
            golden_similarity_score=float(survey.golden_similarity_score) if survey.golden_similarity_score else None,  # type: ignore
            validation_results=validation_results,
            edit_suggestions=edit_suggestions
        )
        
        logger.info(f"🎉 [Survey API] Returning survey response: status={response.status}")
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
    """Delete a survey"""
    try:
        survey = db.query(Survey).filter(Survey.id == survey_id).first()
        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found")
        
        db.delete(survey)
        db.commit()
        
        return {"status": "success", "message": "Survey deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete survey: {str(e)}")