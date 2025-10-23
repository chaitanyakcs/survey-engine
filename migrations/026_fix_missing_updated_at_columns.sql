-- Migration: Fix missing updated_at columns in existing tables
-- Issue: Bootstrap schema expects updated_at columns but some tables were created without them
-- This migration is idempotent and safe to run multiple times

-- Add updated_at column to golden_sections if it doesn't exist
ALTER TABLE golden_sections 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Add updated_at column to golden_questions if it doesn't exist
ALTER TABLE golden_questions 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Add updated_at column to golden_example_states if it doesn't exist
ALTER TABLE golden_example_states 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Add updated_at column to retrieval_weights if it doesn't exist
ALTER TABLE retrieval_weights 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Add updated_at column to methodology_compatibility if it doesn't exist
ALTER TABLE methodology_compatibility 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Add updated_at column to survey_rules if it doesn't exist
ALTER TABLE survey_rules 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Add updated_at column to question_annotations if it doesn't exist
ALTER TABLE question_annotations 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Add updated_at column to section_annotations if it doesn't exist
ALTER TABLE section_annotations 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Add updated_at column to survey_annotations if it doesn't exist
ALTER TABLE survey_annotations 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Add updated_at column to human_reviews if it doesn't exist
ALTER TABLE human_reviews 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Add updated_at column to workflow_states if it doesn't exist
ALTER TABLE workflow_states 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Add updated_at column to settings if it doesn't exist
ALTER TABLE settings 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Add updated_at column to document_uploads if it doesn't exist
ALTER TABLE document_uploads 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Add updated_at column to llm_audit if it doesn't exist
ALTER TABLE llm_audit 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Add updated_at column to llm_hyperparameter_configs if it doesn't exist
ALTER TABLE llm_hyperparameter_configs 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Add updated_at column to llm_prompt_templates if it doesn't exist
ALTER TABLE llm_prompt_templates 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Add updated_at column to qnr_label_definitions if it doesn't exist
ALTER TABLE qnr_label_definitions 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Add updated_at column to qnr_tag_definitions if it doesn't exist
ALTER TABLE qnr_tag_definitions 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Add comments for documentation
COMMENT ON COLUMN golden_sections.updated_at IS 'Timestamp when the golden section was last updated';
COMMENT ON COLUMN golden_questions.updated_at IS 'Timestamp when the golden question was last updated';
COMMENT ON COLUMN golden_example_states.updated_at IS 'Timestamp when the golden example state was last updated';
COMMENT ON COLUMN retrieval_weights.updated_at IS 'Timestamp when the retrieval weight was last updated';
COMMENT ON COLUMN methodology_compatibility.updated_at IS 'Timestamp when the methodology compatibility was last updated';
COMMENT ON COLUMN survey_rules.updated_at IS 'Timestamp when the survey rule was last updated';
COMMENT ON COLUMN question_annotations.updated_at IS 'Timestamp when the question annotation was last updated';
COMMENT ON COLUMN section_annotations.updated_at IS 'Timestamp when the section annotation was last updated';
COMMENT ON COLUMN survey_annotations.updated_at IS 'Timestamp when the survey annotation was last updated';
COMMENT ON COLUMN human_reviews.updated_at IS 'Timestamp when the human review was last updated';
COMMENT ON COLUMN workflow_states.updated_at IS 'Timestamp when the workflow state was last updated';
COMMENT ON COLUMN settings.updated_at IS 'Timestamp when the setting was last updated';
COMMENT ON COLUMN document_uploads.updated_at IS 'Timestamp when the document upload was last updated';
COMMENT ON COLUMN llm_audit.updated_at IS 'Timestamp when the LLM audit record was last updated';
COMMENT ON COLUMN llm_hyperparameter_configs.updated_at IS 'Timestamp when the LLM hyperparameter config was last updated';
COMMENT ON COLUMN llm_prompt_templates.updated_at IS 'Timestamp when the LLM prompt template was last updated';
COMMENT ON COLUMN qnr_label_definitions.updated_at IS 'Timestamp when the QNR label definition was last updated';
COMMENT ON COLUMN qnr_tag_definitions.updated_at IS 'Timestamp when the QNR tag definition was last updated';
