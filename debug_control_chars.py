#!/usr/bin/env python3
"""
Debug exactly what's happening with control character removal
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.generation_service import GenerationService
from unittest.mock import MagicMock
import json
import re

def debug_sanitization_step_by_step():
    """Debug each step of the sanitization process"""

    mock_db = MagicMock()
    service = GenerationService(mock_db)

    # Small test case with embedded newlines like production
    test_input = """{

 "
title
":
 "
Test
",

 "
questions
":
 [
 {
 "
id
":
 "
q1
",
 "
text
":
 "
What
 is
 your
 age
?"
 }
 ]
}"""

    print("=== STEP-BY-STEP SANITIZATION DEBUG ===")
    print(f"Original: {repr(test_input[:100])}...")
    print(f"Original length: {len(test_input)}")

    # Step 1: Initial cleanup
    sanitized = test_input

    # Find JSON boundaries
    start = sanitized.find('{')
    end = sanitized.rfind('}')
    if start >= 0 and end > start:
        sanitized = sanitized[start:end + 1]
    print(f"\nAfter boundary trim: {repr(sanitized[:100])}...")

    # Step 2: Control character removal
    print(f"\nBefore control char removal:")
    print(f"  Has \\n: {'\\n' in sanitized}")
    print(f"  Has \\r: {'\\r' in sanitized}")
    print(f"  Char codes at start: {[ord(c) for c in sanitized[:10]]}")

    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)
    print(f"After control char removal: {repr(sanitized[:100])}...")
    print(f"  Has \\n: {'\\n' in sanitized}")
    print(f"  Length: {len(sanitized)}")

    # Step 3: Try JSON parsing
    try:
        parsed = json.loads(sanitized)
        print(f"✅ JSON parsing successful!")
        return True
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing failed: {e}")
        print(f"Error at position {e.pos}: {repr(sanitized[max(0, e.pos-10):e.pos+10])}")
        return False

if __name__ == "__main__":
    debug_sanitization_step_by_step()