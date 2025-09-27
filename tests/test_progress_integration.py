"""
End-to-end integration tests for progress tracking
Tests the complete workflow from backend to frontend coordination
"""
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.orm import Session
import time

# Import the modules directly - the dependencies should be available
from src.workflows.workflow import create_workflow
from src.workflows.state import SurveyGenerationState
from src.services.workflow_service import WorkflowService
from src.services.websocket_client import WebSocketNotificationService


class ProgressTracker:
    """Helper class to track progress updates during integration tests"""
    
    def __init__(self):
        self.progress_history = []
        self.step_transitions = []
        self.errors = []
    
    def record_progress(self, workflow_id: str, message: dict):
        """Record a progress update"""
        if message.get("type") == "progress":
            self.progress_history.append({
                "workflow_id": workflow_id,
                "step": message.get("step"),
                "percent": message.get("percent"),
                "message": message.get("message"),
                "timestamp": time.time()
            })
            
            # Track step transitions
            if len(self.progress_history) > 1:
                prev_step = self.progress_history[-2]["step"]
                curr_step = message.get("step")
                if prev_step != curr_step:
                    self.step_transitions.append((prev_step, curr_step))
        
        elif message.get("type") == "error":
            self.errors.append({
                "workflow_id": workflow_id,
                "error": message.get("message"),
                "timestamp": time.time()
            })
    
    def get_progress_sequence(self):
        """Get the sequence of progress percentages"""
        return [p["percent"] for p in self.progress_history]
    
    def get_step_sequence(self):
        """Get the sequence of step names"""
        return [p["step"] for p in self.progress_history]
    
    def verify_sequential_progress(self):
        """Verify that progress percentages are sequential"""
        percentages = self.get_progress_sequence()
        for i in range(1, len(percentages)):
            assert percentages[i] >= percentages[i-1], \
                f"Progress went backwards: {percentages[i-1]}% -> {percentages[i]}%"
    
    def verify_expected_steps(self, expected_steps):
        """Verify that all expected steps were executed"""
        actual_steps = set(self.get_step_sequence())
        missing_steps = set(expected_steps) - actual_steps
        assert not missing_steps, f"Missing expected steps: {missing_steps}"
    
    def verify_no_errors(self):
        """Verify that no errors occurred during workflow"""
        assert not self.errors, f"Errors occurred during workflow: {self.errors}"


class MockConnectionManager:
    """Mock connection manager that records all messages"""
    
    def __init__(self, progress_tracker: ProgressTracker):
        self.progress_tracker = progress_tracker
        self.connections = {}
    
    async def broadcast_to_workflow(self, workflow_id: str, message: dict):
        """Mock broadcast that records messages"""
        self.progress_tracker.record_progress(workflow_id, message)


@pytest.fixture
def progress_tracker():
    """Progress tracker for recording workflow events"""
    return ProgressTracker()


@pytest.fixture
def mock_connection_manager(progress_tracker):
    """Mock connection manager with progress tracking"""
    return MockConnectionManager(progress_tracker)


@pytest.fixture
def mock_db():
    """Mock database session"""
    return MagicMock(spec=Session)


@pytest.fixture
def sample_state():
    """Sample workflow state for testing"""
    return SurveyGenerationState(
        rfq_id=None,
        survey_id="test-survey-123",
        workflow_id="test-workflow-123",
        rfq_text="We need a comprehensive pricing study for our new smartphone product targeting tech-savvy consumers aged 25-45.",
        rfq_title="Smartphone Pricing Research",
        product_category="electronics",
        target_segment="tech_consumers",
        research_goal="pricing_research",
        workflow_start_time=time.time()
    )


