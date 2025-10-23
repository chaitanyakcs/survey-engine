-- Add annotation_id foreign key columns to golden_questions and golden_sections tables
-- This links RAG entries back to their source annotations for tracking and quality updates

-- Add annotation_id column to golden_questions table
ALTER TABLE golden_questions 
ADD COLUMN IF NOT EXISTS annotation_id INTEGER REFERENCES question_annotations(id) ON DELETE SET NULL;

-- Add annotation_id column to golden_sections table  
ALTER TABLE golden_sections 
ADD COLUMN IF NOT EXISTS annotation_id INTEGER REFERENCES section_annotations(id) ON DELETE SET NULL;

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_golden_questions_annotation 
ON golden_questions(annotation_id);

CREATE INDEX IF NOT EXISTS idx_golden_sections_annotation 
ON golden_sections(annotation_id);

-- Add comments for documentation
COMMENT ON COLUMN golden_questions.annotation_id IS 'Foreign key to question_annotations table - tracks source annotation for this RAG entry';
COMMENT ON COLUMN golden_sections.annotation_id IS 'Foreign key to section_annotations table - tracks source annotation for this RAG entry';


