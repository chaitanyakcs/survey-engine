#!/usr/bin/env python3
"""
Debug with user's exact production sample from logs
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.generation_service import GenerationService
from unittest.mock import MagicMock
import json

def test_production_sample():
    """Test with user's exact production sample from the logs"""

    mock_db = MagicMock()
    service = GenerationService(mock_db)

    # User's EXACT production sample from the logs (truncated for the key parts)
    production_sample = '''{ "
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
 }, { "
id
": "
q5
", "
text
": "
What
 is
 your
 household
 income
 before
 taxes
?", "
type
": "
multiple_choice
", "
options
": ["
Under
 $
25
,
000
", "$
25
,
000-$
49
,
999
", "$
50
,
000-$
74
,
999
", "$
75
,
000-$
99
,
999
", "$
100
,
000-$
149
,
999
", "$
150
,
000+"], "
required
": true, "
methodology
": "
demographics
", "
validation
": "
single_select
", "
order
":
5
 }, { "
id
": "
q6
", "
text
": "
What
 is
 your
 highest
 level
 of
 education
 completed
?", "
type
": "
multiple_choice
", "
options
": ["
Less
 than
 high
 school
", "
High
 school
 or
 equivalent
", "
Some
 college/Associate
", "
Bachelor's
 degree
", "
Graduate
 degree+"], "
required
": true, "
methodology
": "
demographics
", "
validation
": "
single_select
", "
order
":
6
 }, { "
id
": "
q7
", "
text
": "
Which
 of
 the
 following
 best
 describes
 your
 current
 employment
 status
?", "
type
": "
multiple_choice
", "
options
": ["
Full-time
", "
Part-time
", "
Self-employed
", "
Student
", "
Homemaker
", "
Unemployed
", "
Retired
"], "
required
": true, "
methodology
": "
demographics
", "
validation
": "
single_select
", "
order
":
7
 }, { "
id
": "
q8
", "
text
": "
What
 is
 your
 gender
?", "
type
": "
multiple_choice
", "
options
": ["
Female
", "
Male
", "
Non-binary
", "
Prefer
 to
 self-describe
", "
Prefer
 not
 to
 say
"], "
required
": false, "
methodology
": "
demographics
", "
validation
": "
single_select
", "
order
":
8
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
 }, { "
id
": "
q10
", "
text
": "
When
 shopping
 in
 this
 category
,
 how
 do
 you
 usually
 research
 products
 before
 buying
?", "
type
": "
multiple_choice
", "
options
": ["
Read
 online
 reviews
", "
Compare
 prices
 across
 retailers
", "
Ask
 friends
 or
 family
", "
Visit
 brand
 websites
", "
Social
 media
 or
 influencers
", "
In-store
 browsing
", "
I
 do
 not
 research
"], "
required
": true, "
methodology
": "
behavior
", "
validation
": "
multi_select_max_3
", "
order
":
2
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

    print("=== PRODUCTION SAMPLE DEBUG ===")
    print(f"Original length: {len(production_sample)}")

    # Step 1: Test sanitization
    print("\n--- Step 1: Testing Sanitization ---")
    try:
        sanitized = service._sanitize_raw_output(production_sample)
        print(f"✅ Sanitization successful. Length: {len(sanitized)}")

        # Test if sanitized JSON is valid
        try:
            parsed_direct = json.loads(sanitized)
            print(f"✅ Sanitized JSON is valid! Keys: {list(parsed_direct.keys())}")
            if 'sections' in parsed_direct:
                total_questions = 0
                for section in parsed_direct.get('sections', []):
                    section_questions = len(section.get('questions', []))
                    total_questions += section_questions
                    print(f"  Section {section.get('id', '?')}: {section_questions} questions")
                print(f"✅ Direct parsing found {total_questions} total questions")
                return total_questions
        except json.JSONDecodeError as e:
            print(f"❌ Sanitized JSON is still invalid: {e}")
            return 0

    except Exception as e:
        print(f"❌ Sanitization failed: {e}")
        return 0

if __name__ == "__main__":
    result = test_production_sample()