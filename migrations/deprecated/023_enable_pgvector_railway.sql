-- Migration 023: Enable pgvector extension on Railway
-- This migration enables pgvector and sets up vector columns

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify extension is enabled
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        RAISE NOTICE 'pgvector extension is enabled';
    ELSE
        RAISE EXCEPTION 'pgvector extension is not available';
    END IF;
END $$;

-- Check if rfq_embedding column exists and fix its type
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
        
        RAISE NOTICE 'Converted rfq_embedding from text to vector(384)';
    ELSIF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'golden_rfq_survey_pairs' 
        AND column_name = 'rfq_embedding'
    ) THEN
        -- Column doesn't exist, create it
        ALTER TABLE golden_rfq_survey_pairs ADD COLUMN rfq_embedding vector(384);
        
        RAISE NOTICE 'Created rfq_embedding column as vector(384)';
    ELSE
        RAISE NOTICE 'rfq_embedding column already exists as vector type';
    END IF;
END $$;

-- Create vector index for similarity search
CREATE INDEX IF NOT EXISTS idx_golden_rfq_survey_pairs_rfq_embedding 
ON golden_rfq_survey_pairs 
USING ivfflat (rfq_embedding vector_cosine_ops) 
WITH (lists = 100);

-- Add comments
COMMENT ON COLUMN golden_rfq_survey_pairs.rfq_embedding IS 'Vector embedding for RFQ text similarity search using pgvector';
COMMENT ON INDEX idx_golden_rfq_survey_pairs_rfq_embedding IS 'Vector similarity index for cosine distance search';

-- Test vector operations
DO $$
DECLARE
    test_embedding vector(384);
    similarity_result real;
BEGIN
    -- Create a test embedding
    test_embedding := array_fill(0.1, ARRAY[384])::vector(384);
    
    -- Test similarity operation
    SELECT rfq_embedding <=> test_embedding INTO similarity_result
    FROM golden_rfq_survey_pairs 
    WHERE rfq_embedding IS NOT NULL 
    LIMIT 1;
    
    RAISE NOTICE 'Vector operations test successful, similarity: %', similarity_result;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Vector operations test failed: %', SQLERRM;
END $$;
