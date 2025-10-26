from sqlalchemy import Column, String, Text, Integer, DateTime, DECIMAL, ARRAY, ForeignKey, CheckConstraint, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import List, Optional, Any, Dict
from .connection import Base
import uuid

# Import proper pgvector SQLAlchemy type
try:
    from pgvector.sqlalchemy.vector import VECTOR
except ImportError:
    # Handle import error gracefully for testing
    import warnings
    warnings.warn("pgvector not available, using fallback")
    from sqlalchemy import Text as VECTOR  # Fallback for testing


class GoldenRFQSurveyPair(Base):
    __tablename__ = "golden_rfq_survey_pairs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(Text)
    rfq_text = Column(Text, nullable=False)
    rfq_embedding = Column(VECTOR(384))
    survey_json = Column(JSONB, nullable=False)
    methodology_tags: Any = Column(ARRAY(Text))
    industry_category: Any = Column(Text)
    research_goal: Any = Column(Text)
    quality_score: Any = Column(DECIMAL(3, 2))
    usage_count = Column(Integer, default=0)
    human_verified = Column(Boolean, default=False)  # True for manually created, False for auto-migrated
    created_at = Column(DateTime, default=func.now())


class GoldenSection(Base):
    """Model for storing individual sections from golden surveys for rule-based retrieval"""
    __tablename__ = "golden_sections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section_id = Column(String(255), nullable=False)
    survey_id = Column(String(255), nullable=False)
    golden_pair_id = Column(UUID(as_uuid=True), ForeignKey('golden_rfq_survey_pairs.id', ondelete='CASCADE'))
    annotation_id = Column(Integer, ForeignKey('section_annotations.id', ondelete='SET NULL'), nullable=True)  # Link to source annotation
    section_title = Column(String(500))
    section_text = Column(Text, nullable=False)
    section_type = Column(String(100))  # e.g., 'demographics', 'pricing', 'satisfaction', 'behavioral'
    methodology_tags: Any = Column(ARRAY(Text))  # Array of methodology tags for this section
    industry_keywords: Any = Column(ARRAY(Text))  # Array of industry-specific keywords
    question_patterns: Any = Column(ARRAY(Text))  # Array of question patterns found in this section
    quality_score: Any = Column(DECIMAL(3, 2))  # Average quality from annotations
    usage_count = Column(Integer, default=0)
    human_verified = Column(Boolean, default=False)  # True if manually created/verified
    labels = Column(JSONB)  # Labels from annotations
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class GoldenQuestion(Base):
    """Model for storing individual questions from golden surveys for rule-based retrieval"""
    __tablename__ = "golden_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(String(255), nullable=False)
    survey_id = Column(String(255), nullable=False)
    golden_pair_id = Column(UUID(as_uuid=True), ForeignKey('golden_rfq_survey_pairs.id', ondelete='CASCADE'))
    annotation_id = Column(Integer, ForeignKey('question_annotations.id', ondelete='SET NULL'), nullable=True)  # Link to source annotation
    question_text = Column(Text, nullable=False)
    question_type = Column(String(100))  # e.g., 'multiple_choice', 'rating_scale', 'open_text', 'yes_no'
    question_subtype = Column(String(100))  # e.g., 'likert_5', 'likert_7', 'binary', 'text_input'
    methodology_tags: Any = Column(ARRAY(Text))  # Array of methodology tags for this question
    industry_keywords: Any = Column(ARRAY(Text))  # Array of industry-specific keywords
    question_patterns: Any = Column(ARRAY(Text))  # Array of question patterns/templates
    quality_score: Any = Column(DECIMAL(3, 2))  # Suitability score (combines quality and relevance from annotations)
    usage_count = Column(Integer, default=0)
    human_verified = Column(Boolean, default=False)  # True if manually created/verified
    labels = Column(JSONB)  # Labels from annotations
    section_id = Column(Integer)  # QNR section this question belongs to (1-7)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class GoldenQuestionUsage(Base):
    """Model for tracking which surveys use which golden questions"""
    __tablename__ = "golden_question_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    golden_question_id = Column(UUID(as_uuid=True), ForeignKey('golden_questions.id', ondelete='CASCADE'), nullable=False)
    survey_id = Column(UUID(as_uuid=True), ForeignKey('surveys.id', ondelete='CASCADE'), nullable=False)
    used_at = Column(DateTime, default=func.now())


