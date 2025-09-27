"""
LLM Audit API

This module provides API endpoints for managing and monitoring LLM interactions,
hyperparameter configurations, and prompt templates.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
import logging

from src.database import get_db
from src.services.llm_audit_service import LLMAuditService
from src.database.models import LLMAudit, LLMHyperparameterConfig, LLMPromptTemplate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/llm-audit", tags=["LLM Audit"])


# Pydantic models for API responses

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
    interaction_metadata: Optional[Dict[str, Any]]
    tags: Optional[List[str]]
    created_at: str
    updated_at: str


class LLMAuditListResponse(BaseModel):
    records: List[LLMAuditResponse]
    total_count: int
    page: int
    page_size: int


class LLMHyperparameterConfigResponse(BaseModel):
    id: str
    config_name: str
    purpose: str
    sub_purpose: Optional[str]
    temperature: float
    top_p: float
    max_tokens: int
    frequency_penalty: float
    presence_penalty: float
    stop_sequences: List[str]
    preferred_models: List[str]
    fallback_models: List[str]
    description: Optional[str]
    is_active: bool
    is_default: bool
    created_at: str
    updated_at: str


class LLMPromptTemplateResponse(BaseModel):
    id: str
    template_name: str
    purpose: str
    sub_purpose: Optional[str]
    system_prompt_template: str
    user_prompt_template: Optional[str]
    template_variables: Dict[str, Any]
    description: Optional[str]
    version: str
    is_active: bool
    is_default: bool
    created_at: str
    updated_at: str


class CostSummaryResponse(BaseModel):
    total_cost_usd: float
    total_interactions: int
    successful_interactions: int
    success_rate: float
    cost_by_purpose: List[Dict[str, Any]]
    cost_by_model: List[Dict[str, Any]]


class CreateHyperparameterConfigRequest(BaseModel):
    config_name: str = Field(..., description="Unique name for the configuration")
    purpose: str = Field(..., description="Primary purpose (survey_generation, evaluation, etc.)")
    sub_purpose: Optional[str] = Field(None, description="Specific sub-purpose")
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    top_p: float = Field(0.9, ge=0.0, le=1.0)
    max_tokens: int = Field(8000, gt=0)
    frequency_penalty: float = Field(0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(0.0, ge=-2.0, le=2.0)
    stop_sequences: List[str] = Field(default_factory=list)
    preferred_models: List[str] = Field(default_factory=list)
    fallback_models: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    is_default: bool = False


class CreatePromptTemplateRequest(BaseModel):
    template_name: str = Field(..., description="Unique name for the template")
    purpose: str = Field(..., description="Primary purpose (survey_generation, evaluation, etc.)")
    sub_purpose: Optional[str] = Field(None, description="Specific sub-purpose")
    system_prompt_template: str = Field(..., description="System prompt template with placeholders")
    user_prompt_template: Optional[str] = Field(None, description="User prompt template with placeholders")
    template_variables: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None
    is_default: bool = False


# API Endpoints

@router.get("/interactions", response_model=LLMAuditListResponse)
async def get_llm_interactions(
    purpose: Optional[str] = Query(None, description="Filter by purpose"),
    sub_purpose: Optional[str] = Query(None, description="Filter by sub-purpose"),
    model_name: Optional[str] = Query(None, description="Filter by model name"),
    success: Optional[bool] = Query(None, description="Filter by success status"),
    parent_workflow_id: Optional[str] = Query(None, description="Filter by parent workflow ID"),
    parent_survey_id: Optional[str] = Query(None, description="Filter by parent survey ID"),
    parent_rfq_id: Optional[str] = Query(None, description="Filter by parent RFQ ID"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db)
):
    """Get LLM interaction audit records with filtering options"""
    try:
        audit_service = LLMAuditService(db)
        
        offset = (page - 1) * page_size
        records, total_count = await audit_service.get_audit_records(
            purpose=purpose,
            sub_purpose=sub_purpose,
            model_name=model_name,
            success=success,
            parent_workflow_id=parent_workflow_id,
            parent_survey_id=parent_survey_id,
            parent_rfq_id=parent_rfq_id,
            start_date=start_date,
            end_date=end_date,
            limit=page_size,
            offset=offset
        )
        
        # Convert to response format
        audit_responses = []
        for record in records:
            audit_responses.append(LLMAuditResponse(
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
                cost_usd=None,  # Hidden for now
                success=record.success,
                error_message=record.error_message,
                interaction_metadata=record.interaction_metadata,
                tags=record.tags,
                created_at=record.created_at.isoformat() if record.created_at else "",
                updated_at=record.updated_at.isoformat() if record.updated_at else ""
            ))
        
        return LLMAuditListResponse(
            records=audit_responses,
            total_count=total_count,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"❌ [LLM Audit API] Error getting interactions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get LLM interactions: {str(e)}")


@router.get("/interactions/{interaction_id}", response_model=LLMAuditResponse)
async def get_llm_interaction(
    interaction_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific LLM interaction by interaction ID"""
    try:
        record = db.query(LLMAudit).filter(LLMAudit.interaction_id == interaction_id).first()
        
        if not record:
            raise HTTPException(status_code=404, detail="LLM interaction not found")
        
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
            cost_usd=None,  # Hidden for now
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
        logger.error(f"❌ [LLM Audit API] Error getting interaction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get LLM interaction: {str(e)}")


