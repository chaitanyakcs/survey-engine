-- Migration: Add golden_sections and golden_questions tables for multi-level retrieval
-- Created: 2024-10-20
-- Description: Enables section-level and question-level RAG retrieval

-- Create golden_sections table for section-level retrieval
CREATE TABLE IF NOT EXISTS golden_sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    section_id VARCHAR(255) NOT NULL,
    survey_id VARCHAR(255) NOT NULL,
    golden_pair_id UUID REFERENCES golden_rfq_survey_pairs(id) ON DELETE CASCADE,
    section_title VARCHAR(500),
    section_text TEXT NOT NULL,
    section_embedding VECTOR(384),
    section_type VARCHAR(100), -- e.g., 'demographics', 'pricing', 'satisfaction'
    methodology_tags TEXT[], -- Array of methodology tags for this section
    quality_score DECIMAL(3, 2), -- Average quality from annotations
    usage_count INTEGER DEFAULT 0,
    human_verified BOOLEAN DEFAULT FALSE, -- True if manually created/verified
    labels JSONB, -- Labels from annotations
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create golden_questions table for question-level retrieval
CREATE TABLE IF NOT EXISTS golden_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id VARCHAR(255) NOT NULL,
    survey_id VARCHAR(255) NOT NULL,
    golden_pair_id UUID REFERENCES golden_rfq_survey_pairs(id) ON DELETE CASCADE,
    section_id VARCHAR(255), -- Reference to section this question belongs to
    question_text TEXT NOT NULL,
    question_embedding VECTOR(384),
    question_type VARCHAR(100), -- e.g., 'multiple_choice', 'rating_scale', 'open_text'
    methodology_tags TEXT[], -- Array of methodology tags for this question
    quality_score DECIMAL(3, 2), -- Average quality from annotations
    usage_count INTEGER DEFAULT 0,
    human_verified BOOLEAN DEFAULT FALSE, -- True if manually created/verified
    labels JSONB, -- Labels from annotations
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_golden_sections_survey_id ON golden_sections(survey_id);
CREATE INDEX IF NOT EXISTS idx_golden_sections_golden_pair_id ON golden_sections(golden_pair_id);
CREATE INDEX IF NOT EXISTS idx_golden_sections_section_type ON golden_sections(section_type);
CREATE INDEX IF NOT EXISTS idx_golden_sections_quality_score ON golden_sections(quality_score);
CREATE INDEX IF NOT EXISTS idx_golden_sections_human_verified ON golden_sections(human_verified);
CREATE INDEX IF NOT EXISTS idx_golden_sections_usage_count ON golden_sections(usage_count);

CREATE INDEX IF NOT EXISTS idx_golden_questions_survey_id ON golden_questions(survey_id);
CREATE INDEX IF NOT EXISTS idx_golden_questions_golden_pair_id ON golden_questions(golden_pair_id);
CREATE INDEX IF NOT EXISTS idx_golden_questions_section_id ON golden_questions(section_id);
CREATE INDEX IF NOT EXISTS idx_golden_questions_question_type ON golden_questions(question_type);
CREATE INDEX IF NOT EXISTS idx_golden_questions_quality_score ON golden_questions(quality_score);
CREATE INDEX IF NOT EXISTS idx_golden_questions_human_verified ON golden_questions(human_verified);
CREATE INDEX IF NOT EXISTS idx_golden_questions_usage_count ON golden_questions(usage_count);

-- Create vector similarity indexes for fast retrieval
CREATE INDEX IF NOT EXISTS idx_golden_sections_embedding_cosine 
ON golden_sections USING ivfflat (section_embedding vector_cosine_ops) 
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_golden_questions_embedding_cosine 
ON golden_questions USING ivfflat (question_embedding vector_cosine_ops) 
WITH (lists = 100);

-- Add comments for documentation
COMMENT ON TABLE golden_sections IS 'Stores individual sections from golden surveys for section-level RAG retrieval';
COMMENT ON TABLE golden_questions IS 'Stores individual questions from golden surveys for question-level RAG retrieval';

COMMENT ON COLUMN golden_sections.section_embedding IS 'Vector embedding for semantic similarity search';
COMMENT ON COLUMN golden_sections.quality_score IS 'Average quality score from section annotations (0.0-1.0)';
COMMENT ON COLUMN golden_sections.human_verified IS 'True if this section was manually created/verified by a human';
COMMENT ON COLUMN golden_sections.labels IS 'Labels from annotations (e.g., methodology, quality indicators)';

COMMENT ON COLUMN golden_questions.question_embedding IS 'Vector embedding for semantic similarity search';
COMMENT ON COLUMN golden_questions.quality_score IS 'Average quality score from question annotations (0.0-1.0)';
COMMENT ON COLUMN golden_questions.human_verified IS 'True if this question was manually created/verified by a human';
COMMENT ON COLUMN golden_questions.labels IS 'Labels from annotations (e.g., methodology, quality indicators)';
