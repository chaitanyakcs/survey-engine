-- ============================================================================
-- COMPREHENSIVE BOOTSTRAP SCHEMA
-- Survey Engine Database - Complete Schema Definition
-- Version: 1.0.0
-- Generated from: src/database/models.py
-- ============================================================================
-- This file defines the complete database schema for the Survey Engine
-- application. It includes all tables, indexes, constraints, and foreign keys.
-- All operations are idempotent using IF NOT EXISTS.
-- ============================================================================

-- Step 1: Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- RFQs Table
CREATE TABLE IF NOT EXISTS rfqs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT,
    description TEXT NOT NULL,
    product_category TEXT,
    target_segment TEXT,
    research_goal TEXT,
    embedding VECTOR(384),
    enhanced_rfq_data JSONB,
    document_upload_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rfqs_created_at ON rfqs(created_at);

-- Add document_upload_id column if it doesn't exist (for existing tables)
-- Note: This will fail silently if column already exists, which is fine
ALTER TABLE rfqs ADD COLUMN IF NOT EXISTS document_upload_id UUID;

CREATE INDEX IF NOT EXISTS idx_rfqs_document_upload_id ON rfqs(document_upload_id);

-- Surveys Table
CREATE TABLE IF NOT EXISTS surveys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rfq_id UUID REFERENCES rfqs(id),
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    raw_output JSONB,
    final_output JSONB,
    golden_similarity_score DECIMAL(3,2),
    used_golden_examples UUID[],
    used_golden_questions UUID[] DEFAULT '{}',
    used_golden_sections UUID[] DEFAULT '{}',
    cleanup_minutes_actual INTEGER,
    model_version TEXT,
    pillar_scores JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_surveys_rfq_id ON surveys(rfq_id);
CREATE INDEX IF NOT EXISTS idx_surveys_status ON surveys(status);
CREATE INDEX IF NOT EXISTS idx_surveys_created_at ON surveys(created_at);

-- Edits Table
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

CREATE INDEX IF NOT EXISTS idx_edits_survey_id ON edits(survey_id);
CREATE INDEX IF NOT EXISTS idx_edits_created_at ON edits(created_at);

-- ============================================================================
-- GOLDEN EXAMPLE TABLES
-- ============================================================================

-- Golden RFQ Survey Pairs Table
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

CREATE INDEX IF NOT EXISTS idx_golden_rfq_survey_pairs_methodology_tags 
    ON golden_rfq_survey_pairs USING GIN(methodology_tags);
CREATE INDEX IF NOT EXISTS idx_golden_rfq_survey_pairs_industry_category 
    ON golden_rfq_survey_pairs(industry_category);
CREATE INDEX IF NOT EXISTS idx_golden_rfq_survey_pairs_quality_score 
    ON golden_rfq_survey_pairs(quality_score);
CREATE INDEX IF NOT EXISTS idx_golden_rfq_survey_pairs_created_at 
    ON golden_rfq_survey_pairs(created_at);

-- Create vector index for similarity search
CREATE INDEX IF NOT EXISTS idx_golden_rfq_survey_pairs_rfq_embedding 
    ON golden_rfq_survey_pairs 
    USING ivfflat (rfq_embedding vector_cosine_ops) 
    WITH (lists = 100);

-- Golden Sections Table
CREATE TABLE IF NOT EXISTS golden_sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    section_id VARCHAR(255) NOT NULL,
    survey_id VARCHAR(255) NOT NULL,
    golden_pair_id UUID REFERENCES golden_rfq_survey_pairs(id) ON DELETE CASCADE,
    annotation_id INTEGER,
    section_title VARCHAR(500),
    section_text TEXT NOT NULL,
    section_type VARCHAR(100),
    methodology_tags TEXT[],
    industry_keywords TEXT[],
    question_patterns TEXT[],
    quality_score DECIMAL(3,2),
    usage_count INTEGER DEFAULT 0,
    human_verified BOOLEAN DEFAULT FALSE,
    labels JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_golden_sections_golden_pair_id ON golden_sections(golden_pair_id);
CREATE INDEX IF NOT EXISTS idx_golden_sections_section_type ON golden_sections(section_type);
CREATE INDEX IF NOT EXISTS idx_golden_sections_methodology_tags 
    ON golden_sections USING GIN(methodology_tags);
