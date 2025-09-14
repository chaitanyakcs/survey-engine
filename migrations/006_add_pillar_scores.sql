-- Add pillar scores to surveys table
-- Migration: 006_add_pillar_scores.sql

-- Add pillar_scores column to store evaluation results
ALTER TABLE surveys 
ADD COLUMN pillar_scores JSONB;

-- Add index for better performance on pillar scores queries
CREATE INDEX IF NOT EXISTS idx_surveys_pillar_scores 
ON surveys USING GIN (pillar_scores);

-- Add comment explaining the column
COMMENT ON COLUMN surveys.pillar_scores IS 'Stores 5-pillar evaluation scores and breakdown for the survey';

-- Verify the column was added
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'surveys' 
AND column_name = 'pillar_scores';
