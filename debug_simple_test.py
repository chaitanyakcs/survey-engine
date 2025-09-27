#!/usr/bin/env python3
"""
Simple test to see what's happening with JSON sanitization
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.generation_service import GenerationService
from unittest.mock import MagicMock
import json

def test_simple_case():
    """Test a simple malformed JSON case"""

    mock_db = MagicMock()
    service = GenerationService(mock_db)

    # Simple test case
    simple_malformed = '''{ "
title
": "
Test
 Survey
", "
questions
": [ { "
text
": "
What
 is
 your
 age
?" } ] }'''

    print("=== SIMPLE TEST ===")
    print(f"Original: {repr(simple_malformed)}")

    try:
        sanitized = service._sanitize_raw_output(simple_malformed)
        print(f"Sanitized: {repr(sanitized)}")

        parsed = json.loads(sanitized)
        print(f"Parsed successfully: {parsed}")
        return True

    except Exception as e:
        print(f"Error: {e}")
        return False

def test_methods_exist():
    """Check if our new methods exist"""
    mock_db = MagicMock()
    service = GenerationService(mock_db)

    print("=== METHOD CHECK ===")
    print(f"Has _smart_normalize_whitespace: {hasattr(service, '_smart_normalize_whitespace')}")
    print(f"Has _sanitize_raw_output: {hasattr(service, '_sanitize_raw_output')}")

    # Check if the method was updated
    import inspect
    source = inspect.getsource(service._sanitize_raw_output)
    print(f"Contains 'Smart JSON': {'Smart JSON' in source}")
    print(f"Contains 'smart_normalize_whitespace': {'smart_normalize_whitespace' in source}")

if __name__ == "__main__":
    test_methods_exist()
    print()
    test_simple_case()