class GoldenSectionUsage(Base):
    """Model for tracking which surveys use which golden sections"""
    __tablename__ = "golden_section_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    golden_section_id = Column(UUID(as_uuid=True), ForeignKey('golden_sections.id', ondelete='CASCADE'), nullable=False)
    survey_id = Column(UUID(as_uuid=True), ForeignKey('surveys.id', ondelete='CASCADE'), nullable=False)
    used_at = Column(DateTime, default=func.now())


class RetrievalWeights(Base):
    """Configurable weights for multi-factor golden example retrieval scoring"""
    __tablename__ = "retrieval_weights"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    context_type = Column(String(50), nullable=False)  # 'global', 'methodology', 'industry'
    context_value = Column(String(100))  # e.g., 'van_westendorp', 'healthcare'
    semantic_weight = Column(DECIMAL(3, 2), default=0.40)
    methodology_weight = Column(DECIMAL(3, 2), default=0.25)
    industry_weight = Column(DECIMAL(3, 2), default=0.15)
    quality_weight = Column(DECIMAL(3, 2), default=0.10)
    annotation_weight = Column(DECIMAL(3, 2), default=0.10)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class MethodologyCompatibility(Base):
    """Compatibility matrix for methodology-based retrieval scoring"""
    __tablename__ = "methodology_compatibility"

    methodology_a = Column(String(50), primary_key=True)
    methodology_b = Column(String(50), primary_key=True)
    compatibility_score = Column(DECIMAL(3, 2), nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class RFQ(Base):
    __tablename__ = "rfqs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(Text)
    description = Column(Text, nullable=False)
    product_category = Column(Text)
    target_segment = Column(Text)
    research_goal = Column(Text)
    embedding = Column(VECTOR(384))
    enhanced_rfq_data = Column(JSONB)  # Store structured Enhanced RFQ data for analytics and future features
    document_upload_id = Column(UUID(as_uuid=True), ForeignKey("document_uploads.id"))  # Optional reference to source document
    created_at = Column(DateTime, default=func.now())

    surveys = relationship("Survey", back_populates="rfq")
    document_upload = relationship("DocumentUpload", back_populates="rfqs")


class Survey(Base):
    __tablename__ = "surveys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rfq_id = Column(UUID(as_uuid=True), ForeignKey("rfqs.id"))
    status = Column(
        Text,
        CheckConstraint("status IN ('draft','validated','edited','final','reference')"),
        nullable=False
    )
    raw_output = Column(JSONB)
    final_output = Column(JSONB)
    golden_similarity_score: Any = Column(DECIMAL(3, 2))
    used_golden_examples: Any = Column(ARRAY(UUID()))
    used_golden_questions: Any = Column(ARRAY(UUID()), default=[])
    used_golden_sections: Any = Column(ARRAY(UUID()), default=[])
    cleanup_minutes_actual = Column(Integer)
    model_version = Column(Text)
    pillar_scores = Column(JSONB)  # Store 5-pillar evaluation scores
    created_at = Column(DateTime, default=func.now())

    rfq = relationship("RFQ", back_populates="surveys")
    edits = relationship("Edit", back_populates="survey")
    rule_validations = relationship("RuleValidation", back_populates="survey")


class Edit(Base):
    __tablename__ = "edits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    survey_id = Column(UUID(as_uuid=True), ForeignKey("surveys.id"))
    edit_type = Column(Text)
    edit_reason = Column(Text)
    before_text = Column(Text)
    after_text = Column(Text)
    annotation = Column(JSONB)
    created_at = Column(DateTime, default=func.now())

    survey = relationship("Survey", back_populates="edits")


class SurveyRule(Base):
    """Model for storing survey generation rules"""
    __tablename__ = "survey_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_type = Column(String(50), nullable=False)  # 'methodology', 'quality', 'industry', 'custom'
    category = Column(String(100), nullable=False)  # 'van_westendorp', 'question_quality', 'healthcare', etc.
    rule_name = Column(String(200), nullable=False)
    rule_description = Column(Text)
    rule_content = Column(JSONB)  # Store rule details as JSON
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)  # Higher number = higher priority
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(100), default="system")
    
    # Indexes
    __table_args__ = (
        Index('idx_survey_rules_type_category', 'rule_type', 'category'),
        Index('idx_survey_rules_active', 'is_active'),
    )