CREATE INDEX IF NOT EXISTS idx_golden_sections_quality_score ON golden_sections(quality_score);

-- Golden Questions Table
CREATE TABLE IF NOT EXISTS golden_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id VARCHAR(255) NOT NULL,
    survey_id VARCHAR(255) NOT NULL,
    golden_pair_id UUID REFERENCES golden_rfq_survey_pairs(id) ON DELETE CASCADE,
    annotation_id INTEGER,
    question_text TEXT NOT NULL,
    question_type VARCHAR(100),
    question_subtype VARCHAR(100),
    methodology_tags TEXT[],
    industry_keywords TEXT[],
    question_patterns TEXT[],
    quality_score DECIMAL(3,2),
    relevance_score DECIMAL(3,2),
    usage_count INTEGER DEFAULT 0,
    human_verified BOOLEAN DEFAULT FALSE,
    labels JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_golden_questions_golden_pair_id ON golden_questions(golden_pair_id);
CREATE INDEX IF NOT EXISTS idx_golden_questions_question_type ON golden_questions(question_type);
CREATE INDEX IF NOT EXISTS idx_golden_questions_methodology_tags 
    ON golden_questions USING GIN(methodology_tags);
CREATE INDEX IF NOT EXISTS idx_golden_questions_quality_score ON golden_questions(quality_score);

-- Golden Question Usage Tracking Table
CREATE TABLE IF NOT EXISTS golden_question_usage (
    id SERIAL PRIMARY KEY,
    golden_question_id UUID NOT NULL REFERENCES golden_questions(id) ON DELETE CASCADE,
    survey_id UUID NOT NULL REFERENCES surveys(id) ON DELETE CASCADE,
    used_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_question_survey_usage UNIQUE (golden_question_id, survey_id)
);

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

CREATE INDEX IF NOT EXISTS idx_golden_section_usage_section_id 
    ON golden_section_usage(golden_section_id);
CREATE INDEX IF NOT EXISTS idx_golden_section_usage_survey_id 
    ON golden_section_usage(survey_id);
CREATE INDEX IF NOT EXISTS idx_golden_section_usage_used_at 
    ON golden_section_usage(used_at DESC);

-- Golden Example States Table
CREATE TABLE IF NOT EXISTS golden_example_states (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL UNIQUE,
    state_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_golden_example_states_session_id ON golden_example_states(session_id);
CREATE INDEX IF NOT EXISTS idx_golden_example_states_created_at ON golden_example_states(created_at);

-- ============================================================================
-- RAG CONFIGURATION TABLES
-- ============================================================================

-- Retrieval Weights Table
CREATE TABLE IF NOT EXISTS retrieval_weights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    context_type VARCHAR(50) NOT NULL DEFAULT 'global',
    context_value VARCHAR(100) NOT NULL DEFAULT 'default',
    semantic_weight DECIMAL(3,2) DEFAULT 0.40,
    methodology_weight DECIMAL(3,2) DEFAULT 0.25,
    industry_weight DECIMAL(3,2) DEFAULT 0.15,
    quality_weight DECIMAL(3,2) DEFAULT 0.10,
    annotation_weight DECIMAL(3,2) DEFAULT 0.10,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_retrieval_weights_context_type ON retrieval_weights(context_type);
CREATE INDEX IF NOT EXISTS idx_retrieval_weights_enabled ON retrieval_weights(enabled);

-- Methodology Compatibility Table
CREATE TABLE IF NOT EXISTS methodology_compatibility (
    methodology_a VARCHAR(50) NOT NULL,
    methodology_b VARCHAR(50) NOT NULL,
    compatibility_score DECIMAL(3,2) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (methodology_a, methodology_b),
    CHECK (methodology_a != methodology_b),
    CHECK (compatibility_score >= 0 AND compatibility_score <= 1)
);

CREATE INDEX IF NOT EXISTS idx_methodology_compatibility_score 
    ON methodology_compatibility(compatibility_score);

-- ============================================================================
-- RULES AND VALIDATION TABLES
-- ============================================================================

-- Survey Rules Table
CREATE TABLE IF NOT EXISTS survey_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_type VARCHAR(50) NOT NULL,
    category VARCHAR(100) NOT NULL,
    rule_name VARCHAR(200) NOT NULL,
    rule_description TEXT,
    rule_content JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100) DEFAULT 'system'
);

