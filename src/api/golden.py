from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from src.database import get_db
from src.services.golden_service import GoldenService
from src.services.document_parser import document_parser, DocumentParsingError
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/golden-pairs", tags=["Golden Standards"])


class GoldenPairResponse(BaseModel):
    id: str
    title: Optional[str]
    rfq_text: str
    survey_json: Dict[Any, Any]
    methodology_tags: Optional[List[str]]
    industry_category: Optional[str]
    research_goal: Optional[str]
    quality_score: Optional[float]
    usage_count: int


class CreateGoldenPairRequest(BaseModel):
    title: Optional[str] = None
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
):
    """
    List available golden standards with usage stats
    """
    golden_service = GoldenService(db)
    golden_pairs = golden_service.list_golden_pairs(skip=skip, limit=limit)
    
    return [
        GoldenPairResponse(
            id=str(pair.id),
            title=getattr(pair, 'title', None),
            rfq_text=pair.rfq_text,
            survey_json=pair.survey_json,
            methodology_tags=pair.methodology_tags,
            industry_category=pair.industry_category,
            research_goal=pair.research_goal,
            quality_score=float(pair.quality_score) if pair.quality_score else None,
            usage_count=pair.usage_count
        )
        for pair in golden_pairs
    ]


@router.post("/", response_model=GoldenPairResponse)
async def create_golden_pair(
    request: CreateGoldenPairRequest,
    db: Session = Depends(get_db)
):
    """
    Add new golden standard (requires quality_score)
    """
    try:
        golden_service = GoldenService(db)
        golden_pair = await golden_service.create_golden_pair(
            rfq_text=request.rfq_text,
            survey_json=request.survey_json,
            title=request.title,
            methodology_tags=request.methodology_tags,
            industry_category=request.industry_category,
            research_goal=request.research_goal,
            quality_score=request.quality_score
        )
        
        return GoldenPairResponse(
            id=str(golden_pair.id),
            title=getattr(golden_pair, 'title', None),
            rfq_text=golden_pair.rfq_text,
            survey_json=golden_pair.survey_json,
            methodology_tags=golden_pair.methodology_tags,
            industry_category=golden_pair.industry_category,
            research_goal=golden_pair.research_goal,
            quality_score=float(golden_pair.quality_score) if golden_pair.quality_score else None,
            usage_count=golden_pair.usage_count
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create golden pair: {str(e)}")


@router.put("/{golden_id}", response_model=GoldenPairResponse)
async def update_golden_pair(
    golden_id: UUID,
    request: CreateGoldenPairRequest,
    db: Session = Depends(get_db)
):
    """
    Update existing golden pair
    """
    try:
        golden_service = GoldenService(db)
        golden_pair = golden_service.update_golden_pair(
            golden_id=golden_id,
            rfq_text=request.rfq_text,
            survey_json=request.survey_json,
            methodology_tags=request.methodology_tags,
            industry_category=request.industry_category,
            research_goal=request.research_goal,
            quality_score=request.quality_score
        )
        
        return GoldenPairResponse(
            id=str(golden_pair.id),
            rfq_text=golden_pair.rfq_text,
            survey_json=golden_pair.survey_json,
            methodology_tags=golden_pair.methodology_tags or [],
            industry_category=golden_pair.industry_category or "General",
            research_goal=golden_pair.research_goal or "Market Research",
            quality_score=float(golden_pair.quality_score) if golden_pair.quality_score else None,
            usage_count=golden_pair.usage_count
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update golden pair: {str(e)}")


@router.delete("/{golden_id}")
async def delete_golden_pair(
    golden_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a golden pair
    """
    try:
        golden_service = GoldenService(db)
        success = golden_service.delete_golden_pair(golden_id=golden_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Golden pair not found")
        
        return {"status": "success", "message": "Golden pair deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete golden pair: {str(e)}")


@router.put("/{golden_id}/validate")
async def validate_golden_pair(
    golden_id: UUID,
    validation: ValidationRequest,
    db: Session = Depends(get_db)
):
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


class DocumentParseResponse(BaseModel):
    survey_json: Dict[Any, Any]
    confidence_score: Optional[float]
    extracted_text: str


@router.post("/parse-document", response_model=DocumentParseResponse)
async def parse_document(
    file: UploadFile = File(...),
):
    """
    Parse a DOCX document and convert it to survey JSON using LLM.
    Returns the parsed JSON and metadata for review before creating a golden pair.
    """
    logger.info(f"📄 [Document Parse] Starting document parsing for file: {file.filename}")
    
    # Validate file type
    if not file.filename or not file.filename.lower().endswith('.docx'):
        logger.warning(f"❌ [Document Parse] Invalid file type: {file.filename}")
        raise HTTPException(
            status_code=400, 
            detail="Only DOCX files are supported"
        )
    
    try:
        logger.info(f"📖 [Document Parse] Reading file content for: {file.filename}")
        # Read file content
        file_content = await file.read()
        logger.info(f"✅ [Document Parse] File read successfully, size: {len(file_content)} bytes")
        
        logger.info(f"🤖 [Document Parse] Starting LLM parsing for: {file.filename}")
        # Parse document using LLM
        survey_data = await document_parser.parse_document(file_content)
        logger.info(f"✅ [Document Parse] LLM parsing completed for: {file.filename}")
        
        logger.info(f"📝 [Document Parse] Extracting text preview for: {file.filename}")
        # Extract text for preview
        extracted_text = document_parser.extract_text_from_docx(file_content)
        logger.info(f"✅ [Document Parse] Text extraction completed, length: {len(extracted_text)} chars")
        
        # Log survey data structure for debugging
        logger.info(f"📊 [Document Parse] Survey data keys: {list(survey_data.keys()) if isinstance(survey_data, dict) else 'Not a dict'}")
        if isinstance(survey_data, dict):
            logger.info(f"📊 [Document Parse] Survey title: {survey_data.get('title', 'No title')}")
            logger.info(f"📊 [Document Parse] Questions count: {len(survey_data.get('questions', []))}")
            logger.info(f"📊 [Document Parse] Confidence score: {survey_data.get('confidence_score', 'No score')}")
        
        response = DocumentParseResponse(
            survey_json=survey_data,
            confidence_score=survey_data.get('confidence_score'),
            extracted_text=extracted_text[:1000] + "..." if len(extracted_text) > 1000 else extracted_text
        )
        
        logger.info(f"🎉 [Document Parse] Successfully parsed document: {file.filename}")
        return response
        
    except DocumentParsingError as e:
        logger.error(f"❌ [Document Parse] Document parsing error for {file.filename}: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"❌ [Document Parse] Unexpected error parsing {file.filename}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to parse document: {str(e)}")