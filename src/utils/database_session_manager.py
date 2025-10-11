#!/usr/bin/env python3
"""
Database Session Health Utilities
Provides utilities for managing database session health and recovery
"""

import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional

logger = logging.getLogger(__name__)


class DatabaseSessionManager:
    """Manages database session health and recovery"""
    
    @staticmethod
    def ensure_healthy_session(db: Session) -> bool:
        """
        Ensure the database session is healthy and can execute queries
        
        Args:
            db: SQLAlchemy session
            
        Returns:
            bool: True if session is healthy, False otherwise
        """
        try:
            # Test the session with a simple query
            db.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.warning(f"⚠️ [DatabaseSessionManager] Session is unhealthy: {str(e)}")
            return False
    
    @staticmethod
    def recover_session(db: Session) -> bool:
        """
        Attempt to recover a failed database session
        
        Args:
            db: SQLAlchemy session
            
        Returns:
            bool: True if recovery successful, False otherwise
        """
        try:
            # Rollback any failed transaction
            db.rollback()
            logger.info("🔄 [DatabaseSessionManager] Rolled back failed transaction")
            
            # Test if session is now healthy
            db.execute(text("SELECT 1"))
            logger.info("✅ [DatabaseSessionManager] Session recovered after rollback")
            return True
        except Exception as e:
            logger.error(f"❌ [DatabaseSessionManager] Session recovery failed: {str(e)}")
            return False
    
    @staticmethod
    def safe_query(db: Session, query_func, fallback_value=None, operation_name="database operation"):
        """
        Execute a database query with automatic error handling and recovery
        
        Args:
            db: SQLAlchemy session
            query_func: Function that executes the database query
            fallback_value: Value to return if query fails
            operation_name: Name of the operation for logging
            
        Returns:
            Query result or fallback_value if query fails
        """
        try:
            # Ensure session is healthy before executing query
            if not DatabaseSessionManager.ensure_healthy_session(db):
                if not DatabaseSessionManager.recover_session(db):
                    logger.error(f"❌ [DatabaseSessionManager] Cannot recover session for {operation_name}")
                    return fallback_value
            
            # Execute the query
            result = query_func()
            return result
            
        except Exception as e:
            logger.error(f"❌ [DatabaseSessionManager] Query failed for {operation_name}: {str(e)}")
            
            # Attempt recovery
            if DatabaseSessionManager.recover_session(db):
                try:
                    # Retry the query after recovery
                    result = query_func()
                    logger.info(f"✅ [DatabaseSessionManager] Query succeeded after recovery for {operation_name}")
                    return result
                except Exception as retry_error:
                    logger.error(f"❌ [DatabaseSessionManager] Query retry failed for {operation_name}: {str(retry_error)}")
            
            return fallback_value
