from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src.services.prompt_service import PromptService
from pydantic import BaseModel
from typing import Dict, List, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rules", tags=["Rules"])


# CustomRuleRequest removed - no longer needed


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


# Quality rules API removed - replaced by comprehensive generation rules system


# Custom rules API removed - replaced by comprehensive generation rules system


# Custom rules API removed - replaced by comprehensive generation rules system


# Delete custom rule endpoint removed - replaced by comprehensive generation rules system


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


# Quality rule request models removed - no longer needed


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


# Add quality rule endpoint removed - replaced by comprehensive generation rules system


# Update quality rule endpoint removed - replaced by comprehensive generation rules system


# Delete quality rule endpoint removed - replaced by comprehensive generation rules system


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


# Pillar-based Rules Endpoints
class PillarRuleRequest(BaseModel):
    pillar_name: str
    rule_text: str
    priority: Optional[str] = "medium"  # high, medium, low

class PillarRuleUpdateRequest(BaseModel):
    rule_id: str
    rule_text: str
    priority: Optional[str] = None


@router.get("/pillar-rules")
async def get_all_pillar_rules(db: Session = Depends(get_db)):
    """Get all pillar-based rules organized by pillar category (includes both pillar and generation rules)"""
    try:
        from src.database.models import SurveyRule
        
        # Get both pillar and generation rules from database
        pillar_rules = db.query(SurveyRule).filter(
            SurveyRule.rule_type.in_(["pillar", "generation"]),
            SurveyRule.is_active == True
        ).order_by(SurveyRule.category, SurveyRule.priority.desc()).all()
        
        # Organize by pillar category
        organized_rules = {}
        pillar_categories = ["content_validity", "methodological_rigor", "clarity_comprehensibility", 
                           "structural_coherence", "deployment_readiness"]
        
        for category in pillar_categories:
            organized_rules[category] = {
                "rules": [],
                "count": 0
            }
        
        for rule in pillar_rules:
            if rule.category in organized_rules:
                organized_rules[rule.category]["rules"].append({
                    "id": str(rule.id),
                    "rule_text": rule.rule_description,
                    "priority": rule.rule_content.get("priority", "medium") if rule.rule_content else "medium",
                    "created_at": rule.created_at.isoformat() if rule.created_at else "",
                    "created_by": rule.created_by,
                    "rule_type": rule.rule_type  # Add rule type to distinguish pillar vs generation
                })
                organized_rules[rule.category]["count"] += 1
        
        return {
            "pillar_rules": organized_rules,
            "total_rules": len(pillar_rules),
            "pillar_categories": pillar_categories
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch pillar rules: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch pillar rules: {str(e)}")


@router.get("/pillar-rules/{pillar_name}")
async def get_pillar_rules(pillar_name: str, db: Session = Depends(get_db)):
    """Get all rules for a specific pillar"""
    try:
        from src.database.models import SurveyRule
        
        valid_pillars = ["content_validity", "methodological_rigor", "clarity_comprehensibility", 
                        "structural_coherence", "deployment_readiness"]
        
        if pillar_name not in valid_pillars:
            raise HTTPException(status_code=400, detail=f"Invalid pillar name. Must be one of: {valid_pillars}")
        
        # Get rules for specific pillar
        rules = db.query(SurveyRule).filter(
            SurveyRule.rule_type == "pillar",
            SurveyRule.category == pillar_name,
            SurveyRule.is_active == True
        ).order_by(SurveyRule.priority.desc()).all()
        
        formatted_rules = []
        for rule in rules:
            formatted_rules.append({
                "id": str(rule.id),
                "rule_text": rule.rule_description,
                "priority": rule.rule_content.get("priority", "medium") if rule.rule_content else "medium",
                "created_at": rule.created_at.isoformat() if rule.created_at else "",
                "created_by": rule.created_by
            })
        
        return {
            "pillar_name": pillar_name,
            "rules": formatted_rules,
            "count": len(formatted_rules)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch pillar rules for {pillar_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch pillar rules: {str(e)}")


@router.post("/pillar-rules")
async def add_pillar_rule(request: PillarRuleRequest, db: Session = Depends(get_db)):
    """Add a new pillar-based rule with silent duplicate detection"""
    try:
        from src.database.models import SurveyRule
        import uuid
        
        valid_pillars = ["content_validity", "methodological_rigor", "clarity_comprehensibility", 
                        "structural_coherence", "deployment_readiness"]
        
        if request.pillar_name not in valid_pillars:
            raise HTTPException(status_code=400, detail=f"Invalid pillar name. Must be one of: {valid_pillars}")
        
        # Check for existing duplicate rule (silent duplicate detection)
        existing_rule = db.query(SurveyRule).filter(
            SurveyRule.rule_type == "pillar",
            SurveyRule.category == request.pillar_name,
            SurveyRule.rule_description == request.rule_text,
            SurveyRule.is_active == True
        ).first()
        
        # If duplicate exists, return success silently without creating new rule
        if existing_rule:
            logger.info(f"Duplicate pillar rule detected for {request.pillar_name}, returning existing rule silently")
            return {
                "message": "Pillar rule added successfully",
                "rule_id": str(existing_rule.id),
                "pillar_name": request.pillar_name,
                "rule_text": request.rule_text,
                "duplicate_detected": True
            }
        
        # Map priority to numerical value
        priority_map = {"high": 10, "medium": 5, "low": 1}
        priority_value = priority_map.get(request.priority, 5)
        
        # Create new pillar rule
        new_rule = SurveyRule(
            id=uuid.uuid4(),
            rule_type="pillar",
            category=request.pillar_name,
            rule_name=f"{request.pillar_name.replace('_', ' ').title()} Rule",
            rule_description=request.rule_text,
            rule_content={
                "pillar": request.pillar_name,
                "priority": request.priority,
                "custom": True
            },
            is_active=True,
            priority=priority_value,
            created_by="user"
        )
        
        db.add(new_rule)
        db.commit()
        db.refresh(new_rule)
        
        logger.info(f"Added pillar rule to {request.pillar_name}: {request.rule_text}")
        return {
            "message": "Pillar rule added successfully",
            "rule_id": str(new_rule.id),
            "pillar_name": request.pillar_name,
            "rule_text": request.rule_text
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add pillar rule: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add pillar rule: {str(e)}")


@router.put("/pillar-rules")
async def update_pillar_rule(request: PillarRuleUpdateRequest, db: Session = Depends(get_db)):
    """Update an existing pillar rule"""
    try:
        from src.database.models import SurveyRule
        import uuid
        
        # Find the rule
        rule = db.query(SurveyRule).filter(
            SurveyRule.id == uuid.UUID(request.rule_id),
            SurveyRule.rule_type == "pillar",
            SurveyRule.is_active == True
        ).first()
        
        if not rule:
            raise HTTPException(status_code=404, detail="Pillar rule not found")
        
        # Update rule text
        rule.rule_description = request.rule_text
        
        # Update priority if provided
        if request.priority:
            priority_map = {"high": 10, "medium": 5, "low": 1}
            rule.priority = priority_map.get(request.priority, 5)
            
            if rule.rule_content:
                rule.rule_content["priority"] = request.priority
            else:
                rule.rule_content = {"priority": request.priority}
        
        db.commit()
        
        logger.info(f"Updated pillar rule {request.rule_id}: {request.rule_text}")
        return {"message": "Pillar rule updated successfully"}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid rule ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update pillar rule: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update pillar rule: {str(e)}")


@router.delete("/pillar-rules/{rule_id}")
async def delete_pillar_rule(rule_id: str, db: Session = Depends(get_db)):
    """Delete a pillar rule"""
    try:
        from src.database.models import SurveyRule
        import uuid
        
        # Find the rule
        rule = db.query(SurveyRule).filter(
            SurveyRule.id == uuid.UUID(rule_id),
            SurveyRule.rule_type == "pillar",
            SurveyRule.is_active == True
        ).first()
        
        if not rule:
            raise HTTPException(status_code=404, detail="Pillar rule not found")
        
        # Soft delete
        rule.is_active = False
        db.commit()
        
        logger.info(f"Deleted pillar rule: {rule_id}")
        return {"message": "Pillar rule deleted successfully"}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid rule ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete pillar rule: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete pillar rule: {str(e)}")


# Quality rules cleanup endpoint removed - no longer needed


@router.post("/pillar-rules/deduplicate")
async def deduplicate_pillar_rules(db: Session = Depends(get_db)):
    """Remove duplicate pillar rules and keep only the latest version of each unique rule"""
    try:
        from src.database.models import SurveyRule
        from sqlalchemy import text
        
        # Get all pillar rules
        pillar_rules = db.query(SurveyRule).filter(
            SurveyRule.rule_type == "pillar",
            SurveyRule.is_active == True
        ).order_by(SurveyRule.created_at.desc()).all()
        
        if not pillar_rules:
            return {"message": "No pillar rules found", "duplicates_removed": 0}
        
        # Track unique rules by rule description (rule text)
        seen_rules = {}
        duplicates_to_remove = []
        
        for rule in pillar_rules:
            rule_key = (rule.category, rule.rule_description.strip())
            
            if rule_key in seen_rules:
                # This is a duplicate - mark for removal
                duplicates_to_remove.append(rule.id)
                logger.info(f"Found duplicate rule: {rule.category} - {rule.rule_description[:50]}...")
            else:
                # Keep this rule (first/latest occurrence)
                seen_rules[rule_key] = rule.id
                logger.info(f"Keeping rule: {rule.category} - {rule.rule_description[:50]}...")
        
        # Remove duplicates by setting is_active = False (soft delete)
        duplicates_removed = 0
        for rule_id in duplicates_to_remove:
            db.query(SurveyRule).filter(
                SurveyRule.id == rule_id
            ).update({"is_active": False})
            duplicates_removed += 1
        
        db.commit()
        
        # Get final counts
        remaining_rules = db.query(SurveyRule).filter(
            SurveyRule.rule_type == "pillar",
            SurveyRule.is_active == True
        ).count()
        
        logger.info(f"Deduplication completed: {duplicates_removed} duplicates removed, {remaining_rules} unique rules remaining")
        
        return {
            "message": "Pillar rules deduplication completed successfully",
            "duplicates_removed": duplicates_removed,
            "unique_rules_remaining": remaining_rules,
            "total_processed": len(pillar_rules)
        }
        
    except Exception as e:
        logger.error(f"Failed to deduplicate pillar rules: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to deduplicate pillar rules: {str(e)}")


@router.get("/pillar-rules/stats")
async def get_pillar_rules_stats(db: Session = Depends(get_db)):
    """Get statistics about pillar rules including duplicates"""
    try:
        from src.database.models import SurveyRule
        from sqlalchemy import func, text
        
        # Count active pillar rules by category
        active_rules = db.query(
            SurveyRule.category, 
            func.count(SurveyRule.id).label('count')
        ).filter(
            SurveyRule.rule_type == "pillar",
            SurveyRule.is_active == True
        ).group_by(SurveyRule.category).all()
        
        # Count potential duplicates (same category and rule_description)
        duplicate_check = db.execute(text("""
            SELECT category, rule_description, COUNT(*) as duplicate_count
            FROM survey_rules 
            WHERE rule_type = 'pillar' AND is_active = true
            GROUP BY category, rule_description
            HAVING COUNT(*) > 1
            ORDER BY duplicate_count DESC
        """)).fetchall()
        
        # Total counts
        total_active = db.query(SurveyRule).filter(
            SurveyRule.rule_type == "pillar",
            SurveyRule.is_active == True
        ).count()
        
        total_inactive = db.query(SurveyRule).filter(
            SurveyRule.rule_type == "pillar",
            SurveyRule.is_active == False
        ).count()
        
        return {
            "total_active_rules": total_active,
            "total_inactive_rules": total_inactive,
            "rules_by_category": {rule.category: rule.count for rule in active_rules},
            "potential_duplicates": [
                {
                    "category": dup.category,
                    "rule_description": dup.rule_description[:100] + "..." if len(dup.rule_description) > 100 else dup.rule_description,
                    "duplicate_count": dup.duplicate_count
                }
                for dup in duplicate_check
            ],
            "total_duplicates_found": len(duplicate_check)
        }
        
    except Exception as e:
        logger.error(f"Failed to get pillar rules stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get pillar rules stats: {str(e)}")
