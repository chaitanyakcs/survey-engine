"""
Admin API endpoints for database management - No Alembic dependency
All migrations handled directly via SQL
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.database.connection import get_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/health")
async def admin_health_check(db: Session = Depends(get_db)):
    """
    Basic health check for admin endpoints
    """
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "message": "Admin endpoints are working",
            "database_connected": True
        }
    except Exception as e:
        logger.error(f"❌ Admin health check failed: {str(e)}")
        return {
            "status": "unhealthy", 
            "message": f"Database connection failed: {str(e)}",
            "database_connected": False
        }


@router.post("/migrate-all")
async def migrate_all(db: Session = Depends(get_db)):
    """
    Run all database migrations in the correct order
    """
    try:
        logger.info("🚀 [Admin] Starting comprehensive database migration")
        
        migration_results = []
        
        # Step 1: Core table migrations
        try:
            await _migrate_core_tables(db)
            migration_results.append({
                "step": "core_tables",
                "status": "success",
                "message": "Core tables migration completed"
            })
        except Exception as e:
            migration_results.append({
                "step": "core_tables", 
                "status": "failed",
                "message": f"Core tables migration failed: {str(e)}"
            })
        
        # Step 2: AI annotation fields
        try:
            await _migrate_ai_annotation_fields(db)
            migration_results.append({
                "step": "ai_annotation_fields",
                "status": "success", 
                "message": "AI annotation fields migration completed"
            })
        except Exception as e:
            migration_results.append({
                "step": "ai_annotation_fields",
                "status": "failed",
                "message": f"AI annotation fields migration failed: {str(e)}"
            })
        
        # Step 3: Human override tracking
        try:
            await _migrate_human_override_tracking(db)
            migration_results.append({
                "step": "human_override_tracking",
                "status": "success",
                "message": "Human override tracking migration completed"
            })
        except Exception as e:
            migration_results.append({
                "step": "human_override_tracking",
                "status": "failed", 
                "message": f"Human override tracking migration failed: {str(e)}"
            })
        
        # Step 4: Performance indexes
        try:
            await _migrate_performance_indexes(db)
            migration_results.append({
                "step": "performance_indexes",
                "status": "success",
                "message": "Performance indexes migration completed"
            })
        except Exception as e:
            migration_results.append({
                "step": "performance_indexes",
                "status": "failed",
                "message": f"Performance indexes migration failed: {str(e)}"
            })
        
        # Determine overall success
        successful_migrations = len([r for r in migration_results if r["status"] == "success"])
        failed_migrations = len([r for r in migration_results if r["status"] == "failed"])
        
        if failed_migrations == 0:
            logger.info("🎉 All migrations completed successfully!")
            return {
                "status": "success",
                "message": "All database migrations completed successfully",
                "migration_results": migration_results,
                "summary": {
                    "total_migrations": len(migration_results),
                    "successful_migrations": successful_migrations,
                    "failed_migrations": failed_migrations
                },
                "railway_ready": True
            }
        else:
            logger.warning(f"⚠️ {failed_migrations} migrations failed")
            return {
                "status": "partial",
                "message": f"Database migration completed with {failed_migrations} failures",
                "migration_results": migration_results,
                "summary": {
                    "total_migrations": len(migration_results),
                    "successful_migrations": successful_migrations,
                    "failed_migrations": failed_migrations
                },
                "railway_ready": failed_migrations == 0
            }
            
    except Exception as e:
        logger.error(f"❌ Comprehensive migration error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Comprehensive migration failed: {str(e)}"
        )


async def _migrate_core_tables(db: Session):
    """
    Migrate core database tables
    """
    logger.info("📝 Migrating core tables...")
    
    # Create question_annotations table if it doesn't exist
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS question_annotations (
            id SERIAL PRIMARY KEY,
            question_id VARCHAR(255) NOT NULL,
            survey_id VARCHAR(255) NOT NULL,
            required BOOLEAN NOT NULL DEFAULT TRUE,
            quality INTEGER NOT NULL CHECK (quality >= 1 AND quality <= 5),
            relevant INTEGER NOT NULL CHECK (relevant >= 1 AND relevant <= 5),
            comment TEXT,
            annotator_id VARCHAR(255),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            methodological_rigor INTEGER NOT NULL DEFAULT 3 CHECK (methodological_rigor >= 1 AND methodological_rigor <= 5),
            content_validity INTEGER NOT NULL DEFAULT 3 CHECK (content_validity >= 1 AND content_validity <= 5),
            respondent_experience INTEGER NOT NULL DEFAULT 3 CHECK (respondent_experience >= 1 AND respondent_experience <= 5),
            analytical_value INTEGER NOT NULL DEFAULT 3 CHECK (analytical_value >= 1 AND analytical_value <= 5),
            business_impact INTEGER NOT NULL DEFAULT 3 CHECK (business_impact >= 1 AND business_impact <= 5),
            labels JSONB,
            UNIQUE(question_id, annotator_id)
        )
    """))
    
    # Create section_annotations table if it doesn't exist
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS section_annotations (
            id SERIAL PRIMARY KEY,
            section_id VARCHAR(255) NOT NULL,
            survey_id VARCHAR(255) NOT NULL,
            required BOOLEAN NOT NULL DEFAULT TRUE,
            quality INTEGER NOT NULL CHECK (quality >= 1 AND quality <= 5),
            relevant INTEGER NOT NULL CHECK (relevant >= 1 AND relevant <= 5),
            comment TEXT,
            annotator_id VARCHAR(255),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            methodological_rigor INTEGER NOT NULL DEFAULT 3 CHECK (methodological_rigor >= 1 AND methodological_rigor <= 5),
            content_validity INTEGER NOT NULL DEFAULT 3 CHECK (content_validity >= 1 AND content_validity <= 5),
            respondent_experience INTEGER NOT NULL DEFAULT 3 CHECK (respondent_experience >= 1 AND respondent_experience <= 5),
            analytical_value INTEGER NOT NULL DEFAULT 3 CHECK (analytical_value >= 1 AND analytical_value <= 5),
            business_impact INTEGER NOT NULL DEFAULT 3 CHECK (business_impact >= 1 AND business_impact <= 5),
            labels JSONB,
            UNIQUE(section_id, annotator_id)
        )
    """))
    
    # Create survey_annotations table if it doesn't exist
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS survey_annotations (
            id SERIAL PRIMARY KEY,
            survey_id VARCHAR(255) NOT NULL UNIQUE,
            required BOOLEAN NOT NULL DEFAULT TRUE,
            quality INTEGER NOT NULL CHECK (quality >= 1 AND quality <= 5),
            relevant INTEGER NOT NULL CHECK (relevant >= 1 AND relevant <= 5),
            comment TEXT,
            annotator_id VARCHAR(255),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            methodological_rigor INTEGER NOT NULL DEFAULT 3 CHECK (methodological_rigor >= 1 AND methodological_rigor <= 5),
            content_validity INTEGER NOT NULL DEFAULT 3 CHECK (content_validity >= 1 AND content_validity <= 5),
            respondent_experience INTEGER NOT NULL DEFAULT 3 CHECK (respondent_experience >= 1 AND respondent_experience <= 5),
            analytical_value INTEGER NOT NULL DEFAULT 3 CHECK (analytical_value >= 1 AND analytical_value <= 5),
            business_impact INTEGER NOT NULL DEFAULT 3 CHECK (business_impact >= 1 AND business_impact <= 5),
            labels JSONB
        )
    """))
    
    db.commit()
    logger.info("✅ Core tables migration completed")


