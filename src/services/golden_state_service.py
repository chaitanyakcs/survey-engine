"""Service for managing golden example creation state persistence"""

import json
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from src.database.models import GoldenExampleState

logger = logging.getLogger(__name__)


class GoldenStateService:
    def __init__(self, db: Session):
        self.db = db
    
    def save_state(self, session_id: str, state_data: Dict[str, Any]) -> bool:
        """Save golden example creation state"""
        try:
            existing = self.db.query(GoldenExampleState).filter(
                GoldenExampleState.session_id == session_id
            ).first()
            
            if existing:
                existing.state_data = state_data
                logger.info(f"💾 Updated golden example state for {session_id}")
            else:
                state = GoldenExampleState(
                    session_id=session_id,
                    state_data=state_data
                )
                self.db.add(state)
                logger.info(f"💾 Created golden example state for {session_id}")
            
            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save golden example state: {e}")
            self.db.rollback()
            return False
    
    def load_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load golden example creation state"""
        try:
            state = self.db.query(GoldenExampleState).filter(
                GoldenExampleState.session_id == session_id
            ).first()
            
            if state:
                logger.info(f"📂 Loaded golden example state for {session_id}")
                return state.state_data
            return None
        except Exception as e:
            logger.error(f"❌ Failed to load golden example state: {e}")
            return None
    
    def delete_state(self, session_id: str) -> bool:
        """Delete golden example state after successful creation"""
        try:
            state = self.db.query(GoldenExampleState).filter(
                GoldenExampleState.session_id == session_id
            ).first()
            
            if state:
                self.db.delete(state)
                self.db.commit()
                logger.info(f"🗑️ Deleted golden example state for {session_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to delete golden example state: {e}")
            self.db.rollback()
            return False

