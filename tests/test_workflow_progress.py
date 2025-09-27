"""
Comprehensive test cases for workflow progress tracking
Tests all backend progress updates and step coordination
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.orm import Session
import time

# Use dynamic imports to avoid module conflicts
def import_workflow_modules():
    """Import workflow modules dynamically to avoid conflicts"""
    import sys
    import importlib
    
    # Add current directory to path
    sys.path.insert(0, '.')
    
    # Import modules
    workflow_module = importlib.import_module('src.workflows.workflow')
    state_module = importlib.import_module('src.workflows.state')
    websocket_module = importlib.import_module('src.services.websocket_client')
    generation_module = importlib.import_module('src.services.generation_service')
    evaluator_module = importlib.import_module('src.services.evaluator_service')
    
    return (
        workflow_module.create_workflow,
        state_module.SurveyGenerationState,
        websocket_module.WebSocketNotificationService,
        generation_module.GenerationService,
        evaluator_module.EvaluatorService
    )

# Import the modules
create_workflow, SurveyGenerationState, WebSocketNotificationService, GenerationService, EvaluatorService = import_workflow_modules()


class MockConnectionManager:
    """Mock connection manager for testing"""
    
    def __init__(self):
        self.messages = []
        self.workflows = {}
    
    async def broadcast_to_workflow(self, workflow_id: str, message: dict):
        """Mock broadcast that records messages"""
        if workflow_id not in self.workflows:
            self.workflows[workflow_id] = []
        self.workflows[workflow_id].append(message)
        self.messages.append({"workflow_id": workflow_id, "message": message})


@pytest.fixture
def mock_db():
    """Mock database session"""
    return MagicMock(spec=Session)


@pytest.fixture
def mock_connection_manager():
    """Mock connection manager"""
    return MockConnectionManager()


@pytest.fixture
def mock_ws_client(mock_connection_manager):
    """Mock WebSocket client"""
    return WebSocketNotificationService(mock_connection_manager)


@pytest.fixture
def sample_state():
    """Sample workflow state for testing"""
    return SurveyGenerationState(
        rfq_id=None,
        survey_id="test-survey-123",
        workflow_id="test-workflow-123",
        rfq_text="Test RFQ for pricing research",
        rfq_title="Test Survey",
        product_category="electronics",
        target_segment="consumers",
        research_goal="pricing_research",
        workflow_start_time=time.time()
    )


class TestWorkflowProgressUpdates:
    """Test workflow progress update coordination"""

    @pytest.mark.asyncio
    async def test_parse_rfq_progress_sequence(self, mock_db, mock_connection_manager, sample_state):
        """Test that parse_rfq sends all expected progress updates"""
        workflow = create_workflow(mock_db, mock_connection_manager)
        
        with patch('src.workflows.nodes.RFQNode') as mock_rfq_node:
            mock_rfq_node.return_value = AsyncMock(return_value={"rfq_embedding": [1, 2, 3]})
            
            # Execute parse_rfq node
            parse_rfq_node = workflow.nodes['parse_rfq']
            await parse_rfq_node.func(sample_state)
            
            # Verify progress updates
            messages = mock_connection_manager.workflows.get("test-workflow-123", [])
            
            # Should have 3 progress updates
            assert len(messages) == 3
            
            # Check parsing_rfq update
            assert messages[0]["step"] == "parsing_rfq"
            assert messages[0]["percent"] == 10
            assert "analyzing requirements" in messages[0]["message"].lower()
            
            # Check generating_embeddings update
            assert messages[1]["step"] == "generating_embeddings"
            assert messages[1]["percent"] == 15
            assert "embedding" in messages[1]["message"].lower()
            
            # Check rfq_parsed update
            assert messages[2]["step"] == "rfq_parsed"
            assert messages[2]["percent"] == 20
            assert "analysis" in messages[2]["message"].lower()

    @pytest.mark.asyncio
    async def test_build_context_progress_sequence(self, mock_db, mock_connection_manager, sample_state):
        """Test that build_context sends all expected progress updates"""
        workflow = create_workflow(mock_db, mock_connection_manager)
        
        with patch('src.workflows.nodes.ContextBuilderNode') as mock_context_node:
            mock_context_node.return_value = AsyncMock(return_value={"context": {"methodologies": ["vw"]}})
            
            # Execute build_context node
            build_context_node = workflow.nodes['build_context']
            await build_context_node.func(sample_state)
            
            # Verify progress updates
            messages = mock_connection_manager.workflows.get("test-workflow-123", [])
            
            # Should have 2 progress updates
            assert len(messages) == 2
            
            # Check planning_methodologies update
            assert messages[0]["step"] == "planning_methodologies"
            assert messages[0]["percent"] == 30
            assert "planning" in messages[0]["message"].lower()
            
            # Check build_context update
            assert messages[1]["step"] == "build_context"
            assert messages[1]["percent"] == 35
            assert "finalizing" in messages[1]["message"].lower()

    @pytest.mark.asyncio
    async def test_generate_progress_sequence(self, mock_db, mock_connection_manager, sample_state):
        """Test that generate sends all expected progress updates"""
        workflow = create_workflow(mock_db, mock_connection_manager)
        
        with patch('src.workflows.nodes.GeneratorAgent') as mock_generator:
            mock_generator.return_value = AsyncMock(return_value={
                "generated_survey": {"title": "Test Survey"},
                "generation_metadata": {"model": "openai/gpt-5"}
            })
            
            # Execute generate node
            generate_node = workflow.nodes['generate']
            await generate_node.func(sample_state)
            
            # Verify progress updates
            messages = mock_connection_manager.workflows.get("test-workflow-123", [])
            
            # Should have 2 progress updates (preparing_generation + parsing_output)
            assert len(messages) == 2
            
            # Check preparing_generation update
            assert messages[0]["step"] == "preparing_generation"
            assert messages[0]["percent"] == 55
            assert "setting up" in messages[0]["message"].lower()
            
            # Check parsing_output update
            assert messages[1]["step"] == "parsing_output"
            assert messages[1]["percent"] == 75
            assert "structuring" in messages[1]["message"].lower()

    @pytest.mark.asyncio
    async def test_validate_progress_sequence(self, mock_db, mock_connection_manager, sample_state):
        """Test that validate sends all expected progress updates"""
        workflow = create_workflow(mock_db, mock_connection_manager)
        
        with patch('src.workflows.nodes.ValidatorAgent') as mock_validator:
            mock_validator.return_value = AsyncMock(return_value={
                "quality_gate_passed": True,
                "pillar_scores": {"overall_score": 0.85}
            })
            
            # Execute validate node
            validate_node = workflow.nodes['validate']
            await validate_node.func(sample_state)
            
            # Verify progress updates
            messages = mock_connection_manager.workflows.get("test-workflow-123", [])
            
            # Should have 3 progress updates
            assert len(messages) == 3
            
            # Check validation_scoring update
            assert messages[0]["step"] == "validation_scoring"
            assert messages[0]["percent"] == 80
            assert "evaluation" in messages[0]["message"].lower()
            
            # Check evaluating_pillars update
            assert messages[1]["step"] == "evaluating_pillars"
            assert messages[1]["percent"] == 85
            assert "pillars" in messages[1]["message"].lower()
            
            # Check finalizing update
            assert messages[2]["step"] == "finalizing"
            assert messages[2]["percent"] == 95
            assert "finalizing" in messages[2]["message"].lower()

    @pytest.mark.asyncio
    async def test_progress_percentages_are_sequential(self, mock_db, mock_connection_manager, sample_state):
        """Test that progress percentages increase sequentially"""
        workflow = create_workflow(mock_db, mock_connection_manager)
        
        # Mock all nodes
        with patch('src.workflows.nodes.RFQNode') as mock_rfq, \
             patch('src.workflows.nodes.GoldenRetrieverNode') as mock_golden, \
             patch('src.workflows.nodes.ContextBuilderNode') as mock_context, \
             patch('src.workflows.nodes.GeneratorAgent') as mock_generator, \
             patch('src.workflows.nodes.ValidatorAgent') as mock_validator:
            
            # Setup mocks
            mock_rfq.return_value = AsyncMock(return_value={"rfq_embedding": [1, 2, 3]})
            mock_golden.return_value = AsyncMock(return_value={"golden_examples": []})
            mock_context.return_value = AsyncMock(return_value={"context": {}})
            mock_generator.return_value = AsyncMock(return_value={"generated_survey": {}})
            mock_validator.return_value = AsyncMock(return_value={"quality_gate_passed": True})
            
            # Execute workflow nodes in sequence
            for node_name in ['parse_rfq', 'retrieve_golden', 'build_context', 'generate', 'validate']:
                node = workflow.nodes[node_name]
                await node.func(sample_state)
            
            # Get all messages and extract percentages
            all_messages = mock_connection_manager.workflows.get("test-workflow-123", [])
            percentages = [msg["percent"] for msg in all_messages if "percent" in msg]
            
            # Verify percentages are in ascending order
            assert percentages == sorted(percentages), f"Percentages not sequential: {percentages}"
            
            # Verify we have the expected number of progress updates
            assert len(percentages) >= 10, f"Expected at least 10 progress updates, got {len(percentages)}"
            
            # Verify percentage range
            assert min(percentages) >= 5, f"Minimum percentage too low: {min(percentages)}"
            assert max(percentages) <= 95, f"Maximum percentage too high: {max(percentages)}"


class TestGenerationServiceProgressUpdates:
    """Test GenerationService async progress coordination"""

    @pytest.mark.asyncio
    async def test_streaming_mode_progress_updates(self, mock_db, mock_connection_manager):
        """Test progress updates during streaming mode"""
        service = GenerationService(
            db_session=mock_db,
            workflow_id="test-workflow-123",
            connection_manager=mock_connection_manager
        )
        
        # Mock replicate client
        mock_prediction = MagicMock()
        mock_prediction.id = "test-prediction-123"
        mock_prediction.stream.return_value = [
            MagicMock(event='output', data='{"title": "Test Survey",'),
            MagicMock(event='output', data='"questions": [{"text": "Test question"}]'),
            MagicMock(event='done', data='')
        ]
        
        with patch.object(service, 'replicate_client') as mock_client:
            mock_client.predictions.async_create = AsyncMock(return_value=mock_prediction)
            
            # Mock _extract_survey_json to avoid JSON parsing issues
            with patch.object(service, '_extract_survey_json', return_value={"title": "Test Survey"}):
                start_time = time.time()
                result = await service._stream_with_replicate("test prompt", start_time)
                
                # Verify initial progress update was sent
                messages = mock_connection_manager.workflows.get("test-workflow-123", [])
                assert len(messages) >= 1
                
                # Check initial generating_questions update
                initial_msg = messages[0]
                assert initial_msg["step"] == "generating_questions"
                assert initial_msg["percent"] == 60
                assert "creating survey questions" in initial_msg["message"].lower()

    @pytest.mark.asyncio 
    async def test_async_polling_mode_progress_updates(self, mock_db, mock_connection_manager):
        """Test progress updates during async polling mode"""
        service = GenerationService(
            db_session=mock_db,
            workflow_id="test-workflow-123", 
            connection_manager=mock_connection_manager
        )
        
        # Mock prediction that succeeds after 2 polls
        mock_prediction = MagicMock()
        mock_prediction.id = "test-prediction-123"
        mock_prediction.status = "running"
        mock_prediction.output = ["Test survey output"]
        
        poll_count = 0
        async def mock_reload():
            nonlocal poll_count
            poll_count += 1
            if poll_count >= 2:
                mock_prediction.status = "succeeded"
        
        mock_prediction.async_reload = mock_reload
        
        with patch.object(service, 'replicate_client') as mock_client:
            mock_client.predictions.async_create = AsyncMock(return_value=mock_prediction)
            
            # Mock _extract_survey_json
            with patch.object(service, '_extract_survey_json', return_value={"title": "Test Survey"}):
                start_time = time.time()
                result = await service._generate_with_async_polling("test prompt", start_time)
                
                # Verify progress updates were sent
                messages = mock_connection_manager.workflows.get("test-workflow-123", [])
                assert len(messages) >= 2  # Initial + polling updates
                
                # Check we have both generating_questions and llm_processing updates
                steps = [msg["step"] for msg in messages]
                assert "generating_questions" in steps
                assert "llm_processing" in steps

    @pytest.mark.asyncio
    async def test_sync_fallback_progress_updates(self, mock_db, mock_connection_manager):
        """Test progress updates during sync fallback mode"""
        service = GenerationService(
            db_session=mock_db,
            workflow_id="test-workflow-123",
            connection_manager=mock_connection_manager
        )
        
        with patch.object(service, 'replicate_client') as mock_client:
            mock_client.async_run = AsyncMock(return_value="Test survey output")
            
            # Mock _extract_survey_json
            with patch.object(service, '_extract_survey_json', return_value={"title": "Test Survey"}):
                result = await service._generate_with_sync_fallback("test prompt")
                
                # Verify initial progress update was sent
                messages = mock_connection_manager.workflows.get("test-workflow-123", [])
                assert len(messages) >= 1
                
                # Check initial generating_questions update
                initial_msg = messages[0]
                assert initial_msg["step"] == "generating_questions"
                assert initial_msg["percent"] == 60


class TestEvaluatorServiceProgressUpdates:
    """Test EvaluatorService progress coordination"""

    @pytest.mark.asyncio
    async def test_single_call_evaluation_progress(self, mock_db, mock_connection_manager):
        """Test progress updates during single-call evaluation"""
        service = EvaluatorService(
            db_session=mock_db,
            workflow_id="test-workflow-123",
            connection_manager=mock_connection_manager
        )
        
        # Mock the single-call evaluation
        with patch.object(service, '_evaluate_with_single_call') as mock_eval:
            mock_eval.return_value = {
                "overall_grade": "A",
                "weighted_score": 0.85,
                "pillar_scores": {"content_validity": 0.9}
            }
            
            survey_data = {"title": "Test Survey", "questions": []}
            rfq_text = "Test RFQ"
            
            result = await service.evaluate_survey(survey_data, rfq_text)
            
            # Verify progress updates
            messages = mock_connection_manager.workflows.get("test-workflow-123", [])
            
            # Should have validation_scoring, single_call_evaluator, and pillar_scores_analysis
            steps = [msg["step"] for msg in messages if "step" in msg]
            assert "validation_scoring" in steps
            assert "single_call_evaluator" in steps  
            assert "pillar_scores_analysis" in steps

    @pytest.mark.asyncio
    async def test_evaluation_fallback_chain_progress(self, mock_db, mock_connection_manager):
        """Test progress updates when evaluation falls back to legacy methods"""
        service = EvaluatorService(
            db_session=mock_db,
            workflow_id="test-workflow-123",
            connection_manager=mock_connection_manager
        )
        
        # Mock single-call to fail, legacy to succeed
        with patch.object(service, '_evaluate_with_single_call') as mock_single, \
             patch.object(service, '_evaluate_with_legacy') as mock_legacy:
            
            mock_single.side_effect = Exception("Single call failed")
            mock_legacy.return_value = {
                "overall_grade": "B",
                "weighted_score": 0.75
            }
            
            survey_data = {"title": "Test Survey", "questions": []}
            rfq_text = "Test RFQ"
            
            result = await service.evaluate_survey(survey_data, rfq_text)
            
            # Verify fallback progress updates
            messages = mock_connection_manager.workflows.get("test-workflow-123", [])
            steps = [msg["step"] for msg in messages if "step" in msg]
            
            # Should have validation_scoring, single_call_evaluator, advanced_evaluation, legacy_evaluation
            assert "validation_scoring" in steps
            assert "single_call_evaluator" in steps
            assert "advanced_evaluation" in steps
            assert "legacy_evaluation" in steps


class TestProgressStepMapping:
    """Test that backend steps map correctly to frontend expectations"""

    def test_all_backend_steps_have_frontend_mapping(self):
        """Test that all backend step names are covered in frontend mapping"""
        # All backend steps that can be sent
        backend_steps = {
            "initializing_workflow", "parsing_rfq", "generating_embeddings", "rfq_parsed",
            "matching_golden_examples", "planning_methodologies", "build_context",
            "preparing_generation", "generating_questions", "llm_processing", "parsing_output",
            "validation_scoring", "evaluating_pillars", "single_call_evaluator", 
            "pillar_scores_analysis", "advanced_evaluation", "legacy_evaluation",
            "fallback_evaluation", "finalizing", "completed", "human_review",
            "resuming_from_human_review", "resuming_generation"
        }
        
        # Expected frontend step mapping (from ProgressStepper.tsx)
        frontend_mapping = {
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
        
        # Check that all backend steps have frontend mappings
        unmapped_steps = backend_steps - set(frontend_mapping.keys())
        assert not unmapped_steps, f"Backend steps without frontend mapping: {unmapped_steps}"

    def test_progress_percentage_ranges(self):
        """Test that progress percentages are within expected ranges"""
        # Expected percentage ranges for each major step (updated to match ProgressTracker)
        step_ranges = {
            "building_context": (10, 25),     # 10% to 25%
            "human_review": (65, 75),         # 65% to 75% 
            "question_generation": (35, 65),  # 35% to 65%
            "quality_evaluation": (75, 95),   # 75% to 95%
            "completion": (95, 100)           # 95% to 100%
        }
        
        # Sample progress updates with their expected ranges (updated to match ProgressTracker)
        progress_updates = [
            ("initializing_workflow", 5, "building_context"),
            ("parsing_rfq", 10, "building_context"),
            ("generating_embeddings", 15, "building_context"),
            ("rfq_parsed", 20, "building_context"),
            ("matching_golden_examples", 25, "building_context"),
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
        
        for step_name, percent, expected_category in progress_updates:
            min_percent, max_percent = step_ranges[expected_category]
            assert min_percent <= percent <= max_percent, \
                f"Step '{step_name}' ({percent}%) outside expected range for {expected_category} ({min_percent}-{max_percent}%)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
