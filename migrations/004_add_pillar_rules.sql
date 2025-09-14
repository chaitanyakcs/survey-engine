-- Migration: Add 5-Pillar Evaluation Rules
-- Created: $(date)
-- Description: Extends survey_rules table with pillar-based evaluation rules


-- Add pillar-based rule categories to the existing survey_rules table
-- This extends the current system with 5-pillar framework rules

-- Content Validity Rules
INSERT INTO survey_rules (rule_type, category, rule_name, rule_description, rule_content, priority, is_active, created_by) VALUES
('pillar', 'content_validity', 'RFQ Objective Coverage', 'Survey questions must directly address all stated research objectives from the RFQ', 
 '{"pillar": "content_validity", "weight": 0.20, "priority": "high", "evaluation_criteria": ["objective_alignment", "topic_comprehensiveness", "research_goal_mapping"]}', 
 9, true, 'system'),

('pillar', 'content_validity', 'Research Scope Alignment', 'Survey scope should align with the research goals and target audience specified', 
 '{"pillar": "content_validity", "weight": 0.20, "priority": "high", "evaluation_criteria": ["scope_appropriateness", "audience_targeting", "goal_alignment"]}', 
 9, true, 'system'),

-- Methodological Rigor Rules  
('pillar', 'methodological_rigor', 'Bias Prevention', 'Avoid leading, loaded, or double-barreled questions that introduce bias', 
 '{"pillar": "methodological_rigor", "weight": 0.25, "priority": "critical", "evaluation_criteria": ["bias_detection", "question_neutrality", "leading_language"]}', 
 10, true, 'system'),

('pillar', 'methodological_rigor', 'Question Sequencing', 'Questions must follow logical sequence from general to specific', 
 '{"pillar": "methodological_rigor", "weight": 0.25, "priority": "high", "evaluation_criteria": ["sequence_logic", "flow_optimization", "bias_minimization"]}', 
 9, true, 'system'),

('pillar', 'methodological_rigor', 'Sample Size Appropriateness', 'Sample size and targeting must align with statistical requirements', 
 '{"pillar": "methodological_rigor", "weight": 0.25, "priority": "medium", "evaluation_criteria": ["statistical_adequacy", "methodology_alignment", "feasibility"]}', 
 8, true, 'system'),

-- Clarity & Comprehensibility Rules
('pillar', 'clarity_comprehensibility', 'Language Clarity', 'Use clear, simple language appropriate for the target audience', 
 '{"pillar": "clarity_comprehensibility", "weight": 0.25, "priority": "high", "evaluation_criteria": ["language_accessibility", "reading_level", "terminology_appropriateness"]}', 
 9, true, 'system'),

('pillar', 'clarity_comprehensibility', 'Single Concept Focus', 'Each question should focus on a single concept or idea', 
 '{"pillar": "clarity_comprehensibility", "weight": 0.25, "priority": "high", "evaluation_criteria": ["concept_clarity", "double_barreled_detection", "ambiguity_check"]}', 
 9, true, 'system'),

('pillar', 'clarity_comprehensibility', 'Neutral Wording', 'Question wording should be neutral and unambiguous', 
 '{"pillar": "clarity_comprehensibility", "weight": 0.25, "priority": "high", "evaluation_criteria": ["wording_neutrality", "ambiguity_assessment", "cultural_sensitivity"]}', 
 9, true, 'system'),

-- Structural Coherence Rules
('pillar', 'structural_coherence', 'Logical Organization', 'Survey sections should follow logical progression and organization', 
 '{"pillar": "structural_coherence", "weight": 0.20, "priority": "high", "evaluation_criteria": ["section_logic", "progression_flow", "organizational_structure"]}', 
 9, true, 'system'),

('pillar', 'structural_coherence', 'Question Grouping', 'Related questions should be grouped together appropriately', 
 '{"pillar": "structural_coherence", "weight": 0.20, "priority": "medium", "evaluation_criteria": ["topic_grouping", "thematic_organization", "cognitive_flow"]}', 
 8, true, 'system'),

('pillar', 'structural_coherence', 'Response Scale Consistency', 'Response scales should be consistent within question groups', 
 '{"pillar": "structural_coherence", "weight": 0.20, "priority": "medium", "evaluation_criteria": ["scale_consistency", "format_uniformity", "user_experience"]}', 
 8, true, 'system'),

-- Deployment Readiness Rules
('pillar', 'deployment_readiness', 'Survey Length Optimization', 'Survey length should be appropriate for the target audience (typically 10-25 minutes)', 
 '{"pillar": "deployment_readiness", "weight": 0.10, "priority": "high", "evaluation_criteria": ["length_appropriateness", "audience_tolerance", "completion_feasibility"]}', 
 9, true, 'system'),

('pillar', 'deployment_readiness', 'Sample Size Feasibility', 'Target sample size should be realistic and achievable for the audience', 
 '{"pillar": "deployment_readiness", "weight": 0.10, "priority": "medium", "evaluation_criteria": ["recruitment_feasibility", "audience_availability", "budget_alignment"]}', 
 8, true, 'system'),

('pillar', 'deployment_readiness', 'Technical Readiness', 'Technical requirements should be feasible for the deployment platform', 
 '{"pillar": "deployment_readiness", "weight": 0.10, "priority": "medium", "evaluation_criteria": ["platform_compatibility", "technical_feasibility", "user_experience"]}', 
 8, true, 'system');

-- Add comment about pillar rules
COMMENT ON TABLE survey_rules IS 'Stores survey generation rules and methodologies - includes seeded methodology, quality, industry, and pillar-based evaluation rules';

