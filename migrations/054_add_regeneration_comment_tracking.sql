-- Add comment tracking fields to surveys table
-- This enables tracking which annotation comments were used during regeneration
-- Migration is idempotent - safe to run multiple times

-- Add used_annotation_comment_ids column to track which comments were included in regeneration
ALTER TABLE surveys 
ADD COLUMN IF NOT EXISTS used_annotation_comment_ids JSONB;

-- Add comments_addressed column to store LLM's self-report of which comments were addressed
ALTER TABLE surveys 
ADD COLUMN IF NOT EXISTS comments_addressed JSONB;

-- Create index for efficient queries on surveys with comment tracking
CREATE INDEX IF NOT EXISTS idx_surveys_used_comment_ids ON surveys USING GIN (used_annotation_comment_ids);

-- Add comments for documentation
COMMENT ON COLUMN surveys.used_annotation_comment_ids IS 'Stores array of annotation IDs (question, section, survey) that were included in regeneration. Structure: {"question_annotations": [id1, id2], "section_annotations": [id3], "survey_annotations": [id4]}';
COMMENT ON COLUMN surveys.comments_addressed IS 'Stores array of comment IDs that the LLM reported as addressed during regeneration. Format: ["COMMENT-Q123-V2", "COMMENT-S3-V1", etc.]';

