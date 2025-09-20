"""
Quality Monitoring API endpoints

Provides endpoints for monitoring survey generation quality,
viewing trends, and managing regression alerts.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from ..database.connection import get_db
from ..database.quality_models import QualityMetrics, QualityBaselines, RegressionAlerts, QualityTrendAggregates
from ..services.quality_regression_service import QualityRegressionService
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/quality", tags=["quality_monitoring"])


# Pydantic models for API responses
class QualityMetricsResponse(BaseModel):
    """Response model for quality metrics"""
    survey_id: str
    workflow_id: str
    overall_grade: str
    weighted_score: float
    confidence_score: Optional[float]
    pillar_scores: Dict[str, Any]
    generation_time_seconds: Optional[float]
    golden_similarity: Optional[float]
    methodology_compliance: bool
    error_count: int
    created_at: datetime


class QualityTrendResponse(BaseModel):
    """Response model for quality trends"""
    metric_name: str
    time_series: List[Dict[str, Any]]
    summary_statistics: Dict[str, float]
    trend_direction: str  # improving, stable, declining


class RegressionAlertResponse(BaseModel):
    """Response model for regression alerts"""
    alert_id: str
    metric_name: str
    current_value: float
    baseline_value: float
    regression_severity: str
    confidence_level: float
    detected_at: datetime
    status: str
    description: str
    recommended_actions: List[str]
    affected_surveys_count: int


class QualityOverviewResponse(BaseModel):
    """Response model for quality overview dashboard"""
    current_quality_score: float
    quality_trend: str
    active_alerts_count: int
    recent_surveys_count: int
    avg_generation_time: float
    methodology_compliance_rate: float
    top_issues: List[str]


@router.get("/overview", response_model=QualityOverviewResponse)
async def get_quality_overview(
    hours: int = Query(24, description="Hours to look back for overview"),
    db: Session = Depends(get_db)
):
    """Get overall quality overview for dashboard"""
    try:
        logger.info(f"📊 [QualityAPI] Getting quality overview for last {hours} hours")

        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        # Get recent quality metrics
        recent_metrics = db.query(QualityMetrics).filter(
            QualityMetrics.created_at >= cutoff_time
        ).all()

        if not recent_metrics:
            return QualityOverviewResponse(
                current_quality_score=0.0,
                quality_trend="insufficient_data",
                active_alerts_count=0,
                recent_surveys_count=0,
                avg_generation_time=0.0,
                methodology_compliance_rate=0.0,
                top_issues=["Insufficient data for quality analysis"]
            )

        # Calculate overview statistics
        avg_score = sum(m.weighted_score for m in recent_metrics) / len(recent_metrics)
        avg_generation_time = sum(
            m.generation_time_seconds for m in recent_metrics
            if m.generation_time_seconds is not None
        ) / len([m for m in recent_metrics if m.generation_time_seconds is not None])

        compliance_rate = sum(
            1 for m in recent_metrics if m.methodology_compliance
        ) / len(recent_metrics)

        # Get active alerts
        active_alerts = db.query(RegressionAlerts).filter(
            RegressionAlerts.status == 'open',
            RegressionAlerts.detected_at >= cutoff_time
        ).count()

        # Determine trend (simplified)
        if len(recent_metrics) >= 10:
            first_half = recent_metrics[:len(recent_metrics)//2]
            second_half = recent_metrics[len(recent_metrics)//2:]

            first_avg = sum(m.weighted_score for m in first_half) / len(first_half)
            second_avg = sum(m.weighted_score for m in second_half) / len(second_half)

            if second_avg > first_avg + 0.05:
                trend = "improving"
            elif second_avg < first_avg - 0.05:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        # Get top issues
        top_issues = []
        if active_alerts > 0:
            top_issues.append(f"{active_alerts} active quality alerts")
        if compliance_rate < 0.95:
            top_issues.append(f"Methodology compliance below 95%: {compliance_rate:.1%}")
        if avg_generation_time > 30:
            top_issues.append(f"Generation time above 30s: {avg_generation_time:.1f}s")

        return QualityOverviewResponse(
            current_quality_score=avg_score,
            quality_trend=trend,
            active_alerts_count=active_alerts,
            recent_surveys_count=len(recent_metrics),
            avg_generation_time=avg_generation_time,
            methodology_compliance_rate=compliance_rate,
            top_issues=top_issues if top_issues else ["No major issues detected"]
        )

    except Exception as e:
        logger.error(f"❌ [QualityAPI] Failed to get quality overview: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get quality overview")


@router.get("/metrics", response_model=List[QualityMetricsResponse])
async def get_quality_metrics(
    hours: int = Query(24, description="Hours to look back"),
    limit: int = Query(100, description="Maximum number of results"),
    survey_id: Optional[str] = Query(None, description="Filter by specific survey ID"),
    db: Session = Depends(get_db)
):
    """Get quality metrics for recent surveys"""
    try:
        logger.info(f"📊 [QualityAPI] Getting quality metrics for last {hours} hours")

        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        query = db.query(QualityMetrics).filter(
            QualityMetrics.created_at >= cutoff_time
        )

        if survey_id:
            query = query.filter(QualityMetrics.survey_id == survey_id)

        metrics = query.order_by(desc(QualityMetrics.created_at)).limit(limit).all()

        return [
            QualityMetricsResponse(
                survey_id=str(m.survey_id),
                workflow_id=m.workflow_id,
                overall_grade=m.overall_grade,
                weighted_score=m.weighted_score,
                confidence_score=m.confidence_score,
                pillar_scores=m.pillar_scores or {},
                generation_time_seconds=m.generation_time_seconds,
                golden_similarity=m.golden_similarity,
                methodology_compliance=m.methodology_compliance,
                error_count=m.error_count,
                created_at=m.created_at
            )
            for m in metrics
        ]

    except Exception as e:
        logger.error(f"❌ [QualityAPI] Failed to get quality metrics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get quality metrics")


@router.get("/trends/{metric_name}", response_model=QualityTrendResponse)
async def get_quality_trend(
    metric_name: str,
    days: int = Query(7, description="Days to look back"),
    aggregation: str = Query("hour", description="Aggregation level: hour, day"),
    db: Session = Depends(get_db)
):
    """Get quality trend for specific metric"""
    try:
        logger.info(f"📈 [QualityAPI] Getting {metric_name} trend for last {days} days")

        # Check if we have pre-computed aggregates
        cutoff_time = datetime.utcnow() - timedelta(days=days)

        aggregates = db.query(QualityTrendAggregates).filter(
            QualityTrendAggregates.metric_name == metric_name,
            QualityTrendAggregates.aggregation_level == aggregation,
            QualityTrendAggregates.date >= cutoff_time
        ).order_by(QualityTrendAggregates.date).all()

        if aggregates:
            # Use pre-computed aggregates
            time_series = [
                {
                    "timestamp": agg.date.isoformat(),
                    "value": agg.avg_value,
                    "min": agg.min_value,
                    "max": agg.max_value,
                    "std": agg.std_value,
                    "count": agg.sample_count,
                    "p90": agg.p90_value,
                    "p95": agg.p95_value
                }
                for agg in aggregates
            ]

            summary_stats = {
                "avg": sum(agg.avg_value for agg in aggregates) / len(aggregates),
                "min": min(agg.min_value for agg in aggregates),
                "max": max(agg.max_value for agg in aggregates),
                "total_samples": sum(agg.sample_count for agg in aggregates)
            }
        else:
            # Compute on-demand (fallback)
            time_series, summary_stats = await _compute_trend_on_demand(
                db, metric_name, cutoff_time, aggregation
            )

        # Determine trend direction
        if len(time_series) >= 2:
            first_values = [t["value"] for t in time_series[:len(time_series)//3]]
            last_values = [t["value"] for t in time_series[-len(time_series)//3:]]

            first_avg = sum(first_values) / len(first_values)
            last_avg = sum(last_values) / len(last_values)

            if last_avg > first_avg * 1.05:
                trend_direction = "improving"
            elif last_avg < first_avg * 0.95:
                trend_direction = "declining"
            else:
                trend_direction = "stable"
        else:
            trend_direction = "insufficient_data"

        return QualityTrendResponse(
            metric_name=metric_name,
            time_series=time_series,
            summary_statistics=summary_stats,
            trend_direction=trend_direction
        )

    except Exception as e:
        logger.error(f"❌ [QualityAPI] Failed to get quality trend: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get quality trend")


@router.get("/alerts", response_model=List[RegressionAlertResponse])
async def get_regression_alerts(
    hours: int = Query(24, description="Hours to look back"),
    severity: Optional[str] = Query(None, description="Filter by severity: minor, moderate, severe"),
    status: str = Query("open", description="Filter by status: open, investigating, resolved"),
    db: Session = Depends(get_db)
):
    """Get regression alerts"""
    try:
        logger.info(f"🚨 [QualityAPI] Getting regression alerts for last {hours} hours")

        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        query = db.query(RegressionAlerts).filter(
            RegressionAlerts.detected_at >= cutoff_time,
            RegressionAlerts.status == status
        )

        if severity:
            query = query.filter(RegressionAlerts.regression_severity == severity)

        alerts = query.order_by(desc(RegressionAlerts.detected_at)).all()

        return [
            RegressionAlertResponse(
                alert_id=alert.alert_id,
                metric_name=alert.metric_name,
                current_value=alert.current_value,
                baseline_value=alert.baseline_value,
                regression_severity=alert.regression_severity,
                confidence_level=alert.confidence_level,
                detected_at=alert.detected_at,
                status=alert.status,
                description=alert.description,
                recommended_actions=alert.recommended_actions or [],
                affected_surveys_count=len(alert.affected_survey_ids or [])
            )
            for alert in alerts
        ]

    except Exception as e:
        logger.error(f"❌ [QualityAPI] Failed to get regression alerts: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get regression alerts")


@router.post("/alerts/{alert_id}/update-status")
async def update_alert_status(
    alert_id: str,
    status: str,
    notes: Optional[str] = None,
    assigned_to: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Update regression alert status"""
    try:
        logger.info(f"🔄 [QualityAPI] Updating alert {alert_id} status to {status}")

        alert = db.query(RegressionAlerts).filter(
            RegressionAlerts.alert_id == alert_id
        ).first()

        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")

        alert.status = status
        if notes:
            alert.resolution_notes = notes
        if assigned_to:
            alert.assigned_to = assigned_to
        if status == 'resolved':
            alert.resolved_at = datetime.utcnow()

        alert.updated_at = datetime.utcnow()
        db.commit()

        return {"message": "Alert status updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [QualityAPI] Failed to update alert status: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update alert status")