CREATE INDEX IF NOT EXISTS idx_survey_rules_type_category ON survey_rules(rule_type, category);
CREATE INDEX IF NOT EXISTS idx_survey_rules_active ON survey_rules(is_active);
CREATE INDEX IF NOT EXISTS idx_survey_rules_priority ON survey_rules(priority);

-- Rule Validations Table
CREATE TABLE IF NOT EXISTS rule_validations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    survey_id UUID REFERENCES surveys(id) NOT NULL,
    rule_id UUID REFERENCES survey_rules(id) NOT NULL,
    validation_passed BOOLEAN NOT NULL,
    error_message TEXT,
    warning_message TEXT,
    validation_details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rule_validations_survey ON rule_validations(survey_id);
CREATE INDEX IF NOT EXISTS idx_rule_validations_rule ON rule_validations(rule_id);
CREATE INDEX IF NOT EXISTS idx_rule_validations_passed ON rule_validations(validation_passed);

-- ============================================================================
-- ANNOTATION TABLES
-- ============================================================================

-- Question Annotations Table
CREATE TABLE IF NOT EXISTS question_annotations (
    id SERIAL PRIMARY KEY,
    question_id VARCHAR(255) NOT NULL,
    survey_id VARCHAR(255) NOT NULL,
    required BOOLEAN NOT NULL DEFAULT TRUE,
    quality INTEGER NOT NULL,
    relevant INTEGER NOT NULL,
    methodological_rigor INTEGER NOT NULL,
    content_validity INTEGER NOT NULL,
    respondent_experience INTEGER NOT NULL,
    analytical_value INTEGER NOT NULL,
    business_impact INTEGER NOT NULL,
    comment TEXT,
    annotator_id VARCHAR(255),
    labels JSONB,
    removed_labels JSONB,
    advanced_labels JSONB,
    industry_classification VARCHAR(100),
    respondent_type VARCHAR(100),
    methodology_tags VARCHAR(255)[],
    is_mandatory BOOLEAN DEFAULT FALSE,
    compliance_status VARCHAR(50),
    ai_generated BOOLEAN NOT NULL DEFAULT FALSE,
    ai_confidence DECIMAL(3,2),
    human_verified BOOLEAN NOT NULL DEFAULT FALSE,
    generation_timestamp TIMESTAMP WITH TIME ZONE,
    human_overridden BOOLEAN NOT NULL DEFAULT FALSE,
    override_timestamp TIMESTAMP WITH TIME ZONE,
    original_ai_quality INTEGER,
    original_ai_relevant INTEGER,
    original_ai_comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT check_quality_range CHECK (quality >= 1 AND quality <= 5),
    CONSTRAINT check_relevant_range CHECK (relevant >= 1 AND relevant <= 5),
    CONSTRAINT check_methodological_rigor_range CHECK (methodological_rigor >= 1 AND methodological_rigor <= 5),
    CONSTRAINT check_content_validity_range CHECK (content_validity >= 1 AND content_validity <= 5),
    CONSTRAINT check_respondent_experience_range CHECK (respondent_experience >= 1 AND respondent_experience <= 5),
    CONSTRAINT check_analytical_value_range CHECK (analytical_value >= 1 AND analytical_value <= 5),
    CONSTRAINT check_business_impact_range CHECK (business_impact >= 1 AND business_impact <= 5),
    CONSTRAINT check_ai_confidence_range CHECK (ai_confidence >= 0.00 AND ai_confidence <= 1.00)
);

CREATE INDEX IF NOT EXISTS idx_question_annotations_survey_id ON question_annotations(survey_id);
CREATE INDEX IF NOT EXISTS idx_question_annotations_annotator_id ON question_annotations(annotator_id);
CREATE INDEX IF NOT EXISTS idx_question_annotations_ai_generated ON question_annotations(ai_generated);
CREATE INDEX IF NOT EXISTS idx_question_annotations_human_overridden ON question_annotations(human_overridden);
CREATE UNIQUE INDEX IF NOT EXISTS idx_question_annotations_unique 
    ON question_annotations(question_id, annotator_id);

