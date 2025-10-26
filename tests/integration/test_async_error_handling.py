"""
Integration tests for async error handling patterns.

This test suite tests error handling for async failures across the application,
ensuring that async operations fail gracefully and provide proper error messages.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from src.utils.error_messages import UserFriendlyError
from src.services.prompt_service import PromptService
from src.workflows.nodes import HumanPromptReviewNode
from src.workflows.state import SurveyGenerationState


class TestAsyncErrorHandling:
    """Test async error handling patterns."""
    
    @pytest.mark.asyncio
    async def test_prompt_service_async_error_handling(self):
        """Test that PromptService handles async errors gracefully."""
        prompt_service = PromptService()
        
        # Mock the prompt_builder to raise an exception
        mock_prompt_builder = AsyncMock()
        mock_prompt_builder.build_survey_generation_prompt.side_effect = Exception("Database connection failed")
        prompt_service.prompt_builder = mock_prompt_builder
        
        # Test that async exception is properly raised
        with pytest.raises(Exception, match="Database connection failed"):
            await prompt_service.create_survey_generation_prompt(
                rfq_text="Test RFQ",
                context={"rfq_details": {"text": "Test"}},
                golden_examples=[],
                methodology_blocks=[]
            )
    
    @pytest.mark.asyncio
    async def test_workflow_node_async_error_handling(self):
        """Test that workflow nodes handle async errors gracefully."""
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
                    
                    # Execute the node - should handle error gracefully
                    result = await node(state)
                    
                    # Verify error handling - should fail open
                    assert result["prompt_approved"] is True
                    assert result["pending_human_review"] is False
                    assert "Prompt generation failed" in result["error_message"]
    
    @pytest.mark.asyncio
    async def test_async_timeout_error_handling(self):
        """Test that async timeout errors are handled properly."""
        async def slow_async_operation():
            await asyncio.sleep(2)  # Simulate slow operation
            return "Success"
        
        # Test timeout handling
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(slow_async_operation(), timeout=0.1)
        
        # Test successful operation with sufficient timeout
        result = await asyncio.wait_for(slow_async_operation(), timeout=3.0)
        assert result == "Success"
    
    @pytest.mark.asyncio
    async def test_async_cancellation_error_handling(self):
        """Test that async cancellation errors are handled properly."""
        async def cancellable_operation():
            try:
                await asyncio.sleep(1)
                return "Success"
            except asyncio.CancelledError:
                return "Cancelled"
        
        # Create and cancel the task
        task = asyncio.create_task(cancellable_operation())
        await asyncio.sleep(0.1)
        task.cancel()
        
        result = await task
        assert result == "Cancelled"
    
    @pytest.mark.asyncio
    async def test_concurrent_async_error_handling(self):
        """Test error handling with concurrent async operations."""
        async def failing_operation():
            await asyncio.sleep(0.1)
            raise Exception("Operation failed")
        
        async def successful_operation():
            await asyncio.sleep(0.1)
            return "Success"
        
        # Test that one failure doesn't stop other operations
        tasks = [
            failing_operation(),
            successful_operation(),
            failing_operation()
        ]
        
        results = []
        for task in asyncio.as_completed(tasks):
            try:
                result = await task
                results.append(result)
            except Exception as e:
                results.append(f"Error: {str(e)}")
        
        assert len(results) == 3
        assert "Success" in results
        assert "Error: Operation failed" in results
    
    @pytest.mark.asyncio
    async def test_async_user_friendly_error_handling(self):
        """Test that UserFriendlyError works with async operations."""
        async def async_operation_with_user_error():
            await asyncio.sleep(0.1)
            raise UserFriendlyError(
                message="Async operation failed",
                technical_details="Database connection timeout",
                action_required="Check database configuration"
            )
        
        with pytest.raises(UserFriendlyError) as exc_info:
            await async_operation_with_user_error()
        
        assert exc_info.value.message == "Async operation failed"
        assert exc_info.value.technical_details == "Database connection timeout"
        assert exc_info.value.action_required == "Check database configuration"
    
    @pytest.mark.asyncio
    async def test_async_retry_pattern(self):
        """Test async retry pattern for handling transient failures."""
        attempt_count = 0
        
        async def unreliable_operation():
            nonlocal attempt_count
            attempt_count += 1
            
            if attempt_count < 3:
                await asyncio.sleep(0.1)
                raise Exception(f"Attempt {attempt_count} failed")
            
            return f"Success on attempt {attempt_count}"
        
        async def retry_operation(max_retries: int = 3):
            for attempt in range(max_retries):
                try:
                    return await unreliable_operation()
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    await asyncio.sleep(0.1)  # Brief delay before retry
        
        result = await retry_operation()
        assert result == "Success on attempt 3"
        assert attempt_count == 3
    
    @pytest.mark.asyncio
    async def test_async_circuit_breaker_pattern(self):
        """Test async circuit breaker pattern for handling repeated failures."""
        failure_count = 0
        circuit_open = False
        
        async def failing_service():
            nonlocal failure_count, circuit_open
            failure_count += 1
            
            if failure_count >= 3:
                circuit_open = True
            
            if circuit_open:
                raise Exception("Circuit breaker is open")
            
            raise Exception("Service failure")
        
        async def circuit_breaker_operation():
            nonlocal circuit_open
            
            if circuit_open:
                raise Exception("Circuit breaker is open - service unavailable")
            
            try:
                return await failing_service()
            except Exception as e:
                if "Circuit breaker is open" in str(e):
                    raise e
                # Let the failure count increment
                raise e
        
        # First few calls should fail normally
        with pytest.raises(Exception, match="Service failure"):
            await circuit_breaker_operation()
        
        with pytest.raises(Exception, match="Service failure"):
            await circuit_breaker_operation()
        
        # After threshold, circuit should open
        with pytest.raises(Exception, match="Circuit breaker is open"):
            await circuit_breaker_operation()
    
    @pytest.mark.asyncio
    async def test_async_graceful_degradation(self):
        """Test async graceful degradation when services are unavailable."""
        async def primary_service():
            raise Exception("Primary service unavailable")
        
        async def fallback_service():
            await asyncio.sleep(0.1)
            return "Fallback response"
        
        async def resilient_operation():
            try:
                return await primary_service()
            except Exception:
                # Gracefully degrade to fallback
                return await fallback_service()
        
        result = await resilient_operation()
        assert result == "Fallback response"
    
    @pytest.mark.asyncio
    async def test_async_error_logging(self):
        """Test that async errors are properly logged."""
        import logging
        
        # Capture log messages
        log_messages = []
        
        class TestHandler(logging.Handler):
            def emit(self, record):
                log_messages.append(self.format(record))
        
        logger = logging.getLogger("test_async_error")
        handler = TestHandler()
        logger.addHandler(handler)
        logger.setLevel(logging.ERROR)
        
        async def operation_with_logging():
            try:
                await asyncio.sleep(0.1)
                raise Exception("Test error")
            except Exception as e:
                logger.error(f"Async operation failed: {str(e)}", exc_info=True)
                raise e
        
        with pytest.raises(Exception, match="Test error"):
            await operation_with_logging()
        
        # Verify error was logged
        assert len(log_messages) > 0
        assert "Async operation failed: Test error" in log_messages[0]


if __name__ == "__main__":
    pytest.main([__file__])
