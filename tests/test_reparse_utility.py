"""
Tests for Reparse Utility

Tests the ability to retrieve raw responses from audit records
and rerun parsers for debugging and recovery.
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.utils.reparse_from_audit import (
    reparse_from_audit_record,
    reparse_failed_interactions,
    _get_default_strategies,
    _get_schema_for_parser_type,
    _get_parser_type_from_purpose,
)
from src.utils.json_generation_utils import JSONParseStrategy


@pytest.mark.asyncio
async def test_reparse_from_audit_record_success():
    """Test successful reparse from audit record"""
    # Mock audit record with valid JSON
    mock_audit_record = Mock()
    mock_audit_record.interaction_id = "test_interaction_123"
    mock_audit_record.purpose = "survey_generation"
    mock_audit_record.sub_purpose = "generation"
    mock_audit_record.model_name = "test-model"
    mock_audit_record.model_provider = "replicate"
    mock_audit_record.created_at = datetime.utcnow()
    mock_audit_record.success = False
    mock_audit_record.error_message = "JSON parsing failed"
    mock_audit_record.raw_response = json.dumps({
        "title": "Test Survey",
        "description": "Test description",
        "sections": []
    })
    
    # Mock audit service
    mock_audit_service = AsyncMock()
    mock_audit_service.get_interaction = AsyncMock(return_value=mock_audit_record)
    
    # Mock database session
    mock_db_session = Mock()
    
    with patch("src.utils.reparse_from_audit.LLMAuditService", return_value=mock_audit_service):
        result = await reparse_from_audit_record(
            audit_record_id="test_interaction_123",
            parser_type="survey",
            db_session=mock_db_session,
        )
    
    # Verify success
    assert result["success"] is True
    assert result["data"] is not None
    assert result["error"] is None
    assert result["audit_record"]["interaction_id"] == "test_interaction_123"
    assert result["parsing_result"]["strategy_used"] is not None


@pytest.mark.asyncio
async def test_reparse_from_audit_record_not_found():
    """Test reparse when audit record doesn't exist"""
    # Mock audit service that returns None
    mock_audit_service = AsyncMock()
    mock_audit_service.get_interaction = AsyncMock(return_value=None)
    
    mock_db_session = Mock()
    
    with patch("src.utils.reparse_from_audit.LLMAuditService", return_value=mock_audit_service):
        result = await reparse_from_audit_record(
            audit_record_id="nonexistent_id",
            parser_type="survey",
            db_session=mock_db_session,
        )
    
    # Verify failure
    assert result["success"] is False
    assert "not found" in result["error"]
    assert result["data"] is None


@pytest.mark.asyncio
async def test_reparse_from_audit_record_no_raw_response():
    """Test reparse when audit record has no raw response"""
    # Mock audit record without raw response
    mock_audit_record = Mock()
    mock_audit_record.interaction_id = "test_interaction_123"
    mock_audit_record.purpose = "survey_generation"
    mock_audit_record.model_name = "test-model"
    mock_audit_record.created_at = datetime.utcnow()
    mock_audit_record.raw_response = None  # No raw response
    
    mock_audit_service = AsyncMock()
    mock_audit_service.get_interaction = AsyncMock(return_value=mock_audit_record)
    
    mock_db_session = Mock()
    
    with patch("src.utils.reparse_from_audit.LLMAuditService", return_value=mock_audit_service):
        result = await reparse_from_audit_record(
            audit_record_id="test_interaction_123",
            parser_type="survey",
            db_session=mock_db_session,
        )
    
    # Verify failure
    assert result["success"] is False
    assert "No raw response" in result["error"]


