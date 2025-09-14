-- Migration: Consolidate Quality Rules into Pillar System
-- Created: 2024-01-XX
-- Description: Migrate existing quality rules to pillar-based system and deactivate redundant rules

-- Step 1: Add pillar-based rules (enhanced versions of existing quality rules)
INSERT INTO survey_rules (rule_type, category, rule_name, rule_description, rule_content, priority, is_active, created_by) VALUES

-- CONTENT VALIDITY PILLAR (20% weight) - Migrated from quality rules
('pillar', 'content_validity', 'RFQ Objective Alignment', 'Survey questions must directly address all stated research objectives from the RFQ', 
 '{"pillar": "content_validity", "weight": 0.20, "priority": "high", "migrated_from": "quality/survey_structure", "evaluation_criteria": ["objective_alignment", "topic_comprehensiveness", "research_goal_mapping"]}', 
 10, true, 'migration'),

('pillar', 'content_validity', 'Research Scope Coverage', 'Each key research area mentioned in the RFQ should have corresponding questions', 
 '{"pillar": "content_validity", "weight": 0.20, "priority": "high", "migrated_from": "new", "evaluation_criteria": ["scope_coverage", "gap_analysis", "completeness"]}', 
 10, true, 'migration'),

('pillar', 'content_validity', 'Business Objective Mapping', 'Questions should demonstrate clear mapping to business objectives or research hypotheses', 
 '{"pillar": "content_validity", "weight": 0.20, "priority": "high", "migrated_from": "quality/question_quality", "evaluation_criteria": ["objective_mapping", "hypothesis_alignment", "business_relevance"]}', 
 9, true, 'migration'),

('pillar', 'content_validity', 'Topic Comprehensiveness', 'Question coverage should be comprehensive without significant gaps in topic areas', 
 '{"pillar": "content_validity", "weight": 0.20, "priority": "medium", "migrated_from": "new", "evaluation_criteria": ["topic_coverage", "comprehensiveness", "depth_analysis"]}', 
 8, true, 'migration'),

-- METHODOLOGICAL RIGOR PILLAR (25% weight) - Migrated from quality rules
('pillar', 'methodological_rigor', 'Bias Prevention', 'Avoid leading, loaded, or double-barreled questions that introduce bias', 
 '{"pillar": "methodological_rigor", "weight": 0.25, "priority": "critical", "migrated_from": "quality/question_quality", "evaluation_criteria": ["bias_detection", "question_neutrality", "leading_language"]}', 
 10, true, 'migration'),

('pillar', 'methodological_rigor', 'Question Sequence Logic', 'Questions must follow logical sequence from general to specific', 
 '{"pillar": "methodological_rigor", "weight": 0.25, "priority": "high", "migrated_from": "quality/survey_structure", "evaluation_criteria": ["sequence_logic", "flow_optimization", "progression"]}', 
 10, true, 'migration'),

('pillar', 'methodological_rigor', 'Screening Question Placement', 'Screening questions should appear early in the survey flow', 
 '{"pillar": "methodological_rigor", "weight": 0.25, "priority": "high", "migrated_from": "quality/survey_structure", "evaluation_criteria": ["screening_placement", "qualification_logic", "early_filtering"]}', 
 9, true, 'migration'),

('pillar', 'methodological_rigor', 'Sensitive Question Positioning', 'Sensitive or personal questions should be placed toward the end', 
 '{"pillar": "methodological_rigor", "weight": 0.25, "priority": "high", "migrated_from": "quality/survey_structure", "evaluation_criteria": ["sensitive_placement", "rapport_building", "completion_optimization"]}', 
 9, true, 'migration'),

('pillar', 'methodological_rigor', 'Methodology Implementation', 'Question types must be appropriate for the methodology being implemented', 
 '{"pillar": "methodological_rigor", "weight": 0.25, "priority": "high", "migrated_from": "quality/question_quality", "evaluation_criteria": ["methodology_alignment", "question_type_appropriateness", "implementation_quality"]}', 
 9, true, 'migration'),

