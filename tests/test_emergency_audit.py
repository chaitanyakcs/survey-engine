"""
Tests for Emergency Audit Logging

Tests the emergency logging system that ensures raw LLM responses
are ALWAYS captured, even when normal audit context fails.
"""

import pytest
import os
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.utils.emergency_audit import (
    emergency_log_llm_failure,
    _log_to_independent_db,
    _log_to_file,
    get_emergency_log_files,
    load_emergency_log,
    cleanup_old_emergency_logs,
    EMERGENCY_LOG_DIR,
)


@pytest.mark.asyncio
async def test_emergency_log_to_file():
    """Test that emergency logging to file works"""
    # Prepare test data
    raw_response = "This is a test LLM response that failed to parse"
    service_name = "TestService"
    error_message = "JSON parsing failed"
    interaction_id = "test_12345678"
    
    # Log to file
    file_path = await _log_to_file(
        interaction_id=interaction_id,
        raw_response=raw_response,
        service_name=service_name,
        error_message=error_message,
        model_name="test-model",
        model_provider="test-provider",
        purpose="test_purpose",
        input_prompt="test prompt",
        context={"test_key": "test_value"},
    )
    
    # Verify file was created
    assert os.path.exists(file_path)
    
    # Load and verify contents
    log_data = await load_emergency_log(file_path)
    assert log_data["interaction_id"] == interaction_id
    assert log_data["raw_response"] == raw_response
    assert log_data["service_name"] == service_name
    assert log_data["error_message"] == error_message
    assert log_data["emergency_logged"] is True
    
    # Cleanup
    os.remove(file_path)


@pytest.mark.asyncio
async def test_emergency_log_with_db_failure():
    """Test that emergency logging falls back to file when DB fails"""
    raw_response = "Test response"
    service_name = "TestService"
    error_message = "Test error"
    
    # Mock DB to fail
    with patch("src.utils.emergency_audit._log_to_independent_db", side_effect=Exception("DB failed")):
        interaction_id = await emergency_log_llm_failure(
            raw_response=raw_response,
            service_name=service_name,
            error_message=error_message,
        )
    
    # Verify file was created as fallback
    log_files = get_emergency_log_files()
    assert len(log_files) > 0
    
    # Find our log file
    found = False
    for file_path in log_files:
        if interaction_id in str(file_path):
            found = True
            log_data = await load_emergency_log(str(file_path))
            assert log_data["raw_response"] == raw_response
            # Cleanup
            os.remove(file_path)
            break
    
    assert found, f"Log file with interaction_id {interaction_id} not found"


@pytest.mark.asyncio
async def test_cleanup_old_emergency_logs():
    """Test cleanup of old emergency log files"""
    # Create some test log files
    EMERGENCY_LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    test_files = []
    for i in range(3):
        file_path = EMERGENCY_LOG_DIR / f"test_{i}.json"
        with open(file_path, "w") as f:
            json.dump({"test": i}, f)
        test_files.append(file_path)
    
    # Cleanup (should not delete recent files)
    deleted_count = await cleanup_old_emergency_logs(days=7)
    
    # Verify files still exist (they're recent)
    for file_path in test_files:
        assert file_path.exists()
    
    # Cleanup test files
    for file_path in test_files:
        file_path.unlink()


@pytest.mark.asyncio
async def test_emergency_log_with_large_response():
    """Test emergency logging with very large raw response"""
    # Create a large response (10MB)
    raw_response = "x" * (10 * 1024 * 1024)
    service_name = "TestService"
    error_message = "Large response test"
    
    # Mock DB to fail so we use file logging
    with patch("src.utils.emergency_audit._log_to_independent_db", side_effect=Exception("DB failed")):
        interaction_id = await emergency_log_llm_failure(
            raw_response=raw_response,
            service_name=service_name,
            error_message=error_message,
        )
    
    # Verify file was created
    log_files = get_emergency_log_files()
    found = False
    for file_path in log_files:
        if interaction_id in str(file_path):
            found = True
            # Verify file size is reasonable (compressed)
            file_size = os.path.getsize(file_path)
            assert file_size > 0
            # Cleanup
            os.remove(file_path)
            break
    
    assert found


@pytest.mark.asyncio
async def test_emergency_log_with_unicode():
    """Test emergency logging with unicode characters"""
    raw_response = "Test with unicode: 你好世界 🌍 Ñoño"
    service_name = "TestService"
    error_message = "Unicode test"
    
    # Mock DB to fail
    with patch("src.utils.emergency_audit._log_to_independent_db", side_effect=Exception("DB failed")):
        interaction_id = await emergency_log_llm_failure(
            raw_response=raw_response,
            service_name=service_name,
            error_message=error_message,
        )
    
    # Verify file was created and unicode preserved
    log_files = get_emergency_log_files()
    found = False
    for file_path in log_files:
        if interaction_id in str(file_path):
            found = True
            log_data = await load_emergency_log(str(file_path))
            assert log_data["raw_response"] == raw_response
            # Cleanup
            os.remove(file_path)
            break
    
    assert found


@pytest.mark.asyncio
async def test_emergency_log_interaction_id_generation():
    """Test that interaction IDs are generated when not provided"""
    raw_response = "Test response"
    service_name = "TestService"
    error_message = "Test error"
    
    # Mock DB to fail
    with patch("src.utils.emergency_audit._log_to_independent_db", side_effect=Exception("DB failed")):
        interaction_id = await emergency_log_llm_failure(
            raw_response=raw_response,
            service_name=service_name,
            error_message=error_message,
            interaction_id=None,  # No ID provided
        )
    
    # Verify ID was generated
    assert interaction_id is not None
    assert interaction_id.startswith("emergency_")
    
    # Cleanup
    log_files = get_emergency_log_files()
    for file_path in log_files:
        if interaction_id in str(file_path):
            os.remove(file_path)


@pytest.mark.asyncio
async def test_get_emergency_log_files():
    """Test retrieving emergency log files"""
    # Create some test log files
    EMERGENCY_LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    test_files = []
    for i in range(3):
        file_path = EMERGENCY_LOG_DIR / f"20240101_000000_test_{i}_TestService.json"
        with open(file_path, "w") as f:
            json.dump({"test": i}, f)
        test_files.append(file_path)
    
    # Get log files
    log_files = get_emergency_log_files()
    
    # Verify we got our files
    assert len(log_files) >= 3
    
    # Cleanup
    for file_path in test_files:
        file_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

