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


@router.get("/custom-rules")
async def get_custom_rules(db: Session = Depends(get_db)):
    """Get all custom rules from database"""
    try:
        from src.database.models import SurveyRule
        
        # Query all active custom rules from database
        custom_rules = db.query(SurveyRule).filter(
            SurveyRule.rule_type == "custom",
            SurveyRule.is_active == True
        ).all()
        
        # Format rules for frontend
        rules = []
        for rule in custom_rules:
            rules.append({
                "id": str(rule.id),
                "rule_id": str(rule.id),
                "type": rule.category,
                "rule": rule.rule_description,
                "rule_name": rule.rule_name,
                "created_by": rule.created_by,
                "priority": rule.priority
            })
        
        return {"rules": rules}
        
    except Exception as e:
        logger.error(f"Failed to fetch custom rules: {str(e)}")
        return {"rules": []}


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


class QualityRuleRequest(BaseModel):
    category: str
    rule_text: str


class QualityRuleUpdateRequest(BaseModel):
    category: str
    rule_index: int
    rule_text: str


class QualityRuleDeleteRequest(BaseModel):
    category: str
    rule_index: int


class SystemPromptRequest(BaseModel):
    prompt_text: str


class SystemPromptResponse(BaseModel):
    id: str
    prompt_text: str
    created_at: str
    updated_at: str


class MethodologyRuleRequest(BaseModel):
    methodology_name: str
    description: str
    required_questions: int
    validation_rules: List[str]
    question_flow: Optional[List[str]] = None
    best_practices: Optional[List[str]] = None


class MethodologyRuleUpdateRequest(BaseModel):
    methodology_name: str
    description: Optional[str] = None
    required_questions: Optional[int] = None
    validation_rules: Optional[List[str]] = None
    question_flow: Optional[List[str]] = None
    best_practices: Optional[List[str]] = None


@router.post("/quality-rules")
async def add_quality_rule(request: QualityRuleRequest, db: Session = Depends(get_db)):
    """Add a new quality rule to a category"""
    try:
        from src.database.models import SurveyRule
        import uuid
        
        # Create new quality rule
        new_rule = SurveyRule(
            id=uuid.uuid4(),
            rule_type="quality",
            category=request.category,
            rule_name=f"{request.category} rule",
            rule_description=request.rule_text,
            rule_content={"rule_text": request.rule_text},
            is_active=True,
            priority=0,
            created_by="user"
        )
        
        db.add(new_rule)
        db.commit()
        db.refresh(new_rule)
        
        logger.info(f"Added quality rule to {request.category}: {request.rule_text}")
        return {"message": "Quality rule added successfully", "rule_id": str(new_rule.id)}
        
    except Exception as e:
        logger.error(f"Failed to add quality rule: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add quality rule: {str(e)}")


@router.put("/quality-rules")
async def update_quality_rule(request: QualityRuleUpdateRequest, db: Session = Depends(get_db)):
    """Update an existing quality rule"""
    try:
        from src.database.models import SurveyRule
        
        # Find the rule to update
        rules = db.query(SurveyRule).filter(
            SurveyRule.rule_type == "quality",
            SurveyRule.category == request.category,
            SurveyRule.is_active == True
        ).all()
        
        if request.rule_index >= len(rules):
            raise HTTPException(status_code=404, detail="Rule not found")
        
        rule_to_update = rules[request.rule_index]
        rule_to_update.rule_description = request.rule_text
        rule_to_update.rule_content = {"rule_text": request.rule_text}
        
        db.commit()
        
        logger.info(f"Updated quality rule in {request.category}: {request.rule_text}")
        return {"message": "Quality rule updated successfully"}
        
    except Exception as e:
        logger.error(f"Failed to update quality rule: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update quality rule: {str(e)}")


