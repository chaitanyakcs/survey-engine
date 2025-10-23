-- Migration: Update existing multi-level RAG tables to rule-based schema
-- Created: 2024-10-20
-- Description: Updates existing golden_sections and golden_questions tables to rule-based schema

-- Add missing columns to golden_sections table (if it exists)
ALTER TABLE golden_sections 
ADD COLUMN IF NOT EXISTS section_type VARCHAR(100),
ADD COLUMN IF NOT EXISTS industry_keywords TEXT[],
ADD COLUMN IF NOT EXISTS question_patterns TEXT[],
ADD COLUMN IF NOT EXISTS human_verified BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS methodology_tags TEXT[],
ADD COLUMN IF NOT EXISTS quality_score DECIMAL(3,2) DEFAULT 0.5,
ADD COLUMN IF NOT EXISTS golden_pair_id UUID;

-- Add missing columns to golden_questions table (if it exists)
ALTER TABLE golden_questions 
ADD COLUMN IF NOT EXISTS question_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS survey_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS golden_pair_id UUID,
ADD COLUMN IF NOT EXISTS annotation_id INTEGER,
ADD COLUMN IF NOT EXISTS question_subtype VARCHAR(100),
ADD COLUMN IF NOT EXISTS industry_keywords TEXT[],
ADD COLUMN IF NOT EXISTS question_patterns TEXT[],
ADD COLUMN IF NOT EXISTS human_verified BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS methodology_tags TEXT[],
ADD COLUMN IF NOT EXISTS quality_score DECIMAL(3,2) DEFAULT 0.5,
ADD COLUMN IF NOT EXISTS usage_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS labels JSONB,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- Remove old columns from golden_questions table (if they exist)
ALTER TABLE golden_questions DROP COLUMN IF EXISTS question_embedding;
ALTER TABLE golden_questions DROP COLUMN IF EXISTS section_id;

-- Add foreign key constraints (only if they don't exist)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints 
                   WHERE constraint_name = 'fk_golden_questions_golden_pair_id') THEN
        ALTER TABLE golden_questions 
        ADD CONSTRAINT fk_golden_questions_golden_pair_id 
        FOREIGN KEY (golden_pair_id) REFERENCES golden_rfq_survey_pairs(id) ON DELETE CASCADE;
    END IF;
END $$;

DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints 
                   WHERE constraint_name = 'fk_golden_questions_annotation_id') THEN
        ALTER TABLE golden_questions 
        ADD CONSTRAINT fk_golden_questions_annotation_id 
        FOREIGN KEY (annotation_id) REFERENCES question_annotations(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Update existing records to have default values for required fields
UPDATE golden_questions 
SET question_id = 'q' || EXTRACT(EPOCH FROM created_at)::text || '_' || id::text
WHERE question_id IS NULL;

UPDATE golden_questions 
SET survey_id = 'survey_' || id::text
WHERE survey_id IS NULL;

-- Make question_id and survey_id NOT NULL after setting default values
ALTER TABLE golden_questions ALTER COLUMN question_id SET NOT NULL;
ALTER TABLE golden_questions ALTER COLUMN survey_id SET NOT NULL;

-- Create indexes for golden_sections (will fail gracefully if table doesn't exist)
CREATE INDEX IF NOT EXISTS idx_golden_sections_section_type ON golden_sections(section_type);
CREATE INDEX IF NOT EXISTS idx_golden_sections_methodology_tags ON golden_sections USING GIN(methodology_tags);
CREATE INDEX IF NOT EXISTS idx_golden_sections_industry_keywords ON golden_sections USING GIN(industry_keywords);
CREATE INDEX IF NOT EXISTS idx_golden_sections_human_verified ON golden_sections(human_verified);
CREATE INDEX IF NOT EXISTS idx_golden_sections_quality_score ON golden_sections(quality_score);
CREATE INDEX IF NOT EXISTS idx_golden_sections_golden_pair_id ON golden_sections(golden_pair_id);

-- Create indexes for golden_questions (will fail gracefully if table doesn't exist)
CREATE INDEX IF NOT EXISTS idx_golden_questions_question_id ON golden_questions(question_id);
CREATE INDEX IF NOT EXISTS idx_golden_questions_survey_id ON golden_questions(survey_id);
CREATE INDEX IF NOT EXISTS idx_golden_questions_golden_pair_id ON golden_questions(golden_pair_id);
CREATE INDEX IF NOT EXISTS idx_golden_questions_annotation_id ON golden_questions(annotation_id);
CREATE INDEX IF NOT EXISTS idx_golden_questions_question_type ON golden_questions(question_type);
CREATE INDEX IF NOT EXISTS idx_golden_questions_question_subtype ON golden_questions(question_subtype);
CREATE INDEX IF NOT EXISTS idx_golden_questions_methodology_tags ON golden_questions USING GIN(methodology_tags);
CREATE INDEX IF NOT EXISTS idx_golden_questions_industry_keywords ON golden_questions USING GIN(industry_keywords);
CREATE INDEX IF NOT EXISTS idx_golden_questions_human_verified ON golden_questions(human_verified);
CREATE INDEX IF NOT EXISTS idx_golden_questions_quality_score ON golden_questions(quality_score);

-- Add comments for documentation (will fail gracefully if tables don't exist)
COMMENT ON TABLE golden_sections IS 'Rule-based section-level retrieval without vector embeddings';
COMMENT ON TABLE golden_questions IS 'Rule-based question-level retrieval without vector embeddings';
COMMENT ON COLUMN golden_sections.section_type IS 'Deterministic section classification for exact matching';
COMMENT ON COLUMN golden_sections.methodology_tags IS 'Methodology tags for rule-based filtering';
COMMENT ON COLUMN golden_sections.industry_keywords IS 'Industry keywords for rule-based matching';
COMMENT ON COLUMN golden_sections.question_patterns IS 'Question patterns found in this section for pattern matching';
COMMENT ON COLUMN golden_questions.question_type IS 'Deterministic question type for exact matching';
COMMENT ON COLUMN golden_questions.question_subtype IS 'Question subtype for more specific matching';
COMMENT ON COLUMN golden_questions.methodology_tags IS 'Methodology tags for rule-based filtering';
COMMENT ON COLUMN golden_questions.industry_keywords IS 'Industry keywords for rule-based matching';
COMMENT ON COLUMN golden_questions.question_patterns IS 'Question patterns/templates for pattern matching';

