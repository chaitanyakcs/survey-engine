#!/usr/bin/env python3
"""
Debug the question extraction issue
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.generation_service import GenerationService
from unittest.mock import MagicMock
import json

def test_extraction_pipeline():
    """Test the complete extraction pipeline with user's sample"""

    mock_db = MagicMock()
    service = GenerationService(mock_db)

    # Use the user's exact malformed JSON that was causing issues
    user_sample = '''{ "
title
": "
Market
 Research
 Study
:
 Pricing
 Sensitivity
,
 Feature
 Priorities
,
 and
 Market
 Positioning
", "
description
": "
This
 survey
 collects
 information
 on
 consumer
 demographics
,
 behaviors
,
 brand
 perceptions
,
 and
 reactions
 to
 a
 new
 product
 concept
,
 including
 price
 sensitivity
 using
 the
 Van
 Westendorp
 Price
 Sensitivity
 Meter
 and
 feature
 trade-offs
 using
 Conjoint
 and
 MaxDiff
 methods
.", "
sections
": [ { "
id
":
1
, "
title
": "
Screener
 &
 Demographics
", "
description
": "
Initial
 screening
 questions
 and
 demographic
 information
", "
questions
": [ { "
id
": "
q1
", "
text
": "
What
 is
 your
 age
?", "
type
": "
multiple_choice
", "
options
": ["
Under

18
", "
18-24
", "
25-34
", "
35-44
", "
45-54
", "
55-64
", "
65+"], "
required
": true, "
methodology
": "
screening
", "
validation
": "
single_select
;
 qualify
 if

18-65
", "
order
":
1
 }, { "
id
": "
q2
", "
text
": "
Which
 country
 do
 you
 currently
 live
 in
?", "
type
": "
open_text
", "
options
": [], "
required
": true, "
methodology
": "
screening
", "
validation
": "
text_required
", "
order
":
2
 } ] } ] }'''

    print("=== EXTRACTION PIPELINE DEBUG ===")
    print(f"Original length: {len(user_sample)}")

    # Step 1: Test sanitization
    print("\n--- Step 1: Testing Sanitization ---")
    try:
        sanitized = service._sanitize_raw_output(user_sample)
        print(f"✅ Sanitization successful. Length: {len(sanitized)}")
        print(f"Sanitized preview: {sanitized[:200]}...")

        # Test if sanitized JSON is valid
        try:
            parsed_direct = json.loads(sanitized)
            print(f"✅ Sanitized JSON is valid! Keys: {list(parsed_direct.keys())}")
            if 'sections' in parsed_direct:
                total_questions = sum(len(section.get('questions', [])) for section in parsed_direct.get('sections', []))
                print(f"✅ Direct parsing found {total_questions} questions in sections")
        except json.JSONDecodeError as e:
            print(f"❌ Sanitized JSON is still invalid: {e}")

    except Exception as e:
        print(f"❌ Sanitization failed: {e}")
        return

    # Step 2: Test extraction methods
    print("\n--- Step 2: Testing Extraction Methods ---")

    # Test direct JSON extraction
    try:
        direct_result = service._extract_direct_json(sanitized)
        if direct_result:
            print(f"✅ Direct JSON extraction successful! Keys: {list(direct_result.keys())}")
            if 'sections' in direct_result:
                total_questions = sum(len(section.get('questions', [])) for section in direct_result.get('sections', []))
                print(f"✅ Direct extraction found {total_questions} questions")
        else:
            print(f"❌ Direct JSON extraction returned None")
    except Exception as e:
        print(f"❌ Direct JSON extraction failed: {e}")

    # Test full extraction pipeline
    print("\n--- Step 3: Testing Full Extraction Pipeline ---")
    try:
        full_result = service._extract_survey_json(sanitized)
        if full_result:
            print(f"✅ Full extraction successful! Keys: {list(full_result.keys())}")
            if 'sections' in full_result:
                total_questions = sum(len(section.get('questions', [])) for section in full_result.get('sections', []))
                print(f"✅ Full extraction found {total_questions} questions")
        else:
            print(f"❌ Full extraction returned None")
    except Exception as e:
        print(f"❌ Full extraction failed: {e}")

if __name__ == "__main__":
    test_extraction_pipeline()