-- Migration: Add comprehensive LLM audit system
-- This migration creates a fundamental LLM auditing system that tracks all LLM interactions
-- regardless of purpose, with configurable hyperparameters and prompts

-- Main LLM audit table for tracking all LLM interactions
CREATE TABLE llm_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Core identification
    interaction_id VARCHAR(255) NOT NULL, -- Unique identifier for this LLM interaction
    parent_workflow_id VARCHAR(255), -- Optional parent workflow ID
    parent_survey_id VARCHAR(255), -- Optional parent survey ID
    parent_rfq_id UUID, -- Optional parent RFQ ID
    
    -- LLM Configuration
    model_name VARCHAR(100) NOT NULL, -- e.g., "openai/gpt-4o-mini", "meta/llama-2-70b-chat"
    model_provider VARCHAR(50) NOT NULL, -- e.g., "openai", "replicate", "anthropic"
    model_version VARCHAR(50), -- Specific version if available
    
    -- Purpose and Context
    purpose VARCHAR(100) NOT NULL, -- e.g., "survey_generation", "evaluation", "field_extraction", "document_parsing"
    sub_purpose VARCHAR(100), -- e.g., "content_validity", "methodological_rigor", "rfq_parsing"
    context_type VARCHAR(50), -- e.g., "generation", "evaluation", "validation", "analysis"
    
    -- Input/Output
    input_prompt TEXT NOT NULL, -- The actual prompt sent to LLM
    input_tokens INTEGER, -- Number of input tokens
    output_content TEXT, -- The response content from LLM
    output_tokens INTEGER, -- Number of output tokens
    
    -- Hyperparameters (configurable)
    temperature DECIMAL(3,2), -- 0.0 to 2.0
    top_p DECIMAL(3,2), -- 0.0 to 1.0
    max_tokens INTEGER,
    frequency_penalty DECIMAL(3,2), -- -2.0 to 2.0
    presence_penalty DECIMAL(3,2), -- -2.0 to 2.0
    stop_sequences JSONB, -- Array of stop sequences
    
    -- Performance Metrics
    response_time_ms INTEGER, -- Response time in milliseconds
    cost_usd DECIMAL(10,6), -- Cost in USD if available
    success BOOLEAN NOT NULL DEFAULT true,
    error_message TEXT, -- Error message if failed
    
    -- Metadata
    interaction_metadata JSONB, -- Additional context-specific metadata
    tags JSONB, -- Searchable tags for categorization
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Hyperparameter configuration table for different purposes
CREATE TABLE llm_hyperparameter_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Configuration identification
    config_name VARCHAR(100) NOT NULL UNIQUE, -- e.g., "survey_generation_default", "evaluation_rigorous"
    purpose VARCHAR(100) NOT NULL, -- e.g., "survey_generation", "evaluation"
    sub_purpose VARCHAR(100), -- e.g., "content_validity", "methodological_rigor"
    
    -- Hyperparameters
    temperature DECIMAL(3,2) DEFAULT 0.7,
    top_p DECIMAL(3,2) DEFAULT 0.9,
    max_tokens INTEGER DEFAULT 4000,
    frequency_penalty DECIMAL(3,2) DEFAULT 0.0,
    presence_penalty DECIMAL(3,2) DEFAULT 0.0,
    stop_sequences JSONB DEFAULT '[]'::jsonb,
    
    -- Model preferences
    preferred_models JSONB DEFAULT '[]'::jsonb, -- Array of preferred model names
    fallback_models JSONB DEFAULT '[]'::jsonb, -- Array of fallback model names
    
    -- Configuration metadata
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Prompt templates table for different purposes
CREATE TABLE llm_prompt_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Template identification
    template_name VARCHAR(100) NOT NULL UNIQUE, -- e.g., "survey_generation_base", "evaluation_comprehensive"
    purpose VARCHAR(100) NOT NULL, -- e.g., "survey_generation", "evaluation"
    sub_purpose VARCHAR(100), -- e.g., "content_validity", "methodological_rigor"
    
    -- Template content
    system_prompt_template TEXT NOT NULL, -- Template with placeholders
    user_prompt_template TEXT, -- Optional user prompt template
    template_variables JSONB DEFAULT '{}'::jsonb, -- Available template variables
    
    -- Template metadata
    description TEXT,
    version VARCHAR(20) DEFAULT '1.0',
    is_active BOOLEAN DEFAULT true,
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for efficient querying
CREATE INDEX idx_llm_audit_interaction_id ON llm_audit(interaction_id);
CREATE INDEX idx_llm_audit_parent_workflow_id ON llm_audit(parent_workflow_id);
CREATE INDEX idx_llm_audit_parent_survey_id ON llm_audit(parent_survey_id);
CREATE INDEX idx_llm_audit_parent_rfq_id ON llm_audit(parent_rfq_id);
CREATE INDEX idx_llm_audit_model_name ON llm_audit(model_name);
CREATE INDEX idx_llm_audit_purpose ON llm_audit(purpose);
CREATE INDEX idx_llm_audit_context_type ON llm_audit(context_type);
CREATE INDEX idx_llm_audit_created_at ON llm_audit(created_at);
CREATE INDEX idx_llm_audit_success ON llm_audit(success);
CREATE INDEX idx_llm_audit_cost_usd ON llm_audit(cost_usd);