class RuleValidation(Base):
    """Model for storing rule validation results"""
    __tablename__ = "rule_validations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    survey_id = Column(UUID(as_uuid=True), ForeignKey("surveys.id"), nullable=False)
    rule_id = Column(UUID(as_uuid=True), ForeignKey("survey_rules.id"), nullable=False)
    validation_passed = Column(Boolean, nullable=False)
    error_message = Column(Text)
    warning_message = Column(Text)
    validation_details = Column(JSONB)  # Store detailed validation results
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    survey = relationship("Survey", back_populates="rule_validations")
    rule = relationship("SurveyRule")
    
    # Indexes
    __table_args__ = (
        Index('idx_rule_validations_survey', 'survey_id'),
        Index('idx_rule_validations_rule', 'rule_id'),
    )


class QuestionAnnotation(Base):
    """Model for storing question annotations"""
    __tablename__ = "question_annotations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(String(255), nullable=False)
    survey_id = Column(String(255), nullable=False)
    required = Column(Boolean, nullable=False, default=True)
    quality = Column(Integer, nullable=False)
    relevant = Column(Integer, nullable=False)
    # Individual pillar ratings
    methodological_rigor = Column(Integer, nullable=False)
    content_validity = Column(Integer, nullable=False)
    respondent_experience = Column(Integer, nullable=False)
    analytical_value = Column(Integer, nullable=False)
    business_impact = Column(Integer, nullable=False)
    comment = Column(Text)
    annotator_id = Column(String(255))

    # Labels field
    labels = Column(JSONB)
    removed_labels = Column(JSONB)  # Track auto-generated labels that user explicitly removed

    # Advanced labeling fields
    advanced_labels = Column(JSONB)
    industry_classification = Column(String(100))
    respondent_type = Column(String(100))
    methodology_tags = Column(ARRAY(String))
    is_mandatory = Column(Boolean, default=False)
    compliance_status = Column(String(50))

    # AI-generated annotation tracking
    ai_generated = Column(Boolean, nullable=False, default=False)
    ai_confidence = Column(DECIMAL(3, 2))  # 0.00-1.00 confidence score
    human_verified = Column(Boolean, nullable=False, default=False)
    generation_timestamp = Column(DateTime(timezone=True))

    # Human override tracking
    human_overridden = Column(Boolean, nullable=False, default=False)
    override_timestamp = Column(DateTime(timezone=True))
    original_ai_quality = Column(Integer)
    original_ai_relevant = Column(Integer)
    original_ai_comment = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Constraints
    __table_args__ = (
        CheckConstraint('quality >= 1 AND quality <= 5', name='check_quality_range'),
        CheckConstraint('relevant >= 1 AND relevant <= 5', name='check_relevant_range'),
        CheckConstraint('methodological_rigor >= 1 AND methodological_rigor <= 5', name='check_methodological_rigor_range'),
        CheckConstraint('content_validity >= 1 AND content_validity <= 5', name='check_content_validity_range'),
        CheckConstraint('respondent_experience >= 1 AND respondent_experience <= 5', name='check_respondent_experience_range'),
        CheckConstraint('analytical_value >= 1 AND analytical_value <= 5', name='check_analytical_value_range'),
        CheckConstraint('business_impact >= 1 AND business_impact <= 5', name='check_business_impact_range'),
        CheckConstraint('ai_confidence >= 0.00 AND ai_confidence <= 1.00', name='check_ai_confidence_range'),
        Index('idx_question_annotations_survey_id', 'survey_id'),
        Index('idx_question_annotations_annotator_id', 'annotator_id'),
        Index('idx_question_annotations_ai_generated', 'ai_generated'),
        Index('idx_question_annotations_human_overridden', 'human_overridden'),
        Index('idx_question_annotations_unique', 'question_id', 'annotator_id', unique=True),
    )


