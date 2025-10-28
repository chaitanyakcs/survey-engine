from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from src.database import get_db
from src.services.golden_content_service import GoldenContentService
from src.utils.error_messages import UserFriendlyError, create_error_response
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/golden-content", tags=["Golden Content"])


def parse_labels_to_list(labels_field) -> List[str]:
    """Parse labels field (which can be dict, list, string, or None) to List[str]"""
    if labels_field is None:
        return []
    if isinstance(labels_field, list):
        # If it's already a list, convert all items to strings
        return [str(item) for item in labels_field]
    if isinstance(labels_field, dict):
        # If it's a dict, extract the values or keys
        return [str(v) for v in labels_field.values() if v]
    if isinstance(labels_field, str):
        # If it's a string, return as single-item list
        return [labels_field]
    return []


class GoldenSectionResponse(BaseModel):
    id: str
    section_id: str
    golden_pair_id: Optional[str]
    annotation_id: Optional[int]
    section_title: Optional[str]
    section_text: str
    section_type: Optional[str]
    methodology_tags: List[str]
    industry_keywords: List[str]
    question_patterns: List[str]
    quality_score: Optional[float]
    usage_count: int
    human_verified: bool
    labels: List[str]
    created_at: str
    updated_at: str


class GoldenQuestionResponse(BaseModel):
    id: str
    question_id: str
    golden_pair_id: Optional[str]
    annotation_id: Optional[int]
    question_text: str
    question_type: Optional[str]
    question_subtype: Optional[str]
    methodology_tags: List[str]
    industry_keywords: List[str]
    question_patterns: List[str]
    quality_score: Optional[float]
    usage_count: int
    human_verified: bool
    labels: List[str]
    created_at: str
    updated_at: str


class AnalyticsResponse(BaseModel):
    total_sections: int
    total_questions: int
    human_verified_sections: int
    human_verified_questions: int
    avg_section_quality: float
    avg_question_quality: float
    top_section_types: List[Dict[str, Any]]
    top_question_types: List[Dict[str, Any]]
    methodology_coverage: Dict[str, int]
    industry_coverage: Dict[str, int]


class SectionUpdateRequest(BaseModel):
    section_title: Optional[str] = None
    section_text: Optional[str] = None
    section_type: Optional[str] = None
    methodology_tags: Optional[List[str]] = None
    industry_keywords: Optional[List[str]] = None
    question_patterns: Optional[List[str]] = None
    quality_score: Optional[float] = None
    human_verified: Optional[bool] = None
    labels: Optional[List[str]] = None


class QuestionUpdateRequest(BaseModel):
    question_text: Optional[str] = None
    question_type: Optional[str] = None
    question_subtype: Optional[str] = None
    methodology_tags: Optional[List[str]] = None
    industry_keywords: Optional[List[str]] = None
    question_patterns: Optional[List[str]] = None
    quality_score: Optional[float] = None
    human_verified: Optional[bool] = None
    labels: Optional[List[str]] = None


