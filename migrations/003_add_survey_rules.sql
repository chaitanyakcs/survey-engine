-- Migration: Add survey rules and validation tables
-- Created: 2024-01-XX
-- Description: Adds tables for storing survey generation rules and validation results

-- Create survey_rules table
CREATE TABLE IF NOT EXISTS survey_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_type VARCHAR(50) NOT NULL,
    category VARCHAR(100) NOT NULL,
    rule_name VARCHAR(200) NOT NULL,
    rule_description TEXT,
    rule_content JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100) DEFAULT 'system'
);

-- Create indexes for survey_rules
CREATE INDEX IF NOT EXISTS idx_survey_rules_type_category ON survey_rules(rule_type, category);
CREATE INDEX IF NOT EXISTS idx_survey_rules_active ON survey_rules(is_active);

-- Create rule_validations table
CREATE TABLE IF NOT EXISTS rule_validations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    survey_id UUID NOT NULL REFERENCES surveys(id),
    rule_id UUID NOT NULL REFERENCES survey_rules(id),
    validation_passed BOOLEAN NOT NULL,
    error_message TEXT,
    warning_message TEXT,
    validation_details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for rule_validations
CREATE INDEX IF NOT EXISTS idx_rule_validations_survey ON rule_validations(survey_id);
CREATE INDEX IF NOT EXISTS idx_rule_validations_rule ON rule_validations(rule_id);

-- Add rule_validations relationship to surveys table
-- (This is handled by the relationship in the model, but we can add a comment)
COMMENT ON TABLE rule_validations IS 'Stores validation results for surveys against rules';
COMMENT ON TABLE survey_rules IS 'Stores survey generation rules and methodologies';

-- Seed initial rules data
INSERT INTO survey_rules (rule_type, category, rule_name, rule_description, rule_content, priority, is_active, created_by) VALUES
-- Methodology Rules
('methodology', 'van_westendorp', 'Van Westendorp Price Sensitivity Meter', 'Measures price sensitivity through four key questions', 
 '{"required_questions": 4, "question_flow": ["At what price would you consider this product to be so expensive that you would not consider buying it?", "At what price would you consider this product to be priced so low that you would feel the quality couldn''t be very good?", "At what price would you consider this product starting to get expensive, so that it is not out of the question, but you would have to give some thought to buying it?", "At what price would you consider this product to be a bargain - a great buy for the money?"], "validation_rules": ["Must have exactly 4 price questions", "Questions must follow the exact Van Westendorp format", "Price ranges should be logical and sequential", "Include open-ended follow-up for reasoning", "Use currency-appropriate formatting"], "best_practices": ["Present questions in random order to avoid bias", "Include product description before price questions", "Use realistic price ranges based on market research", "Add demographic questions for segmentation"]}', 
 10, true, 'system'),

('methodology', 'conjoint', 'Conjoint Analysis / Choice Modeling', 'Measures preferences for product attributes',
 '{"required_attributes": 3, "max_attributes": 6, "question_flow": ["Screening questions for product familiarity", "Attribute importance ranking", "Choice sets with different combinations", "Demographic and behavioral questions"], "validation_rules": ["Must have balanced choice sets", "Attributes must be orthogonal (independent)", "Include appropriate sample size calculations", "Use realistic attribute levels", "Include ''None of the above'' option"], "best_practices": ["Limit to 3-6 attributes to avoid cognitive overload", "Use 2-4 levels per attribute", "Include 8-12 choice tasks per respondent", "Randomize choice set presentation"]}',
 10, true, 'system'),

('methodology', 'nps', 'Net Promoter Score', 'Measures customer loyalty and satisfaction',
 '{"required_questions": 2, "question_flow": ["How likely are you to recommend [product/service] to a friend or colleague? (0-10 scale)", "What is the primary reason for your score? (open text)"], "validation_rules": ["Must use 0-10 scale", "Include follow-up question for reasoning", "Properly categorize promoters (9-10), passives (7-8), detractors (0-6)", "Use consistent wording across surveys"], "best_practices": ["Ask NPS question early in survey", "Include context about the product/service", "Add behavioral questions for segmentation", "Use consistent timeframes (e.g., ''in the past 6 months'')"]}',
 10, true, 'system'),

-- Quality Rules
('quality', 'question_quality', 'Question Quality Standards', 'Ensures high-quality question design',
 '{"rules": ["Questions must be clear, concise, and unambiguous", "Avoid leading, loaded, or double-barreled questions", "Use appropriate question types for the data needed", "Include proper validation and skip logic where needed", "Avoid jargon and technical terms unless necessary", "Use consistent terminology throughout the survey", "Ensure questions are culturally appropriate and inclusive"]}',
 8, true, 'system'),

('quality', 'survey_structure', 'Survey Structure Guidelines', 'Ensures proper survey organization and flow',
 '{"rules": ["Start with screening questions to qualify respondents", "Group related questions logically", "Place sensitive questions near the end", "Include demographic questions for segmentation", "Use progress indicators for long surveys", "Include clear instructions and context", "End with thank you message and next steps"]}',
 8, true, 'system'),

('quality', 'respondent_experience', 'Respondent Experience', 'Optimizes survey experience for respondents',
 '{"rules": ["Keep survey length appropriate (5-15 minutes)", "Use clear instructions and progress indicators", "Avoid repetitive or redundant questions", "Ensure mobile-friendly question formats", "Use engaging and conversational language", "Include appropriate incentives information", "Provide clear privacy and data usage information"]}',
 7, true, 'system'),

-- Industry Rules
('industry', 'healthcare', 'Healthcare Research Standards', 'Specialized rules for healthcare research',
 '{"rules": ["Include HIPAA compliance considerations", "Use appropriate medical terminology", "Include consent and privacy statements", "Consider patient confidentiality", "Use validated health assessment tools", "Include appropriate demographic questions", "Ensure cultural sensitivity in health questions"]}',
 7, true, 'system'),

('industry', 'financial_services', 'Financial Services Research', 'Specialized rules for financial services research',
 '{"rules": ["Include appropriate disclaimers", "Use clear financial terminology", "Include risk assessment questions", "Ensure regulatory compliance", "Include appropriate demographic questions", "Use validated financial scales", "Consider privacy and security requirements"]}',
 7, true, 'system'),

('industry', 'technology', 'Technology Research Standards', 'Specialized rules for technology research',
 '{"rules": ["Use current technology terminology", "Include appropriate technical questions", "Consider user experience factors", "Include adoption and usage questions", "Use appropriate demographic questions", "Consider privacy and security concerns", "Include innovation and future trends questions"]}',
 7, true, 'system');

-- Add a comment about the seeded data
COMMENT ON TABLE survey_rules IS 'Stores survey generation rules and methodologies - includes seeded methodology, quality, and industry rules';