('pillar', 'methodological_rigor', 'Sample Size Adequacy', 'Sample size and targeting must align with statistical requirements', 
 '{"pillar": "methodological_rigor", "weight": 0.25, "priority": "medium", "migrated_from": "new", "evaluation_criteria": ["statistical_adequacy", "power_analysis", "recruitment_feasibility"]}', 
 8, true, 'migration'),

('pillar', 'methodological_rigor', 'Randomization and Bias Control', 'Include proper randomization and bias mitigation techniques where applicable', 
 '{"pillar": "methodological_rigor", "weight": 0.25, "priority": "medium", "migrated_from": "quality/question_quality", "evaluation_criteria": ["randomization", "bias_mitigation", "control_techniques"]}', 
 8, true, 'migration'),

-- CLARITY & COMPREHENSIBILITY PILLAR (25% weight) - Migrated from quality rules
('pillar', 'clarity_comprehensibility', 'Language Accessibility', 'Use clear, simple language appropriate for the target audience', 
 '{"pillar": "clarity_comprehensibility", "weight": 0.25, "priority": "high", "migrated_from": "quality/question_quality", "evaluation_criteria": ["language_clarity", "accessibility", "audience_appropriateness"]}', 
 10, true, 'migration'),

('pillar', 'clarity_comprehensibility', 'Jargon Avoidance', 'Avoid jargon, technical terms, and industry-specific language unless necessary', 
 '{"pillar": "clarity_comprehensibility", "weight": 0.25, "priority": "high", "migrated_from": "quality/question_quality", "evaluation_criteria": ["jargon_detection", "terminology_appropriateness", "simplification"]}', 
 10, true, 'migration'),

('pillar', 'clarity_comprehensibility', 'Single Concept Focus', 'Each question should focus on a single concept or idea', 
 '{"pillar": "clarity_comprehensibility", "weight": 0.25, "priority": "high", "migrated_from": "quality/question_quality", "evaluation_criteria": ["concept_clarity", "double_barreled_detection", "focus_analysis"]}', 
 9, true, 'migration'),

('pillar', 'clarity_comprehensibility', 'Neutral Wording', 'Question wording should be neutral and unambiguous', 
 '{"pillar": "clarity_comprehensibility", "weight": 0.25, "priority": "high", "migrated_from": "quality/question_quality", "evaluation_criteria": ["wording_neutrality", "ambiguity_assessment", "clarity_check"]}', 
 9, true, 'migration'),

('pillar', 'clarity_comprehensibility', 'Instruction Clarity', 'Instructions and context should be clear and easy to understand', 
 '{"pillar": "clarity_comprehensibility", "weight": 0.25, "priority": "medium", "migrated_from": "quality/survey_structure", "evaluation_criteria": ["instruction_clarity", "context_provision", "guidance_quality"]}', 
 8, true, 'migration'),

('pillar', 'clarity_comprehensibility', 'Reading Level Appropriateness', 'Reading level should be appropriate for the target demographic', 
 '{"pillar": "clarity_comprehensibility", "weight": 0.25, "priority": "medium", "migrated_from": "new", "evaluation_criteria": ["reading_level", "demographic_appropriateness", "comprehension_difficulty"]}', 
 8, true, 'migration'),

('pillar', 'clarity_comprehensibility', 'Cultural Inclusivity', 'Use inclusive language that avoids cultural bias or assumptions', 
 '{"pillar": "clarity_comprehensibility", "weight": 0.25, "priority": "medium", "migrated_from": "quality/question_quality", "evaluation_criteria": ["cultural_sensitivity", "inclusive_language", "bias_avoidance"]}', 
 7, true, 'migration'),

-- STRUCTURAL COHERENCE PILLAR (20% weight) - Migrated from quality rules
('pillar', 'structural_coherence', 'Logical Organization', 'Survey sections should follow logical progression and organization', 
 '{"pillar": "structural_coherence", "weight": 0.20, "priority": "high", "migrated_from": "quality/survey_structure", "evaluation_criteria": ["section_logic", "progression_flow", "organizational_structure"]}', 
 10, true, 'migration'),

