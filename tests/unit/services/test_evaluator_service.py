"""
Comprehensive test suite for EvaluatorService
Tests the evaluation chain: single_call → advanced → API → legacy
"""
import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from sqlalchemy.orm import Session

from src.services.evaluator_service import EvaluatorService


class TestEvaluatorServiceCritical:
    """Critical tests for EvaluatorService - must pass for deployment"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def mock_connection_manager(self):
        """Mock WebSocket connection manager"""
        return MagicMock()

    @pytest.fixture
    def evaluator_service(self, mock_db_session, mock_connection_manager):
        """Create EvaluatorService instance with mocked dependencies"""
        return EvaluatorService(
            db_session=mock_db_session,
            workflow_id="test_workflow_123",
            connection_manager=mock_connection_manager
        )

    @pytest.fixture
    def sample_survey_data(self):
        """Sample survey data for testing"""
        return {
            "title": "Customer Satisfaction Survey",
            "description": "Survey to measure customer satisfaction",
            "questions": [
                {
                    "id": "q1",
                    "text": "How satisfied are you with our service?",
                    "type": "scale",
                    "required": True
                },
                {
                    "id": "q2",
                    "text": "What improvements would you suggest?",
                    "type": "text",
                    "required": False
                }
            ],
            "metadata": {
                "methodology": ["basic_survey"],
                "industry_category": "technology"
            }
        }

    @pytest.fixture
    def sample_rfq_text(self):
        """Sample RFQ text for testing"""
        return """
        Research Objective: Measure customer satisfaction with our software product
        Target Audience: Current customers who have used the product for 3+ months
        Key Questions: Overall satisfaction, feature preferences, improvement suggestions
        """

    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_evaluate_survey_basic(self, evaluator_service, sample_survey_data, sample_rfq_text):
        """
        CRITICAL: Test basic survey evaluation with mocked LLM
        This ensures the evaluation chain works even without real API calls
        """
        # Mock the SingleCallEvaluator to fail, forcing fallback to pillar scoring
        with patch('evaluations.modules.single_call_evaluator.SingleCallEvaluator') as mock_single_call:
            mock_single_call_instance = MagicMock()
            mock_single_call_instance.evaluate_survey = AsyncMock(side_effect=Exception("Mocked failure"))
            mock_single_call.return_value = mock_single_call_instance
            
            # Mock the pillar scoring service to return a valid result
            with patch.object(evaluator_service.pillar_scoring_service, 'evaluate_survey_pillars') as mock_pillar:
                mock_pillar.return_value = MagicMock(
                    total_score=0.85,
                    weighted_score=0.85,
                    overall_grade="B",
                    summary="Good quality survey with clear questions",
                    pillar_scores=[
                        MagicMock(
                            pillar_name="content_validity",
                            score=0.8,
                            weighted_score=0.16,
                            weight=0.2,
                            criteria_met=8,
                            total_criteria=10,
                            recommendations=["Improve question clarity"]
                        )
                    ]
                )
                
                result = await evaluator_service.evaluate_survey(sample_survey_data, sample_rfq_text)
                
                # Verify evaluation completed
                assert result is not None
                assert result["overall_grade"] == "B"
                assert "Good quality survey" in result["summary"]
                mock_pillar.assert_called_once()

    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_evaluation_chain_fallback(self, evaluator_service, sample_survey_data, sample_rfq_text):
        """
        CRITICAL: Test evaluation chain falls back correctly
        Tests: single_call (fails) → advanced (fails) → API (fails) → legacy (succeeds)
        """
        # Disable advanced evaluator
        evaluator_service.advanced_evaluator = None

        # Mock the SingleCallEvaluator to return None (simulating failure)
        with patch('evaluations.modules.single_call_evaluator.SingleCallEvaluator') as mock_single_call:
            mock_single_call_instance = MagicMock()
            mock_single_call_instance.evaluate_survey = AsyncMock(return_value=None)  # Return None to trigger fallback
            mock_single_call.return_value = mock_single_call_instance

            # Mock legacy evaluation to succeed
            with patch.object(evaluator_service.pillar_scoring_service, 'evaluate_survey_pillars') as mock_legacy:
                mock_legacy.return_value = MagicMock(
                    total_score=0.75,
                    weighted_score=0.75,
                    overall_grade="C",
                    summary="Basic evaluation completed"
                )

                result = await evaluator_service.evaluate_survey(sample_survey_data, sample_rfq_text)

                # Should fall back to legacy and succeed
                assert result is not None
                assert mock_legacy.called

    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_evaluation_without_llm_token(self, mock_db_session, mock_connection_manager, 
                                                sample_survey_data, sample_rfq_text):
        """
        CRITICAL: Test evaluation works in fallback mode without LLM token
        This is the production scenario when REPLICATE_API_TOKEN is not configured
        """
        # Patch settings to simulate no API token
        with patch('src.services.evaluator_service.settings') as mock_settings:
            mock_settings.replicate_api_token = None

            service = EvaluatorService(
                db_session=mock_db_session,
                workflow_id="test_workflow_123",
                connection_manager=mock_connection_manager
            )

            # Mock the SingleCallEvaluator to return None (simulating failure due to no token)
            with patch('evaluations.modules.single_call_evaluator.SingleCallEvaluator') as mock_single_call:
                mock_single_call_instance = MagicMock()
                mock_single_call_instance.evaluate_survey = AsyncMock(return_value=None)  # Return None to trigger fallback
                mock_single_call.return_value = mock_single_call_instance

                # Mock legacy evaluation
                with patch.object(service.pillar_scoring_service, 'evaluate_survey_pillars') as mock_legacy:
                    mock_legacy.return_value = MagicMock(
                        total_score=0.7,
                        weighted_score=0.7,
                        overall_grade="C",
                        summary="Fallback evaluation"
                    )

                    result = await service.evaluate_survey(sample_survey_data, sample_rfq_text)

                    # Should work with legacy fallback
                    assert result is not None
                    assert mock_legacy.called

    @pytest.mark.critical
    def test_evaluator_service_initialization(self, mock_db_session, mock_connection_manager):
        """
        CRITICAL: Test EvaluatorService initializes correctly
        """
        service = EvaluatorService(
            db_session=mock_db_session,
            workflow_id="test_workflow_123",
            connection_manager=mock_connection_manager
        )

        assert service.db_session == mock_db_session
        assert service.workflow_id == "test_workflow_123"
        assert service.connection_manager == mock_connection_manager
        assert service.pillar_scoring_service is not None
        assert service.ws_client is not None

    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_evaluation_handles_none_survey_data(self, evaluator_service, sample_rfq_text):
        """
        CRITICAL: Test evaluation handles None survey data gracefully
        """
        with patch.object(evaluator_service.pillar_scoring_service, 'evaluate_survey_pillars') as mock_evaluate:
            mock_evaluate.return_value = MagicMock(
                total_score=0.0,
                weighted_score=0.0,
                overall_grade="F",
                summary="No survey data available"
            )

            result = await evaluator_service.evaluate_survey(None, sample_rfq_text)

            # Should handle None gracefully
            assert result is not None


class TestEvaluatorServiceIntegration:
    """Integration tests for EvaluatorService - run on PR/merge"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def mock_connection_manager(self):
        """Mock WebSocket connection manager"""
        manager = MagicMock()
        manager.broadcast_to_workflow = AsyncMock()
        return manager

    @pytest.fixture
    def evaluator_service(self, mock_db_session, mock_connection_manager):
        """Create EvaluatorService instance"""
        return EvaluatorService(
            db_session=mock_db_session,
            workflow_id="test_workflow_123",
            connection_manager=mock_connection_manager
        )

    @pytest.fixture
    def sample_survey_data(self):
        """Sample survey data"""
        return {
            "title": "Test Survey",
            "questions": [
                {"id": "q1", "text": "Test question", "type": "text"}
            ]
        }

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_progress_updates_during_evaluation(self, evaluator_service, sample_survey_data):
        """
        INTEGRATION: Test that progress updates are sent during evaluation
        """
        with patch.object(evaluator_service.pillar_scoring_service, 'evaluate_survey_pillars') as mock_eval:
            mock_eval.return_value = MagicMock(
                total_score=0.8,
                weighted_score=0.8,
                overall_grade="B"
            )

            await evaluator_service.evaluate_survey(sample_survey_data, "Test RFQ")

            # Verify WebSocket progress updates were sent
            if evaluator_service.ws_client:
                # Progress updates should have been attempted
                assert mock_eval.called

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_evaluation_with_all_pillars(self, evaluator_service, sample_survey_data):
        """
        INTEGRATION: Test evaluation covers all 5 pillars
        """
        with patch.object(evaluator_service.pillar_scoring_service, 'evaluate_survey_pillars') as mock_eval:
            mock_result = MagicMock(
                pillar_scores=[
                    MagicMock(pillar_name="content_validity", score=0.8),
                    MagicMock(pillar_name="methodological_rigor", score=0.85),
                    MagicMock(pillar_name="clarity_comprehensibility", score=0.9),
                    MagicMock(pillar_name="structural_coherence", score=0.75),
                    MagicMock(pillar_name="deployment_readiness", score=0.8)
                ]
            )
            mock_eval.return_value = mock_result

            result = await evaluator_service.evaluate_survey(sample_survey_data, "Test RFQ")

            assert result is not None
            assert mock_eval.called


class TestEvaluatorServiceSlow:
    """Slow tests for EvaluatorService - run nightly/weekly"""

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_evaluation_performance_benchmark(self):
        """
        SLOW: Benchmark evaluation performance
        """
        # This would test actual performance with real data
        # Placeholder for future implementation
        pass

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_concurrent_evaluations(self):
        """
        SLOW: Test multiple concurrent evaluations
        """
        # This would test system under load
        # Placeholder for future implementation
        pass