@router.delete("/quality-rules")
async def delete_quality_rule(request: QualityRuleDeleteRequest, db: Session = Depends(get_db)):
    """Delete a quality rule"""
    try:
        from src.database.models import SurveyRule
        
        # Find the rule to delete
        rules = db.query(SurveyRule).filter(
            SurveyRule.rule_type == "quality",
            SurveyRule.category == request.category,
            SurveyRule.is_active == True
        ).all()
        
        if request.rule_index >= len(rules):
            raise HTTPException(status_code=404, detail="Rule not found")
        
        rule_to_delete = rules[request.rule_index]
        rule_to_delete.is_active = False
        
        db.commit()
        
        logger.info(f"Deleted quality rule from {request.category}")
        return {"message": "Quality rule deleted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to delete quality rule: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete quality rule: {str(e)}")


@router.get("/system-prompt")
async def get_system_prompt(db: Session = Depends(get_db)):
    """Get the current system prompt"""
    try:
        from src.database.models import SurveyRule
        
        # Get system prompt from database
        system_prompt_rule = db.query(SurveyRule).filter(
            SurveyRule.rule_type == "system_prompt",
            SurveyRule.is_active == True
        ).first()
        
        if system_prompt_rule:
            return {
                "id": str(system_prompt_rule.id),
                "prompt_text": system_prompt_rule.rule_description or "",
                "created_at": system_prompt_rule.created_at.isoformat() if system_prompt_rule.created_at else "",
                "updated_at": system_prompt_rule.updated_at.isoformat() if system_prompt_rule.updated_at else ""
            }
        else:
            return {
                "id": "",
                "prompt_text": "",
                "created_at": "",
                "updated_at": ""
            }
        
    except Exception as e:
        logger.error(f"Failed to fetch system prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch system prompt: {str(e)}")


@router.post("/system-prompt")
async def create_or_update_system_prompt(request: SystemPromptRequest, db: Session = Depends(get_db)):
    """Create or update the system prompt"""
    try:
        from src.database.models import SurveyRule
        import uuid
        from datetime import datetime
        
        # Check if system prompt already exists
        existing_prompt = db.query(SurveyRule).filter(
            SurveyRule.rule_type == "system_prompt",
            SurveyRule.is_active == True
        ).first()
        
        if existing_prompt:
            # Update existing system prompt
            existing_prompt.rule_description = request.prompt_text
            existing_prompt.updated_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Updated system prompt: {request.prompt_text[:100]}...")
            return {
                "message": "System prompt updated successfully",
                "id": str(existing_prompt.id),
                "prompt_text": request.prompt_text,
                "updated_at": existing_prompt.updated_at.isoformat() if existing_prompt.updated_at else ""
            }
        else:
            # Create new system prompt
            new_prompt = SurveyRule(
                id=uuid.uuid4(),
                rule_type="system_prompt",
                category="system",
                rule_name="Custom System Prompt",
                rule_description=request.prompt_text,
                rule_content={"prompt_text": request.prompt_text},
                is_active=True,
                priority=1000,  # High priority
                created_by="user"
            )
            
            db.add(new_prompt)
            db.commit()
            db.refresh(new_prompt)
            
            logger.info(f"Created system prompt: {request.prompt_text[:100]}...")
            return {
                "message": "System prompt created successfully",
                "id": str(new_prompt.id),
                "prompt_text": request.prompt_text,
                "created_at": new_prompt.created_at.isoformat() if new_prompt.created_at else ""
            }
        
    except Exception as e:
        logger.error(f"Failed to create/update system prompt: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create/update system prompt: {str(e)}")


