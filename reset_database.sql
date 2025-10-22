-- Reset database script
-- This will drop all tables and start fresh

-- Drop all tables in the correct order (respecting foreign key constraints)
DROP TABLE IF EXISTS question_annotations CASCADE;
DROP TABLE IF EXISTS section_annotations CASCADE;
DROP TABLE IF EXISTS survey_annotations CASCADE;
DROP TABLE IF EXISTS llm_audit CASCADE;
DROP TABLE IF EXISTS llm_hyperparameter_configs CASCADE;
DROP TABLE IF EXISTS llm_prompt_templates CASCADE;
DROP TABLE IF EXISTS retrieval_weights CASCADE;
DROP TABLE IF EXISTS methodology_compatibility CASCADE;
DROP TABLE IF EXISTS golden_rfq_survey_pairs CASCADE;
DROP TABLE IF EXISTS surveys CASCADE;
DROP TABLE IF EXISTS rfqs CASCADE;
DROP TABLE IF EXISTS survey_rules CASCADE;
DROP TABLE IF EXISTS golden_sections CASCADE;
DROP TABLE IF EXISTS golden_questions CASCADE;

-- Drop any remaining tables
DO $$ 
DECLARE 
    r RECORD;
BEGIN
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') 
    LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
END $$;

-- Reset sequences
DO $$ 
DECLARE 
    r RECORD;
BEGIN
    FOR r IN (SELECT sequence_name FROM information_schema.sequences WHERE sequence_schema = 'public') 
    LOOP
        EXECUTE 'DROP SEQUENCE IF EXISTS ' || quote_ident(r.sequence_name) || ' CASCADE';
    END LOOP;
END $$;

-- Ensure extensions are still available
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Verify reset
SELECT 'Database reset completed' as status;
