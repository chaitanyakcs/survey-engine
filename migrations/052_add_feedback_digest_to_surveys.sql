-- Add feedback_digest column to surveys table
-- This stores the feedback digest that was used during survey generation
-- Migration is idempotent - safe to run multiple times

ALTER TABLE surveys 
ADD COLUMN IF NOT EXISTS feedback_digest JSONB;

COMMENT ON COLUMN surveys.feedback_digest IS 'Stores the feedback digest that was included in the prompt during survey generation';