@router.delete("/system-prompt")
async def delete_system_prompt(db: Session = Depends(get_db)):
    """Delete the system prompt"""
    try:
        from src.database.models import SurveyRule
        
        # Find and deactivate the system prompt
        system_prompt = db.query(SurveyRule).filter(
            SurveyRule.rule_type == "system_prompt",
            SurveyRule.is_active == True
        ).first()
        
        if system_prompt:
            system_prompt.is_active = False
            db.commit()
            logger.info("System prompt deleted successfully")
            return {"message": "System prompt deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="System prompt not found")
        
    except Exception as e:
        logger.error(f"Failed to delete system prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete system prompt: {str(e)}")


@router.post("/methodology-rules")
async def add_methodology_rule(request: MethodologyRuleRequest, db: Session = Depends(get_db)):
    """Add a new methodology rule"""
    try:
        from src.database.models import SurveyRule
        import uuid
        
        # Check if methodology already exists
        existing_rule = db.query(SurveyRule).filter(
            SurveyRule.rule_type == "methodology",
            SurveyRule.category == request.methodology_name,
            SurveyRule.is_active == True
        ).first()
        
        if existing_rule:
            raise HTTPException(status_code=400, detail=f"Methodology '{request.methodology_name}' already exists")
        
        # Create new methodology rule
        rule_content = {
            "required_questions": request.required_questions,
            "validation_rules": request.validation_rules,
            "question_flow": request.question_flow or [],
            "best_practices": request.best_practices or []
        }
        
        new_rule = SurveyRule(
            id=uuid.uuid4(),
            rule_type="methodology",
            category=request.methodology_name,
            rule_name=f"{request.methodology_name} methodology",
            rule_description=request.description,
            rule_content=rule_content,
            is_active=True,
            priority=10,
            created_by="user"
        )
        
        db.add(new_rule)
        db.commit()
        db.refresh(new_rule)
        
        logger.info(f"Added methodology rule: {request.methodology_name}")
        return {
            "message": "Methodology rule added successfully",
            "rule_id": str(new_rule.id),
            "methodology_name": request.methodology_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add methodology rule: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add methodology rule: {str(e)}")


@router.put("/methodology-rules")
async def update_methodology_rule(request: MethodologyRuleUpdateRequest, db: Session = Depends(get_db)):
    """Update an existing methodology rule"""
    try:
        from src.database.models import SurveyRule
        
        # Find the methodology rule
        rule = db.query(SurveyRule).filter(
            SurveyRule.rule_type == "methodology",
            SurveyRule.category == request.methodology_name,
            SurveyRule.is_active == True
        ).first()
        
        if not rule:
            raise HTTPException(status_code=404, detail=f"Methodology '{request.methodology_name}' not found")
        
        # Update fields if provided
        if request.description is not None:
            rule.rule_description = request.description
        
        if rule.rule_content is None:
            rule.rule_content = {}
        
        if request.required_questions is not None:
            rule.rule_content["required_questions"] = request.required_questions
        
        if request.validation_rules is not None:
            rule.rule_content["validation_rules"] = request.validation_rules
        
        if request.question_flow is not None:
            rule.rule_content["question_flow"] = request.question_flow
        
        if request.best_practices is not None:
            rule.rule_content["best_practices"] = request.best_practices
        
        db.commit()
        
        logger.info(f"Updated methodology rule: {request.methodology_name}")
        return {"message": "Methodology rule updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update methodology rule: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update methodology rule: {str(e)}")


@router.delete("/methodology-rules/{methodology_name}")
async def delete_methodology_rule(methodology_name: str, db: Session = Depends(get_db)):
    """Delete a methodology rule"""
    try:
        from src.database.models import SurveyRule
        
        # Find the methodology rule
        rule = db.query(SurveyRule).filter(
            SurveyRule.rule_type == "methodology",
            SurveyRule.category == methodology_name,
            SurveyRule.is_active == True
        ).first()
        
        if not rule:
            raise HTTPException(status_code=404, detail=f"Methodology '{methodology_name}' not found")
        
        # Soft delete by setting is_active to False
        rule.is_active = False
        db.commit()
        
        logger.info(f"Deleted methodology rule: {methodology_name}")
        return {"message": "Methodology rule deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete methodology rule: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete methodology rule: {str(e)}")
