-- Add unique constraints to prevent duplicate pillar rules
-- Migration: 004_add_unique_constraints.sql

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