-- GIN indexes for JSONB columns
CREATE INDEX idx_llm_audit_interaction_metadata ON llm_audit USING GIN(interaction_metadata);
CREATE INDEX idx_llm_audit_tags ON llm_audit USING GIN(tags);

-- Hyperparameter config indexes
CREATE INDEX idx_llm_hyperparameter_configs_purpose ON llm_hyperparameter_configs(purpose);
CREATE INDEX idx_llm_hyperparameter_configs_sub_purpose ON llm_hyperparameter_configs(sub_purpose);
CREATE INDEX idx_llm_hyperparameter_configs_is_active ON llm_hyperparameter_configs(is_active);
CREATE INDEX idx_llm_hyperparameter_configs_is_default ON llm_hyperparameter_configs(is_default);

-- Prompt template indexes
CREATE INDEX idx_llm_prompt_templates_purpose ON llm_prompt_templates(purpose);
CREATE INDEX idx_llm_prompt_templates_sub_purpose ON llm_prompt_templates(sub_purpose);
CREATE INDEX idx_llm_prompt_templates_is_active ON llm_prompt_templates(is_active);
CREATE INDEX idx_llm_prompt_templates_is_default ON llm_prompt_templates(is_default);

-- Add comments
COMMENT ON TABLE llm_audit IS 'Comprehensive audit table for all LLM interactions across the system';
COMMENT ON TABLE llm_hyperparameter_configs IS 'Configuration table for LLM hyperparameters by purpose';
COMMENT ON TABLE llm_prompt_templates IS 'Template table for LLM prompts by purpose';

-- Insert default hyperparameter configurations (with conflict handling)
INSERT INTO llm_hyperparameter_configs (config_name, purpose, sub_purpose, temperature, top_p, max_tokens, frequency_penalty, presence_penalty, description, is_default) VALUES
('survey_generation_default', 'survey_generation', NULL, 0.7, 0.9, 4000, 0.0, 0.0, 'Default configuration for survey generation', true),
('evaluation_comprehensive', 'evaluation', 'comprehensive', 0.3, 0.9, 4000, 0.0, 0.0, 'Configuration for comprehensive evaluation', true),
('evaluation_content_validity', 'evaluation', 'content_validity', 0.2, 0.8, 2000, 0.0, 0.0, 'Configuration for content validity evaluation', false),
('evaluation_methodological_rigor', 'evaluation', 'methodological_rigor', 0.2, 0.8, 2000, 0.0, 0.0, 'Configuration for methodological rigor evaluation', false),
('field_extraction_default', 'field_extraction', NULL, 0.1, 0.9, 1000, 0.0, 0.0, 'Default configuration for field extraction', true),
('document_parsing_default', 'document_parsing', NULL, 0.1, 0.9, 2000, 0.0, 0.0, 'Default configuration for document parsing', true)
ON CONFLICT (config_name) DO NOTHING;

-- Insert default prompt templates (with conflict handling)
INSERT INTO llm_prompt_templates (template_name, purpose, sub_purpose, system_prompt_template, description, is_default) VALUES
('survey_generation_base', 'survey_generation', NULL, 'You are an expert survey researcher. Generate a comprehensive survey based on the provided RFQ and context.', 'Base template for survey generation', true),
('evaluation_comprehensive', 'evaluation', 'comprehensive', 'You are an expert survey evaluator. Evaluate the survey across all quality pillars.', 'Template for comprehensive evaluation', true),
('field_extraction_base', 'field_extraction', NULL, 'You are an expert at extracting structured data from documents. Extract the requested fields accurately.', 'Base template for field extraction', true),
('document_parsing_base', 'document_parsing', NULL, 'You are an expert document parser. Analyze the document and extract relevant information for survey generation.', 'Base template for document parsing', true)
ON CONFLICT (template_name) DO NOTHING;
