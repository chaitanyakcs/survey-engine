from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src.services.prompt_service import PromptService
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rules", tags=["Rules"])


class CustomRuleRequest(BaseModel):
    type: str
    rule: str


class RuleValidationRequest(BaseModel):
    survey: Dict[str, Any]
    methodology_tags: List[str]


class RuleValidationResponse(BaseModel):
    passed: bool
    errors: List[str]
    warnings: List[str]
    methodology_compliance: Dict[str, Any]
    quality_score: float


@router.get("/methodologies")
async def get_available_methodologies(db: Session = Depends(get_db)):
    """Get list of available methodologies and their rules"""
    prompt_service = PromptService(db_session=db)
    return {
        "methodologies": list(prompt_service.methodology_rules.keys()),
        "rules": prompt_service.methodology_rules
    }


@router.get("/quality-rules")
async def get_quality_rules(db: Session = Depends(get_db)):
    """Get current quality rules including custom rules from database"""
    try:
        from src.database.models import SurveyRule
        
        # Get quality rules from service (includes database rules)
        prompt_service = PromptService(db_session=db)
        return prompt_service.quality_rules
        
    except Exception as e:
        logger.error(f"Failed to fetch quality rules: {str(e)}")
        # Fallback to in-memory rules
        prompt_service = PromptService()
        return prompt_service.quality_rules


@router.post("/custom-rule")
async def add_custom_rule(
    request: CustomRuleRequest,
    db: Session = Depends(get_db)
):
    """Add a custom rule to the system"""
    try:
        from src.database.models import SurveyRule
        import uuid
        
        # Create new rule in database
        new_rule = SurveyRule(
            id=uuid.uuid4(),
            rule_type="custom",
            category=request.type,
            rule_name=f"Custom {request.type.replace('_', ' ').title()} Rule",
            rule_description=request.rule,
            rule_content={"rule_text": request.rule},
            is_active=True,
            priority=0,
            created_by="user"
        )
        
        db.add(new_rule)
        db.commit()
        db.refresh(new_rule)
        
        # Also add to in-memory service for immediate use
        prompt_service = PromptService()
        prompt_service.add_custom_rule(request.type, request.rule)
        
        logger.info(f"Added custom rule to database: {request.type} - {request.rule}")
        
        return {
            "message": "Custom rule added successfully",
            "rule_id": str(new_rule.id),
            "rule_type": request.type,
            "rule": request.rule
        }
        
    except Exception as e:
        logger.error(f"Failed to add custom rule: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add custom rule: {str(e)}")


@router.delete("/custom-rule/{rule_id}")
async def delete_custom_rule(
    rule_id: str,
    db: Session = Depends(get_db)
):
    """Delete a custom rule from the system"""
    try:
        from src.database.models import SurveyRule
        import uuid
        
        # Find the rule
        rule = db.query(SurveyRule).filter(
            SurveyRule.id == uuid.UUID(rule_id),
            SurveyRule.rule_type == "custom"
        ).first()
        
        if not rule:
            raise HTTPException(status_code=404, detail="Custom rule not found")
        
        # Soft delete by setting is_active to False
        rule.is_active = False
        db.commit()
        
        logger.info(f"Deleted custom rule: {rule_id}")
        
        return {
            "message": "Custom rule deleted successfully",
            "rule_id": rule_id
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid rule ID format")
    except Exception as e:
        logger.error(f"Failed to delete custom rule: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete custom rule: {str(e)}")


@router.post("/validate", response_model=RuleValidationResponse)
async def validate_survey_against_rules(
    request: RuleValidationRequest,
    db: Session = Depends(get_db)
):
    """Validate a survey against current rules"""
    try:
        prompt_service = PromptService()
        
        validation_results = prompt_service.validate_survey_against_rules(
            survey=request.survey,
            methodology_tags=request.methodology_tags
        )
        
        return RuleValidationResponse(**validation_results)
        
    except Exception as e:
        logger.error(f"Failed to validate survey: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to validate survey: {str(e)}")


@router.get("/methodology/{methodology_name}")
async def get_methodology_guidelines(methodology_name: str):
    """Get specific guidelines for a methodology"""
    try:
        prompt_service = PromptService()
        guidelines = prompt_service.get_methodology_guidelines(methodology_name)
        
        if not guidelines:
            raise HTTPException(
                status_code=404, 
                detail=f"Methodology '{methodology_name}' not found"
            )
        
        return guidelines
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get methodology guidelines: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get guidelines: {str(e)}")


@router.get("/system-prompt")
async def get_system_prompt(
    methodology_tags: Optional[List[str]] = None,
    custom_rules: Optional[Dict[str, Any]] = None
):
    """Get the current system prompt with rules"""
    try:
        prompt_service = PromptService()
        
        # Create a sample context for demonstration
        context = {
            "rfq_details": {
                "title": "Sample RFQ",
                "text": "Sample description",
                "category": "general",
                "segment": "general",
                "goal": "market_research"
            }
        }
        
        system_prompt = prompt_service.build_system_prompt(
            context=context,
            methodology_tags=methodology_tags or [],
            custom_rules=custom_rules
        )
        
        return {
            "system_prompt": system_prompt,
            "methodology_tags": methodology_tags,
            "custom_rules": custom_rules
        }
        
    except Exception as e:
        logger.error(f"Failed to generate system prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate system prompt: {str(e)}")
