from sqlalchemy import Column, String, Text, Integer, DateTime, DECIMAL, ARRAY, ForeignKey, CheckConstraint
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
    created_at = Column(DateTime, default=func.now())

    rfq = relationship("RFQ", back_populates="surveys")
    edits = relationship("Edit", back_populates="survey")


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