@router.post("/regression-check")
async def trigger_regression_check(
    hours: int = Query(24, description="Hours to analyze"),
    db: Session = Depends(get_db)
):
    """Manually trigger regression detection"""
    try:
        logger.info(f"🔍 [QualityAPI] Manually triggering regression check for last {hours} hours")

        service = QualityRegressionService(db_session=db)
        alerts = await service.detect_regressions(lookback_hours=hours)

        return {
            "message": f"Regression check completed",
            "alerts_generated": len(alerts),
            "alerts": [
                {
                    "metric_name": alert.metric_name,
                    "severity": alert.regression_severity,
                    "description": alert.description
                }
                for alert in alerts
            ]
        }

    except Exception as e:
        logger.error(f"❌ [QualityAPI] Failed to trigger regression check: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to trigger regression check")


@router.post("/baselines/update")
async def update_quality_baselines(
    days: int = Query(30, description="Days to use for baseline calculation"),
    db: Session = Depends(get_db)
):
    """Update quality baselines"""
    try:
        logger.info(f"🔄 [QualityAPI] Updating quality baselines using last {days} days")

        service = QualityRegressionService(db_session=db)
        baselines = await service.update_baselines(period_days=days)

        return {
            "message": f"Quality baselines updated",
            "baselines_updated": len(baselines),
            "baselines": {
                name: {
                    "value": baseline.baseline_value,
                    "std": baseline.baseline_std,
                    "sample_size": baseline.sample_size
                }
                for name, baseline in baselines.items()
            }
        }

    except Exception as e:
        logger.error(f"❌ [QualityAPI] Failed to update baselines: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update baselines")


