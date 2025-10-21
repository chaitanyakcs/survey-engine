-- Migration: Update existing multi-level RAG tables to rule-based schema
-- Created: 2024-10-20
-- Description: Updates existing golden_sections and golden_questions tables to rule-based schema

-- Update golden_sections table to add missing columns
ALTER TABLE golden_sections 
ADD COLUMN IF NOT EXISTS section_type VARCHAR(100),
ADD COLUMN IF NOT EXISTS industry_keywords TEXT[],
ADD COLUMN IF NOT EXISTS question_patterns TEXT[];

-- Update golden_questions table to add missing columns and remove vector column
ALTER TABLE golden_questions 
ADD COLUMN IF NOT EXISTS question_subtype VARCHAR(100),
ADD COLUMN IF NOT EXISTS industry_keywords TEXT[],
ADD COLUMN IF NOT EXISTS question_patterns TEXT[];

-- Remove the old vector column if it exists
ALTER TABLE golden_questions DROP COLUMN IF EXISTS question_embedding;

-- Remove the old section_id column if it exists (not needed for rule-based)
ALTER TABLE golden_questions DROP COLUMN IF EXISTS section_id;

-- Create indexes for efficient rule-based queries
CREATE INDEX IF NOT EXISTS idx_golden_sections_section_type ON golden_sections(section_type);
CREATE INDEX IF NOT EXISTS idx_golden_sections_methodology_tags ON golden_sections USING GIN(methodology_tags);
CREATE INDEX IF NOT EXISTS idx_golden_sections_industry_keywords ON golden_sections USING GIN(industry_keywords);
CREATE INDEX IF NOT EXISTS idx_golden_sections_human_verified ON golden_sections(human_verified);
CREATE INDEX IF NOT EXISTS idx_golden_sections_quality_score ON golden_sections(quality_score);
CREATE INDEX IF NOT EXISTS idx_golden_sections_golden_pair_id ON golden_sections(golden_pair_id);

CREATE INDEX IF NOT EXISTS idx_golden_questions_question_type ON golden_questions(question_type);
CREATE INDEX IF NOT EXISTS idx_golden_questions_question_subtype ON golden_questions(question_subtype);
CREATE INDEX IF NOT EXISTS idx_golden_questions_methodology_tags ON golden_questions USING GIN(methodology_tags);
CREATE INDEX IF NOT EXISTS idx_golden_questions_industry_keywords ON golden_questions USING GIN(industry_keywords);
CREATE INDEX IF NOT EXISTS idx_golden_questions_human_verified ON golden_questions(human_verified);
CREATE INDEX IF NOT EXISTS idx_golden_questions_quality_score ON golden_questions(quality_score);
CREATE INDEX IF NOT EXISTS idx_golden_questions_golden_pair_id ON golden_questions(golden_pair_id);

-- Add comments for documentation
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

