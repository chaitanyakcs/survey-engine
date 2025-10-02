"""
Admin API endpoints for database management
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from src.database.connection import get_db
import subprocess
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

@router.post("/migrate")
async def run_migrations(db: Session = Depends(get_db)):
    """
    Run database migrations
    """
    try:
        logger.info("🔄 Starting database migration...")
        
        # Run alembic upgrade
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            cwd="/app"
        )
        
        if result.returncode == 0:
            logger.info("✅ Database migration completed successfully")
            return {
                "status": "success",
                "message": "Database migration completed successfully",
                "output": result.stdout
            }
        else:
            logger.error(f"❌ Database migration failed: {result.stderr}")
            raise HTTPException(
                status_code=500,
                detail=f"Migration failed: {result.stderr}"
            )
            
    except Exception as e:
        logger.error(f"❌ Migration error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Migration error: {str(e)}"
        )

@router.get("/migration-status")
async def get_migration_status(db: Session = Depends(get_db)):
    """
    Get current migration status
    """
    try:
        logger.info("🔍 Checking migration status...")
        
        # Run alembic current
        result = subprocess.run(
            ["alembic", "current"],
            capture_output=True,
            text=True,
            cwd="/app"
        )
        
        if result.returncode == 0:
            logger.info("✅ Migration status retrieved successfully")
            return {
                "status": "success",
                "current_revision": result.stdout.strip(),
                "output": result.stdout
            }
        else:
            logger.error(f"❌ Failed to get migration status: {result.stderr}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get migration status: {result.stderr}"
            )
            
    except Exception as e:
        logger.error(f"❌ Migration status error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Migration status error: {str(e)}"
        )

@router.post("/fix-migration-state")
async def fix_migration_state(db: Session = Depends(get_db)):
    """
    Fix migration state by marking database as up to date
    """
    try:
        logger.info("🔧 Fixing Railway migration state...")
        
        # The target revision that adds the labels column
        target_revision = "8d392146a12e"
        
        # Mark the database as being at the target revision
        logger.info(f"📝 Marking database as revision: {target_revision}")
        
        result = subprocess.run(
            ["alembic", "stamp", target_revision],
            capture_output=True,
            text=True,
            cwd="/app"
        )
        
        if result.returncode == 0:
            logger.info("✅ Successfully marked database as up to date")
            return {
                "status": "success",
                "message": f"Database marked as revision {target_revision}",
                "output": result.stdout
            }
        else:
            logger.error(f"❌ Failed to stamp database: {result.stderr}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to stamp database: {result.stderr}"
            )
            
    except Exception as e:
        logger.error(f"❌ Error fixing migration state: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fixing migration state: {str(e)}"
        )
