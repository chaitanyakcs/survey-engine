from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from src.database import get_db
from src.database.models import LLMAudit
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/system-prompt-audit", tags=["System Prompt Audit"])


class LLMAuditResponse(BaseModel):
    id: str
    interaction_id: str
    parent_workflow_id: Optional[str]
    parent_survey_id: Optional[str]
    parent_rfq_id: Optional[str]
    model_name: str
    model_provider: str
    model_version: Optional[str]
    purpose: str
    sub_purpose: Optional[str]
    context_type: Optional[str]
    input_prompt: str
    input_tokens: Optional[int]
    output_content: Optional[str]
    output_tokens: Optional[int]
    temperature: Optional[float]
    top_p: Optional[float]
    max_tokens: Optional[int]
    frequency_penalty: Optional[float]
    presence_penalty: Optional[float]
    stop_sequences: Optional[List[str]]
    response_time_ms: Optional[int]
    cost_usd: Optional[float]
    success: bool
    error_message: Optional[str]
    interaction_metadata: Optional[dict]
    tags: Optional[List[str]]
    created_at: str
    updated_at: str


class SystemPromptAuditListResponse(BaseModel):
    llm_interactions: List[LLMAuditResponse]
    total_count: int


@router.get("/survey/{survey_id}", response_model=SystemPromptAuditListResponse)
async def get_system_prompts_for_survey(
    survey_id: str,
    purpose: Optional[str] = Query(None, description="Filter by purpose (e.g., 'survey_generation', 'evaluation')"),
    context_type: Optional[str] = Query(None, description="Filter by context type (e.g., 'generation', 'validation')"),
    db: Session = Depends(get_db)
):
    """
    Get all LLM interactions (including system prompts) for a specific survey
    """
    try:
        logger.info(f"🔍 [SystemPromptAudit API] Getting LLM interactions for survey: {survey_id}")

        # Get LLM Audit records for this survey
        query = db.query(LLMAudit).filter(LLMAudit.parent_survey_id == survey_id)
        
        # Apply filters
        if purpose:
            query = query.filter(LLMAudit.purpose == purpose)
        if context_type:
            query = query.filter(LLMAudit.context_type == context_type)
        
        # Order by creation date (newest first)
        query = query.order_by(LLMAudit.created_at.desc())
        llm_records = query.all()

        logger.info(f"✅ [SystemPromptAudit API] Found {len(llm_records)} LLM interactions for survey {survey_id}")

        # Convert LLMAudit to response format
        llm_interactions = []
        for record in llm_records:
            llm_interactions.append(LLMAuditResponse(
                id=str(record.id),
                interaction_id=record.interaction_id,
                parent_workflow_id=record.parent_workflow_id,
                parent_survey_id=record.parent_survey_id,
                parent_rfq_id=str(record.parent_rfq_id) if record.parent_rfq_id else None,
                model_name=record.model_name,
                model_provider=record.model_provider,
                model_version=record.model_version,
                purpose=record.purpose,
                sub_purpose=record.sub_purpose,
                context_type=record.context_type,
                input_prompt=record.input_prompt,
                input_tokens=record.input_tokens,
                output_content=record.output_content,
                output_tokens=record.output_tokens,
                temperature=float(record.temperature) if record.temperature else None,
                top_p=float(record.top_p) if record.top_p else None,
                max_tokens=record.max_tokens,
                frequency_penalty=float(record.frequency_penalty) if record.frequency_penalty else None,
                presence_penalty=float(record.presence_penalty) if record.presence_penalty else None,
                stop_sequences=record.stop_sequences,
                response_time_ms=record.response_time_ms,
                cost_usd=float(record.cost_usd) if record.cost_usd else None,
                success=record.success,
                error_message=record.error_message,
                interaction_metadata=record.interaction_metadata,
                tags=record.tags,
                created_at=record.created_at.isoformat() if record.created_at else "",
                updated_at=record.updated_at.isoformat() if record.updated_at else ""
            ))

        return SystemPromptAuditListResponse(
            llm_interactions=llm_interactions,
            total_count=len(llm_interactions)
        )

    except Exception as e:
        logger.error(f"❌ [SystemPromptAudit API] Error getting LLM interactions for survey {survey_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get LLM interactions: {str(e)}")