# Sections endpoints
@router.get("/sections", response_model=List[GoldenSectionResponse])
async def list_golden_sections(
    db: Session = Depends(get_db),
    section_type: Optional[str] = Query(None, description="Filter by section type"),
    methodology_tags: Optional[str] = Query(None, description="Comma-separated methodology tags"),
    industry: Optional[str] = Query(None, description="Filter by industry keyword"),
    min_quality_score: Optional[float] = Query(None, description="Minimum quality score"),
    human_verified: Optional[bool] = Query(None, description="Filter by human verification status"),
    search: Optional[str] = Query(None, description="Search in section text and title"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return")
):
    """
    List golden sections with filtering and pagination
    """
    try:
        service = GoldenContentService(db)
        
        # Parse methodology tags
        methodology_list = None
        if methodology_tags:
            methodology_list = [tag.strip() for tag in methodology_tags.split(',') if tag.strip()]
        
        filters = {
            'section_type': section_type,
            'methodology_tags': methodology_list,
            'industry': industry,
            'min_quality_score': min_quality_score,
            'human_verified': human_verified,
            'search': search
        }
        
        sections = await service.list_sections(filters, skip, limit)
        
        return [
            GoldenSectionResponse(
                id=str(section.id),
                section_id=section.section_id,
                golden_pair_id=str(section.golden_pair_id) if section.golden_pair_id else None,
                annotation_id=section.annotation_id,
                section_title=section.section_title,
                section_text=section.section_text,
                section_type=section.section_type,
                methodology_tags=section.methodology_tags or [],
                industry_keywords=section.industry_keywords or [],
                question_patterns=section.question_patterns or [],
                quality_score=float(section.quality_score) if section.quality_score else None,
                usage_count=section.usage_count,
                human_verified=section.human_verified,
                labels=parse_labels_to_list(section.labels),
                created_at=section.created_at.isoformat(),
                updated_at=section.updated_at.isoformat()
            )
            for section in sections
        ]
        
    except Exception as e:
        logger.error(f"❌ [Golden Content API] Failed to list sections: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list sections: {str(e)}")


@router.get("/sections/{section_id}", response_model=GoldenSectionResponse)
async def get_golden_section(
    section_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a single golden section by ID
    """
    try:
        service = GoldenContentService(db)
        section = await service.get_section(section_id)
        
        if not section:
            raise HTTPException(status_code=404, detail="Golden section not found")
        
        return GoldenSectionResponse(
            id=str(section.id),
            section_id=section.section_id,
            golden_pair_id=str(section.golden_pair_id) if section.golden_pair_id else None,
            annotation_id=section.annotation_id,
            section_title=section.section_title,
            section_text=section.section_text,
            section_type=section.section_type,
            methodology_tags=section.methodology_tags or [],
            industry_keywords=section.industry_keywords or [],
            question_patterns=section.question_patterns or [],
            quality_score=float(section.quality_score) if section.quality_score else None,
            usage_count=section.usage_count,
            human_verified=section.human_verified,
            labels=parse_labels_to_list(section.labels),
            created_at=section.created_at.isoformat(),
            updated_at=section.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [Golden Content API] Failed to get section {section_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get section: {str(e)}")


@router.put("/sections/{section_id}", response_model=GoldenSectionResponse)
async def update_golden_section(
    section_id: UUID,
    request: SectionUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update a golden section
    """
    try:
        service = GoldenContentService(db)
        
        # Convert to dict, excluding None values
        updates = {k: v for k, v in request.dict().items() if v is not None}
        
        section = await service.update_section(section_id, updates)
        
        if not section:
            raise HTTPException(status_code=404, detail="Golden section not found")
        
        return GoldenSectionResponse(
            id=str(section.id),
            section_id=section.section_id,
            golden_pair_id=str(section.golden_pair_id) if section.golden_pair_id else None,
            annotation_id=section.annotation_id,
            section_title=section.section_title,
            section_text=section.section_text,
            section_type=section.section_type,
            methodology_tags=section.methodology_tags or [],
            industry_keywords=section.industry_keywords or [],
            question_patterns=section.question_patterns or [],
            quality_score=float(section.quality_score) if section.quality_score else None,
            usage_count=section.usage_count,
            human_verified=section.human_verified,
            labels=parse_labels_to_list(section.labels),
            created_at=section.created_at.isoformat(),
            updated_at=section.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [Golden Content API] Failed to update section {section_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update section: {str(e)}")


@router.delete("/sections/{section_id}")
async def delete_golden_section(
    section_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a golden section
    """
    try:
        service = GoldenContentService(db)
        success = await service.delete_section(section_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Golden section not found")
        
        return {"status": "success", "message": "Golden section deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [Golden Content API] Failed to delete section {section_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete section: {str(e)}")


# Questions endpoints
@router.get("/questions", response_model=List[GoldenQuestionResponse])
async def list_golden_questions(
    db: Session = Depends(get_db),
    question_type: Optional[str] = Query(None, description="Filter by question type"),
    question_subtype: Optional[str] = Query(None, description="Filter by question subtype"),
    methodology_tags: Optional[str] = Query(None, description="Comma-separated methodology tags"),
    industry: Optional[str] = Query(None, description="Filter by industry keyword"),
    min_quality_score: Optional[float] = Query(None, description="Minimum quality score"),
    human_verified: Optional[bool] = Query(None, description="Filter by human verification status"),
    search: Optional[str] = Query(None, description="Search in question text"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return")
):
    """
    List golden questions with filtering and pagination
    """
    try:
        service = GoldenContentService(db)
        
        # Parse methodology tags
        methodology_list = None
        if methodology_tags:
            methodology_list = [tag.strip() for tag in methodology_tags.split(',') if tag.strip()]
        
        filters = {
            'question_type': question_type,
            'question_subtype': question_subtype,
            'methodology_tags': methodology_list,
            'industry': industry,
            'min_quality_score': min_quality_score,
            'human_verified': human_verified,
            'search': search
        }
        
        questions = await service.list_questions(filters, skip, limit)
        
        return [
            GoldenQuestionResponse(
                id=str(question.id),
                question_id=question.question_id,
                golden_pair_id=str(question.golden_pair_id) if question.golden_pair_id else None,
                annotation_id=question.annotation_id,
                question_text=question.question_text,
                question_type=question.question_type,
                question_subtype=question.question_subtype,
                methodology_tags=question.methodology_tags or [],
                industry_keywords=question.industry_keywords or [],
                question_patterns=question.question_patterns or [],
                quality_score=float(question.quality_score) if question.quality_score else None,
                usage_count=question.usage_count,
                human_verified=question.human_verified,
                labels=parse_labels_to_list(question.labels),
                created_at=question.created_at.isoformat(),
                updated_at=question.updated_at.isoformat()
            )
            for question in questions
        ]
        
    except Exception as e:
        logger.error(f"❌ [Golden Content API] Failed to list questions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list questions: {str(e)}")


@router.get("/questions/{question_id}", response_model=GoldenQuestionResponse)
async def get_golden_question(
    question_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a single golden question by ID
    """
    try:
        service = GoldenContentService(db)
        question = await service.get_question(question_id)
        
        if not question:
            raise HTTPException(status_code=404, detail="Golden question not found")
        
        return GoldenQuestionResponse(
            id=str(question.id),
            question_id=question.question_id,
            golden_pair_id=str(question.golden_pair_id) if question.golden_pair_id else None,
            annotation_id=question.annotation_id,
            question_text=question.question_text,
            question_type=question.question_type,
            question_subtype=question.question_subtype,
            methodology_tags=question.methodology_tags or [],
            industry_keywords=question.industry_keywords or [],
            question_patterns=question.question_patterns or [],
            quality_score=float(question.quality_score) if question.quality_score else None,
            usage_count=question.usage_count,
            human_verified=question.human_verified,
            labels=parse_labels_to_list(question.labels),
            created_at=question.created_at.isoformat(),
            updated_at=question.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [Golden Content API] Failed to get question {question_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get question: {str(e)}")


@router.put("/questions/{question_id}", response_model=GoldenQuestionResponse)
async def update_golden_question(
    question_id: UUID,
    request: QuestionUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update a golden question
    """
    try:
        service = GoldenContentService(db)
        
        # Convert to dict, excluding None values
        updates = {k: v for k, v in request.dict().items() if v is not None}
        
        question = await service.update_question(question_id, updates)
        
        if not question:
            raise HTTPException(status_code=404, detail="Golden question not found")
        
        return GoldenQuestionResponse(
            id=str(question.id),
            question_id=question.question_id,
            golden_pair_id=str(question.golden_pair_id) if question.golden_pair_id else None,
            annotation_id=question.annotation_id,
            question_text=question.question_text,
            question_type=question.question_type,
            question_subtype=question.question_subtype,
            methodology_tags=question.methodology_tags or [],
            industry_keywords=question.industry_keywords or [],
            question_patterns=question.question_patterns or [],
            quality_score=float(question.quality_score) if question.quality_score else None,
            usage_count=question.usage_count,
            human_verified=question.human_verified,
            labels=parse_labels_to_list(question.labels),
            created_at=question.created_at.isoformat(),
            updated_at=question.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [Golden Content API] Failed to update question {question_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update question: {str(e)}")


@router.delete("/questions/{question_id}")
async def delete_golden_question(
    question_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a golden question
    """
    try:
        service = GoldenContentService(db)
        success = await service.delete_question(question_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Golden question not found")
        
        return {"status": "success", "message": "Golden question deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [Golden Content API] Failed to delete question {question_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete question: {str(e)}")


# Analytics endpoint
@router.get("/analytics", response_model=AnalyticsResponse)
async def get_golden_content_analytics(
    db: Session = Depends(get_db)
):
    """
    Get analytics for golden content usage and quality
    """
    try:
        service = GoldenContentService(db)
        analytics = await service.get_analytics()
        
        return AnalyticsResponse(**analytics)
        
    except Exception as e:
        logger.error(f"❌ [Golden Content API] Failed to get analytics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")