class SectionAnnotation(Base):
    """Model for storing section annotations"""
    __tablename__ = "section_annotations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    section_id = Column(Integer, nullable=False)
    survey_id = Column(String(255), nullable=False)
    quality = Column(Integer, nullable=False)
    relevant = Column(Integer, nullable=False)
    # Individual pillar ratings
    methodological_rigor = Column(Integer, nullable=False)
    content_validity = Column(Integer, nullable=False)
    respondent_experience = Column(Integer, nullable=False)
    analytical_value = Column(Integer, nullable=False)
    business_impact = Column(Integer, nullable=False)
    comment = Column(Text)
    annotator_id = Column(String(255))

    # Labels field
    labels = Column(JSONB)

    # Advanced labeling fields
    section_classification = Column(String(100))
    mandatory_elements = Column(JSONB)
    compliance_score = Column(Integer)

    # AI-generated annotation tracking
    ai_generated = Column(Boolean, nullable=False, default=False)
    ai_confidence = Column(DECIMAL(3, 2))  # 0.00-1.00 confidence score
    human_verified = Column(Boolean, nullable=False, default=False)
    generation_timestamp = Column(DateTime(timezone=True))

    # Human override tracking
    human_overridden = Column(Boolean, nullable=False, default=False)
    override_timestamp = Column(DateTime(timezone=True))
    original_ai_quality = Column(Integer)
    original_ai_relevant = Column(Integer)
    original_ai_comment = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Constraints
    __table_args__ = (
        CheckConstraint('quality >= 1 AND quality <= 5', name='check_quality_range'),
        CheckConstraint('relevant >= 1 AND relevant <= 5', name='check_relevant_range'),
        CheckConstraint('methodological_rigor >= 1 AND methodological_rigor <= 5', name='check_methodological_rigor_range'),
        CheckConstraint('content_validity >= 1 AND content_validity <= 5', name='check_content_validity_range'),
        CheckConstraint('respondent_experience >= 1 AND respondent_experience <= 5', name='check_respondent_experience_range'),
        CheckConstraint('analytical_value >= 1 AND analytical_value <= 5', name='check_analytical_value_range'),
        CheckConstraint('business_impact >= 1 AND business_impact <= 5', name='check_business_impact_range'),
        CheckConstraint('ai_confidence >= 0.00 AND ai_confidence <= 1.00', name='check_ai_confidence_range'),
        Index('idx_section_annotations_survey_id', 'survey_id'),
        Index('idx_section_annotations_annotator_id', 'annotator_id'),
        Index('idx_section_annotations_ai_generated', 'ai_generated'),
        Index('idx_section_annotations_human_overridden', 'human_overridden'),
        Index('idx_section_annotations_unique', 'section_id', 'annotator_id', unique=True),
    )


class SurveyAnnotation(Base):
    """Model for storing survey-level annotation metadata"""
    __tablename__ = "survey_annotations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    survey_id = Column(String(255), nullable=False, unique=True)
    overall_comment = Column(Text)
    annotator_id = Column(String(255))

    # Labels field
    labels = Column(JSONB)

    # Advanced labeling fields
    detected_labels = Column(JSONB)
    compliance_report = Column(JSONB)
    advanced_metadata = Column(JSONB)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_survey_annotations_annotator_id', 'annotator_id'),
    )


