-- Migration: Add system_prompt_audit table for tracking system prompts used in survey generation
-- This table stores system prompts as audit data with loose coupling to surveys
-- to allow persistence even after survey deletion

CREATE TABLE system_prompt_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    survey_id VARCHAR(255) NOT NULL,
    rfq_id UUID,
    system_prompt TEXT NOT NULL,
    prompt_type VARCHAR(50) NOT NULL DEFAULT 'generation',
    model_version VARCHAR(100),
    generation_context JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for efficient querying
CREATE INDEX idx_system_prompt_audit_survey_id ON system_prompt_audit(survey_id);
CREATE INDEX idx_system_prompt_audit_rfq_id ON system_prompt_audit(rfq_id);
CREATE INDEX idx_system_prompt_audit_created_at ON system_prompt_audit(created_at);
CREATE INDEX idx_system_prompt_audit_prompt_type ON system_prompt_audit(prompt_type);

-- Add comment to table
COMMENT ON TABLE system_prompt_audit IS 'Audit table for storing system prompts used in survey generation. Uses loose coupling to surveys to allow persistence after survey deletion.';
COMMENT ON COLUMN system_prompt_audit.survey_id IS 'Loose reference to survey ID (not foreign key) to allow persistence after survey deletion';
COMMENT ON COLUMN system_prompt_audit.system_prompt IS 'The actual system prompt text used for generation';
COMMENT ON COLUMN system_prompt_audit.prompt_type IS 'Type of prompt: generation, validation, etc.';
COMMENT ON COLUMN system_prompt_audit.generation_context IS 'JSON context used for generation (rules, golden examples, etc.)';