-- Section Annotations Table
CREATE TABLE IF NOT EXISTS section_annotations (
    id SERIAL PRIMARY KEY,
    section_id INTEGER NOT NULL,
    survey_id VARCHAR(255) NOT NULL,
    quality INTEGER NOT NULL,
    relevant INTEGER NOT NULL,
    methodological_rigor INTEGER NOT NULL,
    content_validity INTEGER NOT NULL,
    respondent_experience INTEGER NOT NULL,
    analytical_value INTEGER NOT NULL,
    business_impact INTEGER NOT NULL,
    comment TEXT,
    annotator_id VARCHAR(255),
    labels JSONB,
    section_classification VARCHAR(100),
    mandatory_elements JSONB,
    compliance_score INTEGER,
    ai_generated BOOLEAN NOT NULL DEFAULT FALSE,
    ai_confidence DECIMAL(3,2),
    human_verified BOOLEAN NOT NULL DEFAULT FALSE,
    generation_timestamp TIMESTAMP WITH TIME ZONE,
    human_overridden BOOLEAN NOT NULL DEFAULT FALSE,
    override_timestamp TIMESTAMP WITH TIME ZONE,
    original_ai_quality INTEGER,
    original_ai_relevant INTEGER,
    original_ai_comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT check_section_quality_range CHECK (quality >= 1 AND quality <= 5),
    CONSTRAINT check_section_relevant_range CHECK (relevant >= 1 AND relevant <= 5),
    CONSTRAINT check_section_methodological_rigor_range CHECK (methodological_rigor >= 1 AND methodological_rigor <= 5),
    CONSTRAINT check_section_content_validity_range CHECK (content_validity >= 1 AND content_validity <= 5),
    CONSTRAINT check_section_respondent_experience_range CHECK (respondent_experience >= 1 AND respondent_experience <= 5),
    CONSTRAINT check_section_analytical_value_range CHECK (analytical_value >= 1 AND analytical_value <= 5),
    CONSTRAINT check_section_business_impact_range CHECK (business_impact >= 1 AND business_impact <= 5),
    CONSTRAINT check_section_ai_confidence_range CHECK (ai_confidence >= 0.00 AND ai_confidence <= 1.00)
);

CREATE INDEX IF NOT EXISTS idx_section_annotations_survey_id ON section_annotations(survey_id);
CREATE INDEX IF NOT EXISTS idx_section_annotations_annotator_id ON section_annotations(annotator_id);
CREATE INDEX IF NOT EXISTS idx_section_annotations_ai_generated ON section_annotations(ai_generated);
CREATE INDEX IF NOT EXISTS idx_section_annotations_human_overridden ON section_annotations(human_overridden);
CREATE UNIQUE INDEX IF NOT EXISTS idx_section_annotations_unique 
    ON section_annotations(section_id, annotator_id);

