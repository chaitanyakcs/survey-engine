-- Minimal Bootstrap Schema for Railway
-- This creates only the essential tables to get the app running

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Core Tables (minimal set)
CREATE TABLE IF NOT EXISTS rfqs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT,
    content TEXT,
    document_upload_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS surveys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rfq_id UUID REFERENCES rfqs(id),
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    raw_output JSONB,
    final_output JSONB,
    pillar_scores JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS edits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    survey_id UUID REFERENCES surveys(id),
    edit_type TEXT,
    edit_reason TEXT,
    before_text TEXT,
    after_text TEXT,
    annotation JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Golden Example Tables
CREATE TABLE IF NOT EXISTS golden_rfq_survey_pairs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT,
    rfq_text TEXT NOT NULL,
    rfq_embedding VECTOR(384),
    survey_json JSONB NOT NULL,
    methodology_tags TEXT[],
    industry_category VARCHAR(100),
    research_goal TEXT,
    quality_score DECIMAL(3,2) DEFAULT 0.0,
    usage_count INTEGER DEFAULT 0,
    human_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS golden_example_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    state_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Basic indexes
CREATE INDEX IF NOT EXISTS idx_surveys_rfq_id ON surveys(rfq_id);
CREATE INDEX IF NOT EXISTS idx_surveys_status ON surveys(status);
CREATE INDEX IF NOT EXISTS idx_edits_survey_id ON edits(survey_id);
CREATE INDEX IF NOT EXISTS idx_golden_rfq_survey_pairs_methodology_tags 
    ON golden_rfq_survey_pairs USING GIN(methodology_tags);

-- Vector index for similarity search
CREATE INDEX IF NOT EXISTS idx_golden_rfq_survey_pairs_rfq_embedding 
    ON golden_rfq_survey_pairs 
    USING ivfflat (rfq_embedding vector_cosine_ops) 
    WITH (lists = 100);