@pytest.mark.asyncio
async def test_reparse_from_audit_record_invalid_json():
    """Test reparse with invalid JSON that can't be parsed"""
    # Mock audit record with invalid JSON
    mock_audit_record = Mock()
    mock_audit_record.interaction_id = "test_interaction_123"
    mock_audit_record.purpose = "survey_generation"
    mock_audit_record.sub_purpose = "generation"
    mock_audit_record.model_name = "test-model"
    mock_audit_record.model_provider = "replicate"
    mock_audit_record.created_at = datetime.utcnow()
    mock_audit_record.success = False
    mock_audit_record.error_message = "JSON parsing failed"
    mock_audit_record.raw_response = "This is not valid JSON at all { broken"
    
    mock_audit_service = AsyncMock()
    mock_audit_service.get_interaction = AsyncMock(return_value=mock_audit_record)
    
    mock_db_session = Mock()
    
    with patch("src.utils.reparse_from_audit.LLMAuditService", return_value=mock_audit_service):
        result = await reparse_from_audit_record(
            audit_record_id="test_interaction_123",
            parser_type="survey",
            db_session=mock_db_session,
        )
    
    # Verify failure (all strategies failed)
    assert result["success"] is False
    assert "All parsing strategies failed" in result["error"]


@pytest.mark.asyncio
async def test_reparse_failed_interactions():
    """Test batch reparse of failed interactions"""
    # Mock failed audit records
    mock_records = []
    for i in range(3):
        mock_record = Mock()
        mock_record.interaction_id = f"test_interaction_{i}"
        mock_record.purpose = "survey_generation"
        mock_record.sub_purpose = "generation"
        mock_record.model_name = "test-model"
        mock_record.model_provider = "replicate"
        mock_record.created_at = datetime.utcnow()
        mock_record.success = False
        mock_record.error_message = "JSON parsing failed"
        mock_record.raw_response = json.dumps({
            "title": f"Test Survey {i}",
            "sections": []
        })
        mock_records.append(mock_record)
    
    # Mock audit service
    mock_audit_service = AsyncMock()
    mock_audit_service.get_audit_records = AsyncMock(return_value=(mock_records, 3))
    mock_audit_service.get_interaction = AsyncMock(side_effect=mock_records)
    
    mock_db_session = Mock()
    
    with patch("src.utils.reparse_from_audit.LLMAuditService", return_value=mock_audit_service):
        result = await reparse_failed_interactions(
            purpose="survey_generation",
            limit=10,
            db_session=mock_db_session,
        )
    
    # Verify results
    assert result["total_attempted"] == 3
    assert result["successful_reparses"] + result["failed_reparses"] == 3
    assert len(result["results"]) == 3


def test_get_default_strategies():
    """Test getting default parsing strategies for different parser types"""
    # Test survey parser
    survey_strategies = _get_default_strategies("survey")
    assert JSONParseStrategy.REPLICATE_EXTRACT in survey_strategies
    assert JSONParseStrategy.DIRECT in survey_strategies
    assert len(survey_strategies) > 5
    
    # Test document parser
    doc_strategies = _get_default_strategies("document")
    assert JSONParseStrategy.DIRECT in doc_strategies
    assert len(doc_strategies) > 3
    
    # Test field extraction parser
    field_strategies = _get_default_strategies("field_extraction")
    assert JSONParseStrategy.DIRECT in field_strategies
    
    # Test unknown parser type (should return all strategies)
    unknown_strategies = _get_default_strategies("unknown")
    assert len(unknown_strategies) > 0


def test_get_schema_for_parser_type():
    """Test getting schema for different parser types"""
    # Test survey parser
    survey_schema = _get_schema_for_parser_type("survey")
    assert survey_schema is not None
    
    # Test document parser
    doc_schema = _get_schema_for_parser_type("document")
    assert doc_schema is not None
    
    # Test field extraction (no strict schema)
    field_schema = _get_schema_for_parser_type("field_extraction")
    # Field extraction may or may not have schema
    
    # Test unknown type
    unknown_schema = _get_schema_for_parser_type("unknown")
    assert unknown_schema is None


def test_get_parser_type_from_purpose():
    """Test determining parser type from purpose"""
    assert _get_parser_type_from_purpose("survey_generation") == "survey"
    assert _get_parser_type_from_purpose("document_parsing") == "document"
    assert _get_parser_type_from_purpose("field_extraction") == "field_extraction"
    assert _get_parser_type_from_purpose("unknown_purpose") == "survey"  # Default


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

