-- Migration: Add annotation tables for survey annotation functionality
-- Created: 2024-01-XX
-- Description: Adds tables to store question and section annotations

-- Create question_annotations table
CREATE TABLE IF NOT EXISTS question_annotations (
    id SERIAL PRIMARY KEY,
    question_id VARCHAR(255) NOT NULL,
    survey_id VARCHAR(255) NOT NULL,
    required BOOLEAN NOT NULL DEFAULT true,
    quality INTEGER NOT NULL CHECK (quality >= 1 AND quality <= 5),
    relevant INTEGER NOT NULL CHECK (relevant >= 1 AND relevant <= 5),
    pillars INTEGER NOT NULL CHECK (pillars >= 1 AND pillars <= 5),
    comment TEXT,
    annotator_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(question_id, annotator_id)
);

-- Create section_annotations table
CREATE TABLE IF NOT EXISTS section_annotations (
    id SERIAL PRIMARY KEY,
    section_id INTEGER NOT NULL,
    survey_id VARCHAR(255) NOT NULL,
    quality INTEGER NOT NULL CHECK (quality >= 1 AND quality <= 5),
    relevant INTEGER NOT NULL CHECK (relevant >= 1 AND relevant <= 5),
    pillars INTEGER NOT NULL CHECK (pillars >= 1 AND pillars <= 5),
    comment TEXT,
    annotator_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(section_id, annotator_id)
);

-- Create survey_annotations table for overall annotation metadata
CREATE TABLE IF NOT EXISTS survey_annotations (
    id SERIAL PRIMARY KEY,
    survey_id VARCHAR(255) NOT NULL UNIQUE,
    overall_comment TEXT,
    annotator_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_question_annotations_survey_id ON question_annotations(survey_id);
CREATE INDEX IF NOT EXISTS idx_question_annotations_annotator_id ON question_annotations(annotator_id);
CREATE INDEX IF NOT EXISTS idx_section_annotations_survey_id ON section_annotations(survey_id);
CREATE INDEX IF NOT EXISTS idx_section_annotations_annotator_id ON section_annotations(annotator_id);
CREATE INDEX IF NOT EXISTS idx_survey_annotations_annotator_id ON survey_annotations(annotator_id);

-- Add foreign key constraints if the surveys table exists
-- Note: These will be added when the surveys table is properly set up
-- ALTER TABLE question_annotations ADD CONSTRAINT fk_question_annotations_survey_id 
--     FOREIGN KEY (survey_id) REFERENCES surveys(survey_id) ON DELETE CASCADE;
-- ALTER TABLE section_annotations ADD CONSTRAINT fk_section_annotations_survey_id 
--     FOREIGN KEY (survey_id) REFERENCES surveys(survey_id) ON DELETE CASCADE;
-- ALTER TABLE survey_annotations ADD CONSTRAINT fk_survey_annotations_survey_id 
--     FOREIGN KEY (survey_id) REFERENCES surveys(survey_id) ON DELETE CASCADE;

-- Add comments for documentation
COMMENT ON TABLE question_annotations IS 'Stores annotations for individual survey questions';
COMMENT ON TABLE section_annotations IS 'Stores annotations for survey sections';
COMMENT ON TABLE survey_annotations IS 'Stores overall survey annotation metadata';

COMMENT ON COLUMN question_annotations.quality IS 'Quality rating on 1-5 Likert scale';
COMMENT ON COLUMN question_annotations.relevant IS 'Relevance rating on 1-5 Likert scale';
COMMENT ON COLUMN question_annotations.pillars IS 'Pillar strength rating on 1-5 Likert scale';

COMMENT ON COLUMN section_annotations.quality IS 'Quality rating on 1-5 Likert scale';
COMMENT ON COLUMN section_annotations.relevant IS 'Relevance rating on 1-5 Likert scale';
COMMENT ON COLUMN section_annotations.pillars IS 'Pillar strength rating on 1-5 Likert scale';

