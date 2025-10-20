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


@router.get("/debug/check-removed-labels-column")
async def check_removed_labels_column(db: Session = Depends(get_db)):
    """Debug endpoint to check if removed_labels column exists"""
    try:
        # Check if the column exists
        result = db.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'question_annotations' 
            AND column_name = 'removed_labels'
        """)).fetchone()
        
        if result:
            # Also check actual data in the table
            data_result = db.execute(text("""
                SELECT question_id, labels, removed_labels 
                FROM question_annotations 
                WHERE survey_id = '2' 
                ORDER BY created_at DESC 
                LIMIT 3
            """)).fetchall()
            
            return {
                "column_exists": True,
                "column_name": result[0],
                "data_type": result[1],
                "sample_data": [
                    {
                        "question_id": row[0],
                        "labels": row[1],
                        "removed_labels": row[2]
                    } for row in data_result
                ]
            }
        else:
            return {
                "column_exists": False,
                "message": "removed_labels column not found in question_annotations table"
            }
    except Exception as e:
        return {
            "error": str(e),
            "column_exists": False
        }


@router.get("/ready")
async def readiness_check():
    """
    Readiness check - returns 200 if models loaded, 425 if still loading
    Used by load balancers and health check systems
    """
    try:
        from src.services.model_loader import BackgroundModelLoader
        from src.services.embedding_service import EmbeddingService
        
        # Check if models are ready
        if EmbeddingService.is_ready() and BackgroundModelLoader.is_ready():
            return {
                "status": "ready",
                "message": "All systems ready",
                "ready": True,
                "models_loaded": True
            }
        
        # Models still loading - return 425 Too Early
        status = BackgroundModelLoader.get_status()
        from fastapi import HTTPException
        raise HTTPException(
            status_code=425,  # Too Early
            detail={
                "status": "initializing",
                "message": "AI models are still loading",
                "ready": False,
                "progress": status["progress"],
                "estimated_seconds": status["estimated_seconds"],
                "phase": status["phase"],
                "type": "initialization"  # Distinguish from errors
            },
            headers={"Retry-After": str(max(status["estimated_seconds"], 30))}
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (425 Too Early)
        raise
    except Exception as e:
        logger.error(f"❌ Readiness check failed: {str(e)}")
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Readiness check failed: {str(e)}",
                "ready": False,
                "type": "error"
            }
        )


@router.post("/migrate-all")
async def migrate_all(db: Session = Depends(get_db)):
    """
    Run all database migrations in the correct order
    """
    try:
        logger.info("🚀 [Admin] Starting comprehensive database migration")
        
        migration_results = []

        # Step 0: Ensure required extensions (pgcrypto, vector)
        try:
            await _enable_required_extensions(db)
            migration_results.append({
                "step": "enable_extensions",
                "status": "success",
                "message": "Required extensions enabled (pgcrypto, vector)"
            })
        except Exception as e:
            migration_results.append({
                "step": "enable_extensions",
                "status": "failed",
                "message": f"Failed to enable extensions: {str(e)}"
            })
        
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
        
        # Step 2: Add removed_labels column
        try:
            await _migrate_removed_labels_column(db)
            migration_results.append({
                "step": "removed_labels_column",
                "status": "success", 
                "message": "Removed labels column migration completed"
            })
        except Exception as e:
            migration_results.append({
                "step": "removed_labels_column",
                "status": "failed",
                "message": f"Removed labels column migration failed: {str(e)}"
            })
        
        # Step 3: AI annotation fields
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
        
        # Step 4: Human override tracking
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
        
        # Step 4: LLM audit system
        try:
            await _migrate_llm_audit_system(db)
            migration_results.append({
                "step": "llm_audit_system",
                "status": "success",
                "message": "LLM audit system migration completed"
            })
        except Exception as e:
            migration_results.append({
                "step": "llm_audit_system",
                "status": "failed",
                "message": f"LLM audit system migration failed: {str(e)}"
            })
        
        # Step 5: Performance indexes
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
        
        # Step 6: Retrieval configuration tables (weights, methodology compatibility)
        try:
            await _migrate_retrieval_configuration(db)
            migration_results.append({
                "step": "retrieval_configuration",
                "status": "success",
                "message": "Retrieval configuration tables migration completed"
            })
        except Exception as e:
            migration_results.append({
                "step": "retrieval_configuration",
                "status": "failed",
                "message": f"Retrieval configuration migration failed: {str(e)}"
            })

        # Step 7: Fix SurveyAnnotation constraint
        try:
            await _fix_survey_annotation_constraint(db)
            migration_results.append({
                "step": "fix_survey_annotation_constraint",
                "status": "success",
                "message": "SurveyAnnotation constraint fix completed"
            })
        except Exception as e:
            migration_results.append({
                "step": "fix_survey_annotation_constraint",
                "status": "failed", 
                "message": f"SurveyAnnotation constraint fix failed: {str(e)}"
            })
        
        # Step 8: Update survey status constraint
        try:
            await _migrate_survey_status_constraint(db)
            migration_results.append({
                "step": "update_survey_status_constraint",
                "status": "success",
                "message": "Survey status constraint updated to include 'reference' status"
            })
        except Exception as e:
            migration_results.append({
                "step": "update_survey_status_constraint",
                "status": "failed",
                "message": f"Survey status constraint update failed: {str(e)}"
            })
        
        # Step 9: Clean up Alembic version table
        try:
            await _migrate_drop_alembic_version(db)
            migration_results.append({
                "step": "drop_alembic_version",
                "status": "success",
                "message": "Alembic version table cleanup completed"
            })
        except Exception as e:
            migration_results.append({
                "step": "drop_alembic_version",
                "status": "failed",
                "message": f"Alembic version table cleanup failed: {str(e)}"
            })
        
        # Step 10: Seed generation rules
        try:
            await _seed_generation_rules(db)
            migration_results.append({
                "step": "seed_generation_rules",
                "status": "success",
                "message": "Generation rules seeding completed"
            })
        except Exception as e:
            migration_results.append({
                "step": "seed_generation_rules",
                "status": "failed",
                "message": f"Generation rules seeding failed: {str(e)}"
            })
        
        # Step 11: Multi-level RAG tables
        try:
            await _migrate_multi_level_rag_tables(db)
            migration_results.append({
                "step": "multi_level_rag_tables",
                "status": "success",
                "message": "Multi-level RAG tables migration completed"
            })
        except Exception as e:
            migration_results.append({
                "step": "multi_level_rag_tables",
                "status": "failed",
                "message": f"Multi-level RAG tables migration failed: {str(e)}"
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


@router.post("/bootstrap-golden-pairs")
async def bootstrap_golden_pairs(db: Session = Depends(get_db)):
    """
    Bootstrap golden pairs from existing high-quality surveys
    Only runs if production has < 10 golden pairs
    """
    try:
        logger.info("🌱 [Admin] Starting golden pairs bootstrap")
        
        # Import the bootstrap function
        import asyncio
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        
        from scripts.bootstrap_golden_pairs_from_existing import bootstrap_golden_pairs
        
        # Run bootstrap in production mode
        stats = await bootstrap_golden_pairs(
            min_quality_score=0.5,
            dry_run=False,
            production_mode=True
        )
        
        if stats.get('skipped', False):
            logger.info(f"✅ [Admin] Bootstrap skipped - already has {stats['existing_count']} golden pairs")
            return {
                "status": "success",
                "message": f"Bootstrap skipped - already has {stats['existing_count']} golden pairs",
                "skipped": True,
                "existing_count": stats['existing_count']
            }
        elif stats['golden_pairs_created'] > 0:
            logger.info(f"✅ [Admin] Bootstrap completed - created {stats['golden_pairs_created']} golden pairs")
            return {
                "status": "success",
                "message": f"Bootstrap completed - created {stats['golden_pairs_created']} golden pairs",
                "created": stats['golden_pairs_created'],
                "total": stats['existing_count'] + stats['golden_pairs_created']
            }
        else:
            logger.warning("⚠️ [Admin] Bootstrap completed but no golden pairs created")
            return {
                "status": "success",
                "message": "Bootstrap completed but no golden pairs created",
                "created": 0,
                "total": stats['existing_count']
            }
            
    except Exception as e:
        logger.error(f"❌ [Admin] Bootstrap error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Bootstrap failed: {str(e)}"
        )


@router.post("/populate-multi-level-rag")
async def populate_multi_level_rag(db: Session = Depends(get_db)):
    """
    Populate multi-level RAG tables (golden_sections and golden_questions)
    from existing golden pairs
    """
    try:
        logger.info("🔍 [Admin] Starting multi-level RAG population")
        
        import asyncio
        import sys
        import os
        
        # Add project root to Python path
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if project_root not in sys.path:
            sys.path.append(project_root)
        
        # Try different import paths for the population script
        try:
            from scripts.populate_rule_based_multi_level_rag import populate_multi_level_rag
        except ImportError:
            # Fallback: try importing from the current directory structure
            try:
                import populate_rule_based_multi_level_rag
                populate_multi_level_rag = populate_rule_based_multi_level_rag.populate_multi_level_rag
            except ImportError:
                # Last resort: try to find and import the script dynamically
                script_path = os.path.join(project_root, 'scripts', 'populate_rule_based_multi_level_rag.py')
                if os.path.exists(script_path):
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("populate_script", script_path)
                    populate_script = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(populate_script)
                    populate_multi_level_rag = populate_script.populate_multi_level_rag
                else:
                    raise ImportError(f"Could not find population script at {script_path}")
        
        stats = await populate_multi_level_rag(dry_run=False)
        
        if stats['sections_created'] > 0 or stats['questions_created'] > 0:
            logger.info(f"✅ [Admin] Multi-level RAG population completed - created {stats['sections_created']} sections and {stats['questions_created']} questions")
            return {
                "status": "success",
                "message": f"Multi-level RAG population completed - created {stats['sections_created']} sections and {stats['questions_created']} questions",
                "sections_created": stats['sections_created'],
                "questions_created": stats['questions_created'],
                "golden_pairs_processed": stats['golden_pairs_processed'],
                "errors": stats['errors']
            }
        else:
            logger.warning("⚠️ [Admin] Multi-level RAG population completed but no sections/questions created")
            return {
                "status": "success",
                "message": "Multi-level RAG population completed but no sections/questions created",
                "sections_created": 0,
                "questions_created": 0,
                "golden_pairs_processed": stats['golden_pairs_processed'],
                "errors": stats['errors']
            }
            
    except Exception as e:
        logger.error(f"❌ [Admin] Multi-level RAG population error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Multi-level RAG population failed: {str(e)}"
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
            removed_labels JSONB,
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


async def _migrate_removed_labels_column(db: Session):
    """
    Add removed_labels column to question_annotations table
    """
    logger.info("🏷️ Adding removed_labels column...")
    
    # Add removed_labels column to question_annotations
    db.execute(text("""
        ALTER TABLE question_annotations 
        ADD COLUMN IF NOT EXISTS removed_labels JSONB
    """))
    
    # Add comment for documentation
    db.execute(text("""
        COMMENT ON COLUMN question_annotations.removed_labels IS 
        'Array of auto-generated labels that the user has explicitly removed from this annotation'
    """))
    
    db.commit()
    logger.info("✅ Removed labels column migration completed")


async def _migrate_ai_annotation_fields(db: Session):
    """
    Add AI annotation tracking fields
    """
    logger.info("🤖 Adding AI annotation fields...")
    
    # Add AI fields to question_annotations
    db.execute(text("""
        ALTER TABLE question_annotations 
        ADD COLUMN IF NOT EXISTS ai_generated BOOLEAN NOT NULL DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS ai_confidence DECIMAL(3,2) CHECK (ai_confidence >= 0.00 AND ai_confidence <= 1.00),
        ADD COLUMN IF NOT EXISTS human_verified BOOLEAN NOT NULL DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS generation_timestamp TIMESTAMP WITH TIME ZONE
    """))
    
    # Add advanced labeling fields to question_annotations
    db.execute(text("""
        ALTER TABLE question_annotations 
        ADD COLUMN IF NOT EXISTS advanced_labels JSONB,
        ADD COLUMN IF NOT EXISTS industry_classification VARCHAR(100),
        ADD COLUMN IF NOT EXISTS respondent_type VARCHAR(100),
        ADD COLUMN IF NOT EXISTS methodology_tags TEXT[],
        ADD COLUMN IF NOT EXISTS is_mandatory BOOLEAN DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS compliance_status VARCHAR(50)
    """))
    
    # Add AI fields to section_annotations
    db.execute(text("""
        ALTER TABLE section_annotations 
        ADD COLUMN IF NOT EXISTS ai_generated BOOLEAN NOT NULL DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS ai_confidence DECIMAL(3,2) CHECK (ai_confidence >= 0.00 AND ai_confidence <= 1.00),
        ADD COLUMN IF NOT EXISTS human_verified BOOLEAN NOT NULL DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS generation_timestamp TIMESTAMP WITH TIME ZONE
    """))
    
    # Add advanced labeling fields to section_annotations
    db.execute(text("""
        ALTER TABLE section_annotations 
        ADD COLUMN IF NOT EXISTS section_classification VARCHAR(100),
        ADD COLUMN IF NOT EXISTS mandatory_elements JSONB,
        ADD COLUMN IF NOT EXISTS compliance_score INTEGER
    """))
    
    # Add advanced labeling fields to survey_annotations
    db.execute(text("""
        ALTER TABLE survey_annotations 
        ADD COLUMN IF NOT EXISTS detected_labels JSONB,
        ADD COLUMN IF NOT EXISTS compliance_report JSONB,
        ADD COLUMN IF NOT EXISTS advanced_metadata JSONB
    """))
    
    # Create indexes for AI annotation fields
    db.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_question_annotations_ai_generated ON question_annotations(ai_generated);
        CREATE INDEX IF NOT EXISTS idx_question_annotations_human_overridden ON question_annotations(human_overridden);
        CREATE INDEX IF NOT EXISTS idx_question_annotations_human_verified ON question_annotations(human_verified);
        CREATE INDEX IF NOT EXISTS idx_section_annotations_ai_generated ON section_annotations(ai_generated);
        CREATE INDEX IF NOT EXISTS idx_section_annotations_human_overridden ON section_annotations(human_overridden);
        CREATE INDEX IF NOT EXISTS idx_section_annotations_human_verified ON section_annotations(human_verified)
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
        ADD COLUMN IF NOT EXISTS human_overridden BOOLEAN NOT NULL DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS override_timestamp TIMESTAMP WITH TIME ZONE,
        ADD COLUMN IF NOT EXISTS original_ai_quality INTEGER,
        ADD COLUMN IF NOT EXISTS original_ai_relevant INTEGER,
        ADD COLUMN IF NOT EXISTS original_ai_comment TEXT
    """))
    
    # Add override fields to section_annotations
    db.execute(text("""
        ALTER TABLE section_annotations 
        ADD COLUMN IF NOT EXISTS human_overridden BOOLEAN NOT NULL DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS override_timestamp TIMESTAMP WITH TIME ZONE,
        ADD COLUMN IF NOT EXISTS original_ai_quality INTEGER,
        ADD COLUMN IF NOT EXISTS original_ai_relevant INTEGER,
        ADD COLUMN IF NOT EXISTS original_ai_comment TEXT
    """))
    
    db.commit()
    logger.info("✅ Human override tracking fields added")


