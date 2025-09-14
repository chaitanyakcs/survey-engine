-- Fix unique constraints for pillar rules
-- Migration: 005_fix_unique_constraints.sql

-- First, clean up any existing duplicates before adding constraints
WITH duplicates AS (
    SELECT 
        rule_description,
        category,
        rule_type,
        array_agg(id ORDER BY created_at ASC) as rule_ids
    FROM survey_rules 
    WHERE rule_type = 'pillar' AND is_active = true
    GROUP BY rule_description, category, rule_type
    HAVING count(*) > 1
)
DELETE FROM survey_rules 
WHERE id IN (
    SELECT unnest(rule_ids[2:]) -- Keep first, delete rest
    FROM duplicates
);

-- Drop existing constraint if it exists (in case it was created incorrectly)
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'survey_rules' 
        AND constraint_name = 'unique_rule_description_category_type'
    ) THEN
        ALTER TABLE survey_rules DROP CONSTRAINT unique_rule_description_category_type;
    END IF;
END $$;

-- Add unique constraint to prevent future duplicates
-- This ensures no two rules can have the same description, category, and type
ALTER TABLE survey_rules 
ADD CONSTRAINT unique_rule_description_category_type 
UNIQUE (rule_description, category, rule_type);

-- Add index for better performance on rule lookups
CREATE INDEX IF NOT EXISTS idx_survey_rules_lookup 
ON survey_rules (rule_type, category, is_active);

-- Add comment explaining the constraint
COMMENT ON CONSTRAINT unique_rule_description_category_type ON survey_rules 
IS 'Prevents duplicate rules with same description, category, and type';

-- Verify the constraint was created
SELECT 
    constraint_name,
    constraint_type,
    table_name
FROM information_schema.table_constraints 
WHERE table_name = 'survey_rules' 
AND constraint_type = 'UNIQUE';