async def _migrate_ai_annotation_fields(db: Session):
    """
    Add AI annotation tracking fields
    """
    logger.info("🤖 Adding AI annotation fields...")
    
    # Add AI fields to question_annotations
    db.execute(text("""
        ALTER TABLE question_annotations 
        ADD COLUMN IF NOT EXISTS ai_generated BOOLEAN DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS ai_confidence DECIMAL(3,2) CHECK (ai_confidence >= 0.00 AND ai_confidence <= 1.00),
        ADD COLUMN IF NOT EXISTS human_verified BOOLEAN DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS generation_timestamp TIMESTAMP WITH TIME ZONE
    """))
    
    # Add AI fields to section_annotations
    db.execute(text("""
        ALTER TABLE section_annotations 
        ADD COLUMN IF NOT EXISTS ai_generated BOOLEAN DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS ai_confidence DECIMAL(3,2) CHECK (ai_confidence >= 0.00 AND ai_confidence <= 1.00),
        ADD COLUMN IF NOT EXISTS human_verified BOOLEAN DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS generation_timestamp TIMESTAMP WITH TIME ZONE
    """))
    
    db.commit()
    logger.info("✅ AI annotation fields added")


async def _migrate_human_override_tracking(db: Session):
    """
    Add human override tracking fields
    """
    logger.info("👤 Adding human override tracking fields...")
    
    # Add override fields to question_annotations
    db.execute(text("""
        ALTER TABLE question_annotations 
        ADD COLUMN IF NOT EXISTS human_overridden BOOLEAN DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS override_timestamp TIMESTAMP WITH TIME ZONE,
        ADD COLUMN IF NOT EXISTS original_ai_quality INTEGER,
        ADD COLUMN IF NOT EXISTS original_ai_relevant INTEGER,
        ADD COLUMN IF NOT EXISTS original_ai_comment TEXT
    """))
    
    # Add override fields to section_annotations
    db.execute(text("""
        ALTER TABLE section_annotations 
        ADD COLUMN IF NOT EXISTS human_overridden BOOLEAN DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS override_timestamp TIMESTAMP WITH TIME ZONE,
        ADD COLUMN IF NOT EXISTS original_ai_quality INTEGER,
        ADD COLUMN IF NOT EXISTS original_ai_relevant INTEGER,
        ADD COLUMN IF NOT EXISTS original_ai_comment TEXT
    """))
    
    db.commit()
    logger.info("✅ Human override tracking fields added")