-- Survey Annotations Table
CREATE TABLE IF NOT EXISTS survey_annotations (
    id SERIAL PRIMARY KEY,
    survey_id VARCHAR(255) NOT NULL UNIQUE,
    overall_comment TEXT,
    annotator_id VARCHAR(255),
    labels JSONB,
    detected_labels JSONB,
    compliance_report JSONB,
    advanced_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_survey_annotations_annotator_id ON survey_annotations(annotator_id);
CREATE INDEX IF NOT EXISTS idx_survey_annotations_survey_id ON survey_annotations(survey_id);

-- ============================================================================
-- WORKFLOW AND STATE MANAGEMENT TABLES
-- ============================================================================

-- Human Reviews Table
CREATE TABLE IF NOT EXISTS human_reviews (
    id SERIAL PRIMARY KEY,
    workflow_id VARCHAR(255) NOT NULL UNIQUE,
    survey_id VARCHAR(255),
    review_status VARCHAR(50) NOT NULL DEFAULT 'pending',
    prompt_data TEXT NOT NULL,
    original_rfq TEXT NOT NULL,
    reviewer_id VARCHAR(255),
    review_deadline TIMESTAMP WITH TIME ZONE,
    reviewer_notes TEXT,
    approval_reason TEXT,
    rejection_reason TEXT,
    edited_prompt_data TEXT,
    original_prompt_data TEXT,
    prompt_edited BOOLEAN DEFAULT FALSE NOT NULL,
    prompt_edit_timestamp TIMESTAMP WITH TIME ZONE,
    edited_by VARCHAR(255),
    edit_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT check_review_status CHECK (
        review_status IN ('pending', 'in_progress', 'approved', 'rejected', 'expired')
    )
);

CREATE INDEX IF NOT EXISTS idx_human_reviews_workflow_id ON human_reviews(workflow_id);
CREATE INDEX IF NOT EXISTS idx_human_reviews_status ON human_reviews(review_status);
CREATE INDEX IF NOT EXISTS idx_human_reviews_reviewer_id ON human_reviews(reviewer_id);
CREATE INDEX IF NOT EXISTS idx_human_reviews_created_at ON human_reviews(created_at);
CREATE INDEX IF NOT EXISTS idx_human_reviews_prompt_edited ON human_reviews(prompt_edited);
CREATE INDEX IF NOT EXISTS idx_human_reviews_edited_by ON human_reviews(edited_by);
CREATE INDEX IF NOT EXISTS idx_human_reviews_edit_timestamp ON human_reviews(prompt_edit_timestamp);

-- Workflow States Table
CREATE TABLE IF NOT EXISTS workflow_states (
    id SERIAL PRIMARY KEY,
    workflow_id VARCHAR(255) NOT NULL UNIQUE,
    survey_id VARCHAR(255),
    state_data TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_workflow_states_workflow_id ON workflow_states(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_states_survey_id ON workflow_states(survey_id);
CREATE INDEX IF NOT EXISTS idx_workflow_states_created_at ON workflow_states(created_at);

-- ============================================================================
-- SETTINGS AND CONFIGURATION TABLES
-- ============================================================================

-- Settings Table
CREATE TABLE IF NOT EXISTS settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) NOT NULL UNIQUE,
    setting_value JSONB NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_settings_key ON settings(setting_key);
CREATE INDEX IF NOT EXISTS idx_settings_active ON settings(is_active);

-- ============================================================================
-- DOCUMENT MANAGEMENT TABLES
-- ============================================================================

-- Document Uploads Table
CREATE TABLE IF NOT EXISTS document_uploads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255),
    file_size INTEGER,
    content_type VARCHAR(100),
    session_id VARCHAR(100),
    uploaded_by VARCHAR(255),
    upload_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processing_status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    analysis_result JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT check_processing_status CHECK (
        processing_status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')
    )
);

CREATE INDEX IF NOT EXISTS idx_document_uploads_status ON document_uploads(processing_status);
CREATE INDEX IF NOT EXISTS idx_document_uploads_timestamp ON document_uploads(upload_timestamp);
CREATE INDEX IF NOT EXISTS idx_document_uploads_filename ON document_uploads(original_filename);
CREATE INDEX IF NOT EXISTS idx_document_uploads_session_id ON document_uploads(session_id);

-- Document RFQ Mappings Table
CREATE TABLE IF NOT EXISTS document_rfq_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES document_uploads(id) NOT NULL,
    rfq_id UUID REFERENCES rfqs(id) NOT NULL,
    mapping_data JSONB NOT NULL,
    confidence_score DECIMAL(3,2) DEFAULT 0.0,
    fields_mapped JSONB,
    user_corrections JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_document_rfq_mappings_document_id ON document_rfq_mappings(document_id);
CREATE INDEX IF NOT EXISTS idx_document_rfq_mappings_rfq_id ON document_rfq_mappings(rfq_id);
CREATE INDEX IF NOT EXISTS idx_document_rfq_mappings_confidence ON document_rfq_mappings(confidence_score);
CREATE UNIQUE INDEX IF NOT EXISTS idx_document_rfq_mappings_unique 
    ON document_rfq_mappings(document_id, rfq_id);

-- ============================================================================
-- LLM AUDIT AND CONFIGURATION TABLES
-- ============================================================================

