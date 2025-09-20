"""
Quality Integration Service

Integrates quality monitoring with the survey generation pipeline.
Automatically records quality metrics and triggers regression detection.
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from .quality_regression_service import QualityRegressionService, QualityMetrics
from ..database.quality_models import QualityMetrics as QualityMetricsDB
from ..database.connection import get_db

logger = logging.getLogger(__name__)


class QualityIntegrationService:
    """Service to integrate quality monitoring with survey generation"""

    def __init__(self, db_session: Session = None):
        self.db_session = db_session
        self.quality_service = QualityRegressionService(db_session=db_session)

    async def record_generation_quality(self,
                                      survey_data: Dict[str, Any],
                                      generation_context: Dict[str, Any]) -> None:
        """Record quality metrics for a generated survey"""
        try:
            logger.info(f"📊 [QualityIntegration] Recording generation quality for survey: {survey_data.get('survey_id', 'unknown')}")

            # Record metrics using the quality service
            await self.quality_service.record_quality_metrics(survey_data, generation_context)

            # Store in database if session available
            if self.db_session:
                await self._store_quality_metrics_db(survey_data, generation_context)

            logger.info(f"✅ [QualityIntegration] Quality metrics recorded successfully")

        except Exception as e:
            logger.error(f"❌ [QualityIntegration] Failed to record generation quality: {str(e)}", exc_info=True)

    async def check_and_alert_regressions(self, lookback_hours: int = 6) -> int:
        """Check for quality regressions and send alerts if needed"""
        try:
            logger.info(f"🔍 [QualityIntegration] Checking for regressions in last {lookback_hours} hours")

            alerts = await self.quality_service.detect_regressions(lookback_hours=lookback_hours)

            if alerts:
                logger.warning(f"⚠️ [QualityIntegration] {len(alerts)} quality regressions detected")

                # Send notifications for severe alerts
                severe_alerts = [a for a in alerts if a.regression_severity == 'severe']
                if severe_alerts:
                    await self._send_severe_alert_notifications(severe_alerts)

                return len(alerts)
            else:
                logger.info(f"✅ [QualityIntegration] No quality regressions detected")
                return 0

        except Exception as e:
            logger.error(f"❌ [QualityIntegration] Failed to check regressions: {str(e)}", exc_info=True)
            return 0

    async def get_quality_health_status(self) -> Dict[str, Any]:
        """Get overall quality health status"""
        try:
            logger.info(f"🩺 [QualityIntegration] Getting quality health status")

            # Get recent trends
            trends = await self.quality_service.get_quality_trends(days=7)

            # Get active alerts
            alerts = await self.quality_service.get_regression_alerts(hours=24)

            # Calculate health score
            health_score = await self._calculate_health_score(trends, alerts)

            return {
                "health_score": health_score,
                "status": self._get_health_status_text(health_score),
                "active_alerts": len(alerts),
                "severe_alerts": len([a for a in alerts if a.regression_severity == 'severe']),
                "recent_trends": trends,
                "last_updated": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ [QualityIntegration] Failed to get health status: {str(e)}", exc_info=True)
            return {
                "health_score": 0.5,
                "status": "unknown",
                "active_alerts": 0,
                "severe_alerts": 0,
                "error": str(e)
            }

    async def trigger_baseline_update_if_needed(self) -> bool:
        """Update baselines if they're outdated"""
        try:
            logger.info(f"🔄 [QualityIntegration] Checking if baseline update is needed")

            # Get current baselines
            baselines = await self.quality_service._get_quality_baselines()

            # Check if any baseline is older than 7 days
            if baselines:
                oldest_baseline = min(
                    baseline.created_at for baseline in baselines.values()
                )
                days_old = (datetime.utcnow() - oldest_baseline).days

                if days_old > 7:
                    logger.info(f"🔄 [QualityIntegration] Baselines are {days_old} days old, updating")
                    await self.quality_service.update_baselines(period_days=30)
                    return True
                else:
                    logger.info(f"✅ [QualityIntegration] Baselines are current ({days_old} days old)")
                    return False
            else:
                logger.info(f"🔄 [QualityIntegration] No baselines exist, creating initial ones")
                await self.quality_service.update_baselines(period_days=30)
                return True

        except Exception as e:
            logger.error(f"❌ [QualityIntegration] Failed to check/update baselines: {str(e)}", exc_info=True)
            return False

    async def _store_quality_metrics_db(self, survey_data: Dict[str, Any],
                                      generation_context: Dict[str, Any]) -> None:
        """Store quality metrics directly in database"""
        try:
            pillar_scores = survey_data.get('pillar_scores', {})
            survey = survey_data.get('survey', {})

            # Create database record
            metrics_record = QualityMetricsDB(
                survey_id=survey_data.get('survey_id'),
                workflow_id=generation_context.get('workflow_id', ''),
                overall_grade=pillar_scores.get('overall_grade', 'F'),
                weighted_score=pillar_scores.get('weighted_score', 0.0),
                confidence_score=survey.get('confidence_score'),
                pillar_scores=pillar_scores.get('pillar_breakdown', {}),
                generation_time_seconds=generation_context.get('generation_time_seconds'),
                golden_similarity=generation_context.get('golden_similarity'),
                methodology_compliance=self._check_methodology_compliance(survey_data),
                error_count=len(generation_context.get('errors', [])),
                methodology_tags=survey.get('methodologies', []),
                rfq_complexity_score=self._calculate_rfq_complexity(generation_context)
            )

            self.db_session.add(metrics_record)
            self.db_session.commit()

            logger.debug(f"📊 [QualityIntegration] Quality metrics stored in database")

        except Exception as e:
            logger.error(f"❌ [QualityIntegration] Failed to store metrics in DB: {str(e)}", exc_info=True)
            if self.db_session:
                self.db_session.rollback()

    def _check_methodology_compliance(self, survey_data: Dict[str, Any]) -> bool:
        """Check methodology compliance for the survey"""
        try:
            survey = survey_data.get('survey', {})
            methodologies = survey.get('methodologies', [])
            sections = survey.get('sections', [])

            if not sections:
                return False

            # Count total questions
            total_questions = sum(len(section.get('questions', [])) for section in sections)
            if total_questions < 3:
                return False

            # Check methodology-specific requirements
            for methodology in methodologies:
                if methodology == 'van_westendorp':
                    pricing_questions = sum(
                        1 for section in sections
                        for q in section.get('questions', [])
                        if q.get('methodology') == 'van_westendorp'
                    )
                    if pricing_questions != 4:
                        return False

                elif methodology == 'nps':
                    nps_questions = sum(
                        1 for section in sections
                        for q in section.get('questions', [])
                        if q.get('methodology') == 'nps'
                    )
                    if nps_questions == 0:
                        return False

            return True

        except Exception as e:
            logger.error(f"❌ [QualityIntegration] Error checking methodology compliance: {str(e)}")
            return False

    def _calculate_rfq_complexity(self, generation_context: Dict[str, Any]) -> float:
        """Calculate complexity score for the RFQ"""
        try:
            rfq_text = generation_context.get('rfq_text', '')

            # Simple complexity heuristics
            word_count = len(rfq_text.split())

            # Base complexity on word count
            if word_count < 50:
                complexity = 0.2
            elif word_count < 150:
                complexity = 0.4
            elif word_count < 300:
                complexity = 0.6
            elif word_count < 500:
                complexity = 0.8
            else:
                complexity = 1.0

            # Adjust for methodology complexity
            methodologies = generation_context.get('methodologies', [])
            complex_methodologies = ['van_westendorp', 'conjoint', 'maxdiff']

            for methodology in methodologies:
                if methodology in complex_methodologies:
                    complexity += 0.2

            return min(1.0, complexity)

        except Exception as e:
            logger.error(f"❌ [QualityIntegration] Error calculating RFQ complexity: {str(e)}")
            return 0.5

    async def _send_severe_alert_notifications(self, severe_alerts: list) -> None:
        """Send notifications for severe quality alerts"""
        try:
            logger.warning(f"🚨 [QualityIntegration] Sending notifications for {len(severe_alerts)} severe alerts")

            # Here you would integrate with your notification system
            # Examples: Slack, email, PagerDuty, etc.

            for alert in severe_alerts:
                logger.critical(
                    f"🚨 SEVERE QUALITY REGRESSION: {alert.metric_name} - "
                    f"Current: {alert.current_value:.3f}, "
                    f"Baseline: {alert.baseline_value:.3f}, "
                    f"Description: {alert.description}"
                )

            # Mock notification (replace with actual notification service)
            logger.info(f"🔔 [QualityIntegration] Severe alert notifications sent")

        except Exception as e:
            logger.error(f"❌ [QualityIntegration] Failed to send alert notifications: {str(e)}", exc_info=True)

    async def _calculate_health_score(self, trends: Dict[str, Any], alerts: list) -> float:
        """Calculate overall quality health score (0.0 to 1.0)"""
        try:
            health_score = 1.0

            # Penalize for active alerts
            severe_alerts = len([a for a in alerts if a.regression_severity == 'severe'])
            moderate_alerts = len([a for a in alerts if a.regression_severity == 'moderate'])
            minor_alerts = len([a for a in alerts if a.regression_severity == 'minor'])

            health_score -= (severe_alerts * 0.3 + moderate_alerts * 0.15 + minor_alerts * 0.05)

            # Adjust for trends (if available)
            if trends:
                declining_trends = sum(1 for trend in trends.values() if trend and trend[-1] < trend[0])
                total_trends = len([t for t in trends.values() if t])

                if total_trends > 0:
                    trend_penalty = (declining_trends / total_trends) * 0.2
                    health_score -= trend_penalty

            return max(0.0, min(1.0, health_score))

        except Exception as e:
            logger.error(f"❌ [QualityIntegration] Error calculating health score: {str(e)}")
            return 0.5

    def _get_health_status_text(self, health_score: float) -> str:
        """Convert health score to status text"""
        if health_score >= 0.9:
            return "excellent"
        elif health_score >= 0.8:
            return "good"
        elif health_score >= 0.7:
            return "fair"
        elif health_score >= 0.6:
            return "poor"
        else:
            return "critical"


