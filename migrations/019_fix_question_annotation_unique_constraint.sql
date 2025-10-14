-- Fix unique constraint on question_annotations to include survey_id
-- This allows the same question_id and annotator_id combination across different surveys

-- Drop the existing unique constraint
ALTER TABLE question_annotations DROP CONSTRAINT IF EXISTS idx_question_annotations_unique;

-- Create a new unique constraint that includes survey_id
CREATE UNIQUE INDEX idx_question_annotations_unique ON question_annotations (question_id, annotator_id, survey_id);

-- Also fix the same issue for section_annotations
ALTER TABLE section_annotations DROP CONSTRAINT IF EXISTS idx_section_annotations_unique;

-- Create a new unique constraint for section annotations that includes survey_id
CREATE UNIQUE INDEX idx_section_annotations_unique ON section_annotations (section_id, annotator_id, survey_id);