('pillar', 'structural_coherence', 'Question Grouping', 'Related questions should be grouped together appropriately', 
 '{"pillar": "structural_coherence", "weight": 0.20, "priority": "high", "migrated_from": "quality/survey_structure", "evaluation_criteria": ["topic_grouping", "thematic_organization", "cognitive_flow"]}', 
 9, true, 'migration'),

('pillar', 'structural_coherence', 'Question Type Variety', 'Question types should be varied and engaging throughout the survey', 
 '{"pillar": "structural_coherence", "weight": 0.20, "priority": "medium", "migrated_from": "quality/question_quality", "evaluation_criteria": ["type_variety", "engagement_optimization", "format_diversity"]}', 
 8, true, 'migration'),

('pillar', 'structural_coherence', 'Response Scale Consistency', 'Response scales should be consistent within question groups', 
 '{"pillar": "structural_coherence", "weight": 0.20, "priority": "medium", "migrated_from": "quality/question_quality", "evaluation_criteria": ["scale_consistency", "format_uniformity", "user_experience"]}', 
 8, true, 'migration'),

('pillar', 'structural_coherence', 'Skip Logic Quality', 'Skip logic and branching should be clear and purposeful', 
 '{"pillar": "structural_coherence", "weight": 0.20, "priority": "medium", "migrated_from": "quality/question_quality", "evaluation_criteria": ["logic_clarity", "branching_appropriateness", "flow_control"]}', 
 8, true, 'migration'),

('pillar', 'structural_coherence', 'Response Bias Minimization', 'Question order should minimize response bias and priming effects', 
 '{"pillar": "structural_coherence", "weight": 0.20, "priority": "medium", "migrated_from": "new", "evaluation_criteria": ["order_effects", "priming_prevention", "bias_minimization"]}', 
 7, true, 'migration'),

('pillar', 'structural_coherence', 'Progress Indicators', 'Use progress indicators and clear navigation for user experience', 
 '{"pillar": "structural_coherence", "weight": 0.20, "priority": "low", "migrated_from": "quality/survey_structure", "evaluation_criteria": ["progress_tracking", "navigation_clarity", "user_guidance"]}', 
 6, true, 'migration'),

-- DEPLOYMENT READINESS PILLAR (10% weight) - Migrated from quality rules
('pillar', 'deployment_readiness', 'Survey Length Optimization', 'Survey length should be appropriate for the target audience (typically 10-25 minutes)', 
 '{"pillar": "deployment_readiness", "weight": 0.10, "priority": "high", "migrated_from": "quality/respondent_experience", "evaluation_criteria": ["length_appropriateness", "audience_tolerance", "completion_feasibility"]}', 
 10, true, 'migration'),

('pillar', 'deployment_readiness', 'Question Count Balance', 'Question count should balance comprehensiveness with respondent fatigue', 
 '{"pillar": "deployment_readiness", "weight": 0.10, "priority": "high", "migrated_from": "quality/respondent_experience", "evaluation_criteria": ["question_count", "fatigue_prevention", "engagement_balance"]}', 
 9, true, 'migration'),

('pillar', 'deployment_readiness', 'Sample Size Feasibility', 'Target sample size should be realistic and achievable for the audience', 
 '{"pillar": "deployment_readiness", "weight": 0.10, "priority": "medium", "migrated_from": "new", "evaluation_criteria": ["recruitment_feasibility", "audience_availability", "budget_alignment"]}', 
 8, true, 'migration'),

('pillar', 'deployment_readiness', 'Mobile Optimization', 'Survey should be optimized for the primary response channel (web, mobile, phone)', 
 '{"pillar": "deployment_readiness", "weight": 0.10, "priority": "medium", "migrated_from": "quality/respondent_experience", "evaluation_criteria": ["mobile_friendliness", "channel_optimization", "accessibility"]}', 
 8, true, 'migration'),

