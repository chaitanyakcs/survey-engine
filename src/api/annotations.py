"""
API endpoints for survey annotations
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import logging

from src.database.connection import get_db
from src.database.models import QuestionAnnotation, SectionAnnotation, SurveyAnnotation
from src.services.advanced_labeling_service import AdvancedLabelingService

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for API

class QuestionAnnotationRequest(BaseModel):
    question_id: str
    required: bool = True
    quality: int = Field(ge=1, le=5)
    relevant: int = Field(ge=1, le=5)
    methodological_rigor: int = Field(ge=1, le=5)
    content_validity: int = Field(ge=1, le=5)
    respondent_experience: int = Field(ge=1, le=5)
    analytical_value: int = Field(ge=1, le=5)
    business_impact: int = Field(ge=1, le=5)
    comment: Optional[str] = None
    labels: Optional[List[str]] = None
    removed_labels: Optional[List[str]] = None  # Track auto-generated labels that user explicitly removed
    annotator_id: str = "current-user"
    ai_confidence: Optional[float] = Field(ge=0.0, le=1.0, default=None)

class SectionAnnotationRequest(BaseModel):
    section_id: int
    quality: int = Field(ge=1, le=5)
    relevant: int = Field(ge=1, le=5)
    methodological_rigor: int = Field(ge=1, le=5)
    content_validity: int = Field(ge=1, le=5)
    respondent_experience: int = Field(ge=1, le=5)
    analytical_value: int = Field(ge=1, le=5)
    business_impact: int = Field(ge=1, le=5)
    comment: Optional[str] = None
    labels: Optional[List[str]] = None
    annotator_id: str = "current-user"

    # Advanced labeling fields
    section_classification: Optional[str] = None
    mandatory_elements: Optional[Dict[str, Any]] = None
    compliance_score: Optional[int] = None

class SurveyLevelAnnotationRequest(BaseModel):
    survey_id: str
    overall_comment: Optional[str] = None
    labels: Optional[List[str]] = None
    annotator_id: str = "current-user"

    # Advanced labeling fields
    detected_labels: Optional[Dict[str, Any]] = None
    compliance_report: Optional[Dict[str, Any]] = None
    advanced_metadata: Optional[Dict[str, Any]] = None

    # Survey-level quality ratings
    overall_quality: Optional[int] = Field(ge=1, le=5, default=None)
    survey_relevance: Optional[int] = Field(ge=1, le=5, default=None)
    methodology_score: Optional[int] = Field(ge=1, le=5, default=None)
    respondent_experience_score: Optional[int] = Field(ge=1, le=5, default=None)
    business_value_score: Optional[int] = Field(ge=1, le=5, default=None)

    # Survey classification
    survey_type: Optional[str] = None
    industry_category: Optional[str] = None
    research_methodology: Optional[List[str]] = None
    target_audience: Optional[str] = None
    survey_complexity: Optional[str] = None
    estimated_duration: Optional[int] = None
    compliance_status: Optional[str] = None

class BulkAnnotationRequest(BaseModel):
    survey_id: str
    question_annotations: List[QuestionAnnotationRequest] = []
    section_annotations: List[SectionAnnotationRequest] = []
    overall_comment: Optional[str] = None
    annotator_id: str = "current-user"

    # Advanced labeling fields for survey-level
    detected_labels: Optional[Dict[str, Any]] = None
    compliance_report: Optional[Dict[str, Any]] = None
    advanced_metadata: Optional[Dict[str, Any]] = None

class QuestionAnnotationResponse(BaseModel):
    id: int
    question_id: str
    survey_id: str
    required: bool
    quality: int
    relevant: int
    methodological_rigor: int
    content_validity: int
    respondent_experience: int
    analytical_value: int
    business_impact: int
    comment: Optional[str]
    labels: Optional[Any] = None
    removed_labels: Optional[Any] = None
    annotator_id: str
    created_at: datetime
    updated_at: Optional[datetime]
    
    # AI annotation fields
    ai_generated: Optional[bool] = None
    ai_confidence: Optional[float] = None
    human_verified: Optional[bool] = None
    generation_timestamp: Optional[datetime] = None
    
    # Human override tracking fields
    human_overridden: Optional[bool] = None
    override_timestamp: Optional[datetime] = None
    original_ai_quality: Optional[int] = None
    original_ai_relevant: Optional[int] = None
    original_ai_comment: Optional[str] = None

class SectionAnnotationResponse(BaseModel):
    id: int
    section_id: int
    survey_id: str
    quality: int
    relevant: int
    methodological_rigor: int
    content_validity: int
    respondent_experience: int
    analytical_value: int
    business_impact: int
    comment: Optional[str]
    labels: Optional[Any] = None
    annotator_id: str
    created_at: datetime
    updated_at: Optional[datetime]

    # Advanced labeling fields
    section_classification: Optional[str] = None
    mandatory_elements: Optional[Dict[str, Any]] = None
    compliance_score: Optional[int] = None
    
    # AI annotation fields
    ai_generated: Optional[bool] = None
    ai_confidence: Optional[float] = None
    human_verified: Optional[bool] = None
    generation_timestamp: Optional[datetime] = None
    
    # Human override tracking fields
    human_overridden: Optional[bool] = None
    override_timestamp: Optional[datetime] = None
    original_ai_quality: Optional[int] = None
    original_ai_relevant: Optional[int] = None
    original_ai_comment: Optional[str] = None

class SurveyLevelAnnotationResponse(BaseModel):
    id: int
    survey_id: str
    overall_comment: Optional[str] = None
    labels: Optional[List[str]] = None
    annotator_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Advanced labeling fields
    detected_labels: Optional[Dict[str, Any]] = None
    compliance_report: Optional[Dict[str, Any]] = None
    advanced_metadata: Optional[Dict[str, Any]] = None

    # Survey-level quality ratings
    overall_quality: Optional[int] = None
    survey_relevance: Optional[int] = None
    methodology_score: Optional[int] = None
    respondent_experience_score: Optional[int] = None
    business_value_score: Optional[int] = None

    # Survey classification
    survey_type: Optional[str] = None
    industry_category: Optional[str] = None
    research_methodology: Optional[List[str]] = None
    target_audience: Optional[str] = None
    survey_complexity: Optional[str] = None
    estimated_duration: Optional[int] = None
    compliance_status: Optional[str] = None

    class Config:
        from_attributes = True

class SurveyAnnotationsResponse(BaseModel):
    survey_id: str
    question_annotations: List[QuestionAnnotationResponse]
    section_annotations: List[SectionAnnotationResponse]
    overall_comment: Optional[str]
    annotator_id: str
    created_at: datetime
    updated_at: Optional[datetime]

    # Advanced labeling fields
    detected_labels: Optional[Dict[str, Any]] = None
    compliance_report: Optional[Dict[str, Any]] = None
    advanced_metadata: Optional[Dict[str, Any]] = None

# API Endpoints

@router.get("/surveys/{survey_id}/annotations", response_model=SurveyAnnotationsResponse)
def get_survey_annotations(
    survey_id: str,
    annotator_id: Optional[str] = "current-user",
    include_ai_annotations: bool = True,
    db: Session = Depends(get_db)
):
    """Get all annotations for a survey, optionally including AI annotations"""
    
    # Build query conditions
    question_conditions = [QuestionAnnotation.survey_id == survey_id]
    section_conditions = [SectionAnnotation.survey_id == survey_id]
    
    if include_ai_annotations:
        # Include both user and AI annotations (including DOCX parser annotations)
        question_conditions.append(
            or_(
                QuestionAnnotation.annotator_id == annotator_id,
                QuestionAnnotation.annotator_id == "ai_system",
                QuestionAnnotation.ai_generated == True  # Include any AI-generated annotations regardless of annotator_id
            )
        )
        section_conditions.append(
            or_(
                SectionAnnotation.annotator_id == annotator_id,
                SectionAnnotation.annotator_id == "ai_system",
                SectionAnnotation.ai_generated == True  # Include any AI-generated annotations regardless of annotator_id
            )
        )
    else:
        # Only include user annotations
        question_conditions.append(QuestionAnnotation.annotator_id == annotator_id)
        section_conditions.append(SectionAnnotation.annotator_id == annotator_id)
    
    # Get question annotations
    question_annotations = db.query(QuestionAnnotation).filter(
        and_(*question_conditions)
    ).all()
    
    # Log comments being retrieved for debugging
    for qa in question_annotations:
        logger.debug(f"💬 [API] Retrieving comment for question_id={qa.question_id}: '{qa.comment}' (type: {type(qa.comment).__name__}, is None: {qa.comment is None}, length: {len(qa.comment) if qa.comment else 0})")
    
    # Get section annotations
    section_annotations = db.query(SectionAnnotation).filter(
        and_(*section_conditions)
    ).all()
    
    # Log section comments being retrieved
    for sa in section_annotations:
        logger.debug(f"💬 [API] Retrieving comment for section_id={sa.section_id}: '{sa.comment}' (type: {type(sa.comment).__name__}, is None: {sa.comment is None}, length: {len(sa.comment) if sa.comment else 0})")
    
    # Get survey-level annotation
    survey_annotation = db.query(SurveyAnnotation).filter(
        and_(
            SurveyAnnotation.survey_id == survey_id,
            SurveyAnnotation.annotator_id == annotator_id
        )
    ).first()
    
    if survey_annotation:
        logger.debug(f"💬 [API] Retrieving overall_comment for survey_id={survey_id}: '{survey_annotation.overall_comment}' (type: {type(survey_annotation.overall_comment).__name__}, is None: {survey_annotation.overall_comment is None}, length: {len(survey_annotation.overall_comment) if survey_annotation.overall_comment else 0})")
    
    # Return empty response instead of 404 when no annotations exist
    if not question_annotations and not section_annotations and not survey_annotation:
        return SurveyAnnotationsResponse(
            survey_id=survey_id,
            question_annotations=[],
            section_annotations=[],
            overall_comment=None,
            annotator_id=annotator_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    # Get creation/update timestamps
    all_annotations = question_annotations + section_annotations
    if all_annotations:
        created_at = min(ann.created_at for ann in all_annotations)
        updated_at = max(ann.updated_at or ann.created_at for ann in all_annotations)
    else:
        created_at = datetime.now()
        updated_at = datetime.now()
    
    # Build response with explicit comment handling to preserve empty strings
    response = SurveyAnnotationsResponse(
        survey_id=survey_id,
        question_annotations=[
            QuestionAnnotationResponse(
                id=qa.id,
                question_id=qa.question_id,
                survey_id=qa.survey_id,
                required=qa.required,
                quality=qa.quality,
                relevant=qa.relevant,
                methodological_rigor=qa.methodological_rigor,
                content_validity=qa.content_validity,
                respondent_experience=qa.respondent_experience,
                analytical_value=qa.analytical_value,
                business_impact=qa.business_impact,
                # Preserve empty strings - don't convert to None
                comment=qa.comment if qa.comment is not None else None,
                labels=qa.labels,
                removed_labels=qa.removed_labels,
                annotator_id=qa.annotator_id,
                created_at=qa.created_at,
                updated_at=qa.updated_at,
                # AI annotation fields
                ai_generated=qa.ai_generated,
                ai_confidence=float(qa.ai_confidence) if qa.ai_confidence else None,
                human_verified=qa.human_verified,
                generation_timestamp=qa.generation_timestamp,
                # Human override tracking fields
                human_overridden=getattr(qa, 'human_overridden', None),
                override_timestamp=getattr(qa, 'override_timestamp', None),
                original_ai_quality=getattr(qa, 'original_ai_quality', None),
                original_ai_relevant=getattr(qa, 'original_ai_relevant', None),
                original_ai_comment=getattr(qa, 'original_ai_comment', None)
            ) for qa in question_annotations
        ],
        section_annotations=[
            SectionAnnotationResponse(
                id=sa.id,
                section_id=sa.section_id,
                survey_id=sa.survey_id,
                quality=sa.quality,
                relevant=sa.relevant,
                methodological_rigor=sa.methodological_rigor,
                content_validity=sa.content_validity,
                respondent_experience=sa.respondent_experience,
                analytical_value=sa.analytical_value,
                business_impact=sa.business_impact,
                # Preserve empty strings - don't convert to None
                comment=sa.comment if sa.comment is not None else None,
                labels=sa.labels,
                annotator_id=sa.annotator_id,
                created_at=sa.created_at,
                updated_at=sa.updated_at,
                # Advanced labeling fields (only if they exist)
                section_classification=getattr(sa, 'section_classification', None),
                mandatory_elements=getattr(sa, 'mandatory_elements', None),
                compliance_score=getattr(sa, 'compliance_score', None),
                # AI annotation fields
                ai_generated=sa.ai_generated,
                ai_confidence=float(sa.ai_confidence) if sa.ai_confidence else None,
                human_verified=sa.human_verified,
                generation_timestamp=sa.generation_timestamp,
                # Human override tracking fields
                human_overridden=getattr(sa, 'human_overridden', None),
                override_timestamp=getattr(sa, 'override_timestamp', None),
                original_ai_quality=getattr(sa, 'original_ai_quality', None),
                original_ai_relevant=getattr(sa, 'original_ai_relevant', None),
                original_ai_comment=getattr(sa, 'original_ai_comment', None)
            ) for sa in section_annotations
        ],
        # Preserve empty strings for overall_comment - don't convert to None
        overall_comment=survey_annotation.overall_comment if survey_annotation else None,
        annotator_id=annotator_id,
        created_at=created_at,
        updated_at=updated_at,
        # Advanced labeling fields
        detected_labels=survey_annotation.detected_labels if survey_annotation else None,
        compliance_report=survey_annotation.compliance_report if survey_annotation else None,
        advanced_metadata=survey_annotation.advanced_metadata if survey_annotation else None
    )
    
    # Log what we're returning for debugging
    for qa_resp in response.question_annotations:
        logger.debug(f"💬 [API] Returning comment for question_id={qa_resp.question_id}: '{qa_resp.comment}' (type: {type(qa_resp.comment).__name__}, is None: {qa_resp.comment is None})")
    for sa_resp in response.section_annotations:
        logger.debug(f"💬 [API] Returning comment for section_id={sa_resp.section_id}: '{sa_resp.comment}' (type: {type(sa_resp.comment).__name__}, is None: {sa_resp.comment is None})")
    if response.overall_comment is not None:
        logger.debug(f"💬 [API] Returning overall_comment: '{response.overall_comment}' (type: {type(response.overall_comment).__name__}, is None: {response.overall_comment is None})")
    
    return response

@router.post("/annotations/survey/{survey_id}/bulk")
async def save_bulk_annotations(
    survey_id: str,
    annotations: BulkAnnotationRequest,
    db: Session = Depends(get_db)
):
    """Save multiple annotations for a survey in bulk"""
    
    logger.info(f"🔍 [API] Starting bulk annotation save for survey_id={survey_id}")
    logger.info(f"📊 [API] Processing {len(annotations.question_annotations)} question annotations and {len(annotations.section_annotations)} section annotations")
    
    # Log incoming comments to verify they're in the request
    for qa_req in annotations.question_annotations:
        logger.info(f"💬 [API] INCOMING question annotation comment for question_id={qa_req.question_id}: '{qa_req.comment}' (type: {type(qa_req.comment).__name__}, is None: {qa_req.comment is None}, length: {len(qa_req.comment) if qa_req.comment else 0})")
    for sa_req in annotations.section_annotations:
        logger.info(f"💬 [API] INCOMING section annotation comment for section_id={sa_req.section_id}: '{sa_req.comment}' (type: {type(sa_req.comment).__name__}, is None: {sa_req.comment is None}, length: {len(sa_req.comment) if sa_req.comment else 0})")
    if annotations.overall_comment:
        logger.info(f"💬 [API] INCOMING overall_comment: '{annotations.overall_comment}' (type: {type(annotations.overall_comment).__name__}, length: {len(annotations.overall_comment) if annotations.overall_comment else 0})")
    
    try:
        # Process question annotations
        logger.info("📝 [API] Processing question annotations...")
        for i, qa_req in enumerate(annotations.question_annotations):
            logger.debug(f"🔍 [API] Processing question annotation {i+1}/{len(annotations.question_annotations)}: question_id={qa_req.question_id}")
            
            # Check if annotation already exists
            existing_qa = db.query(QuestionAnnotation).filter(
                and_(
                    QuestionAnnotation.question_id == qa_req.question_id,
                    QuestionAnnotation.annotator_id == qa_req.annotator_id,
                    QuestionAnnotation.survey_id == survey_id
                )
            ).first()
            
            if existing_qa:
                logger.debug(f"🔄 [API] Updating existing question annotation for question_id={qa_req.question_id}")
                
                # Check if this is a human override of an AI annotation
                is_human_override = (
                    existing_qa.ai_generated and 
                    existing_qa.annotator_id == "ai_system" and 
                    qa_req.annotator_id == "current-user"
                )
                
                if is_human_override:
                    logger.info(f"👤 [API] Human overriding AI annotation for question_id={qa_req.question_id}")
                    # Store original AI values before updating
                    existing_qa.original_ai_quality = existing_qa.quality
                    existing_qa.original_ai_relevant = existing_qa.relevant
                    existing_qa.original_ai_comment = existing_qa.comment
                    existing_qa.human_overridden = True
                    existing_qa.override_timestamp = datetime.now()
                    existing_qa.human_verified = True  # Mark as human-verified since they're overriding
                
                # Update existing annotation
                existing_qa.required = qa_req.required
                existing_qa.quality = qa_req.quality
                existing_qa.relevant = qa_req.relevant
                existing_qa.methodological_rigor = qa_req.methodological_rigor
                existing_qa.content_validity = qa_req.content_validity
                existing_qa.respondent_experience = qa_req.respondent_experience
                existing_qa.analytical_value = qa_req.analytical_value
                existing_qa.business_impact = qa_req.business_impact
                # Save comment (including empty strings - don't convert to None)
                existing_qa.comment = qa_req.comment if qa_req.comment is not None else None
                logger.info(f"💬 [API] SAVING comment for question_id={qa_req.question_id}: '{qa_req.comment}' (type: {type(qa_req.comment).__name__}, length: {len(qa_req.comment) if qa_req.comment else 0})")
                logger.info(f"💬 [API] Database comment value after assignment: '{existing_qa.comment}' (type: {type(existing_qa.comment).__name__}, is None: {existing_qa.comment is None})")
                existing_qa.labels = qa_req.labels
                existing_qa.removed_labels = qa_req.removed_labels
                existing_qa.updated_at = datetime.now()
            else:
                logger.debug(f"➕ [API] Creating new question annotation for question_id={qa_req.question_id}")
                
                # Determine if this is an AI-generated annotation
                is_ai_generated = qa_req.annotator_id == "ai_system"
                
                # Create new annotation
                # Save comment (including empty strings - don't convert to None)
                comment_value = qa_req.comment if qa_req.comment is not None else None
                logger.info(f"💬 [API] CREATING annotation with comment for question_id={qa_req.question_id}: '{comment_value}' (type: {type(comment_value).__name__}, length: {len(comment_value) if comment_value else 0})")
                new_qa = QuestionAnnotation(
                    question_id=qa_req.question_id,
                    survey_id=survey_id,
                    required=qa_req.required,
                    quality=qa_req.quality,
                    relevant=qa_req.relevant,
                    methodological_rigor=qa_req.methodological_rigor,
                    content_validity=qa_req.content_validity,
                    respondent_experience=qa_req.respondent_experience,
                    analytical_value=qa_req.analytical_value,
                    business_impact=qa_req.business_impact,
                    comment=comment_value,
                    labels=qa_req.labels,
                    removed_labels=qa_req.removed_labels,
                    annotator_id=qa_req.annotator_id,
                    # Set AI-generated fields based on annotator_id
                    ai_generated=is_ai_generated,
                    ai_confidence=qa_req.ai_confidence if is_ai_generated else None,
                    human_verified=False if is_ai_generated else True,
                    generation_timestamp=datetime.now() if is_ai_generated else None,
                    # Set human override tracking fields
                    human_overridden=False
                )
                db.add(new_qa)
        
        logger.info("✅ [API] Completed processing question annotations")
        
        # Process section annotations
        logger.info("📝 [API] Processing section annotations...")
        for i, sa_req in enumerate(annotations.section_annotations):
            logger.debug(f"🔍 [API] Processing section annotation {i+1}/{len(annotations.section_annotations)}: section_id={sa_req.section_id}")
            
            # Check if annotation already exists
            existing_sa = db.query(SectionAnnotation).filter(
                and_(
                    SectionAnnotation.section_id == sa_req.section_id,
                    SectionAnnotation.annotator_id == sa_req.annotator_id,
                    SectionAnnotation.survey_id == survey_id
                )
            ).first()
            
            if existing_sa:
                logger.debug(f"🔄 [API] Updating existing section annotation for section_id={sa_req.section_id}")
                
                # Check if this is a human override of an AI annotation
                is_human_override = (
                    existing_sa.ai_generated and 
                    existing_sa.annotator_id == "ai_system" and 
                    sa_req.annotator_id == "current-user"
                )
                
                if is_human_override:
                    logger.info(f"👤 [API] Human overriding AI annotation for section_id={sa_req.section_id}")
                    # Store original AI values before updating
                    existing_sa.original_ai_quality = existing_sa.quality
                    existing_sa.original_ai_relevant = existing_sa.relevant
                    existing_sa.original_ai_comment = existing_sa.comment
                    existing_sa.human_overridden = True
                    existing_sa.override_timestamp = datetime.now()
                    existing_sa.human_verified = True  # Mark as human-verified since they're overriding
                
                # Update existing annotation
                existing_sa.quality = sa_req.quality
                existing_sa.relevant = sa_req.relevant
                existing_sa.methodological_rigor = sa_req.methodological_rigor
                existing_sa.content_validity = sa_req.content_validity
                existing_sa.respondent_experience = sa_req.respondent_experience
                existing_sa.analytical_value = sa_req.analytical_value
                existing_sa.business_impact = sa_req.business_impact
                # Save comment (including empty strings - don't convert to None)
                existing_sa.comment = sa_req.comment if sa_req.comment is not None else None
                logger.info(f"💬 [API] SAVING comment for section_id={sa_req.section_id}: '{sa_req.comment}' (type: {type(sa_req.comment).__name__}, length: {len(sa_req.comment) if sa_req.comment else 0})")
                logger.info(f"💬 [API] Database comment value after assignment: '{existing_sa.comment}' (type: {type(existing_sa.comment).__name__}, is None: {existing_sa.comment is None})")
                existing_sa.labels = sa_req.labels
                existing_sa.updated_at = datetime.now()
                # Update advanced labeling fields
                existing_sa.section_classification = sa_req.section_classification
                existing_sa.mandatory_elements = sa_req.mandatory_elements
                existing_sa.compliance_score = sa_req.compliance_score
            else:
                logger.debug(f"➕ [API] Creating new section annotation for section_id={sa_req.section_id}")
                # Create new annotation
                # Save comment (including empty strings - don't convert to None)
                comment_value = sa_req.comment if sa_req.comment is not None else None
                logger.info(f"💬 [API] CREATING annotation with comment for section_id={sa_req.section_id}: '{comment_value}' (type: {type(comment_value).__name__}, length: {len(comment_value) if comment_value else 0})")
                new_sa = SectionAnnotation(
                    section_id=sa_req.section_id,
                    survey_id=survey_id,
                    quality=sa_req.quality,
                    relevant=sa_req.relevant,
                    methodological_rigor=sa_req.methodological_rigor,
                    content_validity=sa_req.content_validity,
                    respondent_experience=sa_req.respondent_experience,
                    analytical_value=sa_req.analytical_value,
                    business_impact=sa_req.business_impact,
                    comment=comment_value,
                    labels=sa_req.labels,
                    annotator_id=sa_req.annotator_id,
                    # Advanced labeling fields
                    section_classification=sa_req.section_classification,
                    mandatory_elements=sa_req.mandatory_elements,
                    compliance_score=sa_req.compliance_score
                )
                db.add(new_sa)
        
        logger.info("✅ [API] Completed processing section annotations")
        
        # Process survey-level annotation
        # Always process survey-level annotation if any field is provided (including empty strings for comments)
        # Check if overall_comment is explicitly provided (not None) or if other fields are provided
        should_process_survey = (
            annotations.overall_comment is not None or  # Explicitly check for None, not truthiness
            annotations.detected_labels is not None or
            annotations.compliance_report is not None or
            annotations.advanced_metadata is not None
        )
        
        # Log what we received for survey-level annotation
        if annotations.advanced_metadata:
            logger.info(f"💬 [API] Received advanced_metadata with fields: {list(annotations.advanced_metadata.keys())}")
            logger.info(f"💬 [API] Advanced metadata content: overallQuality={annotations.advanced_metadata.get('overallQuality')}, surveyRelevance={annotations.advanced_metadata.get('surveyRelevance')}, surveyType={annotations.advanced_metadata.get('surveyType')}, researchMethodology={annotations.advanced_metadata.get('researchMethodology')}")
        
        if should_process_survey:
            logger.info("📝 [API] Processing survey-level annotation...")
            existing_survey_ann = db.query(SurveyAnnotation).filter(
                and_(
                    SurveyAnnotation.survey_id == survey_id,
                    SurveyAnnotation.annotator_id == annotations.annotator_id
                )
            ).first()

            if existing_survey_ann:
                logger.debug(f"🔄 [API] Updating existing survey annotation for survey_id={survey_id}")
                # Always update overall_comment if it's provided (even if empty string)
                if annotations.overall_comment is not None:
                    existing_survey_ann.overall_comment = annotations.overall_comment
                    logger.info(f"💬 [API] SAVING overall_comment for survey_id={survey_id}: '{annotations.overall_comment}' (type: {type(annotations.overall_comment).__name__}, length: {len(annotations.overall_comment) if annotations.overall_comment else 0})")
                    logger.info(f"💬 [API] Database overall_comment value after assignment: '{existing_survey_ann.overall_comment}' (type: {type(existing_survey_ann.overall_comment).__name__}, is None: {existing_survey_ann.overall_comment is None})")
                existing_survey_ann.updated_at = datetime.now()
                # Update advanced labeling fields
                if annotations.detected_labels is not None:
                    existing_survey_ann.detected_labels = annotations.detected_labels
                if annotations.compliance_report is not None:
                    existing_survey_ann.compliance_report = annotations.compliance_report
                if annotations.advanced_metadata is not None:
                    existing_survey_ann.advanced_metadata = annotations.advanced_metadata
                    logger.info(f"💬 [API] Saved advanced_metadata with {len(annotations.advanced_metadata)} fields: {list(annotations.advanced_metadata.keys())}")
            else:
                logger.debug(f"➕ [API] Creating new survey annotation for survey_id={survey_id}")
                new_survey_ann = SurveyAnnotation(
                    survey_id=survey_id,
                    overall_comment=annotations.overall_comment if annotations.overall_comment is not None else None,
                    annotator_id=annotations.annotator_id,
                    # Advanced labeling fields
                    detected_labels=annotations.detected_labels,
                    compliance_report=annotations.compliance_report,
                    advanced_metadata=annotations.advanced_metadata
                )
                db.add(new_survey_ann)
            logger.info("✅ [API] Completed processing survey-level annotation")
        
        # Commit all changes
        logger.info("💾 [API] Committing all changes to database...")
        db.commit()
        logger.info("✅ [API] Successfully committed all changes")
        
        # Verify comments were saved by querying back from database
        logger.info("🔍 [API] Verifying comments were saved...")
        for qa_req in annotations.question_annotations:
            saved_qa = db.query(QuestionAnnotation).filter(
                and_(
                    QuestionAnnotation.question_id == qa_req.question_id,
                    QuestionAnnotation.annotator_id == qa_req.annotator_id,
                    QuestionAnnotation.survey_id == survey_id
                )
            ).first()
            if saved_qa:
                logger.info(f"💬 [API] VERIFIED saved comment for question_id={qa_req.question_id}: '{saved_qa.comment}' (type: {type(saved_qa.comment).__name__}, is None: {saved_qa.comment is None}, length: {len(saved_qa.comment) if saved_qa.comment else 0})")
            else:
                logger.warning(f"⚠️ [API] Could not find saved annotation for question_id={qa_req.question_id}")
        
        # Sync annotations to RAG tables (real-time hook)
        logger.info("🔗 [API] Syncing annotations to RAG tables...")
        try:
            from src.services.annotation_rag_sync_service import AnnotationRAGSyncService
            sync_service = AnnotationRAGSyncService(db)
            
            # Sync question annotations
            for qa_req in annotations.question_annotations:
                # Find the saved annotation ID
                qa = db.query(QuestionAnnotation).filter(
                    and_(
                        QuestionAnnotation.question_id == qa_req.question_id,
                        QuestionAnnotation.annotator_id == qa_req.annotator_id,
                        QuestionAnnotation.survey_id == survey_id
                    )
                ).first()
                
                if qa and qa.annotator_id == "current-user":  # Only sync human annotations
                    logger.info(f"🔗 Syncing question annotation {qa.id} to RAG")
                    result = await sync_service.sync_question_annotation(qa.id)
                    if result.get("success"):
                        logger.info(f"✅ Synced question {qa.question_id}: {result.get('action')}")
                    else:
                        logger.warning(f"⚠️ Failed to sync question {qa.question_id}: {result.get('error')}")
            
            # Sync section annotations
            for sa_req in annotations.section_annotations:
                # Find the saved annotation ID
                sa = db.query(SectionAnnotation).filter(
                    and_(
                        SectionAnnotation.section_id == sa_req.section_id,
                        SectionAnnotation.annotator_id == sa_req.annotator_id,
                        SectionAnnotation.survey_id == survey_id
                    )
                ).first()
                
                if sa and sa.annotator_id == "current-user":  # Only sync human annotations
                    logger.info(f"🔗 Syncing section annotation {sa.id} to RAG")
                    result = await sync_service.sync_section_annotation(sa.id)
                    if result.get("success"):
                        logger.info(f"✅ Synced section {sa.section_id}: {result.get('action')}")
                    else:
                        logger.warning(f"⚠️ Failed to sync section {sa.section_id}: {result.get('error')}")
            
            db.commit()  # Commit RAG sync changes
            logger.info("✅ [API] RAG sync completed")
        except Exception as sync_error:
            logger.error(f"⚠️ [API] RAG sync failed (non-fatal): {str(sync_error)}")
            # Don't fail the entire request if RAG sync fails
            db.rollback()  # Rollback RAG changes but keep annotations
        
        logger.info(f"🎉 [API] Bulk annotation save completed successfully for survey_id={survey_id}")
        return {"message": "Annotations saved successfully", "survey_id": survey_id}
        
    except Exception as e:
        logger.error(f"❌ [API] Failed to save bulk annotations for survey_id={survey_id}: {str(e)}", exc_info=True)
        db.rollback()
        logger.error(f"🔄 [API] Database transaction rolled back due to error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save annotations: {str(e)}"
        )

@router.get("/annotations/stats")
def get_annotation_stats(
    annotator_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get annotation statistics"""
    
    # Base queries
    question_query = db.query(QuestionAnnotation)
    section_query = db.query(SectionAnnotation)
    
    # Filter by annotator if specified
    if annotator_id:
        question_query = question_query.filter(QuestionAnnotation.annotator_id == annotator_id)
        section_query = section_query.filter(SectionAnnotation.annotator_id == annotator_id)
    
    # Count annotations
    question_count = question_query.count()
    section_count = section_query.count()
    
    # Get average scores
    question_annotations = question_query.all()
    section_annotations = section_query.all()
    
    if question_annotations:
        avg_question_quality = sum(qa.quality for qa in question_annotations) / len(question_annotations)
        avg_question_relevant = sum(qa.relevant for qa in question_annotations) / len(question_annotations)
        avg_question_pillars = {
            'methodological_rigor': sum(qa.methodological_rigor for qa in question_annotations) / len(question_annotations),
            'content_validity': sum(qa.content_validity for qa in question_annotations) / len(question_annotations),
            'respondent_experience': sum(qa.respondent_experience for qa in question_annotations) / len(question_annotations),
            'analytical_value': sum(qa.analytical_value for qa in question_annotations) / len(question_annotations),
            'business_impact': sum(qa.business_impact for qa in question_annotations) / len(question_annotations),
        }
    else:
        avg_question_quality = 0
        avg_question_relevant = 0
        avg_question_pillars = {}
    
    if section_annotations:
        avg_section_quality = sum(sa.quality for sa in section_annotations) / len(section_annotations)
        avg_section_relevant = sum(sa.relevant for sa in section_annotations) / len(section_annotations)
        avg_section_pillars = {
            'methodological_rigor': sum(sa.methodological_rigor for sa in section_annotations) / len(section_annotations),
            'content_validity': sum(sa.content_validity for sa in section_annotations) / len(section_annotations),
            'respondent_experience': sum(sa.respondent_experience for sa in section_annotations) / len(section_annotations),
            'analytical_value': sum(sa.analytical_value for sa in section_annotations) / len(section_annotations),
            'business_impact': sum(sa.business_impact for sa in section_annotations) / len(section_annotations),
        }
    else:
        avg_section_quality = 0
        avg_section_relevant = 0
        avg_section_pillars = {}
    
    return {
        "question_annotations": {
            "count": question_count,
            "avg_quality": round(avg_question_quality, 2),
            "avg_relevant": round(avg_question_relevant, 2),
            "avg_pillars": {k: round(v, 2) for k, v in avg_question_pillars.items()}
        },
        "section_annotations": {
            "count": section_count,
            "avg_quality": round(avg_section_quality, 2),
            "avg_relevant": round(avg_section_relevant, 2),
            "avg_pillars": {k: round(v, 2) for k, v in avg_section_pillars.items()}
        },
        "total_annotations": question_count + section_count
    }

