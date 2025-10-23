-- Fix duplicate rules and add proper constraints
-- Migration: 015_fix_duplicate_rules.sql

-- First, identify and fix all duplicate rules across all types
WITH duplicates AS (
    SELECT 
        rule_description,
        category,
        rule_type,
        array_agg(id ORDER BY created_at ASC) as rule_ids,
        count(*) as duplicate_count
    FROM survey_rules 
    GROUP BY rule_description, category, rule_type
    HAVING count(*) > 1
),
duplicates_to_keep AS (
    SELECT 
        rule_description,
        category,
        rule_type,
        rule_ids[1] as keep_id  -- Keep the first (oldest) record
    FROM duplicates
),
duplicates_to_delete AS (
    SELECT 
        rule_description,
        category,
        rule_type,
        unnest(rule_ids[2:]) as delete_id  -- Delete all but the first
    FROM duplicates
)
-- Delete duplicate records (keep the oldest)
DELETE FROM survey_rules 
WHERE id IN (
    SELECT delete_id FROM duplicates_to_delete
);

-- Drop the constraint if it exists (in case previous migration failed)
ALTER TABLE survey_rules 
DROP CONSTRAINT IF EXISTS unique_rule_description_category_type;

-- Add the unique constraint
ALTER TABLE survey_rules 
ADD CONSTRAINT unique_rule_description_category_type 
UNIQUE (rule_description, category, rule_type);

-- Add index for better performance on rule lookups
CREATE INDEX IF NOT EXISTS idx_survey_rules_lookup 
ON survey_rules (rule_type, category, is_active);

-- Add comment explaining the constraint
COMMENT ON CONSTRAINT unique_rule_description_category_type ON survey_rules 
IS 'Prevents duplicate rules with same description, category, and type';

-- Verify no duplicates remain
DO $$
DECLARE
    duplicate_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO duplicate_count
    FROM (
        SELECT rule_description, category, rule_type
        FROM survey_rules 
        GROUP BY rule_description, category, rule_type
        HAVING COUNT(*) > 1
    ) duplicates;
    
    IF duplicate_count > 0 THEN
        RAISE EXCEPTION 'Still found % duplicate rule groups after cleanup', duplicate_count;
    ELSE
        RAISE NOTICE 'Successfully cleaned up all duplicate rules';
    END IF;
END $$;
