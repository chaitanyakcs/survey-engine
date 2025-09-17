from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src.database.models import SystemPromptAudit
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/system-prompt-audit", tags=["System Prompt Audit"])


class SystemPromptAuditResponse(BaseModel):
    id: str
    survey_id: str
    rfq_id: Optional[str]
    system_prompt: str
    prompt_type: str
    model_version: Optional[str]
    generation_context: Optional[dict]
    created_at: str


class SystemPromptAuditListResponse(BaseModel):
    prompts: List[SystemPromptAuditResponse]
    total_count: int


@router.get("/survey/{survey_id}", response_model=SystemPromptAuditListResponse)
async def get_system_prompts_for_survey(
    survey_id: str,
    prompt_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all system prompts used for a specific survey
    """
    try:
        logger.info(f"🔍 [SystemPromptAudit API] Getting prompts for survey: {survey_id}")
        
        # Build query
        query = db.query(SystemPromptAudit).filter(SystemPromptAudit.survey_id == survey_id)
        
        if prompt_type:
            query = query.filter(SystemPromptAudit.prompt_type == prompt_type)
        
        # Order by creation time (newest first)
        query = query.order_by(SystemPromptAudit.created_at.desc())
        
        # Execute query
        audit_records = query.all()
        
        logger.info(f"✅ [SystemPromptAudit API] Found {len(audit_records)} prompt records for survey {survey_id}")
        
        # Convert to response format
        prompts = []
        for record in audit_records:
            prompts.append(SystemPromptAuditResponse(
                id=str(record.id),
                survey_id=record.survey_id,
                rfq_id=str(record.rfq_id) if record.rfq_id else None,
                system_prompt=record.system_prompt,
                prompt_type=record.prompt_type,
                model_version=record.model_version,
                generation_context=record.generation_context,
                created_at=record.created_at.isoformat() if record.created_at else ""
            ))
        
        return SystemPromptAuditListResponse(
            prompts=prompts,
            total_count=len(prompts)
        )
        
    except Exception as e:
        logger.error(f"❌ [SystemPromptAudit API] Error getting prompts for survey {survey_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get system prompts: {str(e)}")


@router.get("/{audit_id}", response_model=SystemPromptAuditResponse)
async def get_system_prompt_by_id(
    audit_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific system prompt audit record by ID
    """
    try:
        logger.info(f"🔍 [SystemPromptAudit API] Getting prompt by ID: {audit_id}")
        
        record = db.query(SystemPromptAudit).filter(SystemPromptAudit.id == audit_id).first()
        
        if not record:
            logger.warning(f"❌ [SystemPromptAudit API] Prompt not found: {audit_id}")
            raise HTTPException(status_code=404, detail="System prompt not found")
        
        logger.info(f"✅ [SystemPromptAudit API] Found prompt record: {audit_id}")
        
        return SystemPromptAuditResponse(
            id=str(record.id),
            survey_id=record.survey_id,
            rfq_id=str(record.rfq_id) if record.rfq_id else None,
            system_prompt=record.system_prompt,
            prompt_type=record.prompt_type,
            model_version=record.model_version,
            generation_context=record.generation_context,
            created_at=record.created_at.isoformat() if record.created_at else ""
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [SystemPromptAudit API] Error getting prompt {audit_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get system prompt: {str(e)}")


@router.get("/", response_model=SystemPromptAuditListResponse)
async def list_system_prompts(
    skip: int = 0,
    limit: int = 50,
    prompt_type: Optional[str] = None,
    survey_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List system prompt audit records with optional filtering
    """
    try:
        logger.info(f"🔍 [SystemPromptAudit API] Listing prompts - skip: {skip}, limit: {limit}")
        
        # Build query
        query = db.query(SystemPromptAudit)
        
        if prompt_type:
            query = query.filter(SystemPromptAudit.prompt_type == prompt_type)
        
        if survey_id:
            query = query.filter(SystemPromptAudit.survey_id == survey_id)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        audit_records = query.order_by(SystemPromptAudit.created_at.desc()).offset(skip).limit(limit).all()
        
        logger.info(f"✅ [SystemPromptAudit API] Found {len(audit_records)} prompt records (total: {total_count})")
        
        # Convert to response format
        prompts = []
        for record in audit_records:
            prompts.append(SystemPromptAuditResponse(
                id=str(record.id),
                survey_id=record.survey_id,
                rfq_id=str(record.rfq_id) if record.rfq_id else None,
                system_prompt=record.system_prompt,
                prompt_type=record.prompt_type,
                model_version=record.model_version,
                generation_context=record.generation_context,
                created_at=record.created_at.isoformat() if record.created_at else ""
            ))
        
        return SystemPromptAuditListResponse(
            prompts=prompts,
            total_count=total_count
        )
        
    except Exception as e:
        logger.error(f"❌ [SystemPromptAudit API] Error listing prompts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list system prompts: {str(e)}")

