#!/usr/bin/env python3
"""
Test the fix for large malformed JSON responses with embedded control characters
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.generation_service import GenerationService
from unittest.mock import MagicMock
import json

def test_large_malformed_json():
    """Test with the exact format that was causing issues"""

    mock_db = MagicMock()
    service = GenerationService(mock_db)

    # Simulate the exact problematic format from user's logs
    malformed_json = '''{


 "
title
":
 "
Enterprise
 Software
 Market
 Research
 Study
",


 "
description
":
 "
A
 comprehensive
 study
 to
 assess
 pricing
 sensitivity
,
 feature
 priorities
,
 brand
 perception
,
 and
 reactions
 to
 a
 new
 product
 concept
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
65
 or
 older
"], "
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
 terminate_if
:
Under

18
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
Where
 do
 you
 currently
 reside
?", "
type
": "
multiple_choice
", "
options
": ["
United
 States
", "
Canada
", "
United
 Kingdom
"], "
required
": true, "
methodology
": "
screening
", "
validation
": "
single_select
", "
order
":
2
 } ] }, { "
id
":
2
, "
title
": "
Consumer
 Details
", "
description
": "
Detailed
 consumer
 information
 and
 behavior
 patterns
", "
questions
": [ { "
id
": "
q3
", "
text
": "
How
 many
 different
 software
 subscriptions
 do
 you
 currently
 pay
 for
 personally
?", "
type
": "
multiple_choice
", "
options
": ["
None
", "
1
", "
2
", "
3-4
", "
5
 or
 more
"], "
required
": true, "
methodology
": "
behavior
", "
validation
": "
single_select
", "
order
":
1
 } ] } ], "
metadata
": { "
estimated_time
":
14
, "
methodology_tags
": ["
van_westendorp
", "
pricing
"], "
target_responses
":
600
, "
quality_score
":
0.93
, "
sections_count
":
2
 } }'''

    print("=== LARGE MALFORMED JSON TEST ===")
    print(f"Input length: {len(malformed_json)} characters")
    print(f"Has embedded newlines: {'\\n' in malformed_json}")

    try:
        # Test the sanitization
        sanitized = service._sanitize_raw_output(malformed_json)
        print(f"✅ Sanitization completed. Output length: {len(sanitized)}")
        print(f"Preview: {sanitized[:200]}...")

        # Test if it parses as valid JSON
        parsed = json.loads(sanitized)
        print(f"✅ JSON parsing successful!")

        # Count questions
        if 'sections' in parsed:
            total_questions = sum(len(section.get('questions', [])) for section in parsed.get('sections', []))
            print(f"✅ Found {total_questions} questions in {len(parsed['sections'])} sections")

            for i, section in enumerate(parsed['sections']):
                section_questions = len(section.get('questions', []))
                print(f"  Section {i+1}: {section_questions} questions")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_large_malformed_json()
    if success:
        print("\n🎉 SUCCESS: Large malformed JSON handling fixed!")
    else:
        print("\n❌ FAILURE: Still has issues")