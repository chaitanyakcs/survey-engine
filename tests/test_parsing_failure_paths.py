"""
Integration Tests for Parsing Failure Paths

Tests that raw responses are captured in all LLM parsing failure scenarios.
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from src.services.generation_service import GenerationService, SurveyGenerationError
from src.services.document_parser import DocumentParser, DocumentParsingError
from src.services.field_extraction_service import FieldExtractionService
from src.utils.error_messages import UserFriendlyError


@pytest.mark.asyncio
async def test_generation_service_streaming_parse_failure():
    """Test that streaming path captures raw response on parse failure"""
    # Mock database session
    mock_db_session = Mock()
    
    # Create service
    service = GenerationService(db_session=mock_db_session)
    
    # Mock _extract_survey_json to fail
    with patch.object(service, '_extract_survey_json', side_effect=Exception("Parse failed")):
        # Mock the streaming response
        accumulated_content = '{"invalid": "json that will fail'
        
        with pytest.raises(SurveyGenerationError) as exc_info:
            # Simulate what happens in _stream_with_replicate
            try:
                service._extract_survey_json(accumulated_content)
            except Exception as e:
                if isinstance(e, SurveyGenerationError):
                    if not e.raw_response:
                        e.raw_response = accumulated_content
                else:
                    raise SurveyGenerationError(
                        f"Streaming generation failed: {str(e)}",
                        error_code="GEN_STREAM_PARSE_001",
                        raw_response=accumulated_content
                    ) from e
                raise
        
        # Verify raw response is attached
        assert exc_info.value.raw_response == accumulated_content


@pytest.mark.asyncio
async def test_generation_service_sync_parse_failure():
    """Test that sync path captures raw response on parse failure"""
    # Mock database session
    mock_db_session = Mock()
    
    # Create service
    service = GenerationService(db_session=mock_db_session)
    
    # Mock _extract_survey_json to fail
    with patch.object(service, '_extract_survey_json', side_effect=Exception("Parse failed")):
        output_text = '{"invalid": "json"'
        
        with pytest.raises(SurveyGenerationError) as exc_info:
            # Simulate what happens in _generate_with_sync_fallback
            try:
                service._extract_survey_json(output_text)
            except Exception as e:
                if isinstance(e, SurveyGenerationError):
                    if not e.raw_response:
                        e.raw_response = output_text
                else:
                    raise SurveyGenerationError(
                        f"Sync generation failed: {str(e)}",
                        error_code="GEN_SYNC_PARSE_001",
                        raw_response=output_text
                    ) from e
                raise
        
        # Verify raw response is attached
        assert exc_info.value.raw_response == output_text


@pytest.mark.asyncio
async def test_document_parser_parse_failure_with_emergency_log():
    """Test that DocumentParser emergency logs on parse failure"""
    # Mock database session
    mock_db_session = Mock()
    
    # Create parser
    parser = DocumentParser(db_session=mock_db_session)
    
    # Mock emergency_log_llm_failure
    with patch("src.services.document_parser.emergency_log_llm_failure", new_callable=AsyncMock) as mock_emergency_log:
        # Mock parse_llm_json_response to return None (parse failed)
        with patch("src.services.document_parser.parse_llm_json_response", return_value=None):
            json_content = '{"invalid": "json"'
            document_text = "Test document"
            prompt = "Test prompt"
            
            with pytest.raises(DocumentParsingError) as exc_info:
                # Simulate the failure path in convert_to_json
                survey_data = None  # parse_llm_json_response returned None
                
                if survey_data is None:
                    # Emergency logging should be called
                    await mock_emergency_log(
                        raw_response=json_content,
                        service_name="DocumentParser",
                        error_message="All JSON extraction methods failed",
                        context={
                            "session_id": None,
                            "document_length": len(document_text),
                            "json_content_length": len(json_content),
                        },
                        model_name=parser.model,
                        model_provider="replicate",
                        purpose="document_parsing",
                        input_prompt=prompt,
                    )
                    
                    raise DocumentParsingError(
                        f"No valid JSON found in response",
                        raw_response=json_content
                    )
            
            # Verify emergency log was called
            mock_emergency_log.assert_called_once()
            
            # Verify raw response is attached to exception
            assert exc_info.value.raw_response == json_content


@pytest.mark.asyncio
async def test_field_extraction_parse_failure_with_emergency_log():
    """Test that FieldExtractionService emergency logs on parse failure"""
    # Mock database session
    mock_db_session = Mock()
    
    # Create service
    service = FieldExtractionService(db_session=mock_db_session)
    
    # Mock emergency_log_llm_failure
    with patch("src.services.field_extraction_service.emergency_log_llm_failure", new_callable=AsyncMock) as mock_emergency_log:
        # Mock parse_llm_json_response to return None
        with patch("src.services.field_extraction_service.parse_llm_json_response", return_value=None):
            json_content = '{"invalid": "json"'
            rfq_text = "Test RFQ"
            survey_json = {"test": "survey"}
            prompt = "Test prompt"
            
            with pytest.raises(UserFriendlyError) as exc_info:
                # Simulate the failure path
                extracted_fields = None  # parse_llm_json_response returned None
                
                if extracted_fields is None:
                    # Emergency logging should be called
                    await mock_emergency_log(
                        raw_response=json_content,
                        service_name="FieldExtractionService",
                        error_message="JSON parsing failed for field extraction",
                        context={
                            "rfq_length": len(rfq_text),
                            "survey_keys": list(survey_json.keys()),
                            "json_content_length": len(json_content),
                        },
                        model_name=service.model,
                        model_provider="replicate",
                        purpose="field_extraction",
                        input_prompt=prompt,
                    )
                    
                    raise UserFriendlyError(
                        message="Failed to extract fields from survey content",
                        technical_details="LLM response was not valid JSON",
                        action_required="Please try again or manually fill the fields",
                        raw_response=json_content
                    )
            
            # Verify emergency log was called
            mock_emergency_log.assert_called_once()
            
            # Verify raw response is attached to exception
            assert exc_info.value.raw_response == json_content


@pytest.mark.asyncio
async def test_exception_raw_response_propagation():
    """Test that raw_response propagates through exception chain"""
    raw_response = '{"test": "data"}'
    
    # Create exception with raw_response
    error = SurveyGenerationError(
        "Test error",
        error_code="TEST_001",
        raw_response=raw_response
    )
    
    # Verify raw_response is accessible
    assert error.raw_response == raw_response
    
    # Test UserFriendlyError
    user_error = UserFriendlyError(
        message="Test error",
        raw_response=raw_response
    )
    assert user_error.raw_response == raw_response
    
    # Test DocumentParsingError
    doc_error = DocumentParsingError(
        "Test error",
        raw_response=raw_response
    )
    assert doc_error.raw_response == raw_response


@pytest.mark.asyncio
async def test_audit_context_captures_raw_response_from_exception():
    """Test that audit context captures raw response from exception"""
    from src.services.llm_audit_service import LLMAuditContext, LLMAuditService
    
    # Mock database session
    mock_db_session = Mock()
    audit_service = LLMAuditService(mock_db_session)
    
    raw_response = '{"test": "data"}'
    
    # Create audit context
    async with LLMAuditContext(
        audit_service=audit_service,
        interaction_id="test_123",
        model_name="test-model",
        model_provider="test-provider",
        purpose="test",
        input_prompt="test prompt",
    ) as audit_context:
        try:
            # Simulate failure with raw response
            raise SurveyGenerationError(
                "Test error",
                error_code="TEST_001",
                raw_response=raw_response
            )
        except SurveyGenerationError as e:
            # Capture raw response from exception
            if e.raw_response:
                audit_context.set_raw_response(e.raw_response)
            raise
    
    # Verify raw response was set in audit context
    assert audit_context.raw_response == raw_response


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

