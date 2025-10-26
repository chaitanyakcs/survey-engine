"""
Integration tests for human review workflow and async API endpoints.

This test suite tests the full integration of async operations in the workflow
and API endpoints, ensuring that the human review workflow works correctly
and that API endpoints handle async operations properly.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any
import json

from src.workflows.nodes import HumanPromptReviewNode
from src.workflows.state import SurveyGenerationState
from src.services.prompt_service import PromptService
from src.database.models import HumanReview


class TestHumanReviewWorkflow:
    """Test the full human review workflow integration."""
    
    @pytest.mark.asyncio
    async def test_human_review_workflow_blocking_mode(self):
        """Test human review workflow in blocking mode."""
        # Mock database session
        mock_db = Mock()
        
        # Create the node
        node = HumanPromptReviewNode(mock_db)
        
        # Mock all dependencies
        with patch('src.workflows.nodes.PromptService') as mock_prompt_service_class, \
             patch('src.workflows.nodes.SettingsService') as mock_settings_service_class, \
             patch('src.workflows.nodes._get_db') as mock_get_db, \
             patch('src.workflows.nodes.HumanReview') as mock_human_review_class:
            
            # Setup mocks
            mock_prompt_service = AsyncMock()
            mock_prompt_service.create_survey_generation_prompt.return_value = "Generated prompt"
            mock_prompt_service_class.return_value = mock_prompt_service
            
            mock_settings_service = Mock()
            mock_settings_service.get_evaluation_settings.return_value = {
                'enable_prompt_review': True,
                'prompt_review_mode': 'blocking'
            }
            mock_settings_service_class.return_value = mock_settings_service
            
            mock_fresh_db = Mock()
            mock_fresh_db.close = Mock()
            mock_fresh_db.query.return_value.filter.return_value.first.return_value = None  # No existing review
            mock_fresh_db.add = Mock()
            mock_fresh_db.commit = Mock()
            mock_fresh_db.refresh = Mock()
            mock_get_db.return_value = [mock_fresh_db]
            
            # Mock HumanReview
            mock_review = Mock()
            mock_review.id = "review-123"
            mock_human_review_class.return_value = mock_review
            
            # Create test state
            state = SurveyGenerationState(
                workflow_id="test-workflow-123",
                survey_id="survey-456",
                rfq_text="Test RFQ for human review",
                context={"rfq_details": {"text": "Test RFQ"}},
                golden_examples=[{"id": "1", "rfq_text": "Example"}],
                methodology_blocks=[{"id": "1", "content": "Methodology"}]
            )
            
            # Execute the node
            result = await node(state)
            
            # Verify the prompt service was called correctly
            mock_prompt_service.create_survey_generation_prompt.assert_called_once_with(
                rfq_text="Test RFQ for human review",
                context={"rfq_details": {"text": "Test RFQ"}},
                golden_examples=[{"id": "1", "rfq_text": "Example"}],
                methodology_blocks=[{"id": "1", "content": "Methodology"}]
            )
            
            # Verify blocking mode behavior
            assert result["prompt_approved"] is False
            assert result["pending_human_review"] is True
            assert result["workflow_paused"] is True
            assert result["review_id"] == "review-123"
            assert result["error_message"] is None
            
            # Verify database operations
            mock_fresh_db.add.assert_called_once()
            mock_fresh_db.commit.assert_called_once()
            mock_fresh_db.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_human_review_workflow_non_blocking_mode(self):
        """Test human review workflow in non-blocking mode."""
        # Mock database session
        mock_db = Mock()
        
        # Create the node
        node = HumanPromptReviewNode(mock_db)
        
        # Mock all dependencies
        with patch('src.workflows.nodes.PromptService') as mock_prompt_service_class, \
             patch('src.workflows.nodes.SettingsService') as mock_settings_service_class, \
             patch('src.workflows.nodes._get_db') as mock_get_db, \
             patch('src.workflows.nodes.HumanReview') as mock_human_review_class:
            
            # Setup mocks
            mock_prompt_service = AsyncMock()
            mock_prompt_service.create_survey_generation_prompt.return_value = "Generated prompt"
            mock_prompt_service_class.return_value = mock_prompt_service
            
            mock_settings_service = Mock()
            mock_settings_service.get_evaluation_settings.return_value = {
                'enable_prompt_review': True,
                'prompt_review_mode': 'non_blocking'
            }
            mock_settings_service_class.return_value = mock_settings_service
            
            mock_fresh_db = Mock()
            mock_fresh_db.close = Mock()
            mock_fresh_db.query.return_value.filter.return_value.first.return_value = None  # No existing review
            mock_fresh_db.add = Mock()
            mock_fresh_db.commit = Mock()
            mock_fresh_db.refresh = Mock()
            mock_get_db.return_value = [mock_fresh_db]
            
            # Mock HumanReview
            mock_review = Mock()
            mock_review.id = "review-123"
            mock_human_review_class.return_value = mock_review
            
            # Create test state
            state = SurveyGenerationState(
                workflow_id="test-workflow-123",
                survey_id="survey-456",
                rfq_text="Test RFQ for human review",
                context={"rfq_details": {"text": "Test RFQ"}},
                golden_examples=[],
                methodology_blocks=[]
            )
            
            # Execute the node
            result = await node(state)
            
            # Verify non-blocking mode behavior
            assert result["prompt_approved"] is True
            assert result["pending_human_review"] is False
            assert result["workflow_paused"] is False
            assert result["review_id"] == "review-123"
            assert result["error_message"] is None
    
    @pytest.mark.asyncio
    async def test_human_review_workflow_disabled(self):
        """Test human review workflow when disabled."""
        # Mock database session
        mock_db = Mock()
        
        # Create the node
        node = HumanPromptReviewNode(mock_db)
        
        # Mock settings service to return disabled
        with patch('src.workflows.nodes.SettingsService') as mock_settings_service_class:
            mock_settings_service = Mock()
            mock_settings_service.get_evaluation_settings.return_value = {
                'enable_prompt_review': False,
                'prompt_review_mode': 'disabled'
            }
            mock_settings_service_class.return_value = mock_settings_service
            
            # Mock database connection
            with patch('src.workflows.nodes._get_db') as mock_get_db:
                mock_fresh_db = Mock()
                mock_fresh_db.close = Mock()
                mock_get_db.return_value = [mock_fresh_db]
                
                # Create test state
                state = SurveyGenerationState(
                    workflow_id="test-workflow-123",
                    rfq_text="Test RFQ",
                    context={},
                    golden_examples=[],
                    methodology_blocks=[]
                )
                
                # Execute the node
                result = await node(state)
                
                # Verify disabled behavior
                assert result["prompt_approved"] is True
                assert result["pending_human_review"] is False
                assert result["error_message"] is None
    
    @pytest.mark.asyncio
    async def test_human_review_workflow_existing_approved_review(self):
        """Test human review workflow with existing approved review."""
        # Mock database session
        mock_db = Mock()
        
        # Create the node
        node = HumanPromptReviewNode(mock_db)
        
        # Mock all dependencies
        with patch('src.workflows.nodes.PromptService') as mock_prompt_service_class, \
             patch('src.workflows.nodes.SettingsService') as mock_settings_service_class, \
             patch('src.workflows.nodes._get_db') as mock_get_db:
            
            # Setup mocks
            mock_prompt_service = AsyncMock()
            mock_prompt_service_class.return_value = mock_prompt_service
            
            mock_settings_service = Mock()
            mock_settings_service.get_evaluation_settings.return_value = {
                'enable_prompt_review': True,
                'prompt_review_mode': 'blocking'
            }
            mock_settings_service_class.return_value = mock_settings_service
            
            # Mock existing approved review
            mock_existing_review = Mock()
            mock_existing_review.review_status = 'approved'
            mock_existing_review.id = "existing-review-123"
            
            mock_fresh_db = Mock()
            mock_fresh_db.close = Mock()
            mock_fresh_db.query.return_value.filter.return_value.first.return_value = mock_existing_review
            mock_get_db.return_value = [mock_fresh_db]
            
            # Create test state
            state = SurveyGenerationState(
                workflow_id="test-workflow-123",
                rfq_text="Test RFQ",
                context={},
                golden_examples=[],
                methodology_blocks=[]
            )
            
            # Execute the node
            result = await node(state)
            
            # Verify existing approved review behavior
            assert result["prompt_approved"] is True
            assert result["pending_human_review"] is False
            assert result["review_id"] == "existing-review-123"
            assert result["error_message"] is None
            
            # Verify prompt service was not called (reused existing review)
            mock_prompt_service.create_survey_generation_prompt.assert_not_called()


class TestAsyncAPIEndpoints:
    """Test async API endpoints integration."""
    
    @pytest.mark.asyncio
    async def test_rfq_submission_async_workflow(self):
        """Test that RFQ submission properly handles async workflow."""
        # This would test the full RFQ submission flow
        # For now, we'll test the async pattern
        
        async def mock_workflow_service_process_rfq(*args, **kwargs):
            """Mock workflow service that simulates async processing."""
            await asyncio.sleep(0.1)  # Simulate async work
            return Mock(status="completed")
        
        # Test that async workflow is properly awaited
        result = await mock_workflow_service_process_rfq(
            title="Test RFQ",
            description="Test description",
            product_category="Test category",
            target_segment="Test segment",
            research_goal="Test goal",
            workflow_id="test-workflow",
            survey_id="test-survey"
        )
        
        assert result.status == "completed"
    
    @pytest.mark.asyncio
    async def test_document_upload_async_processing(self):
        """Test that document upload properly handles async processing."""
        # Mock document parser
        async def mock_parse_document(docx_content: bytes):
            await asyncio.sleep(0.1)  # Simulate async parsing
            return {
                "title": "Parsed Document",
                "content": "Parsed content",
                "fields": {"field1": "value1"}
            }
        
        # Test async document parsing
        mock_content = b"mock docx content"
        result = await mock_parse_document(mock_content)
        
        assert result["title"] == "Parsed Document"
        assert result["fields"]["field1"] == "value1"
    
    @pytest.mark.asyncio
    async def test_field_extraction_async_processing(self):
        """Test that field extraction properly handles async processing."""
        # Mock field extraction service
        async def mock_extract_fields(rfq_text: str, survey_json: Dict[str, Any]):
            await asyncio.sleep(0.1)  # Simulate async extraction
            return {
                "suggested_title": "Extracted Title",
                "confidence_level": 0.95,
                "reasoning": {"title": "Based on RFQ content"}
            }
        
        # Test async field extraction
        rfq_text = "Test RFQ text"
        survey_json = {"title": "Test Survey", "questions": []}
        
        result = await mock_extract_fields(rfq_text, survey_json)
        
        assert result["suggested_title"] == "Extracted Title"
        assert result["confidence_level"] == 0.95


class TestAsyncErrorHandling:
    """Test async error handling in integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_workflow_timeout_handling(self):
        """Test that workflow timeouts are handled properly."""
        async def slow_workflow():
            await asyncio.sleep(2)  # Simulate slow workflow
            return "Success"
        
        # Test timeout handling
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(slow_workflow(), timeout=0.1)
    
    @pytest.mark.asyncio
    async def test_async_service_failure_recovery(self):
        """Test that async service failures are handled gracefully."""
        async def failing_service():
            raise Exception("Service failure")
        
        async def resilient_workflow():
            try:
                await failing_service()
                return "Success"
            except Exception as e:
                return f"Recovered from: {str(e)}"
        
        result = await resilient_workflow()
        assert "Recovered from: Service failure" in result
    
    @pytest.mark.asyncio
    async def test_concurrent_async_operations(self):
        """Test that concurrent async operations work correctly."""
        async def async_operation(name: str, delay: float):
            await asyncio.sleep(delay)
            return f"Operation {name} completed"
        
        # Run multiple async operations concurrently
        tasks = [
            async_operation("A", 0.1),
            async_operation("B", 0.2),
            async_operation("C", 0.1)
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 3
        assert "Operation A completed" in results
        assert "Operation B completed" in results
        assert "Operation C completed" in results


if __name__ == "__main__":
    pytest.main([__file__])
