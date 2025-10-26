"""
QNR Label Service
Manages CRUD operations for QNR labels with audit trail
"""

import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from src.database.models import QNRLabel, QNRSection, QNRLabelHistory
from datetime import datetime

logger = logging.getLogger(__name__)


class QNRLabelService:
    """Service for managing QNR labels"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def list_labels(
        self,
        category: Optional[str] = None,
        section_id: Optional[int] = None,
        mandatory_only: bool = False,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List QNR labels with optional filtering
        
        Args:
            category: Filter by category (screener, brand, concept, methodology, additional)
            section_id: Filter by section ID (1-7)
            mandatory_only: Only return mandatory labels
            active_only: Only return active labels
            
        Returns:
            List of label dictionaries
        """
        query = self.db.query(QNRLabel)
        
        if active_only:
            query = query.filter(QNRLabel.active == True)
        
        if category:
            query = query.filter(QNRLabel.category == category)
        
        if section_id:
            query = query.filter(QNRLabel.section_id == section_id)
        
        if mandatory_only:
            query = query.filter(QNRLabel.mandatory == True)
        
        labels = query.order_by(QNRLabel.display_order, QNRLabel.name).all()
        
        return [self._label_to_dict(label) for label in labels]
    
    def get_label(self, label_id: int) -> Optional[Dict[str, Any]]:
        """Get a single QNR label by ID"""
        label = self.db.query(QNRLabel).filter(QNRLabel.id == label_id).first()
        return self._label_to_dict(label) if label else None
    
    def get_label_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a single QNR label by name"""
        label = self.db.query(QNRLabel).filter(QNRLabel.name == name).first()
        return self._label_to_dict(label) if label else None
    
    def get_required_labels(
        self,
        section_id: int,
        methodology: Optional[List[str]] = None,
        industry: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get required labels for a section based on context
        
        Args:
            section_id: Section ID (1-7)
            methodology: List of methodology tags (e.g., ['Van Westendorp', 'Conjoint'])
            industry: Industry category (e.g., 'Healthcare', 'Consumer Goods')
            
        Returns:
            List of required labels with relevance scores (sorted by score)
        """
        query = self.db.query(QNRLabel)\
            .filter(QNRLabel.section_id == section_id)\
            .filter(QNRLabel.mandatory == True)\
            .filter(QNRLabel.active == True)
        
        labels = query.order_by(QNRLabel.display_order, QNRLabel.name).all()
        
        # Industry exclusion rules (labels that should NEVER appear for certain industries)
        industry_exclusions = {
            'food_beverage': ['Medical_Conditions_General', 'Medical_Conditions_Study', 
                            'Healthcare', 'MedTech', 'Patients']
        }
        
        # Score and sort labels by relevance
        scored_labels = []
        for label in labels:
            # Check if label should be excluded for this industry
            should_exclude = False
            if industry:
                excluded_labels = industry_exclusions.get(industry, [])
                if label.name in excluded_labels:
                    should_exclude = True
                # Also check if label's applicable_labels conflict with industry
                elif label.applicable_labels:
                    for app_label in label.applicable_labels:
                        app_lower = app_label.lower()
                        # Healthcare-specific labels shouldn't appear in food/beverage surveys
                        if industry == 'food_beverage' and app_lower in ['consumer health', 'healthcare', 'medtech', 'patients']:
                            if 'medical' in label.name.lower() or 'health' in label.name.lower():
                                should_exclude = True
                                break
            
            if should_exclude:
                continue  # Skip this label entirely
            
            label_dict = self._label_to_dict(label)
            
            # Calculate relevance score
            score = 1.0  # Base score for all mandatory labels
            
            # Boost score if label matches context
            if label.applicable_labels:
                applicable_lower = [a.lower() for a in label.applicable_labels]
                
                # Check methodology match
                if methodology:
                    methodology_lower = [m.lower() for m in methodology]
                    if any(m in applicable_lower for m in methodology_lower):
                        score += 1.0  # Matches methodology - higher priority
                
                # Check industry match
                if industry:
                    industry_lower = industry.lower()
                    if industry_lower in applicable_lower:
                        score += 1.0  # Matches industry - higher priority
            else:
                # No restrictions = universally applicable
                score += 0.5
            
            label_dict['relevance_score'] = score
            scored_labels.append(label_dict)
        
        # Sort by relevance score (descending), then by display_order
        scored_labels.sort(key=lambda x: (x['relevance_score'], -x.get('display_order', 0)), reverse=True)
        
        return scored_labels
    
    def create_label(
        self,
        label_data: Dict[str, Any],
        changed_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new QNR label
        
        Args:
            label_data: Label data including name, category, description, etc.
            changed_by: User ID who made the change
            
        Returns:
            Created label dictionary
        """
        label = QNRLabel(
            name=label_data['name'],
            category=label_data['category'],
            description=label_data['description'],
            mandatory=label_data.get('mandatory', False),
            label_type=label_data.get('label_type', 'QNR'),
            applicable_labels=label_data.get('applicable_labels', []),
            detection_patterns=label_data.get('detection_patterns', []),
            section_id=label_data['section_id'],
            display_order=label_data.get('display_order', 0),
            active=label_data.get('active', True)
        )
        
        self.db.add(label)
        self.db.commit()
        self.db.refresh(label)
        
        # Log to audit trail
        self._log_history(label.id, 'created', None, self._label_to_dict(label), changed_by)
        
        logger.info(f"Created QNR label: {label.name}")
        
        return self._label_to_dict(label)
    
    def update_label(
        self,
        label_id: int,
        label_data: Dict[str, Any],
        changed_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update an existing QNR label
        
        Args:
            label_id: Label ID to update
            label_data: Updated label data
            changed_by: User ID who made the change
            
        Returns:
            Updated label dictionary
        """
        label = self.db.query(QNRLabel).filter(QNRLabel.id == label_id).first()
        
        if not label:
            raise ValueError(f"QNR label not found: {label_id}")
        
        # Store old value for audit trail
        old_value = self._label_to_dict(label)
        
        # Update fields
        if 'name' in label_data:
            label.name = label_data['name']
        if 'category' in label_data:
            label.category = label_data['category']
        if 'description' in label_data:
            label.description = label_data['description']
        if 'mandatory' in label_data:
            label.mandatory = label_data['mandatory']
        if 'label_type' in label_data:
            label.label_type = label_data['label_type']
        if 'applicable_labels' in label_data:
            label.applicable_labels = label_data['applicable_labels']
        if 'detection_patterns' in label_data:
            label.detection_patterns = label_data['detection_patterns']
        if 'section_id' in label_data:
            label.section_id = label_data['section_id']
        if 'display_order' in label_data:
            label.display_order = label_data['display_order']
        if 'active' in label_data:
            label.active = label_data['active']
        
        label.updated_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(label)
        
        # Log to audit trail
        new_value = self._label_to_dict(label)
        self._log_history(label_id, 'updated', old_value, new_value, changed_by)
        
        logger.info(f"Updated QNR label: {label.name}")
        
        return new_value
    
    def delete_label(
        self,
        label_id: int,
        changed_by: Optional[str] = None
    ) -> bool:
        """
        Soft delete a QNR label (set active=False)
        
        Args:
            label_id: Label ID to delete
            changed_by: User ID who made the change
            
        Returns:
            True if deleted successfully
        """
        label = self.db.query(QNRLabel).filter(QNRLabel.id == label_id).first()
        
        if not label:
            raise ValueError(f"QNR label not found: {label_id}")
        
        # Store old value for audit trail
        old_value = self._label_to_dict(label)
        
        # Soft delete
        label.active = False
        label.updated_at = datetime.now()
        
        self.db.commit()
        
        # Log to audit trail
        self._log_history(label_id, 'deleted', old_value, None, changed_by)
        
        logger.info(f"Soft deleted QNR label: {label.name}")
        
        return True
    
    def get_sections(self) -> List[Dict[str, Any]]:
        """Get all QNR sections"""
        sections = self.db.query(QNRSection)\
            .filter(QNRSection.active == True)\
            .order_by(QNRSection.display_order)\
            .all()
        
        return [
            {
                'id': section.id,
                'name': section.name,
                'description': section.description,
                'display_order': section.display_order,
                'mandatory': section.mandatory,
                'active': section.active
            }
            for section in sections
        ]
    
    def _label_to_dict(self, label: QNRLabel) -> Dict[str, Any]:
        """Convert QNRLabel entity to dictionary"""
        if not label:
            return None
        
        return {
            'id': label.id,
            'name': label.name,
            'category': label.category,
            'description': label.description,
            'mandatory': label.mandatory,
            'label_type': label.label_type,
            'applicable_labels': label.applicable_labels or [],
            'detection_patterns': label.detection_patterns or [],
            'section_id': label.section_id,
            'display_order': label.display_order,
            'active': label.active,
            'created_at': label.created_at.isoformat() if label.created_at else None,
            'updated_at': label.updated_at.isoformat() if label.updated_at else None
        }
    
    def _log_history(
        self,
        label_id: int,
        change_type: str,
        old_value: Optional[Dict],
        new_value: Optional[Dict],
        changed_by: Optional[str]
    ):
        """Log change to audit trail"""
        try:
            history = QNRLabelHistory(
                label_id=label_id,
                change_type=change_type,
                changed_by=changed_by,
                old_value=old_value,
                new_value=new_value,
                changed_at=datetime.now()
            )
            self.db.add(history)
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to log QNR label history: {e}")
            self.db.rollback()