-- LLM Audit Table
CREATE TABLE IF NOT EXISTS llm_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interaction_id VARCHAR(255) NOT NULL,
    parent_workflow_id VARCHAR(255),
    parent_survey_id VARCHAR(255),
    parent_rfq_id UUID,
    model_name VARCHAR(100) NOT NULL,
    model_provider VARCHAR(50) NOT NULL,
    model_version VARCHAR(50),
    purpose VARCHAR(100) NOT NULL,
    sub_purpose VARCHAR(100),
    context_type VARCHAR(50),
    temperature DECIMAL(3,2),
    top_p DECIMAL(3,2),
    max_tokens INTEGER,
    frequency_penalty DECIMAL(3,2),
    presence_penalty DECIMAL(3,2),
    stop_sequences JSONB,
    input_prompt TEXT NOT NULL,
    input_tokens INTEGER,
    output_content TEXT,
    output_tokens INTEGER,
    response_time_ms INTEGER,
    cost_usd DECIMAL(10,6),
    success BOOLEAN NOT NULL DEFAULT TRUE,
    error_message TEXT,
    raw_response TEXT,
    interaction_metadata JSONB,
    tags JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_llm_audit_interaction_id ON llm_audit(interaction_id);
CREATE INDEX IF NOT EXISTS idx_llm_audit_parent_workflow_id ON llm_audit(parent_workflow_id);
CREATE INDEX IF NOT EXISTS idx_llm_audit_parent_survey_id ON llm_audit(parent_survey_id);
CREATE INDEX IF NOT EXISTS idx_llm_audit_parent_rfq_id ON llm_audit(parent_rfq_id);
CREATE INDEX IF NOT EXISTS idx_llm_audit_model_name ON llm_audit(model_name);
CREATE INDEX IF NOT EXISTS idx_llm_audit_model_provider ON llm_audit(model_provider);
CREATE INDEX IF NOT EXISTS idx_llm_audit_purpose ON llm_audit(purpose);
CREATE INDEX IF NOT EXISTS idx_llm_audit_created_at ON llm_audit(created_at);
CREATE INDEX IF NOT EXISTS idx_llm_audit_updated_at ON llm_audit(updated_at);

-- LLM Hyperparameter Config Table
CREATE TABLE IF NOT EXISTS llm_hyperparameter_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_name VARCHAR(100) NOT NULL UNIQUE,
    purpose VARCHAR(100) NOT NULL,
    sub_purpose VARCHAR(100),
    temperature DECIMAL(3,2) DEFAULT 0.7,
    top_p DECIMAL(3,2) DEFAULT 0.9,
    max_tokens INTEGER DEFAULT 4000,
    frequency_penalty DECIMAL(3,2) DEFAULT 0.0,
    presence_penalty DECIMAL(3,2) DEFAULT 0.0,
    stop_sequences JSONB DEFAULT '[]'::jsonb,
    preferred_models JSONB DEFAULT '[]'::jsonb,
    fallback_models JSONB DEFAULT '[]'::jsonb,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_llm_hyperparameter_configs_name ON llm_hyperparameter_configs(config_name);
CREATE INDEX IF NOT EXISTS idx_llm_hyperparameter_configs_purpose ON llm_hyperparameter_configs(purpose);
CREATE INDEX IF NOT EXISTS idx_llm_hyperparameter_configs_sub_purpose ON llm_hyperparameter_configs(sub_purpose);
CREATE INDEX IF NOT EXISTS idx_llm_hyperparameter_configs_is_active ON llm_hyperparameter_configs(is_active);
CREATE INDEX IF NOT EXISTS idx_llm_hyperparameter_configs_is_default ON llm_hyperparameter_configs(is_default);

-- LLM Prompt Template Table
CREATE TABLE IF NOT EXISTS llm_prompt_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_name VARCHAR(100) NOT NULL UNIQUE,
    purpose VARCHAR(100) NOT NULL,
    sub_purpose VARCHAR(100),
    system_prompt_template TEXT NOT NULL,
    user_prompt_template TEXT,
    template_variables JSONB DEFAULT '{}'::jsonb,
    description TEXT,
    version VARCHAR(20) DEFAULT '1.0',
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_llm_prompt_templates_name ON llm_prompt_templates(template_name);
CREATE INDEX IF NOT EXISTS idx_llm_prompt_templates_purpose ON llm_prompt_templates(purpose);
CREATE INDEX IF NOT EXISTS idx_llm_prompt_templates_sub_purpose ON llm_prompt_templates(sub_purpose);
CREATE INDEX IF NOT EXISTS idx_llm_prompt_templates_is_active ON llm_prompt_templates(is_active);
CREATE INDEX IF NOT EXISTS idx_llm_prompt_templates_is_default ON llm_prompt_templates(is_default);