class TestEndToEndProgressFlow:
    """Test complete end-to-end progress tracking"""

    @pytest.mark.asyncio
    async def test_complete_workflow_progress_tracking(self, mock_db, mock_connection_manager, progress_tracker, sample_state):
        """Test that complete workflow sends all expected progress updates"""
        
        # Create workflow with mocked dependencies
        workflow = create_workflow(mock_db, mock_connection_manager)
        
        # Mock all the node implementations
        with patch('src.workflows.nodes.RFQNode') as mock_rfq, \
             patch('src.workflows.nodes.GoldenRetrieverNode') as mock_golden, \
             patch('src.workflows.nodes.ContextBuilderNode') as mock_context, \
             patch('src.workflows.nodes.HumanPromptReviewNode') as mock_human, \
             patch('src.workflows.nodes.GeneratorAgent') as mock_generator, \
             patch('src.workflows.nodes.ValidatorAgent') as mock_validator:
            
            # Setup realistic mock responses
            mock_rfq.return_value = AsyncMock(return_value={
                "rfq_embedding": [0.1, 0.2, 0.3],
                "rfq_parsed": True
            })
            
            mock_golden.return_value = AsyncMock(return_value={
                "golden_examples": [
                    {"rfq_text": "Sample RFQ", "survey_json": {"title": "Sample Survey"}},
                    {"rfq_text": "Another RFQ", "survey_json": {"title": "Another Survey"}}
                ]
            })
            
            mock_context.return_value = AsyncMock(return_value={
                "context": {
                    "methodologies": ["van_westendorp", "conjoint"],
                    "rfq_details": {"category": "electronics", "segment": "tech_consumers"}
                }
            })
            
            mock_human.return_value = AsyncMock(return_value={
                "pending_human_review": False,
                "prompt_approved": True
            })
            
            mock_generator.return_value = AsyncMock(return_value={
                "generated_survey": {
                    "title": "Smartphone Pricing Research",
                    "sections": [
                        {
                            "id": 1,
                            "title": "Screener & Demographics",
                            "questions": [{"id": "q1", "text": "What is your age?", "type": "multiple_choice"}]
                        }
                    ]
                },
                "generation_metadata": {"model": "openai/gpt-5", "response_time_ms": 5000}
            })
            
            mock_validator.return_value = AsyncMock(return_value={
                "quality_gate_passed": True,
                "pillar_scores": {
                    "content_validity": 0.85,
                    "methodological_rigor": 0.90,
                    "clarity_comprehensibility": 0.88,
                    "structural_coherence": 0.87,
                    "deployment_readiness": 0.92
                },
                "overall_score": 0.88
            })
            
            # Execute the complete workflow
            config = workflow.compile()
            result = await config.ainvoke(sample_state)
            
            # Verify progress tracking
            progress_tracker.verify_no_errors()
            progress_tracker.verify_sequential_progress()
            
            # Verify all expected steps were executed
            expected_steps = [
                "parsing_rfq", "generating_embeddings", "rfq_parsed",
                "matching_golden_examples", "planning_methodologies", "build_context",
                "preparing_generation", "parsing_output",
                "validation_scoring", "evaluating_pillars", "finalizing"
            ]
            progress_tracker.verify_expected_steps(expected_steps)
            
            # Verify percentage ranges
            percentages = progress_tracker.get_progress_sequence()
            assert min(percentages) >= 5, f"Minimum percentage too low: {min(percentages)}"
            assert max(percentages) <= 95, f"Maximum percentage too high: {max(percentages)}"
            
            # Verify we have sufficient granularity (at least 10 progress updates)
            assert len(percentages) >= 10, f"Insufficient progress granularity: {len(percentages)} updates"

    @pytest.mark.asyncio
    async def test_workflow_with_human_review_progress(self, mock_db, mock_connection_manager, progress_tracker, sample_state):
        """Test progress tracking when human review is required"""
        
        workflow = create_workflow(mock_db, mock_connection_manager)
        
        # Mock nodes with human review required
        with patch('src.workflows.nodes.RFQNode') as mock_rfq, \
             patch('src.workflows.nodes.GoldenRetrieverNode') as mock_golden, \
             patch('src.workflows.nodes.ContextBuilderNode') as mock_context, \
             patch('src.workflows.nodes.HumanPromptReviewNode') as mock_human:
            
            mock_rfq.return_value = AsyncMock(return_value={"rfq_embedding": [0.1, 0.2, 0.3]})
            mock_golden.return_value = AsyncMock(return_value={"golden_examples": []})
            mock_context.return_value = AsyncMock(return_value={"context": {}})
            
            # Mock human review requiring pause
            mock_human.return_value = AsyncMock(return_value={
                "pending_human_review": True,
                "workflow_paused": True,
                "review_id": 123
            })
            
            # Execute workflow until human review pause
            config = workflow.compile()
            
            # Should raise exception when hitting human review pause
            with pytest.raises(Exception, match="WORKFLOW_PAUSED_FOR_HUMAN_REVIEW"):
                await config.ainvoke(sample_state)
            
            # Verify progress up to human review
            steps = progress_tracker.get_step_sequence()
            assert "parsing_rfq" in steps
            assert "matching_golden_examples" in steps
            assert "planning_methodologies" in steps
            
            # Verify no errors before pause
            progress_tracker.verify_no_errors()
            progress_tracker.verify_sequential_progress()

    @pytest.mark.asyncio
    async def test_workflow_with_quality_gate_failure(self, mock_db, mock_connection_manager, progress_tracker, sample_state):
        """Test progress tracking when quality gate fails"""
        
        workflow = create_workflow(mock_db, mock_connection_manager)
        
        with patch('src.workflows.nodes.RFQNode') as mock_rfq, \
             patch('src.workflows.nodes.GoldenRetrieverNode') as mock_golden, \
             patch('src.workflows.nodes.ContextBuilderNode') as mock_context, \
             patch('src.workflows.nodes.HumanPromptReviewNode') as mock_human, \
             patch('src.workflows.nodes.GeneratorAgent') as mock_generator, \
             patch('src.workflows.nodes.ValidatorAgent') as mock_validator:
            
            # Setup mocks
            mock_rfq.return_value = AsyncMock(return_value={"rfq_embedding": [0.1, 0.2, 0.3]})
            mock_golden.return_value = AsyncMock(return_value={"golden_examples": []})
            mock_context.return_value = AsyncMock(return_value={"context": {}})
            mock_human.return_value = AsyncMock(return_value={"pending_human_review": False})
            mock_generator.return_value = AsyncMock(return_value={"generated_survey": {"title": "Test"}})
            
            # Mock quality gate failure
            mock_validator.return_value = AsyncMock(return_value={
                "quality_gate_passed": False,
                "pillar_scores": {"overall_score": 0.45},  # Below threshold
                "validation_errors": ["Survey quality too low"]
            })
            
            # Execute workflow
            config = workflow.compile()
            result = await config.ainvoke(sample_state)
            
            # Verify workflow completed (didn't retry due to our no-retry policy)
            assert result is not None
            
            # Verify progress tracking included validation steps
            steps = progress_tracker.get_step_sequence()
            assert "validation_scoring" in steps
            assert "evaluating_pillars" in steps
            
            # Verify no infinite loops (should go to completion)
            progress_tracker.verify_sequential_progress()

    @pytest.mark.asyncio
    async def test_async_generation_service_coordination(self, mock_db, mock_connection_manager, progress_tracker):
        """Test that GenerationService coordinates properly with workflow progress"""
        
        from src.services.generation_service import GenerationService
        
        # Create GenerationService with our mock connection manager
        service = GenerationService(
            db_session=mock_db,
            workflow_id="test-workflow-123",
            connection_manager=mock_connection_manager
        )
        
        # Mock replicate client for async polling
        mock_prediction = MagicMock()
        mock_prediction.id = "test-prediction-123"
        mock_prediction.status = "running"
        mock_prediction.output = ["Generated survey content"]
        
        poll_count = 0
        async def mock_reload():
            nonlocal poll_count
            poll_count += 1
            if poll_count >= 3:  # Simulate 3 polling cycles
                mock_prediction.status = "succeeded"
        
        mock_prediction.async_reload = mock_reload
        
        with patch.object(service, 'replicate_client') as mock_client:
            mock_client.predictions.async_create = AsyncMock(return_value=mock_prediction)
            
            # Mock JSON extraction
            with patch.object(service, '_extract_survey_json', return_value={"title": "Test Survey"}):
                start_time = time.time()
                result = await service._generate_with_async_polling("test prompt", start_time)
                
                # Verify progress updates were sent
                steps = progress_tracker.get_step_sequence()
                assert "generating_questions" in steps  # Initial step
                assert "llm_processing" in steps       # Polling updates
                
                # Verify progress coordination (should have multiple updates during polling)
                llm_processing_updates = [
                    p for p in progress_tracker.progress_history 
                    if p["step"] == "llm_processing"
                ]
                assert len(llm_processing_updates) >= 2, "Should have multiple LLM processing updates"
                
                # Verify percentages are in expected range
                percentages = [p["percent"] for p in llm_processing_updates]
                assert all(55 <= p <= 75 for p in percentages), f"LLM processing percentages out of range: {percentages}"