async def _compute_trend_on_demand(db: Session, metric_name: str, cutoff_time: datetime,
                                 aggregation: str) -> tuple[List[Dict[str, Any]], Dict[str, float]]:
    """Compute trend data on-demand when pre-computed aggregates aren't available"""
    try:
        # Get raw metrics
        metrics = db.query(QualityMetrics).filter(
            QualityMetrics.created_at >= cutoff_time
        ).order_by(QualityMetrics.created_at).all()

        if not metrics:
            return [], {}

        # Group by time period
        time_groups = {}
        for metric in metrics:
            if aggregation == "hour":
                time_key = metric.created_at.strftime("%Y-%m-%d %H:00:00")
            else:  # day
                time_key = metric.created_at.strftime("%Y-%m-%d 00:00:00")

            if time_key not in time_groups:
                time_groups[time_key] = []

            # Extract the specific metric value
            if metric_name == 'overall_score':
                value = metric.weighted_score
            elif metric_name == 'generation_time' and metric.generation_time_seconds:
                value = metric.generation_time_seconds
            elif metric_name == 'golden_similarity' and metric.golden_similarity:
                value = metric.golden_similarity
            elif metric_name == 'confidence_score' and metric.confidence_score:
                value = metric.confidence_score
            else:
                continue

            time_groups[time_key].append(value)

        # Compute aggregates for each time period
        time_series = []
        all_values = []

        for time_key in sorted(time_groups.keys()):
            values = time_groups[time_key]
            if values:
                time_series.append({
                    "timestamp": time_key,
                    "value": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values)
                })
                all_values.extend(values)

        # Compute summary statistics
        summary_stats = {}
        if all_values:
            summary_stats = {
                "avg": sum(all_values) / len(all_values),
                "min": min(all_values),
                "max": max(all_values),
                "total_samples": len(all_values)
            }

        return time_series, summary_stats

    except Exception as e:
        logger.error(f"❌ [QualityAPI] Failed to compute trend on-demand: {str(e)}", exc_info=True)
        return [], {}