-- Migration: Update survey status constraint to include 'reference' status
-- This allows reference examples to have proper survey records with 'reference' status

-- First, update any invalid statuses to 'draft' to avoid constraint violations
UPDATE surveys 
SET status = 'draft' 
WHERE status NOT IN ('draft','validated','edited','final','reference');

-- Drop the existing constraint
ALTER TABLE surveys 
DROP CONSTRAINT IF EXISTS surveys_status_check;

-- Add the new constraint with 'reference' status included
ALTER TABLE surveys 
ADD CONSTRAINT surveys_status_check 
CHECK (status IN ('draft','validated','edited','final','reference'));

-- Add comment for documentation
COMMENT ON CONSTRAINT surveys_status_check ON surveys IS 'Survey status must be one of: draft, validated, edited, final, or reference';
