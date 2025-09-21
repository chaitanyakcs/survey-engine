-- Migration: Add prompt editing fields to human_reviews table
-- These fields support manual prompt editing during human review

-- Add prompt editing columns
ALTER TABLE human_reviews 
ADD COLUMN IF NOT EXISTS edited_prompt_data TEXT,
ADD COLUMN IF NOT EXISTS original_prompt_data TEXT,
ADD COLUMN IF NOT EXISTS prompt_edited BOOLEAN DEFAULT FALSE NOT NULL,
ADD COLUMN IF NOT EXISTS prompt_edit_timestamp TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS edited_by VARCHAR(255),
ADD COLUMN IF NOT EXISTS edit_reason TEXT;

-- Create indexes for the new columns
CREATE INDEX IF NOT EXISTS idx_human_reviews_prompt_edited ON human_reviews (prompt_edited);
CREATE INDEX IF NOT EXISTS idx_human_reviews_edited_by ON human_reviews (edited_by);
CREATE INDEX IF NOT EXISTS idx_human_reviews_edit_timestamp ON human_reviews (prompt_edit_timestamp);

-- Add comment to table
COMMENT ON TABLE human_reviews IS 'Human review system for prompt approval and editing. Supports manual prompt editing with audit trail.';
COMMENT ON COLUMN human_reviews.edited_prompt_data IS 'Manually edited prompt data by human reviewer';
COMMENT ON COLUMN human_reviews.original_prompt_data IS 'Original prompt data preserved for comparison';
COMMENT ON COLUMN human_reviews.prompt_edited IS 'Flag indicating if prompt was manually edited';
COMMENT ON COLUMN human_reviews.prompt_edit_timestamp IS 'Timestamp when prompt was edited';
COMMENT ON COLUMN human_reviews.edited_by IS 'User ID who made the edit';
COMMENT ON COLUMN human_reviews.edit_reason IS 'Optional reason for the edit';

