-- Migration: Add raw_response field to llm_audit table
-- Description: Add raw_response field to store the unprocessed LLM response

-- Add raw_response column to llm_audit table
ALTER TABLE llm_audit 
ADD COLUMN raw_response TEXT;

-- Add comment for documentation
COMMENT ON COLUMN llm_audit.raw_response IS 'Raw response from LLM before any processing';