@router.post("/annotations/survey/{survey_id}/advanced-labeling")
def apply_advanced_labeling(
    survey_id: str,
    db: Session = Depends(get_db)
):
    """Apply advanced labeling to all annotations for a survey"""

    try:
        # Initialize advanced labeling service
        labeling_service = AdvancedLabelingService(db)

        # Apply bulk labeling
        results = labeling_service.apply_bulk_labeling(survey_id)

        return {
            "message": "Advanced labeling applied successfully",
            "results": results
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply advanced labeling: {str(e)}"
        )

@router.get("/annotations/survey/{survey_id}/compliance-report")
def get_compliance_report(
    survey_id: str,
    db: Session = Depends(get_db)
):
    """Get compliance report for a survey"""

    try:
        # Get survey annotation
        survey_annotation = db.query(SurveyAnnotation).filter(
            SurveyAnnotation.survey_id == survey_id
        ).first()

        if not survey_annotation or not survey_annotation.compliance_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Compliance report not found. Run advanced labeling first."
            )

        return {
            "survey_id": survey_id,
            "compliance_report": survey_annotation.compliance_report,
            "advanced_metadata": survey_annotation.advanced_metadata
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get compliance report: {str(e)}"
        )

@router.get("/annotations/survey/{survey_id}/detected-labels")
def get_detected_labels(
    survey_id: str,
    db: Session = Depends(get_db)
):
    """Get detected labels for a survey"""

    try:
        # Get survey annotation
        survey_annotation = db.query(SurveyAnnotation).filter(
            SurveyAnnotation.survey_id == survey_id
        ).first()

        if not survey_annotation or not survey_annotation.detected_labels:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Detected labels not found. Run advanced labeling first."
            )

        return {
            "survey_id": survey_id,
            "detected_labels": survey_annotation.detected_labels
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get detected labels: {str(e)}"
        )

