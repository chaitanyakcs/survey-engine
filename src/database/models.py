from sqlalchemy import Column, String, Text, Integer, DateTime, DECIMAL, ARRAY, ForeignKey, CheckConstraint, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import List, Optional, Any, Dict
from .connection import Base
import uuid

# Import proper pgvector SQLAlchemy type
from pgvector.sqlalchemy import Vector


class GoldenRFQSurveyPair(Base):
    __tablename__ = "golden_rfq_survey_pairs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(Text)
    rfq_text = Column(Text, nullable=False)
    rfq_embedding = Column(Vector(384))
    survey_json = Column(JSONB, nullable=False)
    methodology_tags: Any = Column(ARRAY(Text))
    industry_category: Any = Column(Text)
    research_goal: Any = Column(Text)
    quality_score: Any = Column(DECIMAL(3, 2))
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())


class RFQ(Base):
    __tablename__ = "rfqs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(Text)
    description = Column(Text, nullable=False)
    product_category = Column(Text)
    target_segment = Column(Text)
    research_goal = Column(Text)
    embedding = Column(Vector(384))
    created_at = Column(DateTime, default=func.now())

    surveys = relationship("Survey", back_populates="rfq")


class Survey(Base):
    __tablename__ = "surveys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rfq_id = Column(UUID(as_uuid=True), ForeignKey("rfqs.id"))
    status = Column(
        Text,
        CheckConstraint("status IN ('draft','validated','edited','final')"),
        nullable=False
    )
    raw_output = Column(JSONB)
    final_output = Column(JSONB)
    golden_similarity_score: Any = Column(DECIMAL(3, 2))
    used_golden_examples: Any = Column(ARRAY(UUID()))
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
        Index('idx_question_annotations_survey_id', 'survey_id'),
        Index('idx_question_annotations_annotator_id', 'annotator_id'),
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
        Index('idx_section_annotations_survey_id', 'survey_id'),
        Index('idx_section_annotations_annotator_id', 'annotator_id'),
        Index('idx_section_annotations_unique', 'section_id', 'annotator_id', unique=True),
    )


class SurveyAnnotation(Base):
    """Model for storing survey-level annotation metadata"""
    __tablename__ = "survey_annotations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    survey_id = Column(String(255), nullable=False, unique=True)
    overall_comment = Column(Text)
    annotator_id = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_survey_annotations_annotator_id', 'annotator_id'),
    )