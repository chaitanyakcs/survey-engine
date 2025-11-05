-- Fix unique constraints on annotation tables to include survey_id
-- This allows the same question_id/section_id and annotator_id combination across different surveys
-- Migration is idempotent - safe to run multiple times

-- Drop the existing unique index for question_annotations
DROP INDEX IF EXISTS idx_question_annotations_unique;

-- Create a new unique index that includes survey_id
CREATE UNIQUE INDEX IF NOT EXISTS idx_question_annotations_unique 
    ON question_annotations(question_id, annotator_id, survey_id);

-- Drop the existing unique index for section_annotations
DROP INDEX IF EXISTS idx_section_annotations_unique;

-- Create a new unique index that includes survey_id
CREATE UNIQUE INDEX IF NOT EXISTS idx_section_annotations_unique 
    ON section_annotations(section_id, annotator_id, survey_id);