class HumanReview(Base):
    """Model for storing human review state for prompt reviews"""
    __tablename__ = "human_reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_id = Column(String(255), nullable=False, unique=True)
    survey_id = Column(String(255), nullable=True)
    review_status = Column(String(50), nullable=False, default='pending')
    prompt_data = Column(Text, nullable=False)
    original_rfq = Column(Text, nullable=False)
    reviewer_id = Column(String(255), nullable=True)
    review_deadline = Column(DateTime(timezone=True), nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    approval_reason = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # Prompt editing fields
    edited_prompt_data = Column(Text, nullable=True)  # Store manually edited prompt
    original_prompt_data = Column(Text, nullable=True)  # Preserve original for comparison
    prompt_edited = Column(Boolean, default=False, nullable=False)  # Flag to track if prompt was edited
    prompt_edit_timestamp = Column(DateTime(timezone=True), nullable=True)  # When edit occurred
    edited_by = Column(String(255), nullable=True)  # Who made the edit
    edit_reason = Column(Text, nullable=True)  # Optional reason for the edit

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_human_reviews_workflow_id', 'workflow_id'),
        Index('idx_human_reviews_status', 'review_status'),
        Index('idx_human_reviews_reviewer_id', 'reviewer_id'),
        Index('idx_human_reviews_created_at', 'created_at'),
        Index('idx_human_reviews_prompt_edited', 'prompt_edited'),
        Index('idx_human_reviews_edited_by', 'edited_by'),
        Index('idx_human_reviews_edit_timestamp', 'prompt_edit_timestamp'),
        CheckConstraint(
            "review_status IN ('pending', 'in_progress', 'approved', 'rejected', 'expired')",
            name='check_review_status'
        ),
    )

class WorkflowState(Base):
    """Model for storing workflow state for resumption"""
    __tablename__ = "workflow_states"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_id = Column(String(255), nullable=False, unique=True)
    survey_id = Column(String(255), nullable=True)
    state_data = Column(Text, nullable=False)  # JSON serialized state
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_workflow_states_workflow_id', 'workflow_id'),
        Index('idx_workflow_states_survey_id', 'survey_id'),
        Index('idx_workflow_states_created_at', 'created_at'),
    )


class GoldenExampleState(Base):
    """Model for storing golden example creation state"""
    __tablename__ = "golden_example_states"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(255), nullable=False, unique=True)
    state_data = Column(JSONB, nullable=False)  # Store form data, extracted fields, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_golden_example_states_session_id', 'session_id'),
        Index('idx_golden_example_states_created_at', 'created_at'),
    )


class Settings(Base):
    """Settings table for storing application configuration"""
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    setting_key = Column(String(100), unique=True, nullable=False, index=True)
    setting_value = Column(JSONB, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_settings_key', 'setting_key'),
        Index('idx_settings_active', 'is_active'),
    )


class DocumentUpload(Base):
    """Model for tracking uploaded documents for RFQ analysis"""
    __tablename__ = "document_uploads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=True)  # Made nullable for compatibility
    file_size = Column(Integer, nullable=True)  # Made nullable since we update it after reading
    content_type = Column(String(100))
    session_id = Column(String(100), nullable=True, index=True)  # Track session for status lookup
    uploaded_by = Column(String(255), nullable=True)  # User tracking (optional)
    upload_timestamp = Column(DateTime(timezone=True), default=func.now())
    processing_status = Column(
        String(50),
        CheckConstraint("processing_status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')"),
        default='pending',
        nullable=False
    )
    analysis_result = Column(JSONB)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships
    rfqs = relationship("RFQ", back_populates="document_upload")
    document_rfq_mappings = relationship("DocumentRFQMapping", back_populates="document_upload")

    # Indexes
    __table_args__ = (
        Index('idx_document_uploads_status', 'processing_status'),
        Index('idx_document_uploads_timestamp', 'upload_timestamp'),
        Index('idx_document_uploads_filename', 'original_filename'),
        Index('idx_document_uploads_session_id', 'session_id'),  # Index for fast session lookup
    )


