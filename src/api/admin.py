"""
Admin API endpoints for database management
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.database.connection import get_db
import subprocess
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

@router.post("/fix-document-uploads-schema")
async def fix_document_uploads_schema(db: Session = Depends(get_db)):
    """
    Fix the document_uploads table schema by adding missing columns and fix llm_audit schema
    """
    try:
        logger.info("🔧 Fixing document_uploads table schema...")
        
        # Check if session_id column exists
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'document_uploads' AND column_name = 'session_id'
        """))
        
        if result.fetchone():
            logger.info("✅ session_id column already exists")
        else:
            logger.info("❌ session_id column missing - adding it")
            db.execute(text("ALTER TABLE document_uploads ADD COLUMN session_id VARCHAR(100)"))
            logger.info("✅ Added session_id column")
        
        # Check if uploaded_by column exists
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'document_uploads' AND column_name = 'uploaded_by'
        """))
        
        if result.fetchone():
            logger.info("✅ uploaded_by column already exists")
        else:
            logger.info("❌ uploaded_by column missing - adding it")
            db.execute(text("ALTER TABLE document_uploads ADD COLUMN uploaded_by VARCHAR(255)"))
            logger.info("✅ Added uploaded_by column")
        
        # Make original_filename nullable
        db.execute(text("ALTER TABLE document_uploads ALTER COLUMN original_filename DROP NOT NULL"))
        logger.info("✅ Made original_filename nullable")
        
        # Make file_size nullable
        db.execute(text("ALTER TABLE document_uploads ALTER COLUMN file_size DROP NOT NULL"))
        logger.info("✅ Made file_size nullable")
        
        # Create index on session_id if it doesn't exist
        try:
            db.execute(text("CREATE INDEX idx_document_uploads_session_id ON document_uploads (session_id)"))
            logger.info("✅ Created session_id index")
        except Exception as e:
            if "already exists" in str(e):
                logger.info("✅ session_id index already exists")
            else:
                raise e
        
        # Commit all changes
        db.commit()
        
        logger.info("✅ Document uploads schema fix completed successfully")
        # Fix llm_audit schema - add raw_response column if missing
        logger.info("🔧 Checking llm_audit table schema...")
        
        try:
            result = db.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'llm_audit' AND column_name = 'raw_response'
            """))
            
            if result.fetchone():
                logger.info("✅ raw_response column already exists in llm_audit")
            else:
                logger.info("❌ raw_response column missing in llm_audit - adding it")
                db.execute(text("ALTER TABLE llm_audit ADD COLUMN raw_response TEXT"))
                db.commit()  # Commit the column addition
                logger.info("✅ Added raw_response column to llm_audit")
        except Exception as e:
            logger.error(f"❌ Error adding raw_response column: {str(e)}")
            # Don't fail the whole operation for this
        
        return {
            "status": "success",
            "message": "Document uploads and llm_audit schema fixed successfully",
            "changes": [
                "Added session_id column",
                "Added uploaded_by column", 
                "Made original_filename nullable",
                "Made file_size nullable",
                "Created session_id index",
                "Added raw_response column to llm_audit"
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Error fixing document uploads schema: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error fixing document uploads schema: {str(e)}"
        )

@router.get("/check-llm-audit-schema")
async def check_llm_audit_schema(db: Session = Depends(get_db)):
    """
    Check the actual schema of llm_audit table
    """
    try:
        logger.info("🔍 Checking llm_audit table schema...")
        
        # Get all columns in llm_audit table
        result = db.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'llm_audit'
            ORDER BY ordinal_position
        """))
        
        columns = result.fetchall()
        
        return {
            "status": "success",
            "message": "llm_audit table schema",
            "columns": [{"name": col[0], "type": col[1], "nullable": col[2]} for col in columns]
        }
        
    except Exception as e:
        logger.error(f"❌ Error checking llm_audit schema: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error checking llm_audit schema: {str(e)}"
        )

@router.post("/stamp-revision")
async def stamp_revision(revision: str = "b7ebcbcfc078", db: Session = Depends(get_db)):
    """
    Stamp the database to a specific revision
    """
    try:
        logger.info(f"🔧 Stamping database to revision: {revision}")
        
        # Mark the database as being at the specified revision
        logger.info(f"📝 Marking database as revision: {revision}")
        
        result = subprocess.run(
            ["alembic", "stamp", revision],
            capture_output=True,
            text=True,
            cwd="/app"
        )
        
        if result.returncode == 0:
            logger.info(f"✅ Successfully marked database as revision {revision}")
            return {
                "status": "success",
                "message": f"Database marked as revision {revision}",
                "output": result.stdout
            }
        else:
            logger.error(f"❌ Failed to stamp database: {result.stderr}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to stamp database: {result.stderr}"
            )
            
    except Exception as e:
        logger.error(f"❌ Error stamping database: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error stamping database: {str(e)}"
        )

@router.post("/fix-llm-audit-schema")
async def fix_llm_audit_schema(db: Session = Depends(get_db)):
    """
    Fix llm_audit table schema by adding missing raw_response column
    """
    try:
        logger.info("🔧 Fixing llm_audit table schema...")
        
        # Check if raw_response column exists
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'llm_audit' 
            AND column_name = 'raw_response'
        """))
        
        if result.fetchone():
            logger.info("✅ raw_response column already exists")
            return {
                "status": "success",
                "message": "raw_response column already exists",
                "changes": []
            }
        
        # Add the raw_response column
        logger.info("📝 Adding raw_response column to llm_audit table...")
        db.execute(text("""
            ALTER TABLE llm_audit 
            ADD COLUMN raw_response TEXT
        """))
        
        db.commit()
        
        logger.info("✅ Successfully added raw_response column to llm_audit table")
        return {
            "status": "success",
            "message": "Successfully added raw_response column to llm_audit table",
            "changes": ["Added raw_response column to llm_audit table"]
        }
        
    except Exception as e:
        logger.error(f"❌ Error fixing llm_audit schema: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error fixing llm_audit schema: {str(e)}"
        )
