from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src.services.golden_service import GoldenService
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID

router = APIRouter(prefix="/golden-pairs", tags=["Golden Standards"])


class GoldenPairResponse(BaseModel):
    id: str
    rfq_text: str
    survey_json: Dict[Any, Any]
    methodology_tags: Optional[List[str]]
    industry_category: Optional[str]
    research_goal: Optional[str]
    quality_score: Optional[float]
    usage_count: int


class CreateGoldenPairRequest(BaseModel):
    rfq_text: str
    survey_json: Dict[Any, Any]
    methodology_tags: Optional[List[str]] = None
    industry_category: Optional[str] = None
    research_goal: Optional[str] = None
    quality_score: float


class ValidationRequest(BaseModel):
    expert_validation: bool
    quality_score: Optional[float] = None


@router.get("/", response_model=List[GoldenPairResponse])
async def list_golden_pairs(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
) -> List[GoldenPairResponse]:
    """
    List available golden standards with usage stats
    """
    golden_service = GoldenService(db)
    golden_pairs = golden_service.list_golden_pairs(skip=skip, limit=limit)
    
    return [
        GoldenPairResponse(
            id=str(pair.id),
            rfq_text=pair.rfq_text,  # type: ignore
            survey_json=pair.survey_json,  # type: ignore
            methodology_tags=pair.methodology_tags,  # type: ignore
            industry_category=pair.industry_category,  # type: ignore
            research_goal=pair.research_goal,  # type: ignore
            quality_score=float(pair.quality_score) if pair.quality_score else None,  # type: ignore
            usage_count=pair.usage_count  # type: ignore
        )
        for pair in golden_pairs
    ]


@router.post("/", response_model=GoldenPairResponse)
async def create_golden_pair(
    request: CreateGoldenPairRequest,
    db: Session = Depends(get_db)
) -> GoldenPairResponse:
    """
    Add new golden standard (requires quality_score)
    """
    try:
        golden_service = GoldenService(db)
        golden_pair = await golden_service.create_golden_pair(
            rfq_text=request.rfq_text,
            survey_json=request.survey_json,
            methodology_tags=request.methodology_tags,
            industry_category=request.industry_category,
            research_goal=request.research_goal,
            quality_score=request.quality_score
        )
        
        return GoldenPairResponse(
            id=str(golden_pair.id),
            rfq_text=golden_pair.rfq_text,  # type: ignore
            survey_json=golden_pair.survey_json,  # type: ignore
            methodology_tags=golden_pair.methodology_tags,  # type: ignore
            industry_category=golden_pair.industry_category,  # type: ignore
            research_goal=golden_pair.research_goal,  # type: ignore
            quality_score=float(golden_pair.quality_score) if golden_pair.quality_score else None,  # type: ignore
            usage_count=golden_pair.usage_count  # type: ignore
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create golden pair: {str(e)}")


@router.put("/{golden_id}/validate")
async def validate_golden_pair(
    golden_id: UUID,
    validation: ValidationRequest,
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    """
    Expert validation of golden pair
    """
    try:
        golden_service = GoldenService(db)
        result = golden_service.validate_golden_pair(
            golden_id=golden_id,
            expert_validation=validation.expert_validation,
            quality_score=validation.quality_score
        )
        
        return {"status": "success", "validation_result": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate golden pair: {str(e)}")