('pillar', 'deployment_readiness', 'Technical Feasibility', 'Technical requirements should be feasible for the deployment platform', 
 '{"pillar": "deployment_readiness", "weight": 0.10, "priority": "medium", "migrated_from": "new", "evaluation_criteria": ["platform_compatibility", "technical_feasibility", "implementation_complexity"]}', 
 7, true, 'migration'),

('pillar', 'deployment_readiness', 'Incentive Alignment', 'Survey complexity should match the incentive and value proposition', 
 '{"pillar": "deployment_readiness", "weight": 0.10, "priority": "medium", "migrated_from": "quality/respondent_experience", "evaluation_criteria": ["incentive_appropriateness", "value_proposition", "completion_motivation"]}', 
 7, true, 'migration'),

('pillar', 'deployment_readiness', 'Privacy and Compliance', 'Compliance and privacy requirements should be addressed', 
 '{"pillar": "deployment_readiness", "weight": 0.10, "priority": "medium", "migrated_from": "quality/respondent_experience", "evaluation_criteria": ["privacy_compliance", "data_protection", "regulatory_adherence"]}', 
 7, true, 'migration');

-- Step 2: Create a mapping table to track the migration
CREATE TABLE IF NOT EXISTS rule_migration_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_rule_id UUID REFERENCES survey_rules(id),
    new_pillar_rule_id UUID REFERENCES survey_rules(id),
    migration_type VARCHAR(50) NOT NULL, -- 'consolidated', 'enhanced', 'new'
    migration_reason TEXT,
    migrated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Step 3: Log the migration of existing quality rules to pillar rules
-- This helps track what was consolidated where

-- Get IDs for logging (this would need to be done dynamically in a real migration)
DO $$
DECLARE
    old_rule_record RECORD;
    new_rule_record RECORD;
BEGIN
    -- Log migration for question_quality rules
    FOR old_rule_record IN 
        SELECT id, rule_description FROM survey_rules 
        WHERE rule_type = 'quality' AND category = 'question_quality' AND is_active = true
    LOOP
        -- Find corresponding pillar rules
        FOR new_rule_record IN
            SELECT id FROM survey_rules 
            WHERE rule_type = 'pillar' 
            AND rule_content->>'migrated_from' LIKE '%question_quality%'
            AND is_active = true
        LOOP
            INSERT INTO rule_migration_log (original_rule_id, new_pillar_rule_id, migration_type, migration_reason)
            VALUES (old_rule_record.id, new_rule_record.id, 'consolidated', 
                   'Quality rule consolidated into pillar-based system for better organization and LLM context');
        END LOOP;
    END LOOP;
    
    -- Log migration for survey_structure rules
    FOR old_rule_record IN 
        SELECT id, rule_description FROM survey_rules 
        WHERE rule_type = 'quality' AND category = 'survey_structure' AND is_active = true
    LOOP
        FOR new_rule_record IN
            SELECT id FROM survey_rules 
            WHERE rule_type = 'pillar' 
            AND rule_content->>'migrated_from' LIKE '%survey_structure%'
            AND is_active = true
        LOOP
            INSERT INTO rule_migration_log (original_rule_id, new_pillar_rule_id, migration_type, migration_reason)
            VALUES (old_rule_record.id, new_rule_record.id, 'consolidated', 
                   'Structure rule consolidated into pillar-based system for better categorization');
        END LOOP;
    END LOOP;
    
    -- Log migration for respondent_experience rules
    FOR old_rule_record IN 
        SELECT id, rule_description FROM survey_rules 
        WHERE rule_type = 'quality' AND category = 'respondent_experience' AND is_active = true
    LOOP
        FOR new_rule_record IN
            SELECT id FROM survey_rules 
            WHERE rule_type = 'pillar' 
            AND rule_content->>'migrated_from' LIKE '%respondent_experience%'
            AND is_active = true
        LOOP
            INSERT INTO rule_migration_log (original_rule_id, new_pillar_rule_id, migration_type, migration_reason)
            VALUES (old_rule_record.id, new_rule_record.id, 'consolidated', 
                   'Experience rule consolidated into deployment readiness pillar');
        END LOOP;
    END LOOP;
