-- ============================================================================
-- ADD SECTION_ID TO GOLDEN_QUESTIONS
-- ============================================================================
-- Adds section_id column to link golden questions to their QNR sections
-- ============================================================================

-- Add section_id column if not exists
ALTER TABLE golden_questions ADD COLUMN IF NOT EXISTS section_id INTEGER;

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_golden_questions_section_id ON golden_questions(section_id);