# Survey-Level Annotation Endpoints

@router.post("/surveys/{survey_id}/survey-annotation", response_model=SurveyLevelAnnotationResponse)
def create_or_update_survey_annotation(
    survey_id: str,
    annotation: SurveyLevelAnnotationRequest,
    db: Session = Depends(get_db)
):
    """Create or update survey-level annotation"""
    
    try:
        # Check if survey annotation already exists
        existing_annotation = db.query(SurveyAnnotation).filter(
            SurveyAnnotation.survey_id == survey_id
        ).first()
        
        if existing_annotation:
            # Update existing annotation
            existing_annotation.overall_comment = annotation.overall_comment
            existing_annotation.annotator_id = annotation.annotator_id
            existing_annotation.detected_labels = annotation.detected_labels
            existing_annotation.compliance_report = annotation.compliance_report
            existing_annotation.advanced_metadata = annotation.advanced_metadata
            existing_annotation.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(existing_annotation)
            return existing_annotation
        else:
            # Create new annotation
            new_annotation = SurveyAnnotation(
                survey_id=survey_id,
                overall_comment=annotation.overall_comment,
                annotator_id=annotation.annotator_id,
                detected_labels=annotation.detected_labels,
                compliance_report=annotation.compliance_report,
                advanced_metadata=annotation.advanced_metadata
            )
            
            db.add(new_annotation)
            db.commit()
            db.refresh(new_annotation)
            return new_annotation
            
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save survey annotation: {str(e)}"
        )

