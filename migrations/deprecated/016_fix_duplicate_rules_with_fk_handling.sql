-- Fix duplicate rules with proper foreign key constraint handling
-- Migration: 016_fix_duplicate_rules_with_fk_handling.sql

-- First, check if rule_migration_log table exists and handle it
DO $$
BEGIN
    -- If rule_migration_log table exists, we need to handle the foreign key constraint
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'rule_migration_log') THEN
        -- Delete from rule_migration_log first to avoid foreign key constraint violations
        DELETE FROM rule_migration_log 
        WHERE original_rule_id IN (
            SELECT id FROM survey_rules 
            WHERE (rule_description, category, rule_type) IN (
                SELECT rule_description, category, rule_type
                FROM survey_rules 
                GROUP BY rule_description, category, rule_type
                HAVING COUNT(*) > 1
            )
            AND id NOT IN (
                -- Keep the oldest record for each duplicate group
                SELECT DISTINCT ON (rule_description, category, rule_type) id
                FROM survey_rules 
                WHERE (rule_description, category, rule_type) IN (
                    SELECT rule_description, category, rule_type
                    FROM survey_rules 
                    GROUP BY rule_description, category, rule_type
                    HAVING COUNT(*) > 1
                )
                ORDER BY rule_description, category, rule_type, created_at ASC
            )
        );
        
        RAISE NOTICE 'Cleaned up rule_migration_log references to duplicate rules';
    END IF;
END $$;

-- Now safely delete duplicate rules
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
duplicates_to_delete AS (
    SELECT 
        unnest(rule_ids[2:]) as delete_id  -- Delete all but the first (oldest)
    FROM duplicates
)
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
        RAISE WARNING 'Still found % duplicate rule groups after cleanup', duplicate_count;
    ELSE
        RAISE NOTICE 'Successfully cleaned up all duplicate rules';
    END IF;
END $$;