@router.get("/{interaction_id}", response_model=LLMAuditResponse)
async def get_llm_interaction_by_id(
    interaction_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific LLM interaction by interaction_id
    """
    try:
        logger.info(f"🔍 [SystemPromptAudit API] Getting LLM interaction by ID: {interaction_id}")
        
        record = db.query(LLMAudit).filter(LLMAudit.interaction_id == interaction_id).first()
        
        if not record:
            logger.warning(f"❌ [SystemPromptAudit API] LLM interaction not found: {interaction_id}")
            raise HTTPException(status_code=404, detail="LLM interaction not found")
        
        logger.info(f"✅ [SystemPromptAudit API] Found LLM interaction: {interaction_id}")
        
        return LLMAuditResponse(
            id=str(record.id),
            interaction_id=record.interaction_id,
            parent_workflow_id=record.parent_workflow_id,
            parent_survey_id=record.parent_survey_id,
            parent_rfq_id=str(record.parent_rfq_id) if record.parent_rfq_id else None,
            model_name=record.model_name,
            model_provider=record.model_provider,
            model_version=record.model_version,
            purpose=record.purpose,
            sub_purpose=record.sub_purpose,
            context_type=record.context_type,
            input_prompt=record.input_prompt,
            input_tokens=record.input_tokens,
            output_content=record.output_content,
            output_tokens=record.output_tokens,
            temperature=float(record.temperature) if record.temperature else None,
            top_p=float(record.top_p) if record.top_p else None,
            max_tokens=record.max_tokens,
            frequency_penalty=float(record.frequency_penalty) if record.frequency_penalty else None,
            presence_penalty=float(record.presence_penalty) if record.presence_penalty else None,
            stop_sequences=record.stop_sequences,
            response_time_ms=record.response_time_ms,
            cost_usd=float(record.cost_usd) if record.cost_usd else None,
            success=record.success,
            error_message=record.error_message,
            interaction_metadata=record.interaction_metadata,
            tags=record.tags,
            created_at=record.created_at.isoformat() if record.created_at else "",
            updated_at=record.updated_at.isoformat() if record.updated_at else ""
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [SystemPromptAudit API] Error getting LLM interaction {interaction_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get LLM interaction: {str(e)}")


@router.get("/", response_model=SystemPromptAuditListResponse)
async def list_llm_interactions(
    skip: int = 0,
    limit: int = 50,
    purpose: Optional[str] = Query(None, description="Filter by purpose"),
    context_type: Optional[str] = Query(None, description="Filter by context type"),
    survey_id: Optional[str] = Query(None, description="Filter by survey ID"),
    db: Session = Depends(get_db)
):
    """
    List LLM interactions with optional filtering
    """
    try:
        logger.info(f"🔍 [SystemPromptAudit API] Listing LLM interactions - skip: {skip}, limit: {limit}")
        
        # Build query
        query = db.query(LLMAudit)
        
        if purpose:
            query = query.filter(LLMAudit.purpose == purpose)
        if context_type:
            query = query.filter(LLMAudit.context_type == context_type)
        if survey_id:
            query = query.filter(LLMAudit.parent_survey_id == survey_id)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        llm_records = query.order_by(LLMAudit.created_at.desc()).offset(skip).limit(limit).all()
        
        logger.info(f"✅ [SystemPromptAudit API] Found {len(llm_records)} LLM interactions (total: {total_count})")
        
        # Convert to response format
        llm_interactions = []
        for record in llm_records:
            llm_interactions.append(LLMAuditResponse(
                id=str(record.id),
                interaction_id=record.interaction_id,
                parent_workflow_id=record.parent_workflow_id,
                parent_survey_id=record.parent_survey_id,
                parent_rfq_id=str(record.parent_rfq_id) if record.parent_rfq_id else None,
                model_name=record.model_name,
                model_provider=record.model_provider,
                model_version=record.model_version,
                purpose=record.purpose,
                sub_purpose=record.sub_purpose,
                context_type=record.context_type,
                input_prompt=record.input_prompt,
                input_tokens=record.input_tokens,
                output_content=record.output_content,
                output_tokens=record.output_tokens,
                temperature=float(record.temperature) if record.temperature else None,
                top_p=float(record.top_p) if record.top_p else None,
                max_tokens=record.max_tokens,
                frequency_penalty=float(record.frequency_penalty) if record.frequency_penalty else None,
                presence_penalty=float(record.presence_penalty) if record.presence_penalty else None,
                stop_sequences=record.stop_sequences,
                response_time_ms=record.response_time_ms,
                cost_usd=float(record.cost_usd) if record.cost_usd else None,
                success=record.success,
                error_message=record.error_message,
                interaction_metadata=record.interaction_metadata,
                tags=record.tags,
                created_at=record.created_at.isoformat() if record.created_at else "",
                updated_at=record.updated_at.isoformat() if record.updated_at else ""
            ))
        
        return SystemPromptAuditListResponse(
            llm_interactions=llm_interactions,
            total_count=total_count
        )
        
    except Exception as e:
        logger.error(f"❌ [SystemPromptAudit API] Error listing LLM interactions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list LLM interactions: {str(e)}")