async def _migrate_performance_indexes(db: Session):
    """
    Add performance indexes for human vs AI stats
    """
    logger.info("📊 Adding performance indexes...")
    
    indexes_sql = [
        # Question annotations indexes
        "CREATE INDEX IF NOT EXISTS idx_question_annotations_ai_generated ON question_annotations (ai_generated)",
        "CREATE INDEX IF NOT EXISTS idx_question_annotations_ai_confidence ON question_annotations (ai_confidence) WHERE ai_confidence IS NOT NULL",
        "CREATE INDEX IF NOT EXISTS idx_question_annotations_ai_verified ON question_annotations (human_verified) WHERE human_verified = true",
        "CREATE INDEX IF NOT EXISTS idx_question_annotations_ai_overridden ON question_annotations (human_overridden) WHERE human_overridden = true",
        "CREATE INDEX IF NOT EXISTS idx_question_annotations_annotator_current_user ON question_annotations (annotator_id) WHERE annotator_id = 'current-user'",
        "CREATE INDEX IF NOT EXISTS idx_question_annotations_survey_id ON question_annotations (survey_id)",
        "CREATE INDEX IF NOT EXISTS idx_question_annotations_annotator_id ON question_annotations (annotator_id)",
        
        # Section annotations indexes
        "CREATE INDEX IF NOT EXISTS idx_section_annotations_ai_generated ON section_annotations (ai_generated)",
        "CREATE INDEX IF NOT EXISTS idx_section_annotations_ai_confidence ON section_annotations (ai_confidence) WHERE ai_confidence IS NOT NULL",
        "CREATE INDEX IF NOT EXISTS idx_section_annotations_ai_verified ON section_annotations (human_verified) WHERE human_verified = true",
        "CREATE INDEX IF NOT EXISTS idx_section_annotations_ai_overridden ON section_annotations (human_overridden) WHERE human_overridden = true",
        "CREATE INDEX IF NOT EXISTS idx_section_annotations_annotator_current_user ON section_annotations (annotator_id) WHERE annotator_id = 'current-user'",
        "CREATE INDEX IF NOT EXISTS idx_section_annotations_survey_id ON section_annotations (survey_id)",
        "CREATE INDEX IF NOT EXISTS idx_section_annotations_annotator_id ON section_annotations (annotator_id)",
        
        # Survey annotations indexes
        "CREATE INDEX IF NOT EXISTS idx_survey_annotations_survey_id ON survey_annotations (survey_id)",
        "CREATE INDEX IF NOT EXISTS idx_survey_annotations_annotator_id ON survey_annotations (annotator_id)"
    ]
    
    for sql in indexes_sql:
        try:
            db.execute(text(sql))
        except Exception as e:
            logger.warning(f"⚠️ Index creation warning: {e}")
    
    db.commit()
    logger.info("✅ Performance indexes added")