-- ============================================================================
-- QNR TAXONOMY TABLES (Replaced with newer implementation below)
-- ============================================================================
-- Note: Old qnr_label_definitions and qnr_tag_definitions tables removed
-- New QNR taxonomy uses qnr_sections, qnr_labels, qnr_label_history tables

-- ============================================================================
-- PERFORMANCE INDEXES FOR AI ANNOTATIONS
-- ============================================================================

-- Question annotations performance indexes
CREATE INDEX IF NOT EXISTS idx_question_annotations_ai_confidence ON question_annotations (ai_confidence) WHERE ai_confidence IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_question_annotations_ai_verified ON question_annotations (human_verified) WHERE human_verified = true;
CREATE INDEX IF NOT EXISTS idx_question_annotations_ai_overridden ON question_annotations (human_overridden) WHERE human_overridden = true;
CREATE INDEX IF NOT EXISTS idx_question_annotations_annotator_current_user ON question_annotations (annotator_id) WHERE annotator_id = 'current-user';

-- Section annotations performance indexes  
CREATE INDEX IF NOT EXISTS idx_section_annotations_ai_confidence ON section_annotations (ai_confidence) WHERE ai_confidence IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_section_annotations_ai_verified ON section_annotations (human_verified) WHERE human_verified = true;
CREATE INDEX IF NOT EXISTS idx_section_annotations_ai_overridden ON section_annotations (human_overridden) WHERE human_overridden = true;
CREATE INDEX IF NOT EXISTS idx_section_annotations_annotator_current_user ON section_annotations (annotator_id) WHERE annotator_id = 'current-user';

-- ============================================================================
-- QNR TAXONOMY TABLES
-- ============================================================================

-- QNR Sections Table
CREATE TABLE IF NOT EXISTS qnr_sections (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    display_order INTEGER NOT NULL,
    mandatory BOOLEAN DEFAULT TRUE,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- QNR Labels Table
CREATE TABLE IF NOT EXISTS qnr_labels (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    category VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    mandatory BOOLEAN DEFAULT FALSE,
    label_type VARCHAR(20) NOT NULL,
    applicable_labels TEXT[],
    detection_patterns TEXT[],
    section_id INTEGER NOT NULL REFERENCES qnr_sections(id),
    display_order INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- QNR Label History Table (Audit Trail)
CREATE TABLE IF NOT EXISTS qnr_label_history (
    id SERIAL PRIMARY KEY,
    label_id INTEGER REFERENCES qnr_labels(id),
    changed_by VARCHAR(255),
    change_type VARCHAR(50),
    old_value JSONB,
    new_value JSONB,
    changed_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for QNR tables
CREATE INDEX IF NOT EXISTS idx_qnr_labels_category ON qnr_labels(category);
CREATE INDEX IF NOT EXISTS idx_qnr_labels_section_id ON qnr_labels(section_id);
CREATE INDEX IF NOT EXISTS idx_qnr_labels_mandatory ON qnr_labels(mandatory);
CREATE INDEX IF NOT EXISTS idx_qnr_labels_active ON qnr_labels(active);

-- Seed QNR Sections (idempotent)
INSERT INTO qnr_sections (id, name, description, display_order, mandatory) VALUES
(1, 'Sample Plan', 'Sample plan and quotas', 1, TRUE),
(2, 'Screener Recruitment', 'Screening and qualification questions', 2, TRUE),
(3, 'Brand/Product Awareness & Usage', 'Brand awareness and product usage', 3, TRUE),
(4, 'Concept Exposure', 'Concept testing and evaluation', 4, TRUE),
(5, 'Methodology', 'Pricing and methodology-specific questions', 5, TRUE),
(6, 'Additional Questions', 'Demographics and psychographics', 6, TRUE),
(7, 'Programmer Instructions', 'Programming notes and QC', 7, TRUE)
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- FOREIGN KEY CONSTRAINTS
-- ============================================================================

-- Note: Foreign key constraints are defined inline with table definitions
-- for better compatibility with PostgreSQL and Railway deployment

-- ============================================================================
-- COMPLETION MESSAGE
-- ============================================================================

-- This bootstrap schema creates all 27 tables with proper indexes and constraints
-- All operations are idempotent and safe to run multiple times