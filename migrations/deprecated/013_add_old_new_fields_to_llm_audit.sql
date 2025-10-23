-- Migration: Add old_fields and new_fields to llm_audit table
-- Description: Add fields to track field changes in LLM interactions

-- Add old_fields and new_fields columns to llm_audit table
ALTER TABLE llm_audit 
ADD COLUMN old_fields JSONB,
ADD COLUMN new_fields JSONB;

-- Add comments for documentation
COMMENT ON COLUMN llm_audit.old_fields IS 'Previous field values before LLM processing';
COMMENT ON COLUMN llm_audit.new_fields IS 'New field values after LLM processing';

-- Create index for better query performance on field changes
CREATE INDEX idx_llm_audit_old_fields ON llm_audit USING GIN (old_fields);
CREATE INDEX idx_llm_audit_new_fields ON llm_audit USING GIN (new_fields);

-- Add composite index for field change queries
CREATE INDEX idx_llm_audit_field_changes ON llm_audit (purpose, sub_purpose) 
WHERE old_fields IS NOT NULL AND new_fields IS NOT NULL;
