-- Migration: Add updated_at column to llm_audit table
-- Issue: SQLAlchemy model expects updated_at but bootstrap schema didn't create it
-- This migration is idempotent and safe to run multiple times

-- Add updated_at column if it doesn't exist
ALTER TABLE llm_audit 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Add comment for documentation
COMMENT ON COLUMN llm_audit.updated_at IS 'Timestamp when the audit record was last updated';

-- Create index for updated_at if it doesn't exist (for sorting/filtering)
CREATE INDEX IF NOT EXISTS idx_llm_audit_updated_at ON llm_audit(updated_at);

