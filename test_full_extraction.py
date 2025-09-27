#!/usr/bin/env python3
"""
Test the complete extraction pipeline exactly as it happens in production
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.generation_service import GenerationService
from unittest.mock import MagicMock
import json

def test_full_pipeline():
    """Test the complete extraction pipeline"""

    mock_db = MagicMock()
    service = GenerationService(mock_db)

    # Use the beginning portion of the user's actual production JSON (the exact format that causes issues)
    # This is structured exactly like their production logs
    production_json = '''{ "
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
 }, { "
id
": "
q3
", "
text
": "
Are
 you
 involved
 in
 decisions
 to
 purchase
 consumer
 products
 for
 yourself
 or
 your
 household
?", "
type
": "
multiple_choice
", "
options
": ["
Yes
,
 I
 am
 the
 primary
 decision-maker
", "
Yes
,
 I
 share
 decisions
 equally
", "
Yes
,
 I
 influence
 but
 do
 not
 decide
", "
No
,
 I
 am
 not
 involved
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
 disqualify
 if
 No
,
 I
 am
 not
 involved
", "
order
":
3
 }, { "
id
": "
q4
", "
text
": "
Have
 you
 worked
 in
 any
 of
 the
 following
 industries
 in
 the
 past

12
 months
?", "
type
": "
multiple_choice
", "
options
": ["
Market
 research
", "
Advertising
 or
 PR
", "
Consumer
 product
 manufacturer
", "
Retailer
 of
 the
 target
 category
", "
None
 of
 the
 above
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
 disqualify
 if
 Market
 research
 or
 Advertising
 or
 PR
", "
order
":
4
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
q9
", "
text
": "
How
 often
 do
 you
 purchase
 new
 consumer
 products
 in
 this
 category
?", "
type
": "
multiple_choice
", "
options
": ["
Weekly
", "
Monthly
", "
Every

2-3
 months
", "
Twice
 a
 year
", "
Once
 a
 year
 or
 less
", "
Never
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
15
, "
methodology_tags
": ["
van_westendorp
", "
pricing
", "
conjoint
", "
cbc
", "
maxdiff
", "
segmentation
", "
brand_perception
"], "
target_responses
":
400
, "
quality_score
":
0.93
, "
sections_count
":
5
 } }'''

    print("=== FULL PIPELINE TEST ===")
    print(f"Input length: {len(production_json)} characters")

    # Test the complete _extract_survey_json method that's called in production
    try:
        result = service._extract_survey_json(production_json)
        if result:
            print(f"✅ Full extraction succeeded! Keys: {list(result.keys())}")
            if 'sections' in result:
                total_questions = sum(len(section.get('questions', [])) for section in result.get('sections', []))
                print(f"✅ Full extraction found {total_questions} total questions")
            return total_questions
        else:
            print(f"❌ Full extraction returned None")
            return 0
    except Exception as e:
        print(f"❌ Full extraction failed: {e}")
        return 0

if __name__ == "__main__":
    result = test_full_pipeline()
    if result > 0:
        print(f"\n🎉 SUCCESS: Pipeline extracted {result} questions correctly!")
    else:
        print(f"\n❌ FAILURE: Pipeline extracted 0 questions - needs investigation")