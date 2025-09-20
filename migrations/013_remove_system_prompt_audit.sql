-- Migration: Remove system_prompt_audit table
-- System prompts are now tracked via the llm_audit table

-- Drop the system_prompt_audit table
DROP TABLE IF EXISTS system_prompt_audit CASCADE;

-- Add comment
COMMENT ON TABLE llm_audit IS 'Comprehensive audit table for all LLM interactions including system prompts, evaluations, and other AI operations';