END $$;

-- Step 4: Deactivate the old redundant quality rules (soft delete)
UPDATE survey_rules 
SET is_active = false, 
    updated_at = NOW(),
    rule_content = COALESCE(rule_content, '{}') || '{"migration_status": "consolidated_to_pillars", "migrated_at": "' || NOW()::text || '"}'
WHERE rule_type = 'quality' 
AND category IN ('question_quality', 'survey_structure', 'respondent_experience')
AND is_active = true;

-- Step 5: Add comments for clarity
COMMENT ON TABLE rule_migration_log IS 'Tracks migration of quality rules to pillar-based system';

-- Update main table comment
COMMENT ON TABLE survey_rules IS 'Stores survey generation rules: methodology (specific), pillar (evaluation framework), industry (domain-specific). Quality rules migrated to pillar system.';

-- Step 6: Create index for migration tracking
CREATE INDEX IF NOT EXISTS idx_rule_migration_original ON rule_migration_log(original_rule_id);
CREATE INDEX IF NOT EXISTS idx_rule_migration_pillar ON rule_migration_log(new_pillar_rule_id);

-- Step 7: Create a view for active evaluation rules (excludes migrated quality rules)
CREATE OR REPLACE VIEW active_evaluation_rules AS
SELECT 
    id,
    rule_type,
    category,
    rule_name,
    rule_description,
    rule_content,
    priority,
    created_at,
    updated_at,
    created_by,
    CASE 
        WHEN rule_type = 'pillar' THEN (rule_content->>'weight')::float
        WHEN rule_type = 'methodology' THEN 0.0
        WHEN rule_type = 'industry' THEN 0.0
        ELSE NULL
    END as pillar_weight,
    CASE
        WHEN rule_type = 'pillar' THEN rule_content->>'pillar'
        ELSE NULL
    END as pillar_name
FROM survey_rules
WHERE is_active = true
AND (
    rule_type IN ('methodology', 'industry', 'pillar')
    OR (rule_type = 'quality' AND category NOT IN ('question_quality', 'survey_structure', 'respondent_experience'))
)
ORDER BY 
    CASE rule_type 
        WHEN 'pillar' THEN 1 
        WHEN 'methodology' THEN 2 
        WHEN 'industry' THEN 3 
        ELSE 4 
    END,
    category,
    priority DESC;

COMMENT ON VIEW active_evaluation_rules IS 'Active rules for evaluation system - excludes migrated quality rules, shows pillar weights';

-- Step 8: Migration summary
DO $$
DECLARE
    migrated_count INTEGER;
    new_pillar_count INTEGER;
    total_active_rules INTEGER;
BEGIN
    SELECT COUNT(*) INTO migrated_count 
    FROM survey_rules 
    WHERE rule_type = 'quality' 
    AND category IN ('question_quality', 'survey_structure', 'respondent_experience')
    AND is_active = false;
    
    SELECT COUNT(*) INTO new_pillar_count 
    FROM survey_rules 
    WHERE rule_type = 'pillar' 
    AND created_by = 'migration';
    
    SELECT COUNT(*) INTO total_active_rules 
    FROM active_evaluation_rules;
    
    RAISE NOTICE 'MIGRATION COMPLETED SUCCESSFULLY:';
    RAISE NOTICE '  - Migrated % redundant quality rules to inactive status', migrated_count;
    RAISE NOTICE '  - Created % new pillar-based rules', new_pillar_count;
    RAISE NOTICE '  - Total active evaluation rules: %', total_active_rules;
    RAISE NOTICE '  - Active rule types: pillar (5-pillar framework), methodology (specific), industry (domain)';
END $$;