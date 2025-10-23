-- Rollback Migration: Restore Quality Rules from Pillar Consolidation
-- Created: 2024-01-XX
-- Description: Rollback the consolidation of quality rules to pillar system if needed

-- Step 1: Reactivate the original quality rules
UPDATE survey_rules 
SET is_active = true,
    updated_at = NOW(),
    rule_content = rule_content - 'migration_status' - 'migrated_at'
WHERE rule_type = 'quality' 
AND category IN ('question_quality', 'survey_structure', 'respondent_experience')
AND is_active = false
AND rule_content->>'migration_status' = 'consolidated_to_pillars';

-- Step 2: Deactivate the migrated pillar rules (those created during migration)
UPDATE survey_rules 
SET is_active = false,
    updated_at = NOW(),
    rule_content = COALESCE(rule_content, '{}') || '{"rollback_status": "deactivated_on_rollback", "rollback_at": "' || NOW()::text || '"}'
WHERE rule_type = 'pillar' 
AND created_by = 'migration'
AND is_active = true;

-- Step 3: Clean up migration log (optional - keep for audit trail)
-- DELETE FROM rule_migration_log WHERE migration_type = 'consolidated';

-- Step 4: Drop the view (will be recreated with original structure)
DROP VIEW IF EXISTS active_evaluation_rules;

-- Step 5: Restore original table comment
COMMENT ON TABLE survey_rules IS 'Stores survey generation rules and methodologies - includes seeded methodology, quality, and industry rules';

-- Step 6: Rollback summary
DO $$
DECLARE
    restored_count INTEGER;
    deactivated_pillar_count INTEGER;
    total_active_rules INTEGER;
BEGIN
    SELECT COUNT(*) INTO restored_count 
    FROM survey_rules 
    WHERE rule_type = 'quality' 
    AND category IN ('question_quality', 'survey_structure', 'respondent_experience')
    AND is_active = true;
    
    SELECT COUNT(*) INTO deactivated_pillar_count 
    FROM survey_rules 
    WHERE rule_type = 'pillar' 
    AND created_by = 'migration'
    AND is_active = false;
    
    SELECT COUNT(*) INTO total_active_rules 
    FROM survey_rules 
    WHERE is_active = true;
    
    RAISE NOTICE 'ROLLBACK COMPLETED:';
    RAISE NOTICE '  - Restored % quality rules to active status', restored_count;
    RAISE NOTICE '  - Deactivated % pillar rules created during migration', deactivated_pillar_count;
    RAISE NOTICE '  - Total active rules after rollback: %', total_active_rules;
    RAISE NOTICE '  - System restored to pre-migration state';
END $$;