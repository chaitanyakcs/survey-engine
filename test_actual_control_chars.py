#!/usr/bin/env python3
"""
Test with ACTUAL control characters and newlines that match production logs
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.generation_service import GenerationService
from unittest.mock import MagicMock
import json

def test_actual_control_characters():
    """Test with the actual problematic format including real newlines"""

    mock_db = MagicMock()
    service = GenerationService(mock_db)

    # This matches the EXACT format from user's production logs with embedded newlines
    actual_malformed = """{


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
.",


 "
sections
":
 [


 {


 "
id
":

1
,


 "
title
":
 "
Screener
 &
 Demographics
",


 "
description
":
 "
Initial
 screening
 questions
 and
 demographic
 information
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
?",


 "
type
":
 "
multiple_choice
",


 "
options
":
 ["
Under

18
",
 "
18
-
24
",
 "
25
-
34
",
 "
35
-
44
",
 "
45
-
54
",
 "
55
-
64
",
 "
65
 or
 older
"],


 "
required
":
 true
,


 "
methodology
":
 "
screening
",


 "
validation
":
 "
single_select
;
 terminate_if
:
Under

18
",


 "
order
":

1



 },


 {


 "
id
":
 "
q2
",


 "
text
":
 "
Where
 do
 you
 currently
 reside
?",


 "
type
":
 "
multiple_choice
",


 "
options
":
 ["
United
 States
",
 "
Canada
",
 "
United
 Kingdom
"],


 "
required
":
 true
,


 "
methodology
":
 "
screening
",


 "
validation
":
 "
single_select
",


 "
order
":

2



 }


 ]


 }


 ],


 "
metadata
":
 {


 "
estimated_time
":

14
,


 "
methodology_tags
":
 ["
van_westendorp
",
 "
pricing
"],


 "
target_responses
":

600
,


 "
quality_score
":

0
.
93
,


 "
sections_count
":

1



 }

}"""

    print("=== ACTUAL CONTROL CHARACTERS TEST ===")
    print(f"Input length: {len(actual_malformed)} characters")
    print(f"Has actual newlines: {repr(actual_malformed[:100])}")

    try:
        # Test the complete extraction pipeline
        result = service._extract_survey_json(actual_malformed)

        if result:
            print(f"✅ Full extraction successful!")
            if 'sections' in result:
                total_questions = sum(len(section.get('questions', [])) for section in result.get('sections', []))
                print(f"✅ Extracted {total_questions} questions from {len(result['sections'])} sections")
                return total_questions
            else:
                print(f"⚠️ No sections found in result: {list(result.keys())}")
                return 0
        else:
            print(f"❌ Full extraction returned None")
            return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == "__main__":
    questions_found = test_actual_control_characters()
    if questions_found > 0:
        print(f"\n🎉 SUCCESS: Extracted {questions_found} questions with control character fix!")
    else:
        print(f"\n❌ FAILURE: No questions extracted")