class DocumentRFQMapping(Base):
    """Model for tracking how documents are mapped to RFQs"""
    __tablename__ = "document_rfq_mappings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("document_uploads.id"), nullable=False)
    rfq_id = Column(UUID(as_uuid=True), ForeignKey("rfqs.id"), nullable=False)
    mapping_data = Column(JSONB, nullable=False)
    confidence_score = Column(DECIMAL(3, 2), default=0.0)
    fields_mapped = Column(JSONB)  # Track which fields were mapped and with what confidence
    user_corrections = Column(JSONB)  # Track user corrections to improve future mappings
    created_at = Column(DateTime(timezone=True), default=func.now())

    # Relationships
    document_upload = relationship("DocumentUpload", back_populates="document_rfq_mappings")
    rfq = relationship("RFQ")

    # Constraints and indexes
    __table_args__ = (
        Index('idx_document_rfq_mappings_document_id', 'document_id'),
        Index('idx_document_rfq_mappings_rfq_id', 'rfq_id'),
        Index('idx_document_rfq_mappings_confidence', 'confidence_score'),
        # Ensure each document can only be mapped to an RFQ once
        Index('idx_document_rfq_mappings_unique', 'document_id', 'rfq_id', unique=True),
    )


class LLMAudit(Base):
    """Comprehensive audit table for all LLM interactions across the system"""
    __tablename__ = "llm_audit"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Core identification
    interaction_id = Column(String(255), nullable=False)  # Unique identifier for this LLM interaction
    parent_workflow_id = Column(String(255))  # Optional parent workflow ID
    parent_survey_id = Column(String(255))  # Optional parent survey ID
    parent_rfq_id = Column(UUID(as_uuid=True))  # Optional parent RFQ ID
    
    # LLM Configuration
    model_name = Column(String(100), nullable=False)  # e.g., "openai/gpt-4o-mini", "meta/llama-2-70b-chat"
    model_provider = Column(String(50), nullable=False)  # e.g., "openai", "replicate", "anthropic"
    model_version = Column(String(50))  # Specific version if available
    
    # Purpose and Context
    purpose = Column(String(100), nullable=False)  # e.g., "survey_generation", "evaluation", "field_extraction"
    sub_purpose = Column(String(100))  # e.g., "content_validity", "methodological_rigor", "rfq_parsing"
    context_type = Column(String(50))  # e.g., "generation", "evaluation", "validation", "analysis"
    
    # Input/Output
    input_prompt = Column(Text, nullable=False)  # The actual prompt sent to LLM
    input_tokens = Column(Integer)  # Number of input tokens
    output_content = Column(Text)  # The response content from LLM
    output_tokens = Column(Integer)  # Number of output tokens
    raw_response = Column(Text)  # Raw response from LLM before any processing
    
    # Hyperparameters (configurable)
    temperature = Column(DECIMAL(3, 2))  # 0.0 to 2.0
    top_p = Column(DECIMAL(3, 2))  # 0.0 to 1.0
    max_tokens = Column(Integer)
    frequency_penalty = Column(DECIMAL(3, 2))  # -2.0 to 2.0
    presence_penalty = Column(DECIMAL(3, 2))  # -2.0 to 2.0
    stop_sequences = Column(JSONB)  # Array of stop sequences
    
    # Performance Metrics
    response_time_ms = Column(Integer)  # Response time in milliseconds
    cost_usd = Column(DECIMAL(10, 6))  # Cost in USD if available
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text)  # Error message if failed
    
    # Metadata
    interaction_metadata = Column(JSONB)  # Additional context-specific metadata
    tags = Column(JSONB)  # Searchable tags for categorization
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_llm_audit_interaction_id', 'interaction_id'),
        Index('idx_llm_audit_parent_workflow_id', 'parent_workflow_id'),
        Index('idx_llm_audit_parent_survey_id', 'parent_survey_id'),
        Index('idx_llm_audit_parent_rfq_id', 'parent_rfq_id'),
        Index('idx_llm_audit_model_name', 'model_name'),
        Index('idx_llm_audit_purpose', 'purpose'),
        Index('idx_llm_audit_context_type', 'context_type'),
        Index('idx_llm_audit_created_at', 'created_at'),
        Index('idx_llm_audit_success', 'success'),
        Index('idx_llm_audit_cost_usd', 'cost_usd'),
    )


