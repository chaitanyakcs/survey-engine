-- Fix SurveyAnnotation unique constraint to allow multiple annotators per survey
-- The current constraint only allows one annotation per survey_id, but we need one per (survey_id, annotator_id)

-- First, drop the existing unique constraint
ALTER TABLE survey_annotations DROP CONSTRAINT IF EXISTS survey_annotations_survey_id_key;

-- Add a new unique constraint on (survey_id, annotator_id)
ALTER TABLE survey_annotations ADD CONSTRAINT survey_annotations_survey_id_annotator_id_key UNIQUE (survey_id, annotator_id);

-- Add an index for better query performance
CREATE INDEX IF NOT EXISTS idx_survey_annotations_survey_id_annotator_id ON survey_annotations(survey_id, annotator_id);
