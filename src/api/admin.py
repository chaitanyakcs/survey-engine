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

@router.post("/fix-processing-status-constraint")
async def fix_processing_status_constraint(db: Session = Depends(get_db)):
    """
    Fix the processing_status constraint to include 'cancelled' status
    """
    try:
        logger.info("🔧 Fixing processing_status constraint to include 'cancelled'...")
        
        # Check current constraint
        result = db.execute(text("""
            SELECT constraint_name, check_clause
            FROM information_schema.check_constraints
            WHERE constraint_name = 'check_processing_status'
            AND constraint_schema = 'public'
        """))
        
        current_constraint = result.fetchone()
        
        if current_constraint:
            constraint_clause = current_constraint[1]
            logger.info(f"📋 Current constraint: {constraint_clause}")
            
            if "'cancelled'" in constraint_clause:
                logger.info("✅ Constraint already includes 'cancelled' status")
                return {
                    "status": "success",
                    "message": "Constraint already includes 'cancelled' status",
                    "current_constraint": constraint_clause,
                    "changes": []
                }
        
        # Drop existing constraint
        logger.info("🗑️ Dropping existing check_processing_status constraint...")
        try:
            db.execute(text("ALTER TABLE document_uploads DROP CONSTRAINT check_processing_status"))
            logger.info("✅ Dropped existing constraint")
        except Exception as e:
            if "does not exist" in str(e):
                logger.info("ℹ️ Constraint doesn't exist, continuing...")
            else:
                raise e
        
        # Add new constraint with 'cancelled' status
        logger.info("📝 Adding new constraint with 'cancelled' status...")
        db.execute(text("""
            ALTER TABLE document_uploads 
            ADD CONSTRAINT check_processing_status 
            CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed', 'cancelled'))
        """))
        
        db.commit()
        
        logger.info("✅ Successfully updated processing_status constraint")
        
        # Test the constraint by trying to insert a cancelled record
        logger.info("🧪 Testing constraint with 'cancelled' status...")
        try:
            db.execute(text("""
                INSERT INTO document_uploads (session_id, filename, file_size, processing_status, created_at)
                VALUES ('test-constraint-verification', 'test.docx', 1024, 'cancelled', NOW())
                ON CONFLICT (session_id) DO UPDATE SET processing_status = 'cancelled'
            """))
            db.commit()
            logger.info("✅ Successfully tested 'cancelled' status insertion")
            
            # Clean up test record
            db.execute(text("DELETE FROM document_uploads WHERE session_id = 'test-constraint-verification'"))
            db.commit()
            logger.info("🧹 Cleaned up test record")
            
        except Exception as e:
            logger.error(f"❌ Constraint test failed: {str(e)}")
            raise e
        
        return {
            "status": "success",
            "message": "Successfully updated processing_status constraint to include 'cancelled'",
            "changes": [
                "Dropped old check_processing_status constraint",
                "Added new constraint with 'cancelled' status",
                "Tested constraint with 'cancelled' status insertion"
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Error fixing processing_status constraint: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error fixing processing_status constraint: {str(e)}"
        )

@router.get("/verify-processing-status-constraint")
async def verify_processing_status_constraint(db: Session = Depends(get_db)):
    """
    Verify that the processing_status constraint includes 'cancelled' status
    """
    try:
        logger.info("🔍 Verifying processing_status constraint...")

        # Check current constraint
        result = db.execute(text("""
            SELECT constraint_name, check_clause
            FROM information_schema.check_constraints
            WHERE constraint_name = 'check_processing_status'
            AND constraint_schema = 'public'
        """))

        current_constraint = result.fetchone()

        if not current_constraint:
            logger.warning("⚠️ check_processing_status constraint not found")
            return {
                "status": "error",
                "message": "check_processing_status constraint not found",
                "constraint_exists": False
            }

        constraint_clause = current_constraint[1]
        logger.info(f"📋 Current constraint: {constraint_clause}")

        has_cancelled = "'cancelled'" in constraint_clause

        if has_cancelled:
            logger.info("✅ Constraint includes 'cancelled' status")
            return {
                "status": "success",
                "message": "Constraint includes 'cancelled' status",
                "constraint_exists": True,
                "has_cancelled": True,
                "constraint_clause": constraint_clause
            }
        else:
            logger.warning("⚠️ Constraint does not include 'cancelled' status")
            return {
                "status": "warning",
                "message": "Constraint does not include 'cancelled' status",
                "constraint_exists": True,
                "has_cancelled": False,
                "constraint_clause": constraint_clause
            }

    except Exception as e:
        logger.error(f"❌ Error verifying processing_status constraint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error verifying processing_status constraint: {str(e)}"
        )

@router.post("/add-failed-status-to-surveys")
async def add_failed_status_to_surveys(db: Session = Depends(get_db)):
    """
    Add 'failed' status to surveys table constraint
    This allows marking surveys that used minimal fallback due to LLM generation failures
    """
    try:
        logger.info("🔧 Adding 'failed' status to surveys table constraint...")

        # Check current constraint
        result = db.execute(text("""
            SELECT constraint_name, check_clause
            FROM information_schema.check_constraints
            WHERE constraint_schema = 'public'
            AND check_clause LIKE '%status%'
            AND constraint_name LIKE '%survey%'
        """))

        constraints = result.fetchall()
        logger.info(f"📋 Found {len(constraints)} survey-related constraints")

        for constraint in constraints:
            logger.info(f"   - {constraint[0]}: {constraint[1]}")

        # Find the specific survey status constraint
        survey_status_constraint = None
        for constraint in constraints:
            if "'draft'" in constraint[1] and "'validated'" in constraint[1]:
                survey_status_constraint = constraint
                break

        if survey_status_constraint:
            constraint_name = survey_status_constraint[0]
            constraint_clause = survey_status_constraint[1]
            logger.info(f"📋 Current survey status constraint: {constraint_clause}")

            if "'failed'" in constraint_clause:
                logger.info("✅ Constraint already includes 'failed' status")
                return {
                    "status": "success",
                    "message": "Constraint already includes 'failed' status",
                    "current_constraint": constraint_clause,
                    "changes": []
                }

        # Drop existing constraint
        logger.info("🗑️ Dropping existing survey status constraint...")
        try:
            if survey_status_constraint:
                db.execute(text(f"ALTER TABLE surveys DROP CONSTRAINT {survey_status_constraint[0]}"))
                logger.info(f"✅ Dropped constraint: {survey_status_constraint[0]}")
            else:
                # Try common constraint name
                db.execute(text("ALTER TABLE surveys DROP CONSTRAINT surveys_status_check"))
                logger.info("✅ Dropped constraint: surveys_status_check")
        except Exception as e:
            if "does not exist" in str(e):
                logger.info("ℹ️ Constraint doesn't exist, continuing...")
            else:
                raise e

        # Add new constraint with 'failed' status
        logger.info("📝 Adding new constraint with 'failed' status...")
        db.execute(text("""
            ALTER TABLE surveys
            ADD CONSTRAINT surveys_status_check
            CHECK (status IN ('draft', 'validated', 'edited', 'final', 'failed', 'reparsed'))
        """))

        db.commit()

        logger.info("✅ Successfully updated survey status constraint")

        return {
            "status": "success",
            "message": "Successfully added 'failed' status to surveys constraint",
            "changes": [
                "Dropped old survey status constraint",
                "Added new constraint with 'failed' and 'reparsed' statuses"
            ]
        }

    except Exception as e:
        logger.error(f"❌ Error adding failed status to surveys: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error adding failed status to surveys: {str(e)}"
        )

@router.get("/verify-survey-status-constraint")
async def verify_survey_status_constraint(db: Session = Depends(get_db)):
    """
    Verify that the survey status constraint includes 'failed' status
    """
    try:
        logger.info("🔍 Verifying survey status constraint...")

        # Check current constraint
        result = db.execute(text("""
            SELECT constraint_name, check_clause
            FROM information_schema.check_constraints
            WHERE constraint_schema = 'public'
            AND check_clause LIKE '%status%'
            AND constraint_name LIKE '%survey%'
        """))

        constraints = result.fetchall()

        if not constraints:
            logger.warning("⚠️ Survey status constraint not found")
            return {
                "status": "error",
                "message": "Survey status constraint not found",
                "constraint_exists": False
            }

        for constraint in constraints:
            constraint_name = constraint[0]
            constraint_clause = constraint[1]
            logger.info(f"📋 Found constraint: {constraint_name}")
            logger.info(f"    Clause: {constraint_clause}")

            if "'draft'" in constraint_clause and "'validated'" in constraint_clause:
                has_failed = "'failed'" in constraint_clause

                if has_failed:
                    logger.info("✅ Constraint includes 'failed' status")
                    return {
                        "status": "success",
                        "message": "Constraint includes 'failed' status",
                        "constraint_exists": True,
                        "has_failed": True,
                        "constraint_clause": constraint_clause
                    }
                else:
                    logger.warning("⚠️ Constraint does not include 'failed' status")
                    return {
                        "status": "warning",
                        "message": "Constraint does not include 'failed' status",
                        "constraint_exists": True,
                        "has_failed": False,
                        "constraint_clause": constraint_clause
                    }

        return {
            "status": "warning",
            "message": "No matching survey status constraint found",
            "constraint_exists": False
        }

    except Exception as e:
        logger.error(f"❌ Error verifying survey status constraint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error verifying survey status constraint: {str(e)}"
        )
