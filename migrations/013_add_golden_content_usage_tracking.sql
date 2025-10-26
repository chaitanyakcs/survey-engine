-- ============================================================================
-- Migration 013: Add Golden Content Usage Tracking
-- Description: Track which surveys use specific golden questions and sections
-- Date: 2025-10-24
-- ============================================================================
-- This migration adds comprehensive usage tracking for golden questions and
-- sections, allowing the system to track which surveys used which golden
-- content, along with usage counts and timestamps.
-- ============================================================================

-- Golden Question Usage Tracking Table
CREATE TABLE IF NOT EXISTS golden_question_usage (
    id SERIAL PRIMARY KEY,
    golden_question_id UUID NOT NULL REFERENCES golden_questions(id) ON DELETE CASCADE,
    survey_id UUID NOT NULL REFERENCES surveys(id) ON DELETE CASCADE,
    used_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_question_survey_usage UNIQUE (golden_question_id, survey_id)
);

-- Indexes for efficient queries on golden_question_usage
CREATE INDEX IF NOT EXISTS idx_golden_question_usage_question_id 
    ON golden_question_usage(golden_question_id);
CREATE INDEX IF NOT EXISTS idx_golden_question_usage_survey_id 
    ON golden_question_usage(survey_id);
CREATE INDEX IF NOT EXISTS idx_golden_question_usage_used_at 
    ON golden_question_usage(used_at DESC);

-- Golden Section Usage Tracking Table
CREATE TABLE IF NOT EXISTS golden_section_usage (
    id SERIAL PRIMARY KEY,
    golden_section_id UUID NOT NULL REFERENCES golden_sections(id) ON DELETE CASCADE,
    survey_id UUID NOT NULL REFERENCES surveys(id) ON DELETE CASCADE,
    used_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_section_survey_usage UNIQUE (golden_section_id, survey_id)
);

-- Indexes for efficient queries on golden_section_usage
CREATE INDEX IF NOT EXISTS idx_golden_section_usage_section_id 
    ON golden_section_usage(golden_section_id);
CREATE INDEX IF NOT EXISTS idx_golden_section_usage_survey_id 
    ON golden_section_usage(survey_id);
CREATE INDEX IF NOT EXISTS idx_golden_section_usage_used_at 
    ON golden_section_usage(used_at DESC);

-- Add tracking fields to surveys table
DO $$ 
BEGIN
    -- Add used_golden_questions column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'surveys' AND column_name = 'used_golden_questions'
    ) THEN
        ALTER TABLE surveys ADD COLUMN used_golden_questions UUID[] DEFAULT '{}';
        RAISE NOTICE 'Added used_golden_questions column to surveys table';
    ELSE
        RAISE NOTICE 'used_golden_questions column already exists in surveys table';
    END IF;
    
    -- Add used_golden_sections column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'surveys' AND column_name = 'used_golden_sections'
    ) THEN
        ALTER TABLE surveys ADD COLUMN used_golden_sections UUID[] DEFAULT '{}';
        RAISE NOTICE 'Added used_golden_sections column to surveys table';
    ELSE
        RAISE NOTICE 'used_golden_sections column already exists in surveys table';
    END IF;
END $$;

-- Add comments for documentation
COMMENT ON TABLE golden_question_usage IS 'Tracks which surveys use which golden questions with timestamps';
COMMENT ON TABLE golden_section_usage IS 'Tracks which surveys use which golden sections with timestamps';
COMMENT ON COLUMN surveys.used_golden_questions IS 'Array of golden question UUIDs used in this survey';
COMMENT ON COLUMN surveys.used_golden_sections IS 'Array of golden section UUIDs used in this survey';

-- Verification queries (for manual testing)
-- SELECT COUNT(*) as golden_question_usage_count FROM golden_question_usage;
-- SELECT COUNT(*) as golden_section_usage_count FROM golden_section_usage;
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'surveys' AND column_name IN ('used_golden_questions', 'used_golden_sections');