async def _migrate_llm_audit_system(db: Session):
    """
    Migrate LLM audit system tables
    """
    logger.info("🤖 Migrating LLM audit system...")
    
    # Create llm_audit table if it doesn't exist
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS llm_audit (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            
            -- Core identification
            interaction_id VARCHAR(255) NOT NULL,
            parent_workflow_id VARCHAR(255),
            parent_survey_id VARCHAR(255),
            parent_rfq_id UUID,
            
            -- LLM Configuration
            model_name VARCHAR(100) NOT NULL,
            model_provider VARCHAR(50) NOT NULL,
            model_version VARCHAR(50),
            
            -- Purpose and Context
            purpose VARCHAR(100) NOT NULL,
            sub_purpose VARCHAR(100),
            context_type VARCHAR(50),
            
            -- Input/Output
            input_prompt TEXT NOT NULL,
            input_tokens INTEGER,
            output_content TEXT,
            output_tokens INTEGER,
            
            -- Hyperparameters (configurable)
            temperature DECIMAL(3,2),
            top_p DECIMAL(3,2),
            max_tokens INTEGER,
            frequency_penalty DECIMAL(3,2),
            presence_penalty DECIMAL(3,2),
            stop_sequences JSONB,
            
            -- Performance Metrics
            response_time_ms INTEGER,
            cost_usd DECIMAL(10,6),
            success BOOLEAN NOT NULL DEFAULT true,
            error_message TEXT,
            
            -- Metadata
            interaction_metadata JSONB,
            tags JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
            -- Field tracking
            old_fields JSONB,
            new_fields JSONB
        )
    """))
    
    # Create llm_hyperparameter_configs table if it doesn't exist
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS llm_hyperparameter_configs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            
            -- Configuration identification
            config_name VARCHAR(100) NOT NULL UNIQUE,
            purpose VARCHAR(100) NOT NULL,
            sub_purpose VARCHAR(100),
            
            -- Hyperparameters
            temperature DECIMAL(3,2) DEFAULT 0.7,
            top_p DECIMAL(3,2) DEFAULT 0.9,
            max_tokens INTEGER DEFAULT 4000,
            frequency_penalty DECIMAL(3,2) DEFAULT 0.0,
            presence_penalty DECIMAL(3,2) DEFAULT 0.0,
            stop_sequences JSONB DEFAULT '[]'::jsonb,
            
            -- Model preferences
            preferred_models JSONB DEFAULT '[]'::jsonb,
            fallback_models JSONB DEFAULT '[]'::jsonb,
            
            -- Configuration metadata
            description TEXT,
            is_active BOOLEAN DEFAULT true,
            is_default BOOLEAN DEFAULT false,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """))
    
    # Create llm_prompt_templates table if it doesn't exist
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS llm_prompt_templates (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            
            -- Template identification
            template_name VARCHAR(100) NOT NULL UNIQUE,
            purpose VARCHAR(100) NOT NULL,
            sub_purpose VARCHAR(100),
            
            -- Template content
            system_prompt_template TEXT NOT NULL,
            user_prompt_template TEXT,
            template_variables JSONB DEFAULT '{}'::jsonb,
            
            -- Template metadata
            description TEXT,
            version VARCHAR(20) DEFAULT '1.0',
            is_active BOOLEAN DEFAULT true,
            is_default BOOLEAN DEFAULT false,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """))
    
    # Insert default hyperparameter configurations (with ON CONFLICT handling)
    db.execute(text("""
        INSERT INTO llm_hyperparameter_configs (config_name, purpose, sub_purpose, temperature, top_p, max_tokens, frequency_penalty, presence_penalty, description, is_default) VALUES
        ('survey_generation_default', 'survey_generation', NULL, 0.7, 0.9, 4000, 0.0, 0.0, 'Default configuration for survey generation', true),
        ('evaluation_comprehensive', 'evaluation', 'comprehensive', 0.3, 0.9, 4000, 0.0, 0.0, 'Configuration for comprehensive evaluation', true),
        ('evaluation_content_validity', 'evaluation', 'content_validity', 0.2, 0.8, 2000, 0.0, 0.0, 'Configuration for content validity evaluation', false),
        ('evaluation_methodological_rigor', 'evaluation', 'methodological_rigor', 0.2, 0.8, 2000, 0.0, 0.0, 'Configuration for methodological rigor evaluation', false),
        ('field_extraction_default', 'field_extraction', NULL, 0.1, 0.9, 1000, 0.0, 0.0, 'Default configuration for field extraction', true),
        ('document_parsing_default', 'document_parsing', NULL, 0.1, 0.9, 2000, 0.0, 0.0, 'Default configuration for document parsing', true)
        ON CONFLICT (config_name) DO NOTHING
    """))
    
    # Insert default prompt templates (with ON CONFLICT handling)
    db.execute(text("""
        INSERT INTO llm_prompt_templates (template_name, purpose, sub_purpose, system_prompt_template, description, is_default) VALUES
        ('survey_generation_base', 'survey_generation', NULL, 'You are an expert survey researcher. Generate a comprehensive survey based on the provided RFQ and context.', 'Base template for survey generation', true),
        ('evaluation_comprehensive', 'evaluation', 'comprehensive', 'You are an expert survey evaluator. Evaluate the survey across all quality pillars.', 'Template for comprehensive evaluation', true),
        ('field_extraction_base', 'field_extraction', NULL, 'You are an expert at extracting structured data from documents. Extract the requested fields accurately.', 'Base template for field extraction', true),
        ('document_parsing_base', 'document_parsing', NULL, 'You are an expert document parser. Analyze the document and extract relevant information for survey generation.', 'Base template for document parsing', true)
        ON CONFLICT (template_name) DO NOTHING
    """))
    
    # Create indexes for efficient querying
    indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_llm_audit_interaction_id ON llm_audit(interaction_id)",
        "CREATE INDEX IF NOT EXISTS idx_llm_audit_parent_workflow_id ON llm_audit(parent_workflow_id)",
        "CREATE INDEX IF NOT EXISTS idx_llm_audit_parent_survey_id ON llm_audit(parent_survey_id)",
        "CREATE INDEX IF NOT EXISTS idx_llm_audit_parent_rfq_id ON llm_audit(parent_rfq_id)",
        "CREATE INDEX IF NOT EXISTS idx_llm_audit_model_name ON llm_audit(model_name)",
        "CREATE INDEX IF NOT EXISTS idx_llm_audit_purpose ON llm_audit(purpose)",
        "CREATE INDEX IF NOT EXISTS idx_llm_audit_context_type ON llm_audit(context_type)",
        "CREATE INDEX IF NOT EXISTS idx_llm_audit_created_at ON llm_audit(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_llm_audit_success ON llm_audit(success)",
        "CREATE INDEX IF NOT EXISTS idx_llm_audit_cost_usd ON llm_audit(cost_usd)",
        "CREATE INDEX IF NOT EXISTS idx_llm_audit_interaction_metadata ON llm_audit USING GIN(interaction_metadata)",
        "CREATE INDEX IF NOT EXISTS idx_llm_audit_tags ON llm_audit USING GIN(tags)",
        "CREATE INDEX IF NOT EXISTS idx_llm_audit_old_fields ON llm_audit USING GIN (old_fields)",
        "CREATE INDEX IF NOT EXISTS idx_llm_audit_new_fields ON llm_audit USING GIN (new_fields)",
        "CREATE INDEX IF NOT EXISTS idx_llm_audit_field_changes ON llm_audit (purpose, sub_purpose) WHERE old_fields IS NOT NULL AND new_fields IS NOT NULL",
        "CREATE INDEX IF NOT EXISTS idx_llm_hyperparameter_configs_purpose ON llm_hyperparameter_configs(purpose)",
        "CREATE INDEX IF NOT EXISTS idx_llm_hyperparameter_configs_sub_purpose ON llm_hyperparameter_configs(sub_purpose)",
        "CREATE INDEX IF NOT EXISTS idx_llm_hyperparameter_configs_is_active ON llm_hyperparameter_configs(is_active)",
        "CREATE INDEX IF NOT EXISTS idx_llm_hyperparameter_configs_is_default ON llm_hyperparameter_configs(is_default)",
        "CREATE INDEX IF NOT EXISTS idx_llm_prompt_templates_purpose ON llm_prompt_templates(purpose)",
        "CREATE INDEX IF NOT EXISTS idx_llm_prompt_templates_sub_purpose ON llm_prompt_templates(sub_purpose)",
        "CREATE INDEX IF NOT EXISTS idx_llm_prompt_templates_is_active ON llm_prompt_templates(is_active)",
        "CREATE INDEX IF NOT EXISTS idx_llm_prompt_templates_is_default ON llm_prompt_templates(is_default)"
    ]
    
    for sql in indexes_sql:
        try:
            db.execute(text(sql))
        except Exception as e:
            logger.warning(f"⚠️ LLM audit index creation warning: {e}")
    
    db.commit()
    logger.info("✅ LLM audit system migration completed")


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


async def _fix_survey_annotation_constraint(db: Session):
    """
    Fix SurveyAnnotation unique constraint to allow multiple annotators per survey
    """
    logger.info("🔧 Fixing SurveyAnnotation unique constraint...")
    
    try:
        # Drop the existing unique constraint on survey_id only
        db.execute(text("ALTER TABLE survey_annotations DROP CONSTRAINT IF EXISTS survey_annotations_survey_id_key"))
        
        # Add a new unique constraint on (survey_id, annotator_id) - use IF NOT EXISTS equivalent
        db.execute(text("ALTER TABLE survey_annotations ADD CONSTRAINT survey_annotations_survey_id_annotator_id_key UNIQUE (survey_id, annotator_id)"))
        
        # Add an index for better query performance
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_survey_annotations_survey_id_annotator_id ON survey_annotations(survey_id, annotator_id)"))
        
        db.commit()
        logger.info("✅ SurveyAnnotation constraint fixed")
    except Exception as e:
        if "already exists" in str(e):
            logger.info("✅ SurveyAnnotation constraint already exists, skipping")
            db.rollback()
        else:
            logger.error(f"❌ Error fixing SurveyAnnotation constraint: {e}")
            db.rollback()
            raise


async def _migrate_drop_alembic_version(db: Session):
    """
    Drop the alembic_version table as we transition to SQL-only migrations
    """
    logger.info("🧹 Dropping alembic_version table...")
    
    # Read and execute the migration SQL file
    migration_file = "migrations/017_drop_alembic_version.sql"
    try:
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        db.execute(text(migration_sql))
        db.commit()
        logger.info("✅ alembic_version table dropped successfully")
    except FileNotFoundError:
        logger.warning(f"⚠️ Migration file {migration_file} not found, skipping")
    except Exception as e:
        logger.warning(f"⚠️ Error dropping alembic_version table: {e}")
        # Don't fail the migration if this step fails
        db.rollback()


@router.get("/check-migration-status")
async def check_migration_status(db: Session = Depends(get_db)):
    """
    Check the status of all migrations
    """
    try:
        logger.info("🔍 Checking migration status...")
        
        # Check if tables exist
        tables_check = {}
        tables = ['question_annotations', 'section_annotations', 'survey_annotations', 'llm_audit', 'llm_hyperparameter_configs', 'llm_prompt_templates']
        
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


async def _migrate_survey_status_constraint(db: Session):
    """
    Update survey status constraint to include 'reference' status
    """
    logger.info("📝 Updating survey status constraint to include 'reference' status...")
    
    # Read and execute the migration SQL file
    migration_file = "migrations/018_update_survey_status_constraint.sql"
    try:
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        db.execute(text(migration_sql))
        db.commit()
        logger.info("✅ Survey status constraint updated successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to update survey status constraint: {str(e)}")
        db.rollback()
        raise


async def _seed_generation_rules(db: Session):
    """
    Seed 58 core generation rules from AiRA v1 framework
    """
    logger.info("🌱 Seeding generation rules...")
    
    from src.database.core_generation_rules import CORE_GENERATION_RULES
    import json
    
    # Clear existing AiRA v1 generation rules
    db.execute(text("""
        DELETE FROM survey_rules
        WHERE rule_type = 'generation'
        AND rule_content->>'source_framework' = 'aira_v1'
    """))
    
    # Insert all 58 generation rules with ON CONFLICT handling
    for rule_data in CORE_GENERATION_RULES:
        rule_content_json = json.dumps({
            'generation_guideline': rule_data['generation_guideline'],
            'implementation_notes': rule_data['implementation_notes'],
            'quality_indicators': rule_data['quality_indicators'],
            'source_framework': 'aira_v1',
            'priority': rule_data['priority'],
            'weight': rule_data['weight']
        })
        
        # Check if rule already exists
        existing = db.execute(text("""
            SELECT id FROM survey_rules 
            WHERE rule_type = 'generation' 
            AND category = :category 
            AND rule_description = :rule_description
        """), {
            'category': rule_data['category'],
            'rule_description': rule_data['generation_guideline']
        }).fetchone()
        
        if not existing:
            db.execute(text("""
                INSERT INTO survey_rules (
                    id, rule_type, category, rule_name, rule_description,
                    rule_content, is_active, priority, created_by, created_at
                ) VALUES (
                    gen_random_uuid(), 'generation', :category, :rule_name,
                    :rule_description, CAST(:rule_content AS jsonb), true,
                    :priority, 'aira_v1_system', NOW()
                )
            """), {
            'category': rule_data['category'],
            'rule_name': f"Core Quality: {rule_data['generation_guideline'][:80]}",
            'rule_description': rule_data['generation_guideline'],
            'rule_content': rule_content_json,
            'priority': {'core': 1000, 'high': 800, 'medium': 600, 'low': 400}[rule_data['priority']]
        })
    
    db.commit()
    logger.info("✅ Seeded 58 generation rules")


async def _migrate_multi_level_rag_tables(db: Session):
    """
    Update existing multi-level RAG tables to rule-based schema
    Handles existing tables by adding missing columns and removing vector dependencies
    """
    logger.info("📝 Updating existing multi-level RAG tables to rule-based schema...")
    
    try:
        # Read the update migration SQL file
        with open('migrations/update_existing_multi_level_rag_tables.sql', 'r') as f:
            migration_sql = f.read()
        
        # Split by semicolon and execute each statement
        statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
        
        for statement in statements:
            if statement:
                db.execute(text(statement))
        
        db.commit()
        logger.info("✅ Rule-based multi-level RAG tables migration completed")
        
    except Exception as e:
        logger.error(f"❌ Error migrating rule-based multi-level RAG tables: {e}")
        db.rollback()
        raise


async def _enable_required_extensions(db: Session):
    """
    Ensure required PostgreSQL extensions are enabled (pgcrypto, vector)
    """
    logger.info("🧩 Enabling required PostgreSQL extensions (pgcrypto, vector)...")
    try:
        # pgcrypto for gen_random_uuid()
        db.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
        # pgvector for VECTOR columns
        db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        db.commit()
        logger.info("✅ Extensions enabled (pgcrypto, vector)")
    except Exception as e:
        logger.error(f"❌ Failed to enable extensions: {e}")
        db.rollback()
        raise


async def _migrate_retrieval_configuration(db: Session):
    """
    Create retrieval configuration tables (retrieval_weights, methodology_compatibility)
    from SQL file migrations/add_retrieval_configuration_tables.sql
    """
    logger.info("📝 Migrating retrieval configuration tables (weights, compatibility)...")
    try:
        migration_file = 'migrations/add_retrieval_configuration_tables.sql'
        with open(migration_file, 'r') as f:
            migration_sql = f.read()

        # Execute statements individually to tolerate partial failures
        statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
        for statement in statements:
            try:
                db.execute(text(statement))
            except Exception as stmt_err:
                # Log and rethrow to surface meaningful failure in migrate-all
                logger.error(f"❌ Retrieval config statement failed: {stmt_err}")
                raise

        db.commit()
        logger.info("✅ Retrieval configuration migration completed")
    except FileNotFoundError:
        logger.warning("⚠️ Retrieval configuration migration file not found, skipping")
        db.rollback()
        # Do not raise; allow environments without this migration file
    except Exception as e:
        logger.error(f"❌ Error migrating retrieval configuration: {e}")
        db.rollback()
        raise