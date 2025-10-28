"""
QNR Labels API
RESTful endpoints for managing QNR label taxonomy
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from src.database.connection import get_db
from src.services.qnr_label_service import QNRLabelService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/qnr-labels", tags=["qnr-labels"])


# Pydantic models
class QNRLabelResponse(BaseModel):
    """QNR Label response model"""
    id: int
    name: str
    category: str
    description: str
    mandatory: bool
    label_type: str
    applicable_labels: List[str]
    detection_patterns: List[str]
    section_id: int
    display_order: int
    active: bool
    created_at: Optional[str]
    updated_at: Optional[str]


class QNRLabelCreate(BaseModel):
    """QNR Label creation model"""
    name: str
    category: str
    description: str
    mandatory: bool = False
    label_type: str = 'QNR'
    applicable_labels: List[str] = []
    detection_patterns: List[str] = []
    section_id: int
    display_order: int = 0
    active: bool = True


class QNRLabelUpdate(BaseModel):
    """QNR Label update model"""
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    mandatory: Optional[bool] = None
    label_type: Optional[str] = None
    applicable_labels: Optional[List[str]] = None
    detection_patterns: Optional[List[str]] = None
    section_id: Optional[int] = None
    display_order: Optional[int] = None
    active: Optional[bool] = None


class QNRSectionResponse(BaseModel):
    """QNR Section response model"""
    id: int
    name: str
    description: Optional[str]
    display_order: int
    mandatory: bool
    active: bool


# Endpoints
@router.get("", response_model=List[QNRLabelResponse])
@router.get("/", response_model=List[QNRLabelResponse])
async def list_labels(
    category: Optional[str] = Query(None, description="Filter by category"),
    section_id: Optional[int] = Query(None, description="Filter by section ID"),
    mandatory_only: bool = Query(False, description="Only return mandatory labels"),
    active_only: bool = Query(True, description="Only return active labels"),
    db: Session = Depends(get_db)
):
    """
    Get all QNR labels with optional filtering
    
    Query params:
    - category: Filter by category (screener, brand, concept, methodology, additional)
    - section_id: Filter by section ID (1-7)
    - mandatory_only: Only return mandatory labels
    - active_only: Only return active labels (default: true)
    """
    try:
        service = QNRLabelService(db)
        labels = service.list_labels(
            category=category,
            section_id=section_id,
            mandatory_only=mandatory_only,
            active_only=active_only
        )
        
        logger.info(f"Retrieved {len(labels)} QNR labels")
        return labels
        
    except Exception as e:
        logger.error(f"Failed to list QNR labels: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{label_id}", response_model=QNRLabelResponse)
async def get_label(label_id: int, db: Session = Depends(get_db)):
    """Get a specific QNR label by ID"""
    try:
        service = QNRLabelService(db)
        label = service.get_label(label_id)
        
        if not label:
            raise HTTPException(status_code=404, detail="QNR label not found")
        
        return label
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get QNR label {label_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/name/{label_name}", response_model=QNRLabelResponse)
async def get_label_by_name(label_name: str, db: Session = Depends(get_db)):
    """Get a specific QNR label by name"""
    try:
        service = QNRLabelService(db)
        label = service.get_label_by_name(label_name)
        
        if not label:
            raise HTTPException(status_code=404, detail="QNR label not found")
        
        return label
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get QNR label by name {label_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=QNRLabelResponse, status_code=201)
async def create_label(
    label_data: QNRLabelCreate,
    changed_by: Optional[str] = Query(None, description="User ID who made the change"),
    db: Session = Depends(get_db)
):
    """Create a new QNR label"""
    try:
        service = QNRLabelService(db)
        
        # Convert Pydantic model to dict
        label_dict = label_data.dict()
        
        label = service.create_label(label_dict, changed_by=changed_by)
        
        logger.info(f"Created QNR label: {label['name']}")
        return label
        
    except ValueError as e:
        logger.error(f"Validation error creating QNR label: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create QNR label: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{label_id}", response_model=QNRLabelResponse)
async def update_label(
    label_id: int,
    label_data: QNRLabelUpdate,
    changed_by: Optional[str] = Query(None, description="User ID who made the change"),
    db: Session = Depends(get_db)
):
    """Update an existing QNR label"""
    try:
        service = QNRLabelService(db)
        
        # Convert Pydantic model to dict, excluding None values
        label_dict = {k: v for k, v in label_data.dict().items() if v is not None}
        
        label = service.update_label(label_id, label_dict, changed_by=changed_by)
        
        logger.info(f"Updated QNR label: {label['name']}")
        return label
        
    except ValueError as e:
        logger.error(f"Validation error updating QNR label: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update QNR label {label_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{label_id}")
async def delete_label(
    label_id: int,
    changed_by: Optional[str] = Query(None, description="User ID who made the change"),
    db: Session = Depends(get_db)
):
    """Soft delete a QNR label (sets active=False)"""
    try:
        service = QNRLabelService(db)
        
        success = service.delete_label(label_id, changed_by=changed_by)
        
        if success:
            logger.info(f"Deleted QNR label: {label_id}")
            return {"status": "success", "message": f"QNR label {label_id} deleted"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete QNR label")
        
    except ValueError as e:
        logger.error(f"Validation error deleting QNR label: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete QNR label {label_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sections/{section_id}/required")
async def get_required_labels_for_section(
    section_id: int,
    methodology: Optional[List[str]] = Query(None, description="List of methodology tags"),
    industry: Optional[str] = Query(None, description="Industry category"),
    db: Session = Depends(get_db)
):
    """
    Get required labels for a section based on context
    
    Args:
        section_id: Section ID (1-7)
        methodology: List of methodology tags (e.g., Van Westendorp, Conjoint)
        industry: Industry category (e.g., Healthcare, Consumer Goods)
    """
    try:
        service = QNRLabelService(db)
        
        labels = service.get_required_labels(
            section_id=section_id,
            methodology=methodology,
            industry=industry
        )
        
        logger.info(f"Retrieved {len(labels)} required labels for section {section_id}")
        return {
            "section_id": section_id,
            "methodology": methodology,
            "industry": industry,
            "required_labels": labels,
            "count": len(labels)
        }
        
    except Exception as e:
        logger.error(f"Failed to get required labels for section {section_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sections/list")
async def list_sections(db: Session = Depends(get_db)):
    """Get all QNR sections"""
    try:
        service = QNRLabelService(db)
        sections = service.get_sections()
        
        return sections
        
    except Exception as e:
        logger.error(f"Failed to list QNR sections: {e}")
        raise HTTPException(status_code=500, detail=str(e))

