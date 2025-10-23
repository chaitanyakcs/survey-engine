-- Migration: Add 'failed' status to surveys table constraint
-- This allows surveys to be marked as failed when generation fails

-- First, update any invalid statuses to 'draft' to avoid constraint violations
UPDATE surveys 
SET status = 'draft' 
WHERE status NOT IN ('draft','validated','edited','final','reference','failed');

-- Drop the existing constraint
ALTER TABLE surveys 
DROP CONSTRAINT IF EXISTS surveys_status_check;

-- Add the new constraint with 'failed' status included
ALTER TABLE surveys 
ADD CONSTRAINT surveys_status_check 
CHECK (status IN ('draft','validated','edited','final','reference','failed'));

-- Add comment for documentation
COMMENT ON CONSTRAINT surveys_status_check ON surveys IS 'Survey status must be one of: draft, validated, edited, final, reference, or failed';
