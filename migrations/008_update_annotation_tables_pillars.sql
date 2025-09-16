-- Migration: Update annotation tables to support individual pillar ratings
-- Created: 2024-01-XX
-- Description: Updates question_annotations and section_annotations tables to store individual pillar ratings

-- Update question_annotations table
ALTER TABLE question_annotations 
DROP CONSTRAINT IF EXISTS check_pillars_range;

ALTER TABLE question_annotations 
DROP COLUMN IF EXISTS pillars;

ALTER TABLE question_annotations 
ADD COLUMN methodological_rigor INTEGER NOT NULL DEFAULT 3 CHECK (methodological_rigor >= 1 AND methodological_rigor <= 5);

ALTER TABLE question_annotations 
ADD COLUMN content_validity INTEGER NOT NULL DEFAULT 3 CHECK (content_validity >= 1 AND content_validity <= 5);

ALTER TABLE question_annotations 
ADD COLUMN respondent_experience INTEGER NOT NULL DEFAULT 3 CHECK (respondent_experience >= 1 AND respondent_experience <= 5);

ALTER TABLE question_annotations 
ADD COLUMN analytical_value INTEGER NOT NULL DEFAULT 3 CHECK (analytical_value >= 1 AND analytical_value <= 5);

ALTER TABLE question_annotations 
ADD COLUMN business_impact INTEGER NOT NULL DEFAULT 3 CHECK (business_impact >= 1 AND business_impact <= 5);

-- Update section_annotations table
ALTER TABLE section_annotations 
DROP CONSTRAINT IF EXISTS check_pillars_range;

ALTER TABLE section_annotations 
DROP COLUMN IF EXISTS pillars;

ALTER TABLE section_annotations 
ADD COLUMN methodological_rigor INTEGER NOT NULL DEFAULT 3 CHECK (methodological_rigor >= 1 AND methodological_rigor <= 5);

ALTER TABLE section_annotations 
ADD COLUMN content_validity INTEGER NOT NULL DEFAULT 3 CHECK (content_validity >= 1 AND content_validity <= 5);

ALTER TABLE section_annotations 
ADD COLUMN respondent_experience INTEGER NOT NULL DEFAULT 3 CHECK (respondent_experience >= 1 AND respondent_experience <= 5);

ALTER TABLE section_annotations 
ADD COLUMN analytical_value INTEGER NOT NULL DEFAULT 3 CHECK (analytical_value >= 1 AND analytical_value <= 5);

ALTER TABLE section_annotations 
ADD COLUMN business_impact INTEGER NOT NULL DEFAULT 3 CHECK (business_impact >= 1 AND business_impact <= 5);

-- Add comments for documentation
COMMENT ON COLUMN question_annotations.methodological_rigor IS 'Methodological rigor rating on 1-5 Likert scale';
COMMENT ON COLUMN question_annotations.content_validity IS 'Content validity rating on 1-5 Likert scale';
COMMENT ON COLUMN question_annotations.respondent_experience IS 'Respondent experience rating on 1-5 Likert scale';
COMMENT ON COLUMN question_annotations.analytical_value IS 'Analytical value rating on 1-5 Likert scale';
COMMENT ON COLUMN question_annotations.business_impact IS 'Business impact rating on 1-5 Likert scale';

COMMENT ON COLUMN section_annotations.methodological_rigor IS 'Methodological rigor rating on 1-5 Likert scale';
COMMENT ON COLUMN section_annotations.content_validity IS 'Content validity rating on 1-5 Likert scale';
COMMENT ON COLUMN section_annotations.respondent_experience IS 'Respondent experience rating on 1-5 Likert scale';
COMMENT ON COLUMN section_annotations.analytical_value IS 'Analytical value rating on 1-5 Likert scale';
COMMENT ON COLUMN section_annotations.business_impact IS 'Business impact rating on 1-5 Likert scale';
