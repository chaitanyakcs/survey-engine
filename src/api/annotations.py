"""
API endpoints for survey annotations
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from src.database.connection import get_db
from src.database.models import QuestionAnnotation, SectionAnnotation, SurveyAnnotation
from src.services.advanced_labeling_service import AdvancedLabelingService

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
    annotator_id: str = "current-user"

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
    labels: Optional[List[str]]
    annotator_id: str
    created_at: datetime
    updated_at: Optional[datetime]

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
    labels: Optional[List[str]]
    annotator_id: str
    created_at: datetime
    updated_at: Optional[datetime]

    # Advanced labeling fields
    section_classification: Optional[str] = None
    mandatory_elements: Optional[Dict[str, Any]] = None
    compliance_score: Optional[int] = None

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
    db: Session = Depends(get_db)
):
    """Get all annotations for a survey"""
    
    # Get question annotations
    question_annotations = db.query(QuestionAnnotation).filter(
        and_(
            QuestionAnnotation.survey_id == survey_id,
            QuestionAnnotation.annotator_id == annotator_id
        )
    ).all()
    
    # Get section annotations
    section_annotations = db.query(SectionAnnotation).filter(
        and_(
            SectionAnnotation.survey_id == survey_id,
            SectionAnnotation.annotator_id == annotator_id
        )
    ).all()
    
    # Get survey-level annotation
    survey_annotation = db.query(SurveyAnnotation).filter(
        and_(
            SurveyAnnotation.survey_id == survey_id,
            SurveyAnnotation.annotator_id == annotator_id
        )
    ).first()
    
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
    
    return SurveyAnnotationsResponse(
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
                comment=qa.comment,
                labels=qa.labels,
                annotator_id=qa.annotator_id,
                created_at=qa.created_at,
                updated_at=qa.updated_at
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
                comment=sa.comment,
                labels=sa.labels,
                annotator_id=sa.annotator_id,
                created_at=sa.created_at,
                updated_at=sa.updated_at,
                # Advanced labeling fields
                section_classification=sa.section_classification,
                mandatory_elements=sa.mandatory_elements,
                compliance_score=sa.compliance_score
            ) for sa in section_annotations
        ],
        overall_comment=survey_annotation.overall_comment if survey_annotation else None,
        annotator_id=annotator_id,
        created_at=created_at,
        updated_at=updated_at,
        # Advanced labeling fields
        detected_labels=survey_annotation.detected_labels if survey_annotation else None,
        compliance_report=survey_annotation.compliance_report if survey_annotation else None,
        advanced_metadata=survey_annotation.advanced_metadata if survey_annotation else None
    )

@router.post("/annotations/survey/{survey_id}/bulk")
def save_bulk_annotations(
    survey_id: str,
    annotations: BulkAnnotationRequest,
    db: Session = Depends(get_db)
):
    """Save multiple annotations for a survey in bulk"""
    
    try:
        # Process question annotations
        for qa_req in annotations.question_annotations:
            # Check if annotation already exists
            existing_qa = db.query(QuestionAnnotation).filter(
                and_(
                    QuestionAnnotation.question_id == qa_req.question_id,
                    QuestionAnnotation.annotator_id == qa_req.annotator_id
                )
            ).first()
            
            if existing_qa:
                # Update existing annotation
                existing_qa.required = qa_req.required
                existing_qa.quality = qa_req.quality
                existing_qa.relevant = qa_req.relevant
                existing_qa.methodological_rigor = qa_req.methodological_rigor
                existing_qa.content_validity = qa_req.content_validity
                existing_qa.respondent_experience = qa_req.respondent_experience
                existing_qa.analytical_value = qa_req.analytical_value
                existing_qa.business_impact = qa_req.business_impact
                existing_qa.comment = qa_req.comment
                existing_qa.labels = qa_req.labels
                existing_qa.updated_at = datetime.now()
            else:
                # Create new annotation
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
                    comment=qa_req.comment,
                    labels=qa_req.labels,
                    annotator_id=qa_req.annotator_id
                )
                db.add(new_qa)
        
        # Process section annotations
        for sa_req in annotations.section_annotations:
            # Check if annotation already exists
            existing_sa = db.query(SectionAnnotation).filter(
                and_(
                    SectionAnnotation.section_id == sa_req.section_id,
                    SectionAnnotation.annotator_id == sa_req.annotator_id
                )
            ).first()
            
            if existing_sa:
                # Update existing annotation
                existing_sa.quality = sa_req.quality
                existing_sa.relevant = sa_req.relevant
                existing_sa.methodological_rigor = sa_req.methodological_rigor
                existing_sa.content_validity = sa_req.content_validity
                existing_sa.respondent_experience = sa_req.respondent_experience
                existing_sa.analytical_value = sa_req.analytical_value
                existing_sa.business_impact = sa_req.business_impact
                existing_sa.comment = sa_req.comment
                existing_sa.labels = sa_req.labels
                existing_sa.updated_at = datetime.now()
                # Update advanced labeling fields
                existing_sa.section_classification = sa_req.section_classification
                existing_sa.mandatory_elements = sa_req.mandatory_elements
                existing_sa.compliance_score = sa_req.compliance_score
            else:
                # Create new annotation
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
                    comment=sa_req.comment,
                    labels=sa_req.labels,
                    annotator_id=sa_req.annotator_id,
                    # Advanced labeling fields
                    section_classification=sa_req.section_classification,
                    mandatory_elements=sa_req.mandatory_elements,
                    compliance_score=sa_req.compliance_score
                )
                db.add(new_sa)
        
        # Process survey-level annotation
        if annotations.overall_comment or annotations.detected_labels or annotations.compliance_report or annotations.advanced_metadata:
            existing_survey_ann = db.query(SurveyAnnotation).filter(
                and_(
                    SurveyAnnotation.survey_id == survey_id,
                    SurveyAnnotation.annotator_id == annotations.annotator_id
                )
            ).first()

            if existing_survey_ann:
                existing_survey_ann.overall_comment = annotations.overall_comment
                existing_survey_ann.updated_at = datetime.now()
                # Update advanced labeling fields
                existing_survey_ann.detected_labels = annotations.detected_labels
                existing_survey_ann.compliance_report = annotations.compliance_report
                existing_survey_ann.advanced_metadata = annotations.advanced_metadata
            else:
                new_survey_ann = SurveyAnnotation(
                    survey_id=survey_id,
                    overall_comment=annotations.overall_comment,
                    annotator_id=annotations.annotator_id,
                    # Advanced labeling fields
                    detected_labels=annotations.detected_labels,
                    compliance_report=annotations.compliance_report,
                    advanced_metadata=annotations.advanced_metadata
                )
                db.add(new_survey_ann)
        
        # Commit all changes
        db.commit()
        
        return {"message": "Annotations saved successfully", "survey_id": survey_id}
        
    except Exception as e:
        db.rollback()
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

@router.delete("/surveys/{survey_id}/survey-annotation")
def delete_survey_annotation(
    survey_id: str,
    db: Session = Depends(get_db)
):
    """Delete survey-level annotation"""
    
    try:
        annotation = db.query(SurveyAnnotation).filter(
            SurveyAnnotation.survey_id == survey_id
        ).first()
        
        if not annotation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Survey annotation not found"
            )
        
        db.delete(annotation)
        db.commit()
        
        return {"message": "Survey annotation deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete survey annotation: {str(e)}"
        )