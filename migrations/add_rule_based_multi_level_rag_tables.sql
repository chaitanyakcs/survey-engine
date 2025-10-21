-- Migration: Add rule-based multi-level RAG tables (no vector dependencies)
-- Created: 2024-10-20
-- Description: Enables section-level and question-level RAG retrieval using rule-based matching

-- Create golden_sections table for section-level retrieval (rule-based)
CREATE TABLE IF NOT EXISTS golden_sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    section_id VARCHAR(255) NOT NULL,
    survey_id VARCHAR(255) NOT NULL,
    golden_pair_id UUID, -- Reference to golden pair (FK added later if needed)
    section_title VARCHAR(500),
    section_text TEXT NOT NULL,
    section_type VARCHAR(100), -- e.g., 'demographics', 'pricing', 'satisfaction', 'behavioral'
    methodology_tags TEXT[], -- Array of methodology tags for this section
    industry_keywords TEXT[], -- Array of industry-specific keywords
    question_patterns TEXT[], -- Array of question patterns found in this section
    quality_score DECIMAL(3, 2), -- Average quality from annotations
    usage_count INTEGER DEFAULT 0,
    human_verified BOOLEAN DEFAULT FALSE, -- True if manually created/verified
    labels JSONB, -- Labels from annotations
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create golden_questions table for question-level retrieval (rule-based)
CREATE TABLE IF NOT EXISTS golden_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id VARCHAR(255) NOT NULL,
    survey_id VARCHAR(255) NOT NULL,
    golden_pair_id UUID, -- Reference to golden pair (FK added later if needed)
    question_text TEXT NOT NULL,
    question_type VARCHAR(100), -- e.g., 'multiple_choice', 'rating_scale', 'open_text', 'yes_no'
    question_subtype VARCHAR(100), -- e.g., 'likert_5', 'likert_7', 'binary', 'text_input'
    methodology_tags TEXT[], -- Array of methodology tags for this question
    industry_keywords TEXT[], -- Array of industry-specific keywords
    question_patterns TEXT[], -- Array of question patterns/templates
    quality_score DECIMAL(3, 2), -- Average quality from annotations
    usage_count INTEGER DEFAULT 0,
    human_verified BOOLEAN DEFAULT FALSE, -- True if manually created/verified
    labels JSONB, -- Labels from annotations
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

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