@router.get("/check-migration-status")
async def check_migration_status(db: Session = Depends(get_db)):
    """
    Check the status of all migrations
    """
    try:
        logger.info("🔍 Checking migration status...")
        
        # Check if tables exist
        tables_check = {}
        tables = ['question_annotations', 'section_annotations', 'survey_annotations']
        
        for table in tables:
            try:
                result = db.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = '{table}'
                    )
                """)).fetchone()
                tables_check[table] = result[0] if result else False
            except Exception as e:
                tables_check[table] = f"Error: {str(e)}"
        
        # Check if AI annotation fields exist
        ai_fields_check = {}
        ai_fields = ['ai_generated', 'ai_confidence', 'human_verified', 'generation_timestamp']
        
        for field in ai_fields:
            try:
                result = db.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = 'question_annotations' AND column_name = '{field}'
                    )
                """)).fetchone()
                ai_fields_check[f"question_annotations.{field}"] = result[0] if result else False
                
                result = db.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = 'section_annotations' AND column_name = '{field}'
                    )
                """)).fetchone()
                ai_fields_check[f"section_annotations.{field}"] = result[0] if result else False
            except Exception as e:
                ai_fields_check[f"question_annotations.{field}"] = f"Error: {str(e)}"
                ai_fields_check[f"section_annotations.{field}"] = f"Error: {str(e)}"
        
        # Check if human override fields exist
        override_fields_check = {}
        override_fields = ['human_overridden', 'override_timestamp', 'original_ai_quality', 'original_ai_relevant', 'original_ai_comment']
        
        for field in override_fields:
            try:
                result = db.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = 'question_annotations' AND column_name = '{field}'
                    )
                """)).fetchone()
                override_fields_check[f"question_annotations.{field}"] = result[0] if result else False
                
                result = db.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = 'section_annotations' AND column_name = '{field}'
                    )
                """)).fetchone()
                override_fields_check[f"section_annotations.{field}"] = result[0] if result else False
            except Exception as e:
                override_fields_check[f"question_annotations.{field}"] = f"Error: {str(e)}"
                override_fields_check[f"section_annotations.{field}"] = f"Error: {str(e)}"
        
        # Check indexes
        indexes_check = {}
        expected_indexes = [
            'idx_question_annotations_ai_generated',
            'idx_question_annotations_ai_confidence', 
            'idx_question_annotations_ai_verified',
            'idx_question_annotations_ai_overridden',
            'idx_question_annotations_annotator_current_user',
            'idx_section_annotations_ai_generated',
            'idx_section_annotations_ai_confidence',
            'idx_section_annotations_ai_verified', 
            'idx_section_annotations_ai_overridden',
            'idx_section_annotations_annotator_current_user'
        ]
        
        for index_name in expected_indexes:
            try:
                result = db.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM pg_indexes 
                        WHERE indexname = '{index_name}'
                    )
                """)).fetchone()
                indexes_check[index_name] = result[0] if result else False
            except Exception as e:
                indexes_check[index_name] = f"Error: {str(e)}"
        
        # Calculate overall status
        all_tables_exist = all(isinstance(v, bool) and v for v in tables_check.values())
        all_ai_fields_exist = all(isinstance(v, bool) and v for v in ai_fields_check.values())
        all_override_fields_exist = all(isinstance(v, bool) and v for v in override_fields_check.values())
        all_indexes_exist = all(isinstance(v, bool) and v for v in indexes_check.values())
        
        overall_status = "complete" if all_tables_exist and all_ai_fields_exist and all_override_fields_exist and all_indexes_exist else "incomplete"
        
        return {
            "status": overall_status,
            "message": f"Migration status: {overall_status}",
            "checks": {
                "tables": tables_check,
                "ai_fields": ai_fields_check,
                "override_fields": override_fields_check,
                "indexes": indexes_check
            },
            "summary": {
                "tables_complete": all_tables_exist,
                "ai_fields_complete": all_ai_fields_exist,
                "override_fields_complete": all_override_fields_exist,
                "indexes_complete": all_indexes_exist,
                "overall_complete": overall_status == "complete"
            },
            "railway_ready": overall_status == "complete"
        }
        
    except Exception as e:
        logger.error(f"❌ Migration status check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Migration status check failed: {str(e)}"
        )


