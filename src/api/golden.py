from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from src.database import get_db
from src.api.dependencies import require_models_ready
from src.services.golden_service import GoldenService
from src.services.golden_state_service import GoldenStateService
from src.services.document_parser import document_parser, DocumentParsingError
from src.utils.error_messages import UserFriendlyError, create_error_response
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
    rfq_text: Optional[str] = None  # Made optional - will be auto-generated if not provided
    survey_json: Dict[Any, Any]
    methodology_tags: Optional[List[str]] = None
    industry_category: Optional[str] = None
    research_goal: Optional[str] = None
    quality_score: Optional[float] = None  # Made optional to match frontend
    auto_generate_rfq: Optional[bool] = False  # Flag to indicate if RFQ should be auto-generated


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
    db: Session = Depends(get_db),
    _: bool = Depends(require_models_ready)
):
    """
    Add new golden standard (requires quality_score)
    """
    logger.info(f"🏆 [Golden Pair API] Starting golden pair creation")
    logger.info(f"📝 [Golden Pair API] Request data - title: {request.title}, rfq_text_length: {len(request.rfq_text) if request.rfq_text else 0}")
    logger.info(f"📊 [Golden Pair API] Survey JSON keys: {list(request.survey_json.keys()) if isinstance(request.survey_json, dict) else 'Not a dict'}")
    logger.info(f"🏷️ [Golden Pair API] Methodology tags: {request.methodology_tags}")
    logger.info(f"🏭 [Golden Pair API] Industry category: {request.industry_category}")
    logger.info(f"🎯 [Golden Pair API] Research goal: {request.research_goal}")
    logger.info(f"⭐ [Golden Pair API] Quality score: {request.quality_score}")
    
    try:
        logger.info(f"🔧 [Golden Pair API] Initializing GoldenService")
        golden_service = GoldenService(db)
        
        # Validate that we have enough information to create a meaningful title
        survey_title = request.survey_json.get('title', '').strip() if isinstance(request.survey_json, dict) else ''
        golden_title = (request.title or '').strip()
        
        # Check if we have any meaningful title information
        has_survey_title = bool(survey_title)
        has_golden_title = bool(golden_title)
        has_industry = bool(request.industry_category)
        has_methodology = bool(request.methodology_tags)
        
        if not (has_survey_title or has_golden_title or has_industry or has_methodology):
            logger.warning(f"⚠️ [Golden Pair API] Insufficient information for meaningful title generation")
            logger.warning(f"⚠️ [Golden Pair API] Survey title: '{survey_title}', Golden title: '{golden_title}', Industry: '{request.industry_category}', Methodology: '{request.methodology_tags}'")
            # Don't fail, but log a warning - the service will generate a fallback title
        
        # Handle missing RFQ text
        rfq_text = request.rfq_text
        if not rfq_text or not rfq_text.strip():
            if request.auto_generate_rfq:
                logger.info(f"🤖 [Golden Pair API] RFQ text is empty and auto_generate_rfq is True, will auto-generate from survey")
            else:
                logger.info(f"📝 [Golden Pair API] RFQ text is empty and auto_generate_rfq is False - will create golden example without RFQ")
        else:
            logger.info(f"📝 [Golden Pair API] Using provided RFQ text (length: {len(rfq_text)})")

        logger.info(f"💾 [Golden Pair API] Calling golden_service.create_golden_pair")
        golden_pair = await golden_service.create_golden_pair(
            rfq_text=rfq_text,
            survey_json=request.survey_json,
            title=request.title,
            methodology_tags=request.methodology_tags,
            industry_category=request.industry_category,
            research_goal=request.research_goal,
            quality_score=request.quality_score,
            auto_generate_rfq=request.auto_generate_rfq
        )
        
        logger.info(f"✅ [Golden Pair API] Golden pair created successfully with ID: {golden_pair.id}")
        logger.info(f"📋 [Golden Pair API] Created pair details - title: {getattr(golden_pair, 'title', None)}, quality_score: {golden_pair.quality_score}")
        
        response = GoldenPairResponse(
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
        
        logger.info(f"🎉 [Golden Pair API] Successfully created golden pair: {response.id}")
        return response
        
    except Exception as e:
        logger.error(f"❌ [Golden Pair API] Failed to create golden pair: {str(e)}", exc_info=True)
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
        logger.error(f"❌ [Golden API] Failed to update golden pair {golden_id}: {str(e)}", exc_info=True)
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
    product_category: Optional[str] = None
    research_goal: Optional[str] = None
    methodologies: Optional[List[str]] = None


@router.post("/parse-document", response_model=DocumentParseResponse)
async def parse_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
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
        # Parse document using LLM with database session for audit
        from src.services.document_parser import DocumentParser
        document_parser = DocumentParser(db_session=db)
        survey_data = await document_parser.parse_document(file_content)
        logger.info(f"✅ [Document Parse] LLM parsing completed for: {file.filename}")
        
        # Log detailed survey data structure for debugging
        logger.info(f"📊 [Document Parse] Survey data type: {type(survey_data)}")
        logger.info(f"📊 [Document Parse] Survey data keys: {list(survey_data.keys()) if isinstance(survey_data, dict) else 'Not a dict'}")
        if isinstance(survey_data, dict):
            logger.info(f"📊 [Document Parse] Survey title: {survey_data.get('title', 'No title')}")
            description = survey_data.get('description', 'No description')
            desc_preview = description[:100] if description is not None else '<null>'
            logger.info(f"📊 [Document Parse] Survey description: {desc_preview}...")
            logger.info(f"📊 [Document Parse] Questions count: {len(survey_data.get('questions', []))}")
            logger.info(f"📊 [Document Parse] Confidence score: {survey_data.get('confidence_score', 'No score')}")
            logger.info(f"📊 [Document Parse] Methodologies: {survey_data.get('methodologies', [])}")
            logger.info(f"📊 [Document Parse] Full survey data: {survey_data}")
        else:
            logger.error(f"❌ [Document Parse] Survey data is not a dictionary: {survey_data}")
        
        logger.info(f"📝 [Document Parse] Extracting text preview for: {file.filename}")
        # Extract text for preview
        extracted_text = await document_parser.extract_text_from_docx(file_content)
        logger.info(f"✅ [Document Parse] Text extraction completed, length: {len(extracted_text)} chars")
        logger.info(f"📝 [Document Parse] Extracted text preview: {extracted_text[:200]}...")
        
        # Extract metadata from the correct structure
        # The parsed data has final_output containing the actual survey data
        final_output = survey_data.get('final_output', {}) if isinstance(survey_data, dict) else {}
        
        # Run field extraction to populate category, goal, and methodology
        logger.info(f"🔍 [Document Parse] Running field extraction for metadata")
        try:
            from src.services.field_extraction_service import FieldExtractionService
            field_extractor = FieldExtractionService()
            extracted_fields = await field_extractor.extract_fields(extracted_text, final_output)
            logger.info(f"✅ [Document Parse] Field extraction completed: {extracted_fields}")
        except Exception as e:
            logger.warning(f"⚠️ [Document Parse] Field extraction failed: {e}")
            extracted_fields = {}
        
        response = DocumentParseResponse(
            survey_json=survey_data,
            confidence_score=final_output.get('confidence_score') if isinstance(final_output, dict) else None,
            extracted_text=extracted_text[:1000] + "..." if len(extracted_text) > 1000 else extracted_text,
            product_category=extracted_fields.get('industry_category') or final_output.get('product_category') if isinstance(final_output, dict) else None,
            research_goal=extracted_fields.get('research_goal') or final_output.get('research_goal') if isinstance(final_output, dict) else None,
            methodologies=extracted_fields.get('methodology_tags') or final_output.get('methodologies') if isinstance(final_output, dict) else None
        )
        
        logger.info(f"🎉 [Document Parse] Successfully parsed document: {file.filename}")
        logger.info(f"📤 [Document Parse] Response prepared - survey_json_keys: {list(response.survey_json.keys()) if isinstance(response.survey_json, dict) else 'Not a dict'}")
        logger.info(f"📊 [Document Parse] Metadata fields - product_category: {response.product_category}, research_goal: {response.research_goal}, methodologies: {response.methodologies}")
        return response
        
    except UserFriendlyError as e:
        logger.error(f"❌ [Document Parse] User-friendly error for {file.filename}: {str(e)}")
        error_response = create_error_response(e, f"document parsing for {file.filename}")
        raise HTTPException(status_code=422, detail=error_response)
    except DocumentParsingError as e:
        logger.error(f"❌ [Document Parse] Document parsing error for {file.filename}: {str(e)}")
        error_response = create_error_response(e, f"document parsing for {file.filename}")
        raise HTTPException(status_code=422, detail=error_response)
    except Exception as e:
        logger.error(f"❌ [Document Parse] Unexpected error parsing {file.filename}: {str(e)}", exc_info=True)
        error_response = create_error_response(e, f"document parsing for {file.filename}")
        raise HTTPException(status_code=500, detail=error_response)


# State Management Endpoints

class SaveStateRequest(BaseModel):
    session_id: str
    state_data: Dict[str, Any]


@router.post("/state/save")
async def save_golden_example_state(
    request: SaveStateRequest,
    db: Session = Depends(get_db)
):
    """Save golden example creation state"""
    try:
        service = GoldenStateService(db)
        success = service.save_state(request.session_id, request.state_data)
        
        if success:
            logger.info(f"💾 [Golden State] Saved state for session: {request.session_id}")
            return {"status": "success", "session_id": request.session_id}
        else:
            logger.error(f"❌ [Golden State] Failed to save state for session: {request.session_id}")
            raise HTTPException(status_code=500, detail="Failed to save state")
    except Exception as e:
        logger.error(f"❌ [Golden State] Error saving state: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving state: {str(e)}")


@router.get("/state/{session_id}")
async def load_golden_example_state(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Load golden example creation state"""
    try:
        service = GoldenStateService(db)
        state_data = service.load_state(session_id)
        
        if state_data:
            logger.info(f"📂 [Golden State] Loaded state for session: {session_id}")
            return {"status": "success", "state_data": state_data}
        else:
            logger.warning(f"⚠️ [Golden State] No state found for session: {session_id}")
            raise HTTPException(status_code=404, detail="State not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [Golden State] Error loading state: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error loading state: {str(e)}")


@router.delete("/state/{session_id}")
async def delete_golden_example_state(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Delete golden example state after successful creation"""
    try:
        service = GoldenStateService(db)
        success = service.delete_state(session_id)
        
        if success:
            logger.info(f"🗑️ [Golden State] Deleted state for session: {session_id}")
            return {"status": "success", "message": "State deleted successfully"}
        else:
            logger.warning(f"⚠️ [Golden State] No state found to delete for session: {session_id}")
            return {"status": "success", "message": "No state found to delete"}
    except Exception as e:
        logger.error(f"❌ [Golden State] Error deleting state: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting state: {str(e)}")


# ============================================================================
# GOLDEN CONTENT USAGE TRACKING
# ============================================================================

class QuestionUsageResponse(BaseModel):
    survey_id: str
    survey_title: Optional[str]
    rfq_title: Optional[str]
    used_at: str
    golden_pair_id: Optional[str] = None


class SectionUsageResponse(BaseModel):
    survey_id: str
    survey_title: Optional[str]
    rfq_title: Optional[str]
    used_at: str
    golden_pair_id: Optional[str] = None


@router.get("/questions/{question_id}/usage", response_model=List[QuestionUsageResponse])
async def get_question_usage_history(
    question_id: UUID,
    db: Session = Depends(get_db),
    limit: int = 10
):
    """
    Get usage history for a specific golden question.
    Returns list of surveys that used this question.
    """
    try:
        from sqlalchemy import text
        
        query = text("""
            SELECT 
                s.id as survey_id,
                s.created_at as used_at,
                r.title as rfq_title,
                gq.golden_pair_id
            FROM golden_question_usage gqu
            JOIN surveys s ON gqu.survey_id = s.id
            LEFT JOIN rfqs r ON s.rfq_id = r.id
            LEFT JOIN golden_questions gq ON gqu.golden_question_id = gq.id
            WHERE gqu.golden_question_id = :question_id
            ORDER BY gqu.used_at DESC
            LIMIT :limit
        """)
        
        result = db.execute(query, {"question_id": question_id, "limit": limit})
        rows = result.fetchall()
        
        usage_history = []
        for row in rows:
            usage_history.append(QuestionUsageResponse(
                survey_id=str(row.survey_id),
                survey_title=None,  # TODO: Extract from survey JSON if needed
                rfq_title=row.rfq_title,
                used_at=row.used_at.isoformat() if row.used_at else None,
                golden_pair_id=str(row.golden_pair_id) if row.golden_pair_id else None
            ))
        
        logger.info(f"📊 Retrieved {len(usage_history)} usage records for question {question_id}")
        return usage_history
        
    except Exception as e:
        logger.error(f"❌ Error fetching question usage history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching usage history: {str(e)}")


@router.get("/sections/{section_id}/usage", response_model=List[SectionUsageResponse])
async def get_section_usage_history(
    section_id: UUID,
    db: Session = Depends(get_db),
    limit: int = 10
):
    """
    Get usage history for a specific golden section.
    Returns list of surveys that used this section.
    """
    try:
        from sqlalchemy import text
        
        query = text("""
            SELECT 
                s.id as survey_id,
                s.created_at as used_at,
                r.title as rfq_title,
                gs.golden_pair_id
            FROM golden_section_usage gsu
            JOIN surveys s ON gsu.survey_id = s.id
            LEFT JOIN rfqs r ON s.rfq_id = r.id
            LEFT JOIN golden_sections gs ON gsu.golden_section_id = gs.id
            WHERE gsu.golden_section_id = :section_id
            ORDER BY gsu.used_at DESC
            LIMIT :limit
        """)
        
        result = db.execute(query, {"section_id": section_id, "limit": limit})
        rows = result.fetchall()
        
        usage_history = []
        for row in rows:
            usage_history.append(SectionUsageResponse(
                survey_id=str(row.survey_id),
                survey_title=None,  # TODO: Extract from survey JSON if needed
                rfq_title=row.rfq_title,
                used_at=row.used_at.isoformat() if row.used_at else None,
                golden_pair_id=str(row.golden_pair_id) if row.golden_pair_id else None
            ))
        
        logger.info(f"📊 Retrieved {len(usage_history)} usage records for section {section_id}")
        return usage_history
        
    except Exception as e:
        logger.error(f"❌ Error fetching section usage history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching usage history: {str(e)}")


class MetadataOptionsResponse(BaseModel):
    question_types: List[str]
    question_subtypes: List[str]
    methodology_tags: List[str]
    industry_keywords: List[str]
    question_patterns: List[str]


@router.get("/metadata-options", response_model=MetadataOptionsResponse)
async def get_metadata_options(
    db: Session = Depends(get_db)
):
    """
    Get all unique metadata values from existing golden questions and sections.
    Used to populate dropdown options in the golden question edit UI.
    """
    try:
        from sqlalchemy import text
        from src.database.models import GoldenQuestion, GoldenSection
        
        logger.info("📊 [Golden API] Fetching metadata options")
        
        # Predefined common options
        common_question_types = [
            'multiple_choice', 'rating_scale', 'open_text', 'yes_no', 
            'single_choice', 'matrix', 'ranking', 'slider', 'dropdown',
            'nps', 'van_westendorp', 'gabor_granger', 'conjoint', 'maxdiff',
            'constant_sum', 'numeric_grid', 'numeric_open', 'matrix_likert'
        ]
        
        common_question_subtypes = [
            'likert_5', 'likert_7', 'binary', 'text_input', 'dropdown',
            'radio', 'checkbox', 'nps', 'slider', 'number', 'currency'
        ]
        
        common_methodology_tags = [
            'mixed_methods', 'quantitative', 'qualitative', 'conjoint_analysis',
            'van_westendorp', 'max_diff', 'brand_tracking', 'customer_satisfaction',
            'market_segmentation', 'pricing_research', 'concept_testing', 'nps',
            'gabor_granger', 'attitudinal', 'behavioral', 'competitive_analysis'
        ]
        
        common_question_patterns = [
            'likelihood', 'satisfaction', 'frequency', 'awareness', 'preference',
            'importance', 'agreement', 'recommendation', 'purchase_intent',
            'usage_behavior', 'demographic', 'screening'
        ]
        
        # Get unique values from database
        questions_query = text("""
            SELECT DISTINCT 
                unnest(methodology_tags) as methodology_tag,
                unnest(industry_keywords) as industry_keyword,
                unnest(question_patterns) as question_pattern
            FROM golden_questions
            WHERE methodology_tags IS NOT NULL 
               OR industry_keywords IS NOT NULL
               OR question_patterns IS NOT NULL
        """)
        
        sections_query = text("""
            SELECT DISTINCT 
                unnest(methodology_tags) as methodology_tag,
                unnest(industry_keywords) as industry_keyword
            FROM golden_sections
            WHERE methodology_tags IS NOT NULL 
               OR industry_keywords IS NOT NULL
        """)
        
        # Execute queries
        questions_result = db.execute(questions_query).fetchall()
        sections_result = db.execute(sections_query).fetchall()
        
        # Aggregate unique values
        db_methodology_tags = set()
        db_industry_keywords = set()
        db_question_patterns = set()
        
        for row in questions_result:
            if row.methodology_tag:
                db_methodology_tags.add(row.methodology_tag)
            if row.industry_keyword:
                db_industry_keywords.add(row.industry_keyword)
            if row.question_pattern:
                db_question_patterns.add(row.question_pattern)
        
        for row in sections_result:
            if row.methodology_tag:
                db_methodology_tags.add(row.methodology_tag)
            if row.industry_keyword:
                db_industry_keywords.add(row.industry_keyword)
        
        # Combine common options with database values (deduplicated)
        methodology_tags = sorted(set(common_methodology_tags) | db_methodology_tags)
        industry_keywords = sorted(db_industry_keywords)
        question_patterns = sorted(set(common_question_patterns) | db_question_patterns)
        
        response = MetadataOptionsResponse(
            question_types=common_question_types,
            question_subtypes=common_question_subtypes,
            methodology_tags=methodology_tags,
            industry_keywords=industry_keywords,
            question_patterns=question_patterns
        )
        
        logger.info(f"✅ [Golden API] Metadata options fetched: {len(methodology_tags)} methodology tags, {len(industry_keywords)} industry keywords, {len(question_patterns)} question patterns")
        
        return response
        
    except Exception as e:
        logger.error(f"❌ [Golden API] Error fetching metadata options: {str(e)}", exc_info=True)
        # Return fallback with common options only
        return MetadataOptionsResponse(
            question_types=common_question_types,
            question_subtypes=common_question_subtypes,
            methodology_tags=common_methodology_tags,
            industry_keywords=[],
            question_patterns=common_question_patterns
        )