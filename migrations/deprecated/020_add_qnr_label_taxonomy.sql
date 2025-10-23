-- Migration: Add QNR Label Taxonomy System
-- Description: Creates tables for QNR label definitions and tag definitions
-- Version: 020
-- Date: 2024-01-15

-- QNR Label Definitions table
CREATE TABLE IF NOT EXISTS qnr_label_definitions (
    id SERIAL PRIMARY KEY,
    label_name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50) NOT NULL, -- screener, brand, concept, methodology, additional
    description TEXT,
    mandatory BOOLEAN DEFAULT FALSE,
    applicable_labels JSONB, -- Conditional requirements
    label_type VARCHAR(50), -- Text, QNR, Rules
    detection_patterns JSONB, -- Keywords and patterns for auto-detection
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- QNR Tag Definitions (metadata)
CREATE TABLE IF NOT EXISTS qnr_tag_definitions (
    id SERIAL PRIMARY KEY,
    tag_name VARCHAR(100) NOT NULL,
    tag_values TEXT[], -- Allowed values
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_qnr_labels_category ON qnr_label_definitions(category);
CREATE INDEX IF NOT EXISTS idx_qnr_labels_mandatory ON qnr_label_definitions(mandatory);
CREATE INDEX IF NOT EXISTS idx_qnr_labels_label_type ON qnr_label_definitions(label_type);
CREATE INDEX IF NOT EXISTS idx_qnr_labels_name ON qnr_label_definitions(label_name);

-- Create GIN indexes for JSONB columns
CREATE INDEX IF NOT EXISTS idx_qnr_labels_applicable_labels ON qnr_label_definitions USING GIN(applicable_labels);
CREATE INDEX IF NOT EXISTS idx_qnr_labels_detection_patterns ON qnr_label_definitions USING GIN(detection_patterns);
CREATE INDEX IF NOT EXISTS idx_qnr_tags_values ON qnr_tag_definitions USING GIN(tag_values);

-- Add comments
COMMENT ON TABLE qnr_label_definitions IS 'Stores QNR label definitions for survey structure validation';
COMMENT ON TABLE qnr_tag_definitions IS 'Stores QNR tag definitions for metadata categorization';

COMMENT ON COLUMN qnr_label_definitions.label_name IS 'Standardized label name (e.g., Recent_Participation)';
COMMENT ON COLUMN qnr_label_definitions.category IS 'Label category: screener, brand, concept, methodology, additional';
COMMENT ON COLUMN qnr_label_definitions.mandatory IS 'Whether this label is required for the section';
COMMENT ON COLUMN qnr_label_definitions.applicable_labels IS 'Other labels that must be present when this label is used';
COMMENT ON COLUMN qnr_label_definitions.label_type IS 'Type of label: Text, QNR, Rules';
COMMENT ON COLUMN qnr_label_definitions.detection_patterns IS 'Keywords and patterns for automatic label detection';

-- Seed data from QNR_Labeling CSV files
-- This will be populated by the QNRLabelTaxonomy service at runtime
-- but we can add some critical labels here for reference

INSERT INTO qnr_label_definitions (label_name, category, description, mandatory, applicable_labels, label_type, detection_patterns) VALUES
-- Critical Screener Labels
('Study_Intro', 'screener', 'Thanks for agreeing, inform eligibility, state LOI', TRUE, NULL, 'Text', '["thank you", "participating", "research study", "confidential"]'),
('Recent_Participation', 'screener', 'Participated in Market Research study recently. Terminate', TRUE, NULL, 'QNR', '["participated", "market research", "recent study", "past 6 months"]'),
('Conflict_Of_Interest_Check', 'screener', 'Conflict of Interest check. Terminate', TRUE, NULL, 'QNR', '["work for", "employed by", "conflict of interest", "employee of"]'),
('Demographics_Basic', 'screener', 'Age, Gender. Check categories specific to country', TRUE, NULL, 'QNR', '["age", "gender", "male", "female", "age range"]'),

-- Van Westendorp Labels (Critical for pricing studies)
('VW_Price_Too_Cheap', 'methodology', 'At what price would it be too cheap to trust quality?', TRUE, '["van_westendorp"]', 'QNR', '["too cheap", "too inexpensive", "suspiciously cheap"]'),
('VW_Price_Bargain', 'methodology', 'At what price would it be a bargain/good value?', TRUE, '["van_westendorp"]', 'QNR', '["bargain", "good value", "great deal", "good price"]'),
('VW_Price_Getting_Expensive', 'methodology', 'At what price is it starting to get expensive?', TRUE, '["van_westendorp"]', 'QNR', '["getting expensive", "starting to expensive", "bit expensive"]'),
('VW_Price_Too_Expensive', 'methodology', 'At what price is it too expensive to consider?', TRUE, '["van_westendorp"]', 'QNR', '["too expensive", "prohibitively expensive", "cannot afford"]'),

-- Brand Labels
('Brand_Recall_Unaided', 'brand', 'Top of the mind brands', TRUE, NULL, 'QNR', '["brands", "think of", "top of mind", "come to mind"]'),
('Brand_Awareness_Funnel', 'brand', 'Aware → Considered → Purchased → Continue → Preferred', TRUE, '["consumer_health", "healthcare", "medtech", "patients"]', 'QNR', '["aware", "considered", "purchased", "continue", "prefer"]'),
('Product_Satisfaction', 'brand', 'With the products used in the past and current', TRUE, '["consumer_health", "healthcare", "medtech", "patients"]', 'QNR', '["satisfied", "satisfaction", "rate", "evaluate", "experience"]'),

-- Concept Labels
('Concept_Intro', 'concept', 'Concept Introduction for pricing and reaction with hyperlink', TRUE, '["concept_intro"]', 'Text', '["concept", "product concept", "please review", "carefully"]'),
('Concept_Impression', 'concept', 'Overall Impression', TRUE, NULL, 'QNR', '["overall impression", "first impression", "initial reaction"]'),
('Concept_Purchase_Likelihood', 'concept', 'How likely are you to purchase, how soon will you purchase', TRUE, NULL, 'QNR', '["likely to purchase", "purchase likelihood", "how soon"]')

ON CONFLICT (label_name) DO NOTHING;

-- Add QNR Tag definitions
INSERT INTO qnr_tag_definitions (tag_name, tag_values, description) VALUES
('QNR_Industry', ARRAY['Consumer Electronics', 'Consumer Goods', 'Healthcare', 'MedTech', 'Medical Devices', 'Vision Care'], 'Industry categories for surveys'),
('Respondent_Type', ARRAY['Admin', 'Consumer', 'ECP', 'HCP', 'Nursing Staff', 'Patient'], 'Types of survey respondents'),
('QNR_Country', ARRAY['Canada', 'EU', 'France', 'India', 'Japan', 'UK', 'US'], 'Countries where surveys are conducted'),
('Methodology', ARRAY['Conjoint', 'Feature Importance', 'Pricing'], 'Research methodologies'),
('Pricing_Method', ARRAY['Gabor Granger', 'Van Westendorp'], 'Specific pricing methodologies')

ON CONFLICT (tag_name) DO NOTHING;

-- Create a view for easy querying of label requirements
CREATE OR REPLACE VIEW qnr_label_requirements AS
SELECT 
    l.label_name,
    l.category,
    l.description,
    l.mandatory,
    l.label_type,
    CASE 
        WHEN l.category = 'screener' THEN 2
        WHEN l.category = 'brand' THEN 3
        WHEN l.category = 'concept' THEN 4
        WHEN l.category = 'methodology' THEN 5
        WHEN l.category = 'additional' THEN 6
        ELSE NULL
    END as section_id,
    l.applicable_labels,
    l.detection_patterns
FROM qnr_label_definitions l
WHERE l.mandatory = TRUE
ORDER BY l.category, l.label_name;

-- Create a function to get required labels for a section
CREATE OR REPLACE FUNCTION get_required_labels_for_section(
    p_section_id INTEGER,
    p_methodology TEXT[] DEFAULT NULL,
    p_industry TEXT DEFAULT NULL
)
RETURNS TABLE (
    label_name VARCHAR(100),
    description TEXT,
    label_type VARCHAR(50),
    detection_patterns JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        l.label_name,
        l.description,
        l.label_type,
        l.detection_patterns
    FROM qnr_label_definitions l
    WHERE 
        l.mandatory = TRUE
        AND (
            (p_section_id = 2 AND l.category = 'screener') OR
            (p_section_id = 3 AND l.category = 'brand') OR
            (p_section_id = 4 AND l.category = 'concept') OR
            (p_section_id = 5 AND l.category = 'methodology') OR
            (p_section_id = 6 AND l.category = 'additional')
        )
        AND (
            p_methodology IS NULL OR 
            l.applicable_labels IS NULL OR
            l.applicable_labels ?| p_methodology
        )
        AND (
            p_industry IS NULL OR
            l.applicable_labels IS NULL OR
            l.applicable_labels ? p_industry
        )
    ORDER BY l.label_name;
END;
$$ LANGUAGE plpgsql;

-- Create a function to check if a survey has required labels
CREATE OR REPLACE FUNCTION check_survey_label_compliance(
    p_survey_id TEXT,
    p_detected_labels JSONB
)
RETURNS TABLE (
    section_id INTEGER,
    missing_labels TEXT[],
    compliance_score FLOAT
) AS $$
DECLARE
    section_record RECORD;
    required_labels TEXT[];
    detected_labels_array TEXT[];
    missing_count INTEGER;
    total_count INTEGER;
BEGIN
    -- Get detected labels as array
    SELECT ARRAY(SELECT jsonb_array_elements_text(p_detected_labels)) INTO detected_labels_array;
    
    -- Check each section
    FOR section_record IN 
        SELECT DISTINCT 
            CASE 
                WHEN category = 'screener' THEN 2
                WHEN category = 'brand' THEN 3
                WHEN category = 'concept' THEN 4
                WHEN category = 'methodology' THEN 5
                WHEN category = 'additional' THEN 6
            END as section_id,
            category
        FROM qnr_label_definitions 
        WHERE mandatory = TRUE
    LOOP
        -- Get required labels for this section
        SELECT ARRAY_AGG(label_name) INTO required_labels
        FROM qnr_label_definitions
        WHERE 
            mandatory = TRUE
            AND (
                (section_record.section_id = 2 AND category = 'screener') OR
                (section_record.section_id = 3 AND category = 'brand') OR
                (section_record.section_id = 4 AND category = 'concept') OR
                (section_record.section_id = 5 AND category = 'methodology') OR
                (section_record.section_id = 6 AND category = 'additional')
            );
        
        -- Calculate missing labels
        SELECT ARRAY(
            SELECT unnest(required_labels)
            EXCEPT
            SELECT unnest(detected_labels_array)
        ) INTO missing_labels;
        
        -- Calculate compliance score
        total_count := array_length(required_labels, 1);
        missing_count := array_length(missing_labels, 1);
        
        IF total_count IS NULL OR total_count = 0 THEN
            compliance_score := 1.0;
        ELSE
            compliance_score := (total_count - COALESCE(missing_count, 0))::FLOAT / total_count;
        END IF;
        
        RETURN QUERY SELECT section_record.section_id, missing_labels, compliance_score;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT SELECT ON qnr_label_definitions TO PUBLIC;
GRANT SELECT ON qnr_tag_definitions TO PUBLIC;
GRANT SELECT ON qnr_label_requirements TO PUBLIC;
GRANT EXECUTE ON FUNCTION get_required_labels_for_section TO PUBLIC;
GRANT EXECUTE ON FUNCTION check_survey_label_compliance TO PUBLIC;


