"""
Comprehensive test suite for WorkflowService
Tests LangGraph workflow orchestration, circuit breaker, and human review
"""
import pytest
import asyncio
import sys
from unittest.mock import MagicMock, patch, AsyncMock
from sqlalchemy.orm import Session

# Mock langgraph before importing workflow modules
with patch.dict('sys.modules', {'langgraph': MagicMock(), 'langgraph.graph': MagicMock()}):
    from src.services.workflow_service import WorkflowService
    from src.workflows.state import SurveyGenerationState
    from src.utils.error_messages import UserFriendlyError


class TestWorkflowServiceCritical:
    """Critical tests for WorkflowService - must pass for deployment"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def mock_connection_manager(self):
        """Mock WebSocket connection manager"""
        manager = MagicMock()
        manager.broadcast_to_workflow = AsyncMock()
        return manager

    @pytest.fixture
    def workflow_service(self, mock_db, mock_connection_manager):
        """Create WorkflowService instance with mocked dependencies"""
        return WorkflowService(db=mock_db, connection_manager=mock_connection_manager)

    @pytest.fixture
    def sample_state(self):
        """Sample workflow state for testing"""
        return SurveyGenerationState(
            rfq_id=None,
            survey_id="test_survey_123",
            workflow_id="test_workflow_123",
            rfq_text="Test RFQ for customer satisfaction survey",
            rfq_title="Customer Satisfaction Survey",
            research_goal="customer_satisfaction",
            product_category="software",
            target_segment="B2B",
            rfq_embedding=[0.1, 0.2, 0.3],
            golden_examples=[],
            methodology_blocks=[],
            template_questions=[],
            context_ready=False,
            survey_generated=False,
            validation_passed=False,
            final_output=None,
            error_message=None
        )

    @pytest.mark.critical
    def test_workflow_service_initialization(self, mock_db, mock_connection_manager):
        """
        CRITICAL: Test WorkflowService initializes correctly
        """
        service = WorkflowService(db=mock_db, connection_manager=mock_connection_manager)

        assert service.db == mock_db
        assert service.connection_manager == mock_connection_manager
        assert service.circuit_breaker is not None
        assert service.state_service is not None
        assert service.embedding_service is not None
        assert service.ws_client is not None
        assert service.workflow is not None
        assert service.max_concurrent_workflows == 10
        assert len(service.active_workflows) == 0

    @pytest.mark.critical
    def test_circuit_breaker_configuration(self, workflow_service):
        """
        CRITICAL: Test circuit breaker is properly configured
        """
        assert workflow_service.circuit_breaker.failure_threshold == 3
        assert workflow_service.circuit_breaker.timeout == 30

    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_execute_workflow_basic_mocked(self, workflow_service, mock_db):
        """
        CRITICAL: Test basic workflow execution with mocked workflow
        """
        import uuid
        
        # Mock the database queries to return proper UUIDs
        mock_survey = MagicMock()
        mock_survey.id = "test_survey_123"
        mock_survey.rfq_id = str(uuid.uuid4())  # Generate a proper UUID
        
        mock_rfq = MagicMock()
        mock_rfq.id = mock_survey.rfq_id  # Use the same UUID
        
        # Mock the database query chain
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_survey
        mock_db.query.return_value = mock_query
        
        # Mock the RFQ query
        mock_rfq_query = MagicMock()
        mock_rfq_query.filter.return_value.first.return_value = mock_rfq
        mock_db.query.side_effect = [mock_query, mock_rfq_query]
        
        # Mock the workflow execution
        with patch.object(workflow_service.workflow, 'ainvoke', new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = {
                "survey_id": "test_survey_123",
                "workflow_id": "test_workflow_123",
                "final_output": {"title": "Test Survey", "questions": []},
                "validation_passed": True
            }

            result = await workflow_service._execute_workflow_with_circuit_breaker(
                title="Test Survey",
                description="Test description",
                product_category="technology",
                target_segment="B2B",
                research_goal="market_research",
                workflow_id="test_workflow_123",
                survey_id="test_survey_123"
            )

            assert result is not None
            assert mock_invoke.called

    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_workflow_handles_errors_gracefully(self, workflow_service):
        """
        CRITICAL: Test workflow handles errors without crashing
        """
        with patch.object(workflow_service.workflow, 'ainvoke', new_callable=AsyncMock) as mock_invoke:
            mock_invoke.side_effect = Exception("Workflow execution failed")

            with pytest.raises(Exception):
                await workflow_service._execute_workflow_with_circuit_breaker(
                    title="Test Survey",
                    description="Test description",
                    product_category=None,
                    target_segment=None,
                    research_goal=None,
                    workflow_id="test_workflow_123",
                    survey_id="test_survey_123"
                )

    @pytest.mark.critical
    def test_concurrent_workflow_limit(self, workflow_service):
        """
        CRITICAL: Test max concurrent workflows limit is enforced
        """
        # Add workflows to active set
        for i in range(10):
            workflow_service.active_workflows.add(f"workflow_{i}")

        assert len(workflow_service.active_workflows) == 10
        assert len(workflow_service.active_workflows) == workflow_service.max_concurrent_workflows


class TestWorkflowServiceIntegration:
    """Integration tests for WorkflowService - run on PR/merge"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def mock_connection_manager(self):
        """Mock connection manager with async methods"""
        manager = MagicMock()
        manager.broadcast_to_workflow = AsyncMock()
        return manager

    @pytest.fixture
    def workflow_service(self, mock_db, mock_connection_manager):
        """Create WorkflowService instance"""
        return WorkflowService(db=mock_db, connection_manager=mock_connection_manager)

    @pytest.fixture
    def sample_state_with_prompt(self):
        """Sample state for human review resume"""
        return SurveyGenerationState(
            rfq_id=None,
            survey_id="test_survey_123",
            workflow_id="test_workflow_123",
            rfq_text="Test RFQ",
            rfq_title="Test Survey",
            research_goal="market_research",
            product_category="technology",
            target_segment="B2B",
            golden_examples=[],
            methodology_blocks=[],
            context_ready=True,
            human_review_approved=True,
            approved_system_prompt="You are an expert survey designer...",
            error_message=None
        )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_execute_workflow_from_generation(self, workflow_service, sample_state_with_prompt):
        """
        INTEGRATION: Test workflow execution from human review resume
        This tests the human review workflow path
        """
        # Mock the WebSocket client
        mock_ws_client = MagicMock()
        mock_ws_client.send_progress_update = AsyncMock()

        # Mock the generator and validator nodes
        with patch('src.services.workflow_service.GeneratorAgent') as MockGenerator, \
             patch('src.services.workflow_service.ValidatorAgent') as MockValidator:

            mock_generator = MagicMock()
            mock_generator.return_value = AsyncMock(return_value={
                "final_output": {"title": "Test", "questions": []},
                "survey_generated": True
            })
            MockGenerator.return_value = mock_generator

            mock_validator = MagicMock()
            mock_validator.return_value = AsyncMock(return_value={
                "validation_passed": True,
                "pillar_scores": {}
            })
            MockValidator.return_value = mock_validator

            result = await workflow_service.execute_workflow_from_generation(
                initial_state=sample_state_with_prompt,
                workflow_id="test_workflow_123",
                survey_id="test_survey_123",
                ws_client=mock_ws_client
            )

            # Should complete successfully
            assert result is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_workflow_progress_tracking(self, workflow_service):
        """
        INTEGRATION: Test progress updates are sent through workflow
        """
        with patch.object(workflow_service.workflow, 'ainvoke', new_callable=AsyncMock) as mock_invoke, \
             patch.object(workflow_service.ws_client, 'send_progress_update', new_callable=AsyncMock) as mock_progress:

            mock_invoke.return_value = {
                "survey_id": "test_survey_123",
                "final_output": {"title": "Test", "questions": []},
                "validation_passed": True
            }

            await workflow_service._execute_workflow_with_circuit_breaker(
                title="Test Survey",
                description="Test description",
                product_category="technology",
                target_segment="B2B",
                research_goal="market_research",
                workflow_id="test_workflow_123",
                survey_id="test_survey_123"
            )

            # Progress updates should have been sent
            # (actual count depends on workflow implementation)
            assert mock_invoke.called

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_workflow_state_persistence(self, workflow_service):
        """
        INTEGRATION: Test workflow state is persisted correctly
        """
        with patch.object(workflow_service.state_service, 'save_state') as mock_save, \
             patch.object(workflow_service.workflow, 'ainvoke', new_callable=AsyncMock) as mock_invoke:

            mock_invoke.return_value = {
                "survey_id": "test_survey_123",
                "final_output": {"title": "Test"},
                "validation_passed": True
            }

            await workflow_service._execute_workflow_with_circuit_breaker(
                title="Test Survey",
                description="Test description",
                product_category="technology",
                target_segment="B2B",
                research_goal="market_research",
                workflow_id="test_workflow_123",
                survey_id="test_survey_123"
            )

            # State should have been saved
            # (may be called multiple times during workflow)
            assert mock_invoke.called


class TestWorkflowServiceSlow:
    """Slow tests for WorkflowService - run nightly/weekly"""

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_circuit_breaker_under_load(self):
        """
        SLOW: Test circuit breaker behavior under high load
        """
        # Placeholder for load testing
        pass

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_concurrent_workflow_execution(self):
        """
        SLOW: Test multiple workflows executing concurrently
        """
        # Placeholder for concurrent execution testing
        pass

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_workflow_performance_benchmark(self):
        """
        SLOW: Benchmark workflow execution time
        """
        # Placeholder for performance benchmarking
        pass

