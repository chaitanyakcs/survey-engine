"""
Database models for quality tracking and regression detection
"""

from sqlalchemy import Column, String, Text, Integer, DateTime, DECIMAL, ForeignKey, Boolean, Index, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .connection import Base
import uuid


class QualityMetrics(Base):
    """Store quality metrics for each generated survey"""
    __tablename__ = "quality_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    survey_id = Column(UUID(as_uuid=True), ForeignKey("surveys.id"), nullable=False)
    workflow_id = Column(String(255), nullable=False)

    # Overall quality scores
    overall_grade = Column(String(1), nullable=False)  # A, B, C, D, F
    weighted_score = Column(Float, nullable=False)
    confidence_score = Column(Float)

    # Individual pillar scores
    pillar_scores = Column(JSONB)  # Store all pillar scores as JSON

    # Performance metrics
    generation_time_seconds = Column(Float)
    golden_similarity = Column(Float)
    methodology_compliance = Column(Boolean, default=True)
    error_count = Column(Integer, default=0)

    # Additional context
    methodology_tags = Column(JSONB)  # Array of methodology tags
    rfq_complexity_score = Column(Float)  # How complex was the input RFQ

    # Metadata
    created_at = Column(DateTime, default=func.now())

    # Indexes for performance
    __table_args__ = (
        Index('idx_quality_metrics_survey_id', 'survey_id'),
        Index('idx_quality_metrics_created_at', 'created_at'),
        Index('idx_quality_metrics_weighted_score', 'weighted_score'),
        Index('idx_quality_metrics_workflow_id', 'workflow_id'),
    )


class QualityBaselines(Base):
    """Store quality baselines for regression detection"""
    __tablename__ = "quality_baselines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_name = Column(String(100), nullable=False)

    # Baseline statistics
    baseline_value = Column(Float, nullable=False)
    baseline_std = Column(Float, nullable=False)
    sample_size = Column(Integer, nullable=False)

    # Baseline period
    period_days = Column(Integer, nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)

    # Indexes
    __table_args__ = (
        Index('idx_quality_baselines_metric_name', 'metric_name'),
        Index('idx_quality_baselines_is_active', 'is_active'),
        Index('idx_quality_baselines_created_at', 'created_at'),
    )


class RegressionAlerts(Base):
    """Store regression alerts when quality drops"""
    __tablename__ = "regression_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id = Column(String(255), unique=True, nullable=False)

    # Alert details
    metric_name = Column(String(100), nullable=False)
    current_value = Column(Float, nullable=False)
    baseline_value = Column(Float, nullable=False)
    regression_severity = Column(String(20), nullable=False)  # minor, moderate, severe
    confidence_level = Column(Float, nullable=False)

    # Context
    affected_survey_ids = Column(JSONB)  # Array of survey IDs affected
    description = Column(Text)
    recommended_actions = Column(JSONB)  # Array of recommended actions

    # Status tracking
    status = Column(String(20), default='open')  # open, investigating, resolved, false_positive
    assigned_to = Column(String(255))  # Team member investigating
    resolution_notes = Column(Text)
    resolved_at = Column(DateTime)

    # Metadata
    detected_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Indexes
    __table_args__ = (
        Index('idx_regression_alerts_metric_name', 'metric_name'),
        Index('idx_regression_alerts_severity', 'regression_severity'),
        Index('idx_regression_alerts_status', 'status'),
        Index('idx_regression_alerts_detected_at', 'detected_at'),
    )


class QualityTrendAggregates(Base):
    """Pre-computed quality trend aggregates for dashboard performance"""
    __tablename__ = "quality_trend_aggregates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Time aggregation
    date = Column(DateTime, nullable=False)  # Date for this aggregate
    aggregation_level = Column(String(10), nullable=False)  # hour, day, week

    # Metrics
    metric_name = Column(String(100), nullable=False)
    avg_value = Column(Float, nullable=False)
    min_value = Column(Float, nullable=False)
    max_value = Column(Float, nullable=False)
    std_value = Column(Float, nullable=False)
    sample_count = Column(Integer, nullable=False)

    # Percentiles
    p50_value = Column(Float)  # Median
    p90_value = Column(Float)
    p95_value = Column(Float)
    p99_value = Column(Float)

    # Metadata
    created_at = Column(DateTime, default=func.now())

    # Indexes
    __table_args__ = (
        Index('idx_quality_trends_date_metric', 'date', 'metric_name'),
        Index('idx_quality_trends_aggregation_level', 'aggregation_level'),
        Index('idx_quality_trends_created_at', 'created_at'),
    )


class PerformanceBenchmarks(Base):
    """Store performance benchmarks for different types of surveys"""
    __tablename__ = "performance_benchmarks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Benchmark category
    benchmark_category = Column(String(100), nullable=False)  # methodology, complexity, length, etc.
    benchmark_value = Column(String(100), nullable=False)     # van_westendorp, high, long, etc.

    # Performance targets
    target_generation_time_seconds = Column(Float, nullable=False)
    target_quality_score = Column(Float, nullable=False)
    target_golden_similarity = Column(Float, nullable=False)
    target_confidence_score = Column(Float, nullable=False)

    # Acceptable ranges
    min_quality_score = Column(Float, nullable=False)
    max_generation_time_seconds = Column(Float, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # Indexes
    __table_args__ = (
        Index('idx_performance_benchmarks_category_value', 'benchmark_category', 'benchmark_value'),
        Index('idx_performance_benchmarks_is_active', 'is_active'),
    )


class QualityReports(Base):
    """Store generated quality reports for regular monitoring"""
    __tablename__ = "quality_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Report details
    report_type = Column(String(50), nullable=False)  # daily, weekly, monthly, custom
    report_period_start = Column(DateTime, nullable=False)
    report_period_end = Column(DateTime, nullable=False)

    # Report content
    summary_statistics = Column(JSONB)  # Overall stats for the period
    trend_analysis = Column(JSONB)      # Trend analysis results
    regression_alerts = Column(JSONB)   # Alerts during this period
    recommendations = Column(JSONB)     # Automated recommendations

    # Report status
    status = Column(String(20), default='generated')  # generated, reviewed, archived
    reviewed_by = Column(String(255))
    review_notes = Column(Text)
    reviewed_at = Column(DateTime)

    # File attachments (if any)
    report_file_url = Column(String(500))  # URL to PDF/Excel report if generated

    # Metadata
    generated_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())

    # Indexes
    __table_args__ = (
        Index('idx_quality_reports_type_period', 'report_type', 'report_period_start'),
        Index('idx_quality_reports_status', 'status'),
        Index('idx_quality_reports_generated_at', 'generated_at'),
    )