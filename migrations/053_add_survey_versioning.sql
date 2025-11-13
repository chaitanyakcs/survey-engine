-- Add version tracking fields to surveys table
-- This enables explicit version tracking for surveys with the same RFQ
-- Migration is idempotent - safe to run multiple times

-- Add version tracking columns
ALTER TABLE surveys 
ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1 NOT NULL;

ALTER TABLE surveys 
ADD COLUMN IF NOT EXISTS parent_survey_id UUID REFERENCES surveys(id);

ALTER TABLE surveys 
ADD COLUMN IF NOT EXISTS is_current BOOLEAN DEFAULT TRUE NOT NULL;

ALTER TABLE surveys 
ADD COLUMN IF NOT EXISTS version_notes TEXT;

-- Create indexes for efficient version queries
CREATE INDEX IF NOT EXISTS idx_surveys_rfq_version ON surveys(rfq_id, version);
CREATE INDEX IF NOT EXISTS idx_surveys_parent_survey ON surveys(parent_survey_id);
CREATE INDEX IF NOT EXISTS idx_surveys_is_current ON surveys(rfq_id, is_current) WHERE is_current = TRUE;

-- Add comments for documentation
COMMENT ON COLUMN surveys.version IS 'Explicit version number for this survey (v1, v2, v3, etc.)';
COMMENT ON COLUMN surveys.parent_survey_id IS 'Reference to parent survey (for v2, v3, etc.). NULL for v1.';
COMMENT ON COLUMN surveys.is_current IS 'Mark current/latest version for an RFQ. Only one survey per RFQ should be current.';
COMMENT ON COLUMN surveys.version_notes IS 'Optional notes about what changed in this version';

-- Set existing surveys to version 1 and is_current=true (if not already set)
UPDATE surveys 
SET version = 1, is_current = TRUE, parent_survey_id = NULL
WHERE version IS NULL OR is_current IS NULL;

