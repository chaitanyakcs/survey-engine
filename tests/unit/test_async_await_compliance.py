"""
Unit tests for async/await compliance and prompt service functionality.

This test suite ensures that all async methods are properly awaited and that
the prompt service works correctly with async operations.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from src.services.prompt_service import PromptService
from src.services.prompt_builder import PromptBuilder
from src.workflows.nodes import HumanPromptReviewNode
from src.workflows.state import SurveyGenerationState
from src.utils.error_messages import UserFriendlyError


class TestAsyncAwaitCompliance:
    """Test that all async methods are properly awaited."""
    
    @pytest.mark.asyncio
    async def test_prompt_service_async_methods_are_awaited(self):
        """Test that PromptService async methods are properly awaited."""
        prompt_service = PromptService()
        
        # Mock the prompt_builder to avoid database dependencies
        mock_prompt_builder = AsyncMock()
        mock_prompt_builder.build_survey_generation_prompt.return_value = "Test prompt"
        prompt_service.prompt_builder = mock_prompt_builder
        
        # Test create_survey_generation_prompt
        result = await prompt_service.create_survey_generation_prompt(
            rfq_text="Test RFQ",
            context={"rfq_details": {"text": "Test"}},
            golden_examples=[],
            methodology_blocks=[]
        )
        
        assert result == "Test prompt"
        mock_prompt_builder.build_survey_generation_prompt.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_prompt_service_build_system_prompt_awaited(self):
        """Test that build_system_prompt is properly awaited."""
        prompt_service = PromptService()
        
        # Mock the prompt_builder
        mock_prompt_builder = AsyncMock()
        mock_prompt_builder.build_survey_generation_prompt.return_value = "System prompt"
        prompt_service.prompt_builder = mock_prompt_builder
        
        # Test build_system_prompt
        result = await prompt_service.build_system_prompt(
            context={"rfq_details": {"text": "Test"}},
            methodology_tags=["nps"],
            custom_rules={}
        )
        
        assert result == "System prompt"
        mock_prompt_builder.build_survey_generation_prompt.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_prompt_service_build_golden_enhanced_prompt_awaited(self):
        """Test that build_golden_enhanced_prompt is properly awaited."""
        prompt_service = PromptService()
        
        # Mock the prompt_builder
        mock_prompt_builder = AsyncMock()
        mock_prompt_builder.build_survey_generation_prompt.return_value = "Enhanced prompt"
        prompt_service.prompt_builder = mock_prompt_builder
        
        # Test build_golden_enhanced_prompt
        result = await prompt_service.build_golden_enhanced_prompt(
            context={"rfq_details": {"text": "Test"}},
            golden_examples=[{"id": "1", "rfq_text": "Test"}],
            methodology_blocks=[],
            custom_rules={}
        )
        
        assert result == "Enhanced prompt"
        mock_prompt_builder.build_survey_generation_prompt.assert_called_once()


class TestPromptServiceAsync:
    """Test PromptService async functionality."""
    
    @pytest.mark.asyncio
    async def test_create_survey_prompt_with_rag_context(self):
        """Test that create_survey_prompt properly handles RAG context."""
        prompt_service = PromptService()
        
        # Mock the prompt_builder
        mock_prompt_builder = AsyncMock()
        mock_prompt_builder.build_survey_generation_prompt.return_value = "Survey prompt"
        prompt_service.prompt_builder = mock_prompt_builder
        
        # Test with golden examples
        golden_examples = [
            {
                "id": "1",
                "rfq_text": "Test RFQ",
                "survey_json": {"title": "Test Survey"},
                "quality_score": 0.9,
                "methodology_tags": ["nps"],
                "similarity": 0.8
            }
        ]
        
        result = await prompt_service.create_survey_prompt(
            rfq_text="Test RFQ",
            context={"rfq_details": {"text": "Test"}},
            golden_examples=golden_examples,
            methodology_blocks=[],
            custom_rules={}
        )
        
        assert result == "Survey prompt"
        
        # Verify the call was made with proper RAG context
        call_args = mock_prompt_builder.build_survey_generation_prompt.call_args
        assert call_args[1]["rfq_text"] == "Test RFQ"
        assert call_args[1]["rag_context"] is not None
        assert call_args[1]["rag_context"].example_count == 1
        assert call_args[1]["rag_context"].avg_quality_score == 0.9
    
    @pytest.mark.asyncio
    async def test_prompt_service_error_handling(self):
        """Test that PromptService handles errors gracefully."""
        prompt_service = PromptService()
        
        # Mock the prompt_builder to raise an exception
        mock_prompt_builder = AsyncMock()
        mock_prompt_builder.build_survey_generation_prompt.side_effect = Exception("Test error")
        prompt_service.prompt_builder = mock_prompt_builder
        
        # Test that exception is properly raised
        with pytest.raises(Exception, match="Test error"):
            await prompt_service.create_survey_generation_prompt(
                rfq_text="Test RFQ",
                context={"rfq_details": {"text": "Test"}},
                golden_examples=[],
                methodology_blocks=[]
            )


class TestWorkflowNodesAsync:
    """Test workflow nodes async functionality."""
    
    @pytest.mark.asyncio
    async def test_human_prompt_review_node_awaits_prompt_service(self):
        """Test that HumanPromptReviewNode properly awaits prompt service calls."""
        # Mock database session
        mock_db = Mock()
        
        # Create the node
        node = HumanPromptReviewNode(mock_db)
        
        # Mock the PromptService
        with patch('src.workflows.nodes.PromptService') as mock_prompt_service_class:
            mock_prompt_service = AsyncMock()
            mock_prompt_service.create_survey_generation_prompt.return_value = "Test prompt"
            mock_prompt_service_class.return_value = mock_prompt_service
            
            # Mock settings service
            with patch('src.workflows.nodes.SettingsService') as mock_settings_service_class:
                mock_settings_service = Mock()
                mock_settings_service.get_evaluation_settings.return_value = {
                    'enable_prompt_review': True,
                    'prompt_review_mode': 'blocking'
                }
                mock_settings_service_class.return_value = mock_settings_service
                
                # Mock database connection
                with patch('src.workflows.nodes._get_db') as mock_get_db:
                    mock_fresh_db = Mock()
                    mock_fresh_db.close = Mock()
                    mock_get_db.return_value = [mock_fresh_db]
                    
                    # Create test state
                    state = SurveyGenerationState(
                        workflow_id="test-workflow",
                        rfq_text="Test RFQ",
                        context={"test": "context"},
                        golden_examples=[],
                        methodology_blocks=[]
                    )
                    
                    # Execute the node
                    result = await node(state)
                    
                    # Verify the prompt service was called with await
                    mock_prompt_service.create_survey_generation_prompt.assert_called_once()
                    
                    # Verify the result structure
                    assert "prompt_approved" in result
                    assert "pending_human_review" in result
    
    @pytest.mark.asyncio
    async def test_human_prompt_review_node_error_handling(self):
        """Test that HumanPromptReviewNode handles prompt service errors gracefully."""
        # Mock database session
        mock_db = Mock()
        
        # Create the node
        node = HumanPromptReviewNode(mock_db)
        
        # Mock the PromptService to raise an exception
        with patch('src.workflows.nodes.PromptService') as mock_prompt_service_class:
            mock_prompt_service = AsyncMock()
            mock_prompt_service.create_survey_generation_prompt.side_effect = Exception("Prompt generation failed")
            mock_prompt_service_class.return_value = mock_prompt_service
            
            # Mock settings service
            with patch('src.workflows.nodes.SettingsService') as mock_settings_service_class:
                mock_settings_service = Mock()
                mock_settings_service.get_evaluation_settings.return_value = {
                    'enable_prompt_review': True,
                    'prompt_review_mode': 'blocking'
                }
                mock_settings_service_class.return_value = mock_settings_service
                
                # Mock database connection
                with patch('src.workflows.nodes._get_db') as mock_get_db:
                    mock_fresh_db = Mock()
                    mock_fresh_db.close = Mock()
                    mock_get_db.return_value = [mock_fresh_db]
                    
                    # Create test state
                    state = SurveyGenerationState(
                        workflow_id="test-workflow",
                        rfq_text="Test RFQ",
                        context={"test": "context"},
                        golden_examples=[],
                        methodology_blocks=[]
                    )
                    
                    # Execute the node
                    result = await node(state)
                    
                    # Verify error handling - should fail open
                    assert result["prompt_approved"] is True
                    assert result["pending_human_review"] is False
                    assert "Prompt generation failed" in result["error_message"]


class TestAsyncErrorHandling:
    """Test async error handling patterns."""
    
    @pytest.mark.asyncio
    async def test_async_method_raises_user_friendly_error(self):
        """Test that async methods can raise UserFriendlyError."""
        async def failing_async_method():
            raise UserFriendlyError(
                message="Async operation failed",
                technical_details="Test error details",
                action_required="Check configuration"
            )
        
        with pytest.raises(UserFriendlyError) as exc_info:
            await failing_async_method()
        
        assert exc_info.value.message == "Async operation failed"
        assert exc_info.value.technical_details == "Test error details"
        assert exc_info.value.action_required == "Check configuration"
    
    @pytest.mark.asyncio
    async def test_async_method_with_timeout(self):
        """Test async method with timeout handling."""
        async def slow_async_method():
            await asyncio.sleep(2)  # Simulate slow operation
            return "Success"
        
        # Test with timeout
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(slow_async_method(), timeout=0.1)
        
        # Test without timeout
        result = await asyncio.wait_for(slow_async_method(), timeout=3.0)
        assert result == "Success"


if __name__ == "__main__":
    pytest.main([__file__])
