from sqlalchemy.orm import Session
from sqlalchemy import func, text
from src.database import Survey, Edit, GoldenRFQSurveyPair
from src.config import settings
from typing import Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel


class TrainingDataStatus(BaseModel):
    edits_collected: int
    min_edits_threshold: int
    golden_pairs_available: int
    min_golden_pairs_threshold: int
    ready_for_sft: bool


class QualityTrends(BaseModel):
    cleanup_time_trends: Dict[str, Any]
    edit_density_trends: Dict[str, Any]
    golden_similarity_trends: Dict[str, Any]


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_training_data_status(self) -> TrainingDataStatus:
        """
        Get current collection status vs thresholds for training readiness
        """
        try:
            # Count collected edits
            edits_count = self.db.query(Edit).count()
            
            # Count available golden pairs
            golden_pairs_count = self.db.query(GoldenRFQSurveyPair).count()
            
            # Get thresholds from settings
            min_edits = settings.min_edits_for_sft_prep
            min_golden = settings.min_golden_pairs_for_similarity
            
            # Check readiness for SFT
            ready_for_sft = (
                edits_count >= min_edits and 
                golden_pairs_count >= min_golden
            )
            
            return TrainingDataStatus(
                edits_collected=edits_count,
                min_edits_threshold=min_edits,
                golden_pairs_available=golden_pairs_count,
                min_golden_pairs_threshold=min_golden,
                ready_for_sft=ready_for_sft
            )
            
        except Exception as e:
            raise Exception(f"Failed to get training data status: {str(e)}")
    
    def get_quality_trends(self, days: int = 30) -> QualityTrends:
        """
        Get cleanup time and edit density trends over specified period
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Cleanup time trends
            cleanup_times = self.db.query(
                func.date(Survey.created_at).label('date'),
                func.avg(Survey.cleanup_minutes_actual).label('avg_cleanup_time')
            ).filter(
                Survey.created_at >= start_date,
                Survey.cleanup_minutes_actual.isnot(None)
            ).group_by(
                func.date(Survey.created_at)
            ).order_by('date').all()
            
            cleanup_trend = {
                "daily_averages": [
                    {
                        "date": str(row.date),
                        "avg_cleanup_minutes": float(row.avg_cleanup_time) if row.avg_cleanup_time else 0
                    }
                    for row in cleanup_times
                ],
                "overall_average": (
                    sum(float(row.avg_cleanup_time) for row in cleanup_times if row.avg_cleanup_time) / 
                    len([row for row in cleanup_times if row.avg_cleanup_time])
                ) if cleanup_times else 0
            }
            
            # Edit density trends (edits per survey)
            edit_density = self.db.query(
                func.date(Survey.created_at).label('date'),
                func.count(Edit.id).label('edit_count'),
                func.count(Survey.id).label('survey_count')
            ).outerjoin(
                Edit, Survey.id == Edit.survey_id
            ).filter(
                Survey.created_at >= start_date
            ).group_by(
                func.date(Survey.created_at)
            ).order_by('date').all()
            
            edit_trend = {
                "daily_ratios": [
                    {
                        "date": str(row.date),
                        "edits_per_survey": (
                            float(row.edit_count) / float(row.survey_count) 
                            if row.survey_count > 0 else 0
                        )
                    }
                    for row in edit_density
                ]
            }
            
            # Golden similarity trends
            similarity_trends = self.db.query(
                func.date(Survey.created_at).label('date'),
                func.avg(Survey.golden_similarity_score).label('avg_similarity')
            ).filter(
                Survey.created_at >= start_date,
                Survey.golden_similarity_score.isnot(None)
            ).group_by(
                func.date(Survey.created_at)
            ).order_by('date').all()
            
            similarity_trend = {
                "daily_averages": [
                    {
                        "date": str(row.date),
                        "avg_similarity_score": float(row.avg_similarity) if row.avg_similarity else 0
                    }
                    for row in similarity_trends
                ],
                "target_threshold": settings.golden_similarity_threshold
            }
            
            return QualityTrends(
                cleanup_time_trends=cleanup_trend,
                edit_density_trends=edit_trend,
                golden_similarity_trends=similarity_trend
            )
            
        except Exception as e:
            raise Exception(f"Failed to get quality trends: {str(e)}")
    
    def compare_model_performance(
        self,
        model_a: str,
        model_b: str,
        test_rfqs: int = 10
    ) -> Dict[str, Any]:
        """
        A/B test different model configurations
        TODO: Implement actual model comparison with test RFQs
        """
        try:
            # Placeholder implementation for A/B testing
            # In reality, this would:
            # 1. Take a set of test RFQs
            # 2. Generate surveys with both models
            # 3. Compare quality metrics (golden similarity, validation scores, etc.)
            # 4. Return statistical comparison
            
            comparison_results = {
                "model_a": {
                    "name": model_a,
                    "avg_similarity_score": 0.78,
                    "avg_generation_time": 25.3,
                    "validation_pass_rate": 0.85,
                    "avg_edit_count": 2.1
                },
                "model_b": {
                    "name": model_b,
                    "avg_similarity_score": 0.82,
                    "avg_generation_time": 31.7,
                    "validation_pass_rate": 0.91,
                    "avg_edit_count": 1.6
                },
                "statistical_significance": {
                    "similarity_score_p_value": 0.03,
                    "edit_count_p_value": 0.01,
                    "significant_difference": True
                },
                "recommendation": f"Model {model_b} shows significantly better performance",
                "test_parameters": {
                    "test_rfqs_count": test_rfqs,
                    "test_date": datetime.utcnow().isoformat(),
                    "confidence_level": 0.95
                }
            }
            
            return comparison_results
            
        except Exception as e:
            raise Exception(f"Failed to compare model performance: {str(e)}")
    
    def get_methodology_compliance_stats(self) -> Dict[str, Any]:
        """
        Get statistics on methodology compliance across different survey types
        TODO: Implement methodology compliance tracking
        """
        try:
            # Placeholder implementation
            # Would track compliance rates for different methodologies (VW, GG, Conjoint)
            
            return {
                "overall_compliance_rate": 0.87,
                "methodology_breakdown": {
                    "VW": {"compliance_rate": 0.92, "total_surveys": 45},
                    "GG": {"compliance_rate": 0.83, "total_surveys": 32},
                    "Conjoint": {"compliance_rate": 0.89, "total_surveys": 28}
                },
                "common_compliance_issues": [
                    {"issue": "Missing pricing questions", "frequency": 15},
                    {"issue": "Incorrect price point count", "frequency": 8},
                    {"issue": "Too many conjoint attributes", "frequency": 5}
                ]
            }
            
        except Exception as e:
            raise Exception(f"Failed to get compliance stats: {str(e)}")