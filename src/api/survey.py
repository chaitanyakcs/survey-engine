from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from src.database import get_db, Survey
from src.services.survey_service import SurveyService
from src.utils.survey_utils import get_questions_count
from src.models.survey import QuestionUpdate, SectionUpdate, SurveySection
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
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


class QuestionReorderRequest(BaseModel):
    question_order: List[str]


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
            
            # Extract title with improved logic for reference examples
            title = survey_data.get('title', 'Untitled Survey')
            
            # For reference examples, try to get title from golden pair if survey title is missing
            if survey.status == 'reference' and (not title or title == 'Untitled Survey'):
                try:
                    from src.database.models import GoldenRFQSurveyPair
                    golden_pair = db.query(GoldenRFQSurveyPair).filter(GoldenRFQSurveyPair.id == survey.id).first()
                    if golden_pair and golden_pair.title:
                        title = golden_pair.title
                        logger.info(f"📝 [Survey List] Using golden pair title for reference survey {survey.id}: {title}")
                except Exception as e:
                    logger.warning(f"⚠️ [Survey List] Failed to get golden pair title for survey {survey.id}: {e}")
            
            survey_list.append(SurveyListItem(
                id=str(survey.id),
                title=title,
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


@router.put("/{survey_id}/questions/{question_id}")
async def update_question(
    survey_id: UUID,
    question_id: str,
    question_update: QuestionUpdate,
    db: Session = Depends(get_db)
):
    """Update a specific question in a survey."""
    logger.info(f"📝 [Survey API] Updating question {question_id} in survey {survey_id}")
    
    try:
        # Get the survey
        survey = db.query(Survey).filter(Survey.id == survey_id).first()
        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found")
        
        # Get survey data
        survey_data = survey.final_output or survey.raw_output or {}
        if not survey_data:
            raise HTTPException(status_code=400, detail="Survey has no data to update")
        
        # Find and update the question
        question_found = False
        
        # Check if survey uses sections format
        if 'sections' in survey_data and survey_data['sections']:
            for section in survey_data['sections']:
                if 'questions' in section:
                    for i, question in enumerate(section['questions']):
                        if question.get('id') == question_id:
                            # Update the question with provided fields
                            for field, value in question_update.dict(exclude_unset=True).items():
                                question[field] = value
                            question_found = True
                            logger.info(f"✅ [Survey API] Updated question in section {section.get('id', 'unknown')}")
                            break
                    if question_found:
                        break
        else:
            # Check flat questions format
            if 'questions' in survey_data and survey_data['questions']:
                for i, question in enumerate(survey_data['questions']):
                    if question.get('id') == question_id:
                        # Update the question with provided fields
                        for field, value in question_update.dict(exclude_unset=True).items():
                            question[field] = value
                        question_found = True
                        logger.info(f"✅ [Survey API] Updated question in flat format")
                        break
        
        if not question_found:
            raise HTTPException(status_code=404, detail="Question not found")
        
        # Save the updated survey data
        survey.final_output = survey_data
        survey.updated_at = datetime.now()
        db.commit()
        
        logger.info(f"💾 [Survey API] Successfully saved updated question {question_id}")
        return {"status": "success", "message": "Question updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ [Survey API] Failed to update question {question_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update question: {str(e)}")


@router.put("/{survey_id}/sections/reorder")
async def reorder_sections(
    survey_id: UUID,
    section_order: List[int],
    db: Session = Depends(get_db)
):
    """Reorder sections in a survey."""
    logger.info(f"📝 [Survey API] Reordering sections in survey {survey_id}")
    logger.info(f"📤 [Survey API] Received section order: {section_order}")
    
    try:
        # Get the survey
        survey = db.query(Survey).filter(Survey.id == survey_id).first()
        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found")
        
        # Get survey data
        survey_data = survey.final_output or survey.raw_output or {}
        if not survey_data:
            raise HTTPException(status_code=400, detail="Survey has no data to update")
        
        logger.info(f"📊 [Survey API] Survey data keys: {list(survey_data.keys())}")
        logger.info(f"📊 [Survey API] Has sections key: {'sections' in survey_data}")
        logger.info(f"📊 [Survey API] Sections count: {len(survey_data.get('sections', []))}")
        logger.info(f"📊 [Survey API] Current sections before reorder: {[s.get('id') for s in survey_data.get('sections', [])]}")
        logger.info(f"📊 [Survey API] Current section orders: {[s.get('order') for s in survey_data.get('sections', [])]}")
        
        # Check if we have sections to reorder
        if 'sections' not in survey_data or not survey_data['sections']:
            logger.warning(f"⚠️ [Survey API] No sections found in survey data!")
            logger.warning(f"⚠️ [Survey API] Survey data structure: {survey_data}")
            return {"status": "success", "message": "No sections to reorder"}
        
        # Reorder sections
        if 'sections' in survey_data and survey_data['sections']:
            logger.info(f"📊 [Survey API] Found {len(survey_data['sections'])} sections to reorder")
            
            # Create a mapping of section IDs to sections
            section_map = {section.get('id'): section for section in survey_data['sections']}
            logger.info(f"📊 [Survey API] Section map IDs: {list(section_map.keys())}")
            
            # Reorder based on the provided order
            reordered_sections = []
            for section_id in section_order:
                if section_id in section_map:
                    reordered_sections.append(section_map[section_id])
                    logger.info(f"📊 [Survey API] Added section {section_id} to reordered list")
                else:
                    logger.warning(f"⚠️ [Survey API] Section ID {section_id} not found in section map!")
            
            logger.info(f"📊 [Survey API] Reordered sections count: {len(reordered_sections)}")
            
            # Update the order property for each section to reflect the new position
            for index, section in enumerate(reordered_sections):
                section['order'] = index + 1
                logger.info(f"📊 [Survey API] Set section {section.get('id')} order to {index + 1}")
            
            survey_data['sections'] = reordered_sections
            logger.info(f"📊 [Survey API] Sections after reorder: {[s.get('id') for s in reordered_sections]}")
            logger.info(f"📊 [Survey API] Section orders: {[s.get('order') for s in reordered_sections]}")
        else:
            logger.warning(f"⚠️ [Survey API] No sections found to reorder!")
        
        # Create a completely new dictionary to force SQLAlchemy to detect the change
        new_final_output = dict(survey_data)
        new_final_output['sections'] = [dict(section) for section in survey_data['sections']]
        
        # Save the updated survey data
        survey.final_output = new_final_output
        survey.updated_at = datetime.now()
        
        # Explicitly tell SQLAlchemy that the JSONB field has changed
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(survey, 'final_output')
        
        # Force the database to recognize the change
        db.flush()  # Flush changes to database without committing
        db.commit()
        
        # Verify the changes were saved
        db.refresh(survey)
        logger.info(f"📊 [Survey API] After commit - sections count: {len(survey.final_output.get('sections', []))}")
        logger.info(f"📊 [Survey API] After commit - section IDs: {[s.get('id') for s in survey.final_output.get('sections', [])]}")
        logger.info(f"📊 [Survey API] After commit - section orders: {[s.get('order') for s in survey.final_output.get('sections', [])]}")
        
        logger.info(f"💾 [Survey API] Successfully reordered sections")
        return {"status": "success", "message": "Sections reordered successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ [Survey API] Failed to reorder sections: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to reorder sections: {str(e)}")


@router.put("/{survey_id}/questions/reorder")
async def reorder_questions(
    survey_id: UUID,
    request: QuestionReorderRequest,
    db: Session = Depends(get_db)
):
    """Reorder questions in a survey."""
    logger.info(f"📝 [Survey API] Reordering questions in survey {survey_id}")
    logger.info(f"📤 [Survey API] Received question order: {request.question_order}")
    
    try:
        # Get the survey
        survey = db.query(Survey).filter(Survey.id == survey_id).first()
        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found")
        
        # Get survey data
        survey_data = survey.final_output or survey.raw_output or {}
        if not survey_data:
            raise HTTPException(status_code=400, detail="Survey has no data to update")
        
        logger.info(f"📊 [Survey API] Survey data keys: {list(survey_data.keys())}")
        logger.info(f"📊 [Survey API] Has questions key: {'questions' in survey_data}")
        logger.info(f"📊 [Survey API] Has sections key: {'sections' in survey_data}")
        logger.info(f"📊 [Survey API] Questions count: {len(survey_data.get('questions', []))}")
        logger.info(f"📊 [Survey API] Sections count: {len(survey_data.get('sections', []))}")
        
        # Debug: Log the actual survey data structure
        if 'sections' in survey_data and survey_data['sections']:
            logger.info(f"📊 [Survey API] First section: {survey_data['sections'][0]}")
            if 'questions' in survey_data['sections'][0]:
                logger.info(f"📊 [Survey API] First section questions: {survey_data['sections'][0]['questions']}")
        
        # Handle questions within sections (new format)
        if 'sections' in survey_data and survey_data['sections']:
            logger.info(f"📊 [Survey API] Processing questions within sections")
            
            # Create a mapping of question IDs to their current section and question data
            question_map = {}
            for section in survey_data['sections']:
                if 'questions' in section and section['questions']:
                    for question in section['questions']:
                        question_map[question.get('id')] = {
                            'question': question,
                            'section': section
                        }
            
            logger.info(f"📊 [Survey API] Question map IDs: {list(question_map.keys())}")
            logger.info(f"📊 [Survey API] Request question order: {request.question_order}")
            
            # Debug: Check if any questions from the request are in the map
            found_questions = []
            missing_questions = []
            for question_id in request.question_order:
                if question_id in question_map:
                    found_questions.append(question_id)
                else:
                    missing_questions.append(question_id)
            
            logger.info(f"📊 [Survey API] Found questions: {found_questions}")
            logger.info(f"📊 [Survey API] Missing questions: {missing_questions}")
            
            if not found_questions:
                logger.error(f"❌ [Survey API] No questions from request found in question map!")
                raise HTTPException(status_code=404, detail="Question not found")
            
            # Group questions by section based on the new order
            section_question_groups = {}
            for question_id in request.question_order:
                if question_id in question_map:
                    section_id = question_map[question_id]['section'].get('id')
                    if section_id not in section_question_groups:
                        section_question_groups[section_id] = []
                    section_question_groups[section_id].append(question_map[question_id]['question'])
                    logger.info(f"📊 [Survey API] Added question {question_id} to section {section_id}")
                else:
                    logger.warning(f"⚠️ [Survey API] Question ID {question_id} not found in question map!")
            
            # Update each section with its reordered questions
            for section in survey_data['sections']:
                section_id = section.get('id')
                if section_id in section_question_groups:
                    # Update order property for each question in this section
                    for index, question in enumerate(section_question_groups[section_id]):
                        question['order'] = index + 1
                        logger.info(f"📊 [Survey API] Set question {question.get('id')} order to {index + 1} in section {section_id}")
                    
                    section['questions'] = section_question_groups[section_id]
                    logger.info(f"📊 [Survey API] Updated section {section_id} with {len(section['questions'])} questions")
                else:
                    # If no questions for this section in the new order, keep original questions
                    logger.info(f"📊 [Survey API] No questions in new order for section {section_id}, keeping original")
            
            logger.info(f"📊 [Survey API] Successfully reordered questions within sections")
            
        # Handle legacy flat questions format
        elif 'questions' in survey_data and survey_data['questions']:
            logger.info(f"📊 [Survey API] Processing legacy flat questions format")
            logger.info(f"📊 [Survey API] Current questions before reorder: {[q.get('id') for q in survey_data.get('questions', [])]}")
            logger.info(f"📊 [Survey API] Current question orders: {[q.get('order') for q in survey_data.get('questions', [])]}")
            
            # Create a mapping of question IDs to questions
            question_map = {question.get('id'): question for question in survey_data['questions']}
            logger.info(f"📊 [Survey API] Question map IDs: {list(question_map.keys())}")
            
            # Reorder based on the provided order
            reordered_questions = []
            for question_id in request.question_order:
                if question_id in question_map:
                    reordered_questions.append(question_map[question_id])
                    logger.info(f"📊 [Survey API] Added question {question_id} to reordered list")
                else:
                    logger.warning(f"⚠️ [Survey API] Question ID {question_id} not found in question map!")
            
            logger.info(f"📊 [Survey API] Reordered questions count: {len(reordered_questions)}")
            
            # Update the order property for each question to reflect the new position
            for index, question in enumerate(reordered_questions):
                question['order'] = index + 1
                logger.info(f"📊 [Survey API] Set question {question.get('id')} order to {index + 1}")
            
            survey_data['questions'] = reordered_questions
            logger.info(f"📊 [Survey API] Questions after reorder: {[q.get('id') for q in reordered_questions]}")
            logger.info(f"📊 [Survey API] Question orders: {[q.get('order') for q in reordered_questions]}")
            
        else:
            logger.warning(f"⚠️ [Survey API] No questions found in survey data!")
            logger.warning(f"⚠️ [Survey API] Survey data structure: {survey_data}")
            return {"status": "success", "message": "No questions to reorder"}
        
        # Create a completely new dictionary to force SQLAlchemy to detect the change
        new_final_output = dict(survey_data)
        
        # Deep copy sections if they exist
        if 'sections' in survey_data:
            new_final_output['sections'] = []
            for section in survey_data['sections']:
                new_section = dict(section)
                if 'questions' in section:
                    new_section['questions'] = [dict(question) for question in section['questions']]
                new_final_output['sections'].append(new_section)
        
        # Deep copy questions if they exist (legacy format)
        if 'questions' in survey_data:
            new_final_output['questions'] = [dict(question) for question in survey_data['questions']]
        
        # Save the updated survey data
        survey.final_output = new_final_output
        survey.updated_at = datetime.now()
        
        # Explicitly tell SQLAlchemy that the JSONB field has changed
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(survey, 'final_output')
        
        # Force the database to recognize the change
        db.flush()  # Flush changes to database without committing
        db.commit()
        
        # Verify the changes were saved
        db.refresh(survey)
        if 'sections' in survey.final_output:
            logger.info(f"📊 [Survey API] After commit - sections count: {len(survey.final_output.get('sections', []))}")
            for i, section in enumerate(survey.final_output.get('sections', [])):
                logger.info(f"📊 [Survey API] Section {i+1} - questions count: {len(section.get('questions', []))}")
                logger.info(f"📊 [Survey API] Section {i+1} - question IDs: {[q.get('id') for q in section.get('questions', [])]}")
                logger.info(f"📊 [Survey API] Section {i+1} - question orders: {[q.get('order') for q in section.get('questions', [])]}")
        else:
            logger.info(f"📊 [Survey API] After commit - questions count: {len(survey.final_output.get('questions', []))}")
            logger.info(f"📊 [Survey API] After commit - question IDs: {[q.get('id') for q in survey.final_output.get('questions', [])]}")
            logger.info(f"📊 [Survey API] After commit - question orders: {[q.get('order') for q in survey.final_output.get('questions', [])]}")
        
        logger.info(f"💾 [Survey API] Successfully reordered questions")
        return {"status": "success", "message": "Questions reordered successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ [Survey API] Failed to reorder questions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to reorder questions: {str(e)}")


@router.put("/{survey_id}/sections/{section_id}")
async def update_section(
    survey_id: UUID,
    section_id: int,
    section_update: SectionUpdate,
    db: Session = Depends(get_db)
):
    """Update a specific section in a survey."""
    logger.info(f"📝 [Survey API] Updating section {section_id} in survey {survey_id}")
    
    try:
        # Get the survey
        survey = db.query(Survey).filter(Survey.id == survey_id).first()
        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found")
        
        # Get survey data
        survey_data = survey.final_output or survey.raw_output or {}
        if not survey_data:
            raise HTTPException(status_code=400, detail="Survey has no data to update")
        
        # Find and update the section
        section_found = False
        
        if 'sections' in survey_data and survey_data['sections']:
            for i, section in enumerate(survey_data['sections']):
                if section.get('id') == section_id:
                    # Update the section with provided fields
                    for field, value in section_update.dict(exclude_unset=True).items():
                        section[field] = value
                    section_found = True
                    logger.info(f"✅ [Survey API] Updated section {section_id}")
                    break
        
        if not section_found:
            raise HTTPException(status_code=404, detail="Section not found")
        
        # Create a completely new dictionary to force SQLAlchemy to detect the change
        new_final_output = dict(survey_data)
        
        # Deep copy sections if they exist
        if 'sections' in survey_data:
            new_final_output['sections'] = []
            for section in survey_data['sections']:
                new_section = dict(section)
                if 'questions' in section:
                    new_section['questions'] = [dict(question) for question in section['questions']]
                new_final_output['sections'].append(new_section)
        
        # Deep copy questions if they exist (legacy format)
        if 'questions' in survey_data:
            new_final_output['questions'] = [dict(question) for question in survey_data['questions']]
        
        # Save the updated survey data
        survey.final_output = new_final_output
        survey.updated_at = datetime.now()
        
        # Explicitly tell SQLAlchemy that the JSONB field has changed
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(survey, 'final_output')
        
        # Force the database to recognize the change
        db.flush()  # Flush changes to database without committing
        db.commit()
        
        logger.info(f"💾 [Survey API] Successfully saved updated section {section_id}")
        return {"status": "success", "message": "Section updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ [Survey API] Failed to update section {section_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update section: {str(e)}")


@router.post("/{survey_id}/sections")
async def create_section(
    survey_id: UUID,
    section: SurveySection,
    db: Session = Depends(get_db)
):
    """Create a new section in a survey."""
    logger.info(f"📝 [Survey API] Creating new section in survey {survey_id}")
    
    try:
        # Get the survey
        survey = db.query(Survey).filter(Survey.id == survey_id).first()
        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found")
        
        # Get survey data
        survey_data = survey.final_output or survey.raw_output or {}
        if not survey_data:
            raise HTTPException(status_code=400, detail="Survey has no data to update")
        
        # Initialize sections if they don't exist
        if 'sections' not in survey_data:
            survey_data['sections'] = []
        
        # Add the new section
        survey_data['sections'].append(section.dict())
        
        # Save the updated survey data
        survey.final_output = survey_data
        survey.updated_at = datetime.now()
        db.commit()
        
        logger.info(f"💾 [Survey API] Successfully created new section")
        return {"status": "success", "message": "Section created successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ [Survey API] Failed to create section: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create section: {str(e)}")


@router.delete("/{survey_id}/sections/{section_id}")
async def delete_section(
    survey_id: UUID,
    section_id: int,
    db: Session = Depends(get_db)
):
    """Delete a section from a survey."""
    logger.info(f"📝 [Survey API] Deleting section {section_id} from survey {survey_id}")
    
    try:
        # Get the survey
        survey = db.query(Survey).filter(Survey.id == survey_id).first()
        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found")
        
        # Get survey data
        survey_data = survey.final_output or survey.raw_output or {}
        if not survey_data:
            raise HTTPException(status_code=400, detail="Survey has no data to update")
        
        # Find and remove the section
        section_found = False
        
        if 'sections' in survey_data and survey_data['sections']:
            for i, section in enumerate(survey_data['sections']):
                if section.get('id') == section_id:
                    survey_data['sections'].pop(i)
                    section_found = True
                    logger.info(f"✅ [Survey API] Deleted section {section_id}")
                    break
        
        if not section_found:
            raise HTTPException(status_code=404, detail="Section not found")
        
        # Save the updated survey data
        survey.final_output = survey_data
        survey.updated_at = datetime.now()
        db.commit()
        
        logger.info(f"💾 [Survey API] Successfully deleted section {section_id}")
        return {"status": "success", "message": "Section deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ [Survey API] Failed to delete section {section_id}: {str(e)}")