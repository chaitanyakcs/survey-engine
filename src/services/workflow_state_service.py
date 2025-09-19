"""
Service for managing workflow state persistence and resumption
"""

import json
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from src.database.models import WorkflowState as WorkflowStateModel
from src.workflows.state import SurveyGenerationState

logger = logging.getLogger(__name__)


class WorkflowStateService:
    """Service for persisting and retrieving workflow state"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def save_workflow_state(self, state: SurveyGenerationState) -> bool:
        """Save workflow state to database for later resumption"""
        try:
            # Convert state to dict and serialize
            state_dict = state.model_dump()
            state_json = json.dumps(state_dict, default=str)
            
            # Check if state already exists
            existing_state = self.db.query(WorkflowStateModel).filter(
                WorkflowStateModel.workflow_id == state.workflow_id
            ).first()
            
            if existing_state:
                # Update existing state
                existing_state.state_data = state_json
                existing_state.survey_id = state.survey_id
                logger.info(f"💾 [WorkflowStateService] Updated workflow state for {state.workflow_id}")
            else:
                # Create new state
                workflow_state = WorkflowStateModel(
                    workflow_id=state.workflow_id,
                    survey_id=state.survey_id,
                    state_data=state_json
                )
                self.db.add(workflow_state)
                logger.info(f"💾 [WorkflowStateService] Created new workflow state for {state.workflow_id}")
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ [WorkflowStateService] Failed to save workflow state: {str(e)}")
            self.db.rollback()
            return False
    
    def load_workflow_state(self, workflow_id: str) -> Optional[SurveyGenerationState]:
        """Load workflow state from database"""
        try:
            workflow_state = self.db.query(WorkflowStateModel).filter(
                WorkflowStateModel.workflow_id == workflow_id
            ).first()
            
            if not workflow_state:
                logger.warning(f"⚠️ [WorkflowStateService] No workflow state found for {workflow_id}")
                return None
            
            # Deserialize state
            state_dict = json.loads(workflow_state.state_data)
            
            # Convert back to SurveyGenerationState
            state = SurveyGenerationState(**state_dict)
            
            logger.info(f"📂 [WorkflowStateService] Loaded workflow state for {workflow_id}")
            return state
            
        except Exception as e:
            logger.error(f"❌ [WorkflowStateService] Failed to load workflow state: {str(e)}")
            return None
    
    def delete_workflow_state(self, workflow_id: str) -> bool:
        """Delete workflow state from database"""
        try:
            workflow_state = self.db.query(WorkflowStateModel).filter(
                WorkflowStateModel.workflow_id == workflow_id
            ).first()
            
            if workflow_state:
                self.db.delete(workflow_state)
                self.db.commit()
                logger.info(f"🗑️ [WorkflowStateService] Deleted workflow state for {workflow_id}")
                return True
            else:
                logger.warning(f"⚠️ [WorkflowStateService] No workflow state found to delete for {workflow_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ [WorkflowStateService] Failed to delete workflow state: {str(e)}")
            self.db.rollback()
            return False
    
    def cleanup_old_states(self, days_old: int = 7) -> int:
        """Clean up workflow states older than specified days"""
        try:
            from datetime import datetime, timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            old_states = self.db.query(WorkflowStateModel).filter(
                WorkflowStateModel.created_at < cutoff_date
            ).all()
            
            count = len(old_states)
            for state in old_states:
                self.db.delete(state)
            
            self.db.commit()
            logger.info(f"🧹 [WorkflowStateService] Cleaned up {count} old workflow states")
            return count
            
        except Exception as e:
            logger.error(f"❌ [WorkflowStateService] Failed to cleanup old states: {str(e)}")
            self.db.rollback()
            return 0