# Decorator to automatically record quality metrics
def record_quality_metrics(func):
    """Decorator to automatically record quality metrics after survey generation"""
    async def wrapper(*args, **kwargs):
        start_time = datetime.utcnow()

        try:
            # Call the original function
            result = await func(*args, **kwargs)

            # Calculate generation time
            generation_time = (datetime.utcnow() - start_time).total_seconds()

            # Extract context for quality recording
            generation_context = {
                'generation_time_seconds': generation_time,
                'workflow_id': kwargs.get('workflow_id', ''),
                'errors': [],
                'golden_similarity': kwargs.get('golden_similarity', 0.0)
            }

            # Record quality metrics
            try:
                quality_integration = QualityIntegrationService()
                await quality_integration.record_generation_quality(result, generation_context)
            except Exception as e:
                logger.error(f"❌ [QualityDecorator] Failed to record quality metrics: {str(e)}")

            return result

        except Exception as e:
            # Record error in quality metrics
            generation_time = (datetime.utcnow() - start_time).total_seconds()
            generation_context = {
                'generation_time_seconds': generation_time,
                'workflow_id': kwargs.get('workflow_id', ''),
                'errors': [str(e)],
                'golden_similarity': 0.0
            }

            try:
                quality_integration = QualityIntegrationService()
                error_result = {
                    'survey_id': kwargs.get('survey_id', 'error'),
                    'survey': {'confidence_score': 0.0},
                    'pillar_scores': {'overall_grade': 'F', 'weighted_score': 0.0}
                }
                await quality_integration.record_generation_quality(error_result, generation_context)
            except Exception as quality_e:
                logger.error(f"❌ [QualityDecorator] Failed to record error quality metrics: {str(quality_e)}")

            raise e

    return wrapper


# Global instance
quality_integration_service = QualityIntegrationService()