@router.get("/cost-summary", response_model=CostSummaryResponse)
async def get_cost_summary(
    start_date: Optional[datetime] = Query(None, description="Start date for cost analysis"),
    end_date: Optional[datetime] = Query(None, description="End date for cost analysis"),
    purpose: Optional[str] = Query(None, description="Filter by purpose"),
    model_name: Optional[str] = Query(None, description="Filter by model name"),
    db: Session = Depends(get_db)
):
    """Get cost summary for LLM interactions - Cost tracking disabled for now"""
    try:
        # Return empty cost summary since cost tracking is disabled
        return CostSummaryResponse(
            total_cost_usd=0.0,
            total_interactions=0,
            successful_interactions=0,
            success_rate=0.0,
            cost_by_purpose=[],
            cost_by_model=[]
        )
        
    except Exception as e:
        logger.error(f"❌ [LLM Audit API] Error getting cost summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get cost summary: {str(e)}")


# Hyperparameter Configuration Endpoints

@router.get("/hyperparameter-configs", response_model=List[LLMHyperparameterConfigResponse])
async def get_hyperparameter_configs(
    purpose: Optional[str] = Query(None, description="Filter by purpose"),
    sub_purpose: Optional[str] = Query(None, description="Filter by sub-purpose"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db)
):
    """Get hyperparameter configurations"""
    try:
        query = db.query(LLMHyperparameterConfig)
        
        if purpose:
            query = query.filter(LLMHyperparameterConfig.purpose == purpose)
        if sub_purpose:
            query = query.filter(LLMHyperparameterConfig.sub_purpose == sub_purpose)
        if is_active is not None:
            query = query.filter(LLMHyperparameterConfig.is_active == is_active)
        
        configs = query.order_by(LLMHyperparameterConfig.purpose, LLMHyperparameterConfig.config_name).all()
        
        return [
            LLMHyperparameterConfigResponse(
                id=str(config.id),
                config_name=config.config_name,
                purpose=config.purpose,
                sub_purpose=config.sub_purpose,
                temperature=float(config.temperature),
                top_p=float(config.top_p),
                max_tokens=config.max_tokens,
                frequency_penalty=float(config.frequency_penalty),
                presence_penalty=float(config.presence_penalty),
                stop_sequences=config.stop_sequences or [],
                preferred_models=config.preferred_models or [],
                fallback_models=config.fallback_models or [],
                description=config.description,
                is_active=config.is_active,
                is_default=config.is_default,
                created_at=config.created_at.isoformat() if config.created_at else "",
                updated_at=config.updated_at.isoformat() if config.updated_at else ""
            )
            for config in configs
        ]
        
    except Exception as e:
        logger.error(f"❌ [LLM Audit API] Error getting hyperparameter configs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get hyperparameter configs: {str(e)}")


