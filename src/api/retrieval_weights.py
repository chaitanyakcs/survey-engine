"""
API endpoints for managing retrieval weights configuration
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from decimal import Decimal

from src.database.connection import get_db
from src.database.models import RetrievalWeights, MethodologyCompatibility

router = APIRouter(prefix="/api/v1/retrieval-weights", tags=["retrieval-weights"])


class RetrievalWeightsRequest(BaseModel):
    context_type: str = Field(..., description="Type of context: global, methodology, or industry")
    context_value: Optional[str] = Field(None, description="Specific context value (e.g., van_westendorp, healthcare)")
    semantic_weight: Decimal = Field(0.40, ge=0, le=1, description="Weight for semantic similarity")
    methodology_weight: Decimal = Field(0.25, ge=0, le=1, description="Weight for methodology match")
    industry_weight: Decimal = Field(0.15, ge=0, le=1, description="Weight for industry relevance")
    quality_weight: Decimal = Field(0.10, ge=0, le=1, description="Weight for quality score")
    annotation_weight: Decimal = Field(0.10, ge=0, le=1, description="Weight for annotation score")
    enabled: bool = Field(True, description="Whether this weight configuration is enabled")

    class Config:
        json_encoders = {
            Decimal: str
        }


class RetrievalWeightsUpdateRequest(BaseModel):
    context_type: Optional[str] = Field(None, description="Type of context: global, methodology, or industry")
    context_value: Optional[str] = Field(None, description="Specific context value (e.g., van_westendorp, healthcare)")
    semantic_weight: Optional[Decimal] = Field(None, ge=0, le=1, description="Weight for semantic similarity")
    methodology_weight: Optional[Decimal] = Field(None, ge=0, le=1, description="Weight for methodology match")
    industry_weight: Optional[Decimal] = Field(None, ge=0, le=1, description="Weight for industry relevance")
    quality_weight: Optional[Decimal] = Field(None, ge=0, le=1, description="Weight for quality score")
    annotation_weight: Optional[Decimal] = Field(None, ge=0, le=1, description="Weight for annotation score")
    enabled: Optional[bool] = Field(None, description="Whether this weight configuration is enabled")

    class Config:
        json_encoders = {
            Decimal: str
        }


class RetrievalWeightsResponse(BaseModel):
    id: str
    context_type: str
    context_value: Optional[str]
    semantic_weight: Decimal
    methodology_weight: Decimal
    industry_weight: Decimal
    quality_weight: Decimal
    annotation_weight: Decimal
    enabled: bool
    created_at: str
    updated_at: str

    class Config:
        json_encoders = {
            Decimal: str
        }


class MethodologyCompatibilityRequest(BaseModel):
    methodology_a: str = Field(..., description="First methodology in compatibility pair")
    methodology_b: str = Field(..., description="Second methodology in compatibility pair")
    compatibility_score: Decimal = Field(..., ge=0, le=1, description="Compatibility score between 0.0 and 1.0")
    notes: Optional[str] = Field(None, description="Human-readable explanation of compatibility")

    class Config:
        json_encoders = {
            Decimal: str
        }


class MethodologyCompatibilityResponse(BaseModel):
    methodology_a: str
    methodology_b: str
    compatibility_score: Decimal
    notes: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        json_encoders = {
            Decimal: str
        }


@router.get("/", response_model=List[RetrievalWeightsResponse])
async def get_retrieval_weights(
    context_type: Optional[str] = None,
    enabled_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get retrieval weights configuration"""
    try:
        query = db.query(RetrievalWeights)
        
        if context_type:
            query = query.filter(RetrievalWeights.context_type == context_type)
        
        if enabled_only:
            query = query.filter(RetrievalWeights.enabled == True)
        
        weights = query.order_by(RetrievalWeights.context_type, RetrievalWeights.context_value).all()
        
        return [
            RetrievalWeightsResponse(
                id=str(weight.id),
                context_type=weight.context_type,
                context_value=weight.context_value,
                semantic_weight=weight.semantic_weight,
                methodology_weight=weight.methodology_weight,
                industry_weight=weight.industry_weight,
                quality_weight=weight.quality_weight,
                annotation_weight=weight.annotation_weight,
                enabled=weight.enabled,
                created_at=weight.created_at.isoformat(),
                updated_at=weight.updated_at.isoformat()
            )
            for weight in weights
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve weights: {str(e)}")


@router.post("/", response_model=RetrievalWeightsResponse)
async def create_retrieval_weights(
    request: RetrievalWeightsRequest,
    db: Session = Depends(get_db)
):
    """Create new retrieval weights configuration"""
    try:
        # Validate that weights sum to 1.0
        total_weight = (
            request.semantic_weight + 
            request.methodology_weight + 
            request.industry_weight + 
            request.quality_weight + 
            request.annotation_weight
        )
        
        if abs(total_weight - Decimal('1.0')) > Decimal('0.001'):  # Allow small floating point errors
            raise HTTPException(
                status_code=400, 
                detail=f"Weights must sum to 1.0, got {total_weight}"
            )
        
        # Check if configuration already exists
        existing = db.query(RetrievalWeights).filter(
            RetrievalWeights.context_type == request.context_type,
            RetrievalWeights.context_value == request.context_value
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Weights configuration already exists for {request.context_type}:{request.context_value}"
            )
        
        # Create new weights
        weight = RetrievalWeights(
            context_type=request.context_type,
            context_value=request.context_value,
            semantic_weight=request.semantic_weight,
            methodology_weight=request.methodology_weight,
            industry_weight=request.industry_weight,
            quality_weight=request.quality_weight,
            annotation_weight=request.annotation_weight,
            enabled=request.enabled
        )
        
        db.add(weight)
        db.commit()
        db.refresh(weight)
        
        return RetrievalWeightsResponse(
            id=str(weight.id),
            context_type=weight.context_type,
            context_value=weight.context_value,
            semantic_weight=weight.semantic_weight,
            methodology_weight=weight.methodology_weight,
            industry_weight=weight.industry_weight,
            quality_weight=weight.quality_weight,
            annotation_weight=weight.annotation_weight,
            enabled=weight.enabled,
            created_at=weight.created_at.isoformat(),
            updated_at=weight.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create weights: {str(e)}")


@router.put("/{weight_id}", response_model=RetrievalWeightsResponse)
async def update_retrieval_weights(
    weight_id: str,
    request: RetrievalWeightsUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update existing retrieval weights configuration"""
    try:
        # Find existing weight
        weight = db.query(RetrievalWeights).filter(RetrievalWeights.id == weight_id).first()
        
        if not weight:
            raise HTTPException(status_code=404, detail="Weight configuration not found")
        
        # Update only provided fields
        if request.context_type is not None:
            weight.context_type = request.context_type
        if request.context_value is not None:
            weight.context_value = request.context_value
        if request.semantic_weight is not None:
            weight.semantic_weight = request.semantic_weight
        if request.methodology_weight is not None:
            weight.methodology_weight = request.methodology_weight
        if request.industry_weight is not None:
            weight.industry_weight = request.industry_weight
        if request.quality_weight is not None:
            weight.quality_weight = request.quality_weight
        if request.annotation_weight is not None:
            weight.annotation_weight = request.annotation_weight
        if request.enabled is not None:
            weight.enabled = request.enabled
        
        # Validate that weights sum to 1.0 (only if any weight was updated)
        if any([
            request.semantic_weight is not None,
            request.methodology_weight is not None,
            request.industry_weight is not None,
            request.quality_weight is not None,
            request.annotation_weight is not None
        ]):
            total_weight = (
                weight.semantic_weight + 
                weight.methodology_weight + 
                weight.industry_weight + 
                weight.quality_weight + 
                weight.annotation_weight
            )
            
            if abs(total_weight - Decimal('1.0')) > Decimal('0.001'):  # Allow small floating point errors
                raise HTTPException(
                    status_code=400, 
                    detail=f"Weights must sum to 1.0, got {total_weight}"
                )
        
        db.commit()
        db.refresh(weight)
        
        return RetrievalWeightsResponse(
            id=str(weight.id),
            context_type=weight.context_type,
            context_value=weight.context_value,
            semantic_weight=weight.semantic_weight,
            methodology_weight=weight.methodology_weight,
            industry_weight=weight.industry_weight,
            quality_weight=weight.quality_weight,
            annotation_weight=weight.annotation_weight,
            enabled=weight.enabled,
            created_at=weight.created_at.isoformat(),
            updated_at=weight.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update weights: {str(e)}")


@router.delete("/{weight_id}")
async def delete_retrieval_weights(
    weight_id: str,
    db: Session = Depends(get_db)
):
    """Delete retrieval weights configuration"""
    try:
        weight = db.query(RetrievalWeights).filter(RetrievalWeights.id == weight_id).first()
        
        if not weight:
            raise HTTPException(status_code=404, detail="Weight configuration not found")
        
        db.delete(weight)
        db.commit()
        
        return {"message": "Weight configuration deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete weights: {str(e)}")


@router.get("/methodology-compatibility", response_model=List[MethodologyCompatibilityResponse])
async def get_methodology_compatibility(
    methodology: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get methodology compatibility matrix"""
    try:
        query = db.query(MethodologyCompatibility)
        
        if methodology:
            query = query.filter(
                (MethodologyCompatibility.methodology_a == methodology) |
                (MethodologyCompatibility.methodology_b == methodology)
            )
        
        compatibilities = query.order_by(
            MethodologyCompatibility.methodology_a, 
            MethodologyCompatibility.methodology_b
        ).all()
        
        return [
            MethodologyCompatibilityResponse(
                methodology_a=comp.methodology_a,
                methodology_b=comp.methodology_b,
                compatibility_score=comp.compatibility_score,
                notes=comp.notes,
                created_at=comp.created_at.isoformat(),
                updated_at=comp.updated_at.isoformat()
            )
            for comp in compatibilities
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve compatibility matrix: {str(e)}")


@router.post("/methodology-compatibility", response_model=MethodologyCompatibilityResponse)
async def create_methodology_compatibility(
    request: MethodologyCompatibilityRequest,
    db: Session = Depends(get_db)
):
    """Create new methodology compatibility entry"""
    try:
        # Check if compatibility already exists
        existing = db.query(MethodologyCompatibility).filter(
            MethodologyCompatibility.methodology_a == request.methodology_a,
            MethodologyCompatibility.methodology_b == request.methodology_b
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Compatibility already exists for {request.methodology_a} -> {request.methodology_b}"
            )
        
        # Create new compatibility
        compatibility = MethodologyCompatibility(
            methodology_a=request.methodology_a,
            methodology_b=request.methodology_b,
            compatibility_score=request.compatibility_score,
            notes=request.notes
        )
        
        db.add(compatibility)
        db.commit()
        db.refresh(compatibility)
        
        return MethodologyCompatibilityResponse(
            methodology_a=compatibility.methodology_a,
            methodology_b=compatibility.methodology_b,
            compatibility_score=compatibility.compatibility_score,
            notes=compatibility.notes,
            created_at=compatibility.created_at.isoformat(),
            updated_at=compatibility.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create compatibility: {str(e)}")


@router.put("/methodology-compatibility/{methodology_a}/{methodology_b}", response_model=MethodologyCompatibilityResponse)
async def update_methodology_compatibility(
    methodology_a: str,
    methodology_b: str,
    request: MethodologyCompatibilityRequest,
    db: Session = Depends(get_db)
):
    """Update existing methodology compatibility entry"""
    try:
        compatibility = db.query(MethodologyCompatibility).filter(
            MethodologyCompatibility.methodology_a == methodology_a,
            MethodologyCompatibility.methodology_b == methodology_b
        ).first()
        
        if not compatibility:
            raise HTTPException(status_code=404, detail="Compatibility entry not found")
        
        # Update fields
        compatibility.compatibility_score = request.compatibility_score
        compatibility.notes = request.notes
        
        db.commit()
        db.refresh(compatibility)
        
        return MethodologyCompatibilityResponse(
            methodology_a=compatibility.methodology_a,
            methodology_b=compatibility.methodology_b,
            compatibility_score=compatibility.compatibility_score,
            notes=compatibility.notes,
            created_at=compatibility.created_at.isoformat(),
            updated_at=compatibility.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update compatibility: {str(e)}")


@router.delete("/methodology-compatibility/{methodology_a}/{methodology_b}")
async def delete_methodology_compatibility(
    methodology_a: str,
    methodology_b: str,
    db: Session = Depends(get_db)
):
    """Delete methodology compatibility entry"""
    try:
        compatibility = db.query(MethodologyCompatibility).filter(
            MethodologyCompatibility.methodology_a == methodology_a,
            MethodologyCompatibility.methodology_b == methodology_b
        ).first()
        
        if not compatibility:
            raise HTTPException(status_code=404, detail="Compatibility entry not found")
        
        db.delete(compatibility)
        db.commit()
        
        return {"message": "Compatibility entry deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete compatibility: {str(e)}")
