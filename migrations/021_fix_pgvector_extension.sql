-- Migration 021: Fix pgvector extension and column types
-- This migration ensures pgvector extension is installed and rfq_embedding column is properly typed

-- Enable pgvector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Check if rfq_embedding column exists and is properly typed
DO $$
BEGIN
    -- Check if the column exists and is of wrong type
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'golden_rfq_survey_pairs' 
        AND column_name = 'rfq_embedding' 
        AND data_type = 'text'
    ) THEN
        -- Drop the text column and recreate as vector
        ALTER TABLE golden_rfq_survey_pairs DROP COLUMN rfq_embedding;
        ALTER TABLE golden_rfq_survey_pairs ADD COLUMN rfq_embedding vector(384);
        
        -- Add comment
        COMMENT ON COLUMN golden_rfq_survey_pairs.rfq_embedding IS 'Vector embedding for RFQ text similarity search using pgvector';
    ELSIF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'golden_rfq_survey_pairs' 
        AND column_name = 'rfq_embedding'
    ) THEN
        -- Column doesn't exist, create it
        ALTER TABLE golden_rfq_survey_pairs ADD COLUMN rfq_embedding vector(384);
        
        -- Add comment
        COMMENT ON COLUMN golden_rfq_survey_pairs.rfq_embedding IS 'Vector embedding for RFQ text similarity search using pgvector';
    END IF;
END $$;

-- Create index for vector similarity search if it doesn't exist
CREATE INDEX IF NOT EXISTS idx_golden_rfq_survey_pairs_rfq_embedding 
ON golden_rfq_survey_pairs 
USING ivfflat (rfq_embedding vector_cosine_ops) 
WITH (lists = 100);

-- Verify the extension and column
DO $$
DECLARE
    ext_exists boolean;
    col_type text;
BEGIN
    -- Check if vector extension exists
    SELECT EXISTS(
        SELECT 1 FROM pg_extension WHERE extname = 'vector'
    ) INTO ext_exists;
    
    -- Check column type
    SELECT data_type INTO col_type
    FROM information_schema.columns 
    WHERE table_name = 'golden_rfq_survey_pairs' 
    AND column_name = 'rfq_embedding';
    
    RAISE NOTICE 'Vector extension exists: %', ext_exists;
    RAISE NOTICE 'rfq_embedding column type: %', col_type;
END $$;