class LLMHyperparameterConfig(Base):
    """Configuration table for LLM hyperparameters by purpose"""
    __tablename__ = "llm_hyperparameter_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Configuration identification
    config_name = Column(String(100), nullable=False, unique=True)  # e.g., "survey_generation_default"
    purpose = Column(String(100), nullable=False)  # e.g., "survey_generation", "evaluation"
    sub_purpose = Column(String(100))  # e.g., "content_validity", "methodological_rigor"
    
    # Hyperparameters
    temperature = Column(DECIMAL(3, 2), default=0.7)
    top_p = Column(DECIMAL(3, 2), default=0.9)
    max_tokens = Column(Integer, default=8000)
    frequency_penalty = Column(DECIMAL(3, 2), default=0.0)
    presence_penalty = Column(DECIMAL(3, 2), default=0.0)
    stop_sequences = Column(JSONB, default='[]')  # Array of stop sequences
    
    # Model preferences
    preferred_models = Column(JSONB, default='[]')  # Array of preferred model names
    fallback_models = Column(JSONB, default='[]')  # Array of fallback model names
    
    # Configuration metadata
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_llm_hyperparameter_configs_purpose', 'purpose'),
        Index('idx_llm_hyperparameter_configs_sub_purpose', 'sub_purpose'),
        Index('idx_llm_hyperparameter_configs_is_active', 'is_active'),
        Index('idx_llm_hyperparameter_configs_is_default', 'is_default'),
    )


class LLMPromptTemplate(Base):
    """Template table for LLM prompts by purpose"""
    __tablename__ = "llm_prompt_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Template identification
    template_name = Column(String(100), nullable=False, unique=True)  # e.g., "survey_generation_base"
    purpose = Column(String(100), nullable=False)  # e.g., "survey_generation", "evaluation"
    sub_purpose = Column(String(100))  # e.g., "content_validity", "methodological_rigor"
    
    # Template content
    system_prompt_template = Column(Text, nullable=False)  # Template with placeholders
    user_prompt_template = Column(Text)  # Optional user prompt template
    template_variables = Column(JSONB, default='{}')  # Available template variables
    
    # Template metadata
    description = Column(Text)
    version = Column(String(20), default='1.0')
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_llm_prompt_templates_purpose', 'purpose'),
        Index('idx_llm_prompt_templates_sub_purpose', 'sub_purpose'),
        Index('idx_llm_prompt_templates_is_active', 'is_active'),
        Index('idx_llm_prompt_templates_is_default', 'is_default'),
    )


class QNRSection(Base):
    """QNR section definitions"""
    __tablename__ = "qnr_sections"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    display_order = Column(Integer, nullable=False)
    mandatory = Column(Boolean, default=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class QNRLabel(Base):
    """QNR label definitions"""
    __tablename__ = "qnr_labels"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    category = Column(String(50), nullable=False)  # screener, brand, concept, methodology, additional
    description = Column(Text, nullable=False)
    mandatory = Column(Boolean, default=False)
    label_type = Column(String(20), nullable=False)  # Text, QNR, Rules
    applicable_labels = Column(ARRAY(Text))  # Industries or methodologies this applies to
    detection_patterns = Column(ARRAY(Text))  # Keywords for auto-detection
    section_id = Column(Integer, ForeignKey('qnr_sections.id'), nullable=False)
    display_order = Column(Integer, default=0)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    section = relationship("QNRSection", backref="labels")


class QNRLabelHistory(Base):
    """Audit trail for QNR label changes"""
    __tablename__ = "qnr_label_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    label_id = Column(Integer, ForeignKey('qnr_labels.id'))
    changed_by = Column(String(255))
    change_type = Column(String(50))  # created, updated, deleted
    old_value = Column(JSONB)
    new_value = Column(JSONB)
    changed_at = Column(DateTime, default=func.now())
    
    # Relationship
    label = relationship("QNRLabel", backref="history")