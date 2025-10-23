-- Migration 024: Convert survey output fields from TEXT to JSONB
-- This migration converts raw_output and final_output from TEXT to JSONB
-- to match the local development schema

-- Convert raw_output from TEXT to JSONB
DO $$
BEGIN
    -- Check if raw_output exists and is TEXT type
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'surveys' 
        AND column_name = 'raw_output' 
        AND data_type = 'text'
    ) THEN
        -- First, update any existing TEXT data to be valid JSON
        UPDATE surveys 
        SET raw_output = '{}' 
        WHERE raw_output IS NULL OR raw_output = '';
        
        -- Convert TEXT to JSONB
        ALTER TABLE surveys 
        ALTER COLUMN raw_output TYPE JSONB 
        USING raw_output::JSONB;
        
        RAISE NOTICE 'Converted raw_output from TEXT to JSONB';
    ELSE
        RAISE NOTICE 'raw_output column does not exist or is not TEXT type';
    END IF;
END $$;

-- Convert final_output from TEXT to JSONB
DO $$
BEGIN
    -- Check if final_output exists and is TEXT type
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'surveys' 
        AND column_name = 'final_output' 
        AND data_type = 'text'
    ) THEN
        -- First, update any existing TEXT data to be valid JSON
        UPDATE surveys 
        SET final_output = '{}' 
        WHERE final_output IS NULL OR final_output = '';
        
        -- Convert TEXT to JSONB
        ALTER TABLE surveys 
        ALTER COLUMN final_output TYPE JSONB 
        USING final_output::JSONB;
        
        RAISE NOTICE 'Converted final_output from TEXT to JSONB';
    ELSE
        RAISE NOTICE 'final_output column does not exist or is not TEXT type';
    END IF;
END $$;

-- Add comments
COMMENT ON COLUMN surveys.raw_output IS 'Raw survey output as JSONB for better query performance';
COMMENT ON COLUMN surveys.final_output IS 'Final survey output as JSONB for better query performance';
