"""
Quality Regression Detection Service

Monitors survey generation quality over time and detects regressions
in generation quality, pillar scores, and overall system performance.
"""

import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from statistics import mean, stdev
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

logger = logging.getLogger(__name__)


@dataclass
class QualityMetrics:
    """Quality metrics for a survey or batch of surveys"""
    overall_grade: str
    weighted_score: float
    pillar_scores: Dict[str, float]
    generation_time_seconds: float
    golden_similarity: float
    confidence_score: float
    methodology_compliance: bool
    error_count: int
    timestamp: datetime
    survey_id: str
    workflow_id: str


@dataclass
class QualityBaseline:
    """Quality baseline for comparison"""
    metric_name: str
    baseline_value: float
    baseline_std: float
    sample_size: int
    created_at: datetime
    period_days: int


@dataclass
class RegressionAlert:
    """Quality regression alert"""
    alert_id: str
    metric_name: str
    current_value: float
    baseline_value: float
    regression_severity: str  # 'minor', 'moderate', 'severe'
    confidence_level: float
    detected_at: datetime
    survey_ids: List[str]
    description: str
    recommended_actions: List[str]


class QualityRegressionService:
    """Service for detecting quality regressions in survey generation"""

    def __init__(self, db_session: Session = None):
        self.db_session = db_session
        self.quality_thresholds = {
            'overall_score': {'minor': 0.05, 'moderate': 0.10, 'severe': 0.20},
            'generation_time': {'minor': 1.5, 'moderate': 2.0, 'severe': 3.0},  # multipliers
            'golden_similarity': {'minor': 0.05, 'moderate': 0.10, 'severe': 0.15},
            'confidence_score': {'minor': 0.05, 'moderate': 0.10, 'severe': 0.15},
            'error_rate': {'minor': 0.02, 'moderate': 0.05, 'severe': 0.10},  # absolute percentages
            'pillar_scores': {'minor': 0.05, 'moderate': 0.10, 'severe': 0.20}
        }

    async def record_quality_metrics(self, survey_data: Dict[str, Any],
                                   generation_context: Dict[str, Any]) -> QualityMetrics:
        """Record quality metrics for a generated survey"""
        try:
            logger.info(f"🔍 [QualityRegression] Recording quality metrics for survey: {survey_data.get('survey_id', 'unknown')}")

            # Extract metrics from survey data
            pillar_scores = survey_data.get('pillar_scores', {})

            metrics = QualityMetrics(
                overall_grade=pillar_scores.get('overall_grade', 'F'),
                weighted_score=pillar_scores.get('weighted_score', 0.0),
                pillar_scores={
                    pillar['pillar_name']: pillar['weighted_score']
                    for pillar in pillar_scores.get('pillar_breakdown', [])
                },
                generation_time_seconds=generation_context.get('generation_time_seconds', 0.0),
                golden_similarity=generation_context.get('golden_similarity', 0.0),
                confidence_score=survey_data.get('survey', {}).get('confidence_score', 0.0),
                methodology_compliance=self._check_methodology_compliance(survey_data),
                error_count=len(generation_context.get('errors', [])),
                timestamp=datetime.utcnow(),
                survey_id=survey_data.get('survey_id', ''),
                workflow_id=generation_context.get('workflow_id', '')
            )

            # Store metrics in database
            await self._store_quality_metrics(metrics)

            logger.info(f"✅ [QualityRegression] Quality metrics recorded: score={metrics.weighted_score:.3f}, grade={metrics.overall_grade}")
            return metrics

        except Exception as e:
            logger.error(f"❌ [QualityRegression] Failed to record quality metrics: {str(e)}", exc_info=True)
            raise

    async def detect_regressions(self, lookback_hours: int = 24) -> List[RegressionAlert]:
        """Detect quality regressions in recent survey generation"""
        try:
            logger.info(f"🔍 [QualityRegression] Starting regression detection for last {lookback_hours} hours")

            # Get recent metrics
            recent_metrics = await self._get_recent_metrics(lookback_hours)
            if len(recent_metrics) < 5:
                logger.info(f"⚠️ [QualityRegression] Insufficient data for regression detection: {len(recent_metrics)} samples")
                return []

            # Get baselines
            baselines = await self._get_quality_baselines()
            if not baselines:
                logger.info(f"⚠️ [QualityRegression] No baselines available, creating initial baselines")
                await self._create_initial_baselines()
                return []

            alerts = []

            # Check each metric type
            for metric_name, baseline in baselines.items():
                alert = await self._check_metric_regression(
                    metric_name, recent_metrics, baseline
                )
                if alert:
                    alerts.append(alert)

            logger.info(f"🔍 [QualityRegression] Regression detection completed: {len(alerts)} alerts generated")

            # Store alerts
            for alert in alerts:
                await self._store_regression_alert(alert)

            return alerts

        except Exception as e:
            logger.error(f"❌ [QualityRegression] Failed to detect regressions: {str(e)}", exc_info=True)
            return []

    async def get_quality_trends(self, days: int = 7) -> Dict[str, List[Dict[str, Any]]]:
        """Get quality trends over specified time period"""
        try:
            logger.info(f"📊 [QualityRegression] Getting quality trends for last {days} days")

            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # This would query your database for stored quality metrics
            # For now, returning mock structure
            trends = {
                'overall_score': [],
                'generation_time': [],
                'golden_similarity': [],
                'confidence_score': [],
                'error_rate': [],
                'pillar_scores': {}
            }

            logger.info(f"✅ [QualityRegression] Quality trends retrieved")
            return trends

        except Exception as e:
            logger.error(f"❌ [QualityRegression] Failed to get quality trends: {str(e)}", exc_info=True)
            return {}

    async def update_baselines(self, period_days: int = 30) -> Dict[str, QualityBaseline]:
        """Update quality baselines based on recent performance"""
        try:
            logger.info(f"🔄 [QualityRegression] Updating quality baselines using last {period_days} days")

            cutoff_date = datetime.utcnow() - timedelta(days=period_days)

            # Get metrics from the baseline period
            baseline_metrics = await self._get_metrics_since(cutoff_date)

            if len(baseline_metrics) < 10:
                logger.warning(f"⚠️ [QualityRegression] Insufficient data for baseline update: {len(baseline_metrics)} samples")
                return {}

            baselines = {}

            # Calculate baseline for overall score
            overall_scores = [m.weighted_score for m in baseline_metrics]
            baselines['overall_score'] = QualityBaseline(
                metric_name='overall_score',
                baseline_value=mean(overall_scores),
                baseline_std=stdev(overall_scores) if len(overall_scores) > 1 else 0.0,
                sample_size=len(overall_scores),
                created_at=datetime.utcnow(),
                period_days=period_days
            )

            # Calculate baseline for generation time
            generation_times = [m.generation_time_seconds for m in baseline_metrics if m.generation_time_seconds > 0]
            if generation_times:
                baselines['generation_time'] = QualityBaseline(
                    metric_name='generation_time',
                    baseline_value=mean(generation_times),
                    baseline_std=stdev(generation_times) if len(generation_times) > 1 else 0.0,
                    sample_size=len(generation_times),
                    created_at=datetime.utcnow(),
                    period_days=period_days
                )

            # Calculate baseline for golden similarity
            similarities = [m.golden_similarity for m in baseline_metrics if m.golden_similarity > 0]
            if similarities:
                baselines['golden_similarity'] = QualityBaseline(
                    metric_name='golden_similarity',
                    baseline_value=mean(similarities),
                    baseline_std=stdev(similarities) if len(similarities) > 1 else 0.0,
                    sample_size=len(similarities),
                    created_at=datetime.utcnow(),
                    period_days=period_days
                )

            # Calculate baseline for confidence score
            confidence_scores = [m.confidence_score for m in baseline_metrics if m.confidence_score > 0]
            if confidence_scores:
                baselines['confidence_score'] = QualityBaseline(
                    metric_name='confidence_score',
                    baseline_value=mean(confidence_scores),
                    baseline_std=stdev(confidence_scores) if len(confidence_scores) > 1 else 0.0,
                    sample_size=len(confidence_scores),
                    created_at=datetime.utcnow(),
                    period_days=period_days
                )

            # Calculate baseline for error rate
            error_rates = [m.error_count for m in baseline_metrics]
            baselines['error_rate'] = QualityBaseline(
                metric_name='error_rate',
                baseline_value=mean(error_rates),
                baseline_std=stdev(error_rates) if len(error_rates) > 1 else 0.0,
                sample_size=len(error_rates),
                created_at=datetime.utcnow(),
                period_days=period_days
            )

            # Store updated baselines
            await self._store_baselines(baselines)

            logger.info(f"✅ [QualityRegression] Updated {len(baselines)} quality baselines")
            return baselines

        except Exception as e:
            logger.error(f"❌ [QualityRegression] Failed to update baselines: {str(e)}", exc_info=True)
            return {}

    async def get_regression_alerts(self, hours: int = 24, severity: str = None) -> List[RegressionAlert]:
        """Get recent regression alerts"""
        try:
            logger.info(f"📋 [QualityRegression] Getting regression alerts for last {hours} hours")

            # This would query stored alerts from database
            # For now, returning empty list
            alerts = []

            logger.info(f"✅ [QualityRegression] Retrieved {len(alerts)} regression alerts")
            return alerts

        except Exception as e:
            logger.error(f"❌ [QualityRegression] Failed to get regression alerts: {str(e)}", exc_info=True)
            return []

    def _check_methodology_compliance(self, survey_data: Dict[str, Any]) -> bool:
        """Check if survey complies with methodology requirements"""
        try:
            survey = survey_data.get('survey', {})
            methodologies = survey.get('methodologies', [])
            sections = survey.get('sections', [])

            # Basic compliance checks
            if not sections:
                return False

            # Check for minimum questions
            total_questions = sum(len(section.get('questions', [])) for section in sections)
            if total_questions < 3:
                return False

            # Methodology-specific checks
            for methodology in methodologies:
                if methodology == 'van_westendorp':
                    # Should have 4 pricing questions
                    pricing_questions = [
                        q for section in sections
                        for q in section.get('questions', [])
                        if q.get('methodology') == 'van_westendorp'
                    ]
                    if len(pricing_questions) != 4:
                        return False

                elif methodology == 'nps':
                    # Should have NPS question
                    nps_questions = [
                        q for section in sections
                        for q in section.get('questions', [])
                        if q.get('methodology') == 'nps'
                    ]
                    if len(nps_questions) == 0:
                        return False

            return True

        except Exception as e:
            logger.error(f"❌ [QualityRegression] Error checking methodology compliance: {str(e)}")
            return False

    async def _store_quality_metrics(self, metrics: QualityMetrics):
        """Store quality metrics in database"""
        try:
            if not self.db_session:
                logger.warning("⚠️ [QualityRegression] No database session available for storing metrics")
                return

            # This would store metrics in a quality_metrics table
            # Implementation depends on your database schema
            logger.debug(f"📊 [QualityRegression] Storing quality metrics for survey {metrics.survey_id}")

        except Exception as e:
            logger.error(f"❌ [QualityRegression] Failed to store quality metrics: {str(e)}", exc_info=True)

    async def _get_recent_metrics(self, hours: int) -> List[QualityMetrics]:
        """Get quality metrics from recent hours"""
        try:
            # This would query quality_metrics table
            # For now, returning empty list for mock
            return []

        except Exception as e:
            logger.error(f"❌ [QualityRegression] Failed to get recent metrics: {str(e)}", exc_info=True)
            return []

    async def _get_metrics_since(self, cutoff_date: datetime) -> List[QualityMetrics]:
        """Get quality metrics since specified date"""
        try:
            # This would query quality_metrics table
            return []

        except Exception as e:
            logger.error(f"❌ [QualityRegression] Failed to get metrics since date: {str(e)}", exc_info=True)
            return []

    async def _get_quality_baselines(self) -> Dict[str, QualityBaseline]:
        """Get current quality baselines"""
        try:
            # This would query quality_baselines table
            return {}

        except Exception as e:
            logger.error(f"❌ [QualityRegression] Failed to get quality baselines: {str(e)}", exc_info=True)
            return {}

    async def _create_initial_baselines(self):
        """Create initial baselines when none exist"""
        try:
            logger.info("🔄 [QualityRegression] Creating initial quality baselines")

            # Get last 30 days of data for initial baseline
            await self.update_baselines(period_days=30)

        except Exception as e:
            logger.error(f"❌ [QualityRegression] Failed to create initial baselines: {str(e)}", exc_info=True)

    async def _check_metric_regression(self, metric_name: str, recent_metrics: List[QualityMetrics],
                                     baseline: QualityBaseline) -> Optional[RegressionAlert]:
        """Check if a specific metric shows regression"""
        try:
            # Extract metric values
            if metric_name == 'overall_score':
                current_values = [m.weighted_score for m in recent_metrics]
            elif metric_name == 'generation_time':
                current_values = [m.generation_time_seconds for m in recent_metrics if m.generation_time_seconds > 0]
            elif metric_name == 'golden_similarity':
                current_values = [m.golden_similarity for m in recent_metrics if m.golden_similarity > 0]
            elif metric_name == 'confidence_score':
                current_values = [m.confidence_score for m in recent_metrics if m.confidence_score > 0]
            elif metric_name == 'error_rate':
                current_values = [m.error_count for m in recent_metrics]
            else:
                return None

            if not current_values:
                return None

            current_mean = mean(current_values)

            # Determine regression type and severity
            if metric_name == 'generation_time':
                # For generation time, regression is when it gets significantly slower
                regression_ratio = current_mean / baseline.baseline_value
                if regression_ratio > self.quality_thresholds[metric_name]['severe']:
                    severity = 'severe'
                elif regression_ratio > self.quality_thresholds[metric_name]['moderate']:
                    severity = 'moderate'
                elif regression_ratio > self.quality_thresholds[metric_name]['minor']:
                    severity = 'minor'
                else:
                    return None
            else:
                # For quality metrics, regression is when they get significantly lower
                if metric_name == 'error_rate':
                    # For error rate, regression is when it gets higher
                    difference = current_mean - baseline.baseline_value
                else:
                    # For quality scores, regression is when they get lower
                    difference = baseline.baseline_value - current_mean

                thresholds = self.quality_thresholds.get(metric_name, self.quality_thresholds['overall_score'])

                if difference > thresholds['severe']:
                    severity = 'severe'
                elif difference > thresholds['moderate']:
                    severity = 'moderate'
                elif difference > thresholds['minor']:
                    severity = 'minor'
                else:
                    return None

            # Calculate confidence level
            confidence_level = min(0.95, len(current_values) / 20.0)  # Higher confidence with more samples

            # Create alert
            alert = RegressionAlert(
                alert_id=f"regression_{metric_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                metric_name=metric_name,
                current_value=current_mean,
                baseline_value=baseline.baseline_value,
                regression_severity=severity,
                confidence_level=confidence_level,
                detected_at=datetime.utcnow(),
                survey_ids=[m.survey_id for m in recent_metrics],
                description=self._create_alert_description(metric_name, current_mean, baseline.baseline_value, severity),
                recommended_actions=self._get_recommended_actions(metric_name, severity)
            )

            logger.warning(f"⚠️ [QualityRegression] {severity.upper()} regression detected in {metric_name}: "
                         f"current={current_mean:.3f}, baseline={baseline.baseline_value:.3f}")

            return alert

        except Exception as e:
            logger.error(f"❌ [QualityRegression] Failed to check metric regression for {metric_name}: {str(e)}", exc_info=True)
            return None

    def _create_alert_description(self, metric_name: str, current_value: float,
                                baseline_value: float, severity: str) -> str:
        """Create human-readable alert description"""
        if metric_name == 'overall_score':
            return (f"{severity.title()} regression in overall survey quality detected. "
                   f"Current score: {current_value:.3f}, Baseline: {baseline_value:.3f}")
        elif metric_name == 'generation_time':
            return (f"{severity.title()} regression in generation speed detected. "
                   f"Current time: {current_value:.1f}s, Baseline: {baseline_value:.1f}s")
        elif metric_name == 'golden_similarity':
            return (f"{severity.title()} regression in golden example similarity detected. "
                   f"Current similarity: {current_value:.3f}, Baseline: {baseline_value:.3f}")
        elif metric_name == 'confidence_score':
            return (f"{severity.title()} regression in generation confidence detected. "
                   f"Current confidence: {current_value:.3f}, Baseline: {baseline_value:.3f}")
        elif metric_name == 'error_rate':
            return (f"{severity.title()} increase in error rate detected. "
                   f"Current rate: {current_value:.3f}, Baseline: {baseline_value:.3f}")
        else:
            return f"{severity.title()} regression detected in {metric_name}"

    def _get_recommended_actions(self, metric_name: str, severity: str) -> List[str]:
        """Get recommended actions for regression type"""
        base_actions = [
            "Review recent system changes",
            "Check LLM model performance",
            "Verify API response times",
            "Review recent survey examples"
        ]

        if metric_name == 'overall_score':
            return base_actions + [
                "Review prompt engineering changes",
                "Check golden example quality",
                "Verify pillar scoring accuracy"
            ]
        elif metric_name == 'generation_time':
            return [
                "Check API response times",
                "Review system resource usage",
                "Monitor network connectivity",
                "Check for increased prompt complexity"
            ]
        elif metric_name == 'golden_similarity':
            return [
                "Review golden example selection algorithm",
                "Check embedding service performance",
                "Verify similarity calculation accuracy",
                "Update golden example database"
            ]
        elif metric_name == 'error_rate':
            return [
                "Review recent error logs",
                "Check API authentication",
                "Verify input validation",
                "Monitor system dependencies"
            ]

        return base_actions

    async def _store_regression_alert(self, alert: RegressionAlert):
        """Store regression alert in database"""
        try:
            if not self.db_session:
                logger.warning("⚠️ [QualityRegression] No database session available for storing alert")
                return

            # This would store alert in regression_alerts table
            logger.info(f"🚨 [QualityRegression] Storing {alert.regression_severity} regression alert for {alert.metric_name}")

        except Exception as e:
            logger.error(f"❌ [QualityRegression] Failed to store regression alert: {str(e)}", exc_info=True)

    async def _store_baselines(self, baselines: Dict[str, QualityBaseline]):
        """Store quality baselines in database"""
        try:
            if not self.db_session:
                logger.warning("⚠️ [QualityRegression] No database session available for storing baselines")
                return

            # This would store baselines in quality_baselines table
            logger.info(f"📊 [QualityRegression] Storing {len(baselines)} quality baselines")

        except Exception as e:
            logger.error(f"❌ [QualityRegression] Failed to store baselines: {str(e)}", exc_info=True)


# Global instance
quality_regression_service = QualityRegressionService()