@router.get("/surveys/{survey_id}/survey-annotation", response_model=SurveyLevelAnnotationResponse)
def get_survey_annotation(
    survey_id: str,
    db: Session = Depends(get_db)
):
    """Get survey-level annotation"""
    
    try:
        annotation = db.query(SurveyAnnotation).filter(
            SurveyAnnotation.survey_id == survey_id
        ).first()
        
        if not annotation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Survey annotation not found"
            )
        
        return annotation
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get survey annotation: {str(e)}"
        )







@router.post("/annotations/migrate-ai-flags")
def migrate_ai_flags(db: Session = Depends(get_db)):
    """
    Migration endpoint to fix annotations with annotator_id='ai_system' but ai_generated=False
    """
    try:
        # Find all annotations with ai_system annotator but ai_generated=False
        inconsistent_annotations = db.query(QuestionAnnotation).filter(
            QuestionAnnotation.annotator_id == "ai_system",
            QuestionAnnotation.ai_generated == False
        ).all()
        
        logger.info(f"🔧 [Migration] Found {len(inconsistent_annotations)} inconsistent question annotations")
        
        # Update them to have ai_generated=True
        for annotation in inconsistent_annotations:
            annotation.ai_generated = True
            annotation.human_verified = False
            if not annotation.generation_timestamp:
                annotation.generation_timestamp = datetime.now()
        
        # Also check section annotations
        inconsistent_sections = db.query(SectionAnnotation).filter(
            SectionAnnotation.annotator_id == "ai_system",
            SectionAnnotation.ai_generated == False
        ).all()
        
        logger.info(f"🔧 [Migration] Found {len(inconsistent_sections)} inconsistent section annotations")
        
        for annotation in inconsistent_sections:
            annotation.ai_generated = True
            annotation.human_verified = False
            if not annotation.generation_timestamp:
                annotation.generation_timestamp = datetime.now()
        
        db.commit()
        
        total_fixed = len(inconsistent_annotations) + len(inconsistent_sections)
        logger.info(f"✅ [Migration] Fixed {total_fixed} inconsistent annotations")
        
        return {
            "message": f"Successfully migrated {total_fixed} annotations",
            "question_annotations_fixed": len(inconsistent_annotations),
            "section_annotations_fixed": len(inconsistent_sections)
        }
        
    except Exception as e:
        logger.error(f"❌ [Migration] Error during migration: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")