@router.get("/human-vs-ai-stats")
async def get_human_vs_ai_stats(db: Session = Depends(get_db)):
    """
    Get detailed human vs AI annotation statistics
    """
    try:
        logger.info("🔍 [Admin] Fetching human vs AI annotation statistics")
        
        from src.database.models import QuestionAnnotation, SectionAnnotation, SurveyAnnotation
        from src.utils.database_session_manager import DatabaseSessionManager
        
        # Get basic counts
        total_qa = DatabaseSessionManager.safe_query(
            db,
            lambda: db.query(QuestionAnnotation).count(),
            fallback_value=0,
            operation_name="total question annotations"
        )
        
        total_sa = DatabaseSessionManager.safe_query(
            db,
            lambda: db.query(SectionAnnotation).count(),
            fallback_value=0,
            operation_name="total section annotations"
        )
        
        total_sva = DatabaseSessionManager.safe_query(
            db,
            lambda: db.query(SurveyAnnotation).count(),
            fallback_value=0,
            operation_name="total survey annotations"
        )
        
        # AI vs Human breakdown
        ai_qa = DatabaseSessionManager.safe_query(
            db,
            lambda: db.query(QuestionAnnotation).filter(QuestionAnnotation.ai_generated == True).count(),
            fallback_value=0,
            operation_name="AI question annotations"
        )
        
        human_qa = DatabaseSessionManager.safe_query(
            db,
            lambda: db.query(QuestionAnnotation).filter(QuestionAnnotation.annotator_id == "current-user").count(),
            fallback_value=0,
            operation_name="human question annotations"
        )
        
        ai_sa = DatabaseSessionManager.safe_query(
            db,
            lambda: db.query(SectionAnnotation).filter(SectionAnnotation.ai_generated == True).count(),
            fallback_value=0,
            operation_name="AI section annotations"
        )
        
        human_sa = DatabaseSessionManager.safe_query(
            db,
            lambda: db.query(SectionAnnotation).filter(SectionAnnotation.annotator_id == "current-user").count(),
            fallback_value=0,
            operation_name="human section annotations"
        )
        
        # Override and verification stats
        overridden_qa = DatabaseSessionManager.safe_query(
            db,
            lambda: db.query(QuestionAnnotation).filter(QuestionAnnotation.human_overridden == True).count(),
            fallback_value=0,
            operation_name="overridden question annotations"
        )
        
        overridden_sa = DatabaseSessionManager.safe_query(
            db,
            lambda: db.query(SectionAnnotation).filter(SectionAnnotation.human_overridden == True).count(),
            fallback_value=0,
            operation_name="overridden section annotations"
        )
        
        verified_qa = DatabaseSessionManager.safe_query(
            db,
            lambda: db.query(QuestionAnnotation).filter(QuestionAnnotation.human_verified == True).count(),
            fallback_value=0,
            operation_name="verified question annotations"
        )
        
        verified_sa = DatabaseSessionManager.safe_query(
            db,
            lambda: db.query(SectionAnnotation).filter(SectionAnnotation.human_verified == True).count(),
            fallback_value=0,
            operation_name="verified section annotations"
        )
        
        # Calculate percentages
        total_annotations = total_qa + total_sa + total_sva
        total_ai = ai_qa + ai_sa
        total_human = human_qa + human_sa
        total_overridden = overridden_qa + overridden_sa
        total_verified = verified_qa + verified_sa
        
        ai_percentage = (total_ai / total_annotations * 100) if total_annotations > 0 else 0
        human_percentage = (total_human / total_annotations * 100) if total_annotations > 0 else 0
        verification_rate = (total_verified / total_ai * 100) if total_ai > 0 else 0
        override_rate = (total_overridden / total_ai * 100) if total_ai > 0 else 0
        
        return {
            "status": "success",
            "summary": {
                "total_annotations": total_annotations,
                "total_ai_annotations": total_ai,
                "total_human_annotations": total_human,
                "ai_percentage": round(ai_percentage, 2),
                "human_percentage": round(human_percentage, 2),
                "verification_rate": round(verification_rate, 2),
                "override_rate": round(override_rate, 2)
            },
            "detailed_breakdown": {
                "question_annotations": {
                    "total": total_qa,
                    "ai_generated": ai_qa,
                    "human_created": human_qa,
                    "overridden": overridden_qa,
                    "verified": verified_qa
                },
                "section_annotations": {
                    "total": total_sa,
                    "ai_generated": ai_sa,
                    "human_created": human_sa,
                    "overridden": overridden_sa,
                    "verified": verified_sa
                },
                "survey_annotations": {
                    "total": total_sva
                }
            },
            "metadata": {
                "timestamp": "2024-01-15T10:30:00Z",
                "data_source": "annotation_database",
                "admin_endpoint": True
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch human vs AI stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch human vs AI stats: {str(e)}"
        )