class TestProgressRegressionSafeguards:
    """Test safeguards against progress regressions"""

    @pytest.mark.asyncio
    async def test_no_backward_progress_jumps(self, mock_db, mock_connection_manager, progress_tracker):
        """Test that progress never goes backward"""
        
        # Simulate various progress updates
        ws_client = WebSocketNotificationService(mock_connection_manager)
        workflow_id = "test-workflow-123"
        
        # Send progress updates in sequence
        progress_sequence = [
            ("parsing_rfq", 10),
            ("generating_embeddings", 15),
            ("rfq_parsed", 20),
            ("matching_golden_examples", 25),
            ("planning_methodologies", 30),
            ("preparing_generation", 55),
            ("generating_questions", 60),
            ("llm_processing", 65),
            ("parsing_output", 75),
            ("validation_scoring", 80),
            ("evaluating_pillars", 85),
            ("finalizing", 95),
            ("completed", 100)
        ]
        
        for step, percent in progress_sequence:
            await ws_client.send_progress_update(workflow_id, {
                "type": "progress",
                "step": step,
                "percent": percent,
                "message": f"Processing {step}..."
            })
        
        # Verify no backward progress
        progress_tracker.verify_sequential_progress()
        
        # Verify all steps were recorded
        recorded_steps = progress_tracker.get_step_sequence()
        expected_steps = [step for step, _ in progress_sequence]
        assert recorded_steps == expected_steps

    def test_frontend_step_mapping_completeness(self):
        """Test that all backend steps have corresponding frontend mappings"""
        
        # All possible backend steps (from our implementation)
        all_backend_steps = {
            "initializing_workflow", "parsing_rfq", "generating_embeddings", "rfq_parsed",
            "matching_golden_examples", "planning_methodologies", "build_context",
            "preparing_generation", "generating_questions", "llm_processing", "parsing_output",
            "validation_scoring", "evaluating_pillars", "single_call_evaluator",
            "pillar_scores_analysis", "advanced_evaluation", "legacy_evaluation",
            "fallback_evaluation", "finalizing", "completed", "human_review",
            "resuming_from_human_review", "resuming_generation"
        }
        
        # Expected frontend mapping (should match ProgressStepper.tsx)
        frontend_step_mapping = {
            'generate': 'question_generation',
            'validate': 'quality_evaluation',
            'validation_scoring': 'quality_evaluation',
            'initializing_workflow': 'building_context',
            'parsing_rfq': 'building_context',
            'generating_embeddings': 'building_context',
            'rfq_parsed': 'building_context',
            'matching_golden_examples': 'building_context',
            'planning_methodologies': 'building_context',
            'parse_rfq': 'building_context',
            'retrieve_golden': 'building_context',
            'build_context': 'building_context',
            'preparing_generation': 'question_generation',
            'generating_questions': 'question_generation',
            'llm_processing': 'question_generation',
            'parsing_output': 'question_generation',
            'evaluating_pillars': 'quality_evaluation',
            'single_call_evaluator': 'quality_evaluation',
            'pillar_scores_analysis': 'quality_evaluation',
            'advanced_evaluation': 'quality_evaluation',
            'legacy_evaluation': 'quality_evaluation',
            'fallback_evaluation': 'quality_evaluation',
            'finalizing': 'completion',
            'prompt_review': 'human_review',
            'human_review': 'human_review',
            'resuming_from_human_review': 'question_generation',
            'resuming_generation': 'question_generation',
            'completion_handler': 'completion',
            'completed': 'completion'
        }
        
        # Check that all backend steps have mappings
        unmapped_steps = all_backend_steps - set(frontend_step_mapping.keys())
        assert not unmapped_steps, f"Backend steps without frontend mapping: {unmapped_steps}"

    def test_progress_percentage_ranges_are_valid(self):
        """Test that all progress percentages are within valid ranges"""
        
        # Define expected percentage ranges for each major frontend step (updated to match ProgressTracker)
        frontend_step_ranges = {
            "building_context": (10, 25),
            "human_review": (65, 75),
            "question_generation": (35, 65),
            "quality_evaluation": (75, 95),
            "completion": (95, 100)
        }
        
        # Sample progress updates with their expected frontend step mappings (updated to match ProgressTracker)
        progress_samples = [
            ("initializing_workflow", 5, "building_context"),
            ("parsing_rfq", 10, "building_context"),
            ("generating_embeddings", 15, "building_context"),
            ("planning_methodologies", 30, "building_context"),
            ("build_context", 35, "building_context"),
            ("human_review", 70, "human_review"),
            ("preparing_generation", 30, "question_generation"),
            ("generating_questions", 50, "question_generation"),
            ("llm_processing", 55, "question_generation"),
            ("parsing_output", 62, "question_generation"),
            ("validation_scoring", 80, "quality_evaluation"),
            ("evaluating_pillars", 90, "quality_evaluation"),
            ("advanced_evaluation", 87, "quality_evaluation"),
            ("legacy_evaluation", 88, "quality_evaluation"),
            ("fallback_evaluation", 90, "quality_evaluation"),
            ("finalizing", 95, "completion"),
            ("completed", 100, "completion")
        ]
        
        for step_name, percent, frontend_step in progress_samples:
            min_percent, max_percent = frontend_step_ranges[frontend_step]
            assert min_percent <= percent <= max_percent, \
                f"Step '{step_name}' ({percent}%) outside expected range for {frontend_step} ({min_percent}-{max_percent}%)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