@router.post("/hyperparameter-configs", response_model=LLMHyperparameterConfigResponse)
async def create_hyperparameter_config(
    request: CreateHyperparameterConfigRequest,
    db: Session = Depends(get_db)
):
    """Create a new hyperparameter configuration"""
    try:
        audit_service = LLMAuditService(db)
        
        config_id = await audit_service.create_hyperparameter_config(
            config_name=request.config_name,
            purpose=request.purpose,
            sub_purpose=request.sub_purpose,
            hyperparameters={
                'temperature': request.temperature,
                'top_p': request.top_p,
                'max_tokens': request.max_tokens,
                'frequency_penalty': request.frequency_penalty,
                'presence_penalty': request.presence_penalty,
                'stop_sequences': request.stop_sequences
            },
            preferred_models=request.preferred_models,
            fallback_models=request.fallback_models,
            description=request.description,
            is_default=request.is_default
        )
        
        # Return the created config
        config = db.query(LLMHyperparameterConfig).filter(LLMHyperparameterConfig.id == config_id).first()
        
        return LLMHyperparameterConfigResponse(
            id=str(config.id),
            config_name=config.config_name,
            purpose=config.purpose,
            sub_purpose=config.sub_purpose,
            temperature=float(config.temperature),
            top_p=float(config.top_p),
            max_tokens=config.max_tokens,
            frequency_penalty=float(config.frequency_penalty),
            presence_penalty=float(config.presence_penalty),
            stop_sequences=config.stop_sequences or [],
            preferred_models=config.preferred_models or [],
            fallback_models=config.fallback_models or [],
            description=config.description,
            is_active=config.is_active,
            is_default=config.is_default,
            created_at=config.created_at.isoformat() if config.created_at else "",
            updated_at=config.updated_at.isoformat() if config.updated_at else ""
        )
        
    except Exception as e:
        logger.error(f"❌ [LLM Audit API] Error creating hyperparameter config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create hyperparameter config: {str(e)}")


# Prompt Template Endpoints

@router.get("/prompt-templates", response_model=List[LLMPromptTemplateResponse])
async def get_prompt_templates(
    purpose: Optional[str] = Query(None, description="Filter by purpose"),
    sub_purpose: Optional[str] = Query(None, description="Filter by sub-purpose"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db)
):
    """Get prompt templates"""
    try:
        query = db.query(LLMPromptTemplate)
        
        if purpose:
            query = query.filter(LLMPromptTemplate.purpose == purpose)
        if sub_purpose:
            query = query.filter(LLMPromptTemplate.sub_purpose == sub_purpose)
        if is_active is not None:
            query = query.filter(LLMPromptTemplate.is_active == is_active)
        
        templates = query.order_by(LLMPromptTemplate.purpose, LLMPromptTemplate.template_name).all()
        
        return [
            LLMPromptTemplateResponse(
                id=str(template.id),
                template_name=template.template_name,
                purpose=template.purpose,
                sub_purpose=template.sub_purpose,
                system_prompt_template=template.system_prompt_template,
                user_prompt_template=template.user_prompt_template,
                template_variables=template.template_variables or {},
                description=template.description,
                version=template.version,
                is_active=template.is_active,
                is_default=template.is_default,
                created_at=template.created_at.isoformat() if template.created_at else "",
                updated_at=template.updated_at.isoformat() if template.updated_at else ""
            )
            for template in templates
        ]
        
    except Exception as e:
        logger.error(f"❌ [LLM Audit API] Error getting prompt templates: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get prompt templates: {str(e)}")


@router.post("/prompt-templates", response_model=LLMPromptTemplateResponse)
async def create_prompt_template(
    request: CreatePromptTemplateRequest,
    db: Session = Depends(get_db)
):
    """Create a new prompt template"""
    try:
        audit_service = LLMAuditService(db)
        
        template_id = await audit_service.create_prompt_template(
            template_name=request.template_name,
            purpose=request.purpose,
            sub_purpose=request.sub_purpose,
            system_prompt_template=request.system_prompt_template,
            user_prompt_template=request.user_prompt_template,
            template_variables=request.template_variables,
            description=request.description,
            is_default=request.is_default
        )
        
        # Return the created template
        template = db.query(LLMPromptTemplate).filter(LLMPromptTemplate.id == template_id).first()
        
        return LLMPromptTemplateResponse(
            id=str(template.id),
            template_name=template.template_name,
            purpose=template.purpose,
            sub_purpose=template.sub_purpose,
            system_prompt_template=template.system_prompt_template,
            user_prompt_template=template.user_prompt_template,
            template_variables=template.template_variables or {},
            description=template.description,
            version=template.version,
            is_active=template.is_active,
            is_default=template.is_default,
            created_at=template.created_at.isoformat() if template.created_at else "",
            updated_at=template.updated_at.isoformat() if template.updated_at else ""
        )
        
    except Exception as e:
        logger.error(f"❌ [LLM Audit API] Error creating prompt template: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create prompt template: {str(e)}")
