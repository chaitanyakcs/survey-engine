#!/usr/bin/env python3
"""
TDD Test Suite for JSON Sanitization Methods
Testing GenerationService JSON parsing with real malformed LLM outputs
"""

import pytest
import json
from unittest.mock import MagicMock
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from src.services.generation_service import GenerationService


class TestJSONSanitization:
    """Test suite for JSON sanitization using TDD approach"""

    @pytest.fixture
    def generation_service(self):
        """Create GenerationService instance for testing"""
        mock_db = MagicMock()
        service = GenerationService(mock_db)
        return service

    def test_excessive_whitespace_malformed_json(self, generation_service):
        """
        Test the exact malformed JSON from user example
        This should fail with current implementation
        """
        # Your exact malformed JSON output
        malformed_json = '''{


 "
title
":
 "
Market
 Research
 Study
:
 Pricing
,
 Preferences
,
 and
 Feature
 Prior
ities
",


 "
description
":
 "
Com
prehensive
 study
 to
 understand
 willingness
 to
 pay
,
 feature
 importance
,
 brand
 perception
,
 and
 target
 segment
 characteristics
 for
 a
 new
 consumer
 product
 using
 Van
 West
endor
p
,
 Con
joint
 (
CBC
),
 and
 Max
Diff
 methodologies
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
S
cre
ener
 &
 Dem
ographics
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
q
1
",


 "
text
":
 "
Which
 country
 do
 you
 currently
 live
 in
?",


 "
type
":
 "
multiple
_choice
",


 "
options
":
 [


 "
United
 States
",


 "
Canada
",


 "
United
 Kingdom
",


 "
Australia
",


 "
European
 Union
 (
spec
ify
 country
 in
 next
 question
)",


 "
Other
"


 ],


 "
required
":
 true
,


 "
method
ology
":
 "
screen
ing
",


 "
validation
":
 "
single
_select
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
q
2
",


 "
text
":
 "
Please
 specify
 your
 country
 if
 you
 selected
 European
 Union
 (
optional
 for
 others
).
",


 "
type
":
 "
text
",


 "
options
":
 [],


 "
required
":
 false
,


 "
method
ology
":
 "
screen
ing
",


 "
validation
":
 "
open
_text
",


 "
order
":

2



 }


 ]


 }


 ]

}'''

        # Test current sanitization method (should fail)
        sanitized = generation_service._sanitize_raw_output(malformed_json)

        # Try to parse the result
        try:
            parsed = json.loads(sanitized)

            # Check expected structure
            assert "title" in parsed
            assert "sections" in parsed
            assert len(parsed["sections"]) > 0
            assert "questions" in parsed["sections"][0]

            # Count questions - should be 2 in this sample
            question_count = len(parsed["sections"][0]["questions"])
            assert question_count == 2, f"Expected 2 questions, got {question_count}"

            # Check string content preservation
            first_question = parsed["sections"][0]["questions"][0]
            assert "Which country do you currently live in?" in first_question["text"]
            assert "European Union (specify country in next question)" in first_question["options"]

            # Check title preservation
            assert "Market Research Study" in parsed["title"]
            assert "Pricing" in parsed["title"]

        except json.JSONDecodeError as e:
            pytest.fail(f"JSON parsing failed after sanitization: {e}")
        except AssertionError as e:
            pytest.fail(f"Content validation failed: {e}")

    def test_preserve_string_content_with_spaces(self, generation_service):
        """Test that spaces within quoted strings are preserved"""

        malformed_json = '''{
 "
title
":
 "
Market
 Research
 Study
 with
 Multiple
 Words
",
 "
text
":
 "
What
 is
 your
 age
 group
?"
}'''

        sanitized = generation_service._sanitize_raw_output(malformed_json)
        parsed = json.loads(sanitized)

        # These should preserve spaces between words
        assert parsed["title"] == "Market Research Study with Multiple Words"
        assert parsed["text"] == "What is your age group?"

    def test_fix_json_structure_whitespace(self, generation_service):
        """Test that JSON structural elements are fixed properly"""

        malformed_json = '''{
 "
key1
"
:
 "
value1
"
,
 "
key2
"
:

42
,
 "
array
"
:
 [
 "
item1
"
,
 "
item2
"
 ]
}'''

        sanitized = generation_service._sanitize_raw_output(malformed_json)
        parsed = json.loads(sanitized)

        assert parsed["key1"] == "value1"
        assert parsed["key2"] == 42
        assert parsed["array"] == ["item1", "item2"]

    def test_complex_nested_structures(self, generation_service):
        """Test complex nested JSON with multiple levels"""

        malformed_json = '''{
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
questions
":
 [
       {
         "
text
":
 "
How
 are
 you
 feeling
 today
?",
         "
options
":
 [
 "
Very
 good
",
 "
Good
",
 "
Not
 so
 good
"
 ]
       }
     ]
   }
 ]
}'''

        sanitized = generation_service._sanitize_raw_output(malformed_json)
        parsed = json.loads(sanitized)

        # Check nested structure
        assert len(parsed["sections"]) == 1
        assert len(parsed["sections"][0]["questions"]) == 1

        question = parsed["sections"][0]["questions"][0]
        assert question["text"] == "How are you feeling today?"
        assert "Very good" in question["options"]
        assert "Not so good" in question["options"]

    def test_edge_case_special_characters(self, generation_service):
        """Test JSON with special characters and punctuation"""

        malformed_json = '''{
 "
text
":
 "
What
's
 your
 income
 (
before
 taxes
)
?",
 "
options
":
 [
 "
$0
-$25,000
",
 "
$25,001
-$50,000
"
 ]
}'''

        sanitized = generation_service._sanitize_raw_output(malformed_json)
        parsed = json.loads(sanitized)

        # Check special characters preserved
        assert "What's your income (before taxes)?" == parsed["text"]
        assert "$0-$25,000" in parsed["options"]
        assert "$25,001-$50,000" in parsed["options"]

    def test_empty_and_null_values(self, generation_service):
        """Test handling of empty arrays and null values"""

        malformed_json = '''{
 "
text
":
 "
Optional
 question
",
 "
options
":
 [
 ],
 "
required
":
 false
}'''

        sanitized = generation_service._sanitize_raw_output(malformed_json)
        parsed = json.loads(sanitized)

        assert parsed["text"] == "Optional question"
        assert parsed["options"] == []
        assert parsed["required"] == False

    def test_number_and_boolean_preservation(self, generation_service):
        """Test that numbers and booleans are preserved correctly"""

        malformed_json = '''{
 "
id
":

42
,
 "
order
":

1
,
 "
required
":
 true
,
 "
score
":

3.14
}'''

        sanitized = generation_service._sanitize_raw_output(malformed_json)
        parsed = json.loads(sanitized)

        assert parsed["id"] == 42
        assert parsed["order"] == 1
        assert parsed["required"] == True
        assert parsed["score"] == 3.14

    def test_fix_malformed_json_whitespace_method(self, generation_service):
        """Test the existing _fix_malformed_json_whitespace method directly"""

        malformed_json = '''{"text" : "What
is
your
age?", "type": "multiple_choice"}'''

        fixed = generation_service._fix_malformed_json_whitespace(malformed_json)
        parsed = json.loads(fixed)

        # Should fix newlines within strings
        assert "What is your age?" in parsed["text"]

    def test_full_parsing_pipeline(self, generation_service):
        """Test the complete JSON extraction pipeline"""

        # Use a moderately malformed JSON
        malformed_json = '''{
 "
title
":
 "
Test
 Survey
",
 "
sections
":
 [
   {
     "
questions
":
 [
       {
         "
text
":
 "
Question
 one
?"
       },
       {
         "
text
":
 "
Question
 two
?"
       }
     ]
   }
 ]
}'''

        # Test the full extraction pipeline
        sanitized = generation_service._sanitize_raw_output(malformed_json)
        result = generation_service._extract_survey_json(sanitized)

        assert result is not None
        assert result["title"] == "Test Survey"
        assert len(result["sections"][0]["questions"]) == 2

    def test_performance_large_json(self, generation_service):
        """Test performance with large malformed JSON"""

        # Create a large malformed JSON with many questions
        questions = []
        for i in range(50):
            question = f'''{{
 "
id
":
 "
q{i}
",
 "
text
":
 "
Question
 number
 {i}
 with
 multiple
 words
?",
 "
type
":
 "
multiple
_choice
",
 "
options
":
 [
 "
Option
 A
",
 "
Option
 B
"
 ]
}}'''
            questions.append(question)

        large_json = f'''{{
 "
title
":
 "
Large
 Test
 Survey
",
 "
sections
":
 [
   {{
     "
questions
":
 [
{",".join(questions)}
     ]
   }}
 ]
}}'''

        import time
        start_time = time.time()

        sanitized = generation_service._sanitize_raw_output(large_json)
        result = generation_service._extract_survey_json(sanitized)

        end_time = time.time()
        processing_time = end_time - start_time

        # Should complete within reasonable time (less than 2 seconds)
        assert processing_time < 2.0, f"Processing took too long: {processing_time}s"
        assert result is not None
        assert len(result["sections"][0]["questions"]) == 50

    def test_corrupted_format_with_newlines_between_chars(self, generation_service):
        """
        Test the specific corrupted format we're seeing in production:
        Every character separated by newlines and spaces
        """
        # This is the exact format we're seeing in the real corrupted response
        corrupted_json = '''{

 
 "
title
":
 "
Me
vo
 Concept
 Testing
 &
 Price
 Elastic
ity
 (
Strateg
ic
 Targets
)",

 
 "
description
":
 "
Mixed
-method
s
 quantitative
 survey
 to
 evaluate
 Me
vo
 Start
 and
 Me
vo
 Str
atos
 concepts
 among
 Tech
ies
,
 Expression
ists
,
 and
 traditional
 Me
vo
 targets
,
 and
 to
 estimate
 price
 elasticity
 for
 Me
vo
 Str
atos
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
Sample
 Plan
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
q
1
",
         "
text
":
 "
Please
 confirm
 you
 currently
 reside
 in
 the
 United
 States
.",
         "
type
":
 "
single
_choice
",
         "
options
":
 [
           "
Yes
,
 I
 currently
 reside
 in
 the
 United
 States
",
           "
No
,
 I
 do
 not
 reside
 in
 the
 United
 States
"
         ]
       }
     ]
   }
 ]
}'''

        # Test that the sanitization can handle this format
        sanitized = generation_service._sanitize_raw_output(corrupted_json)
        
        # Should be able to parse the sanitized result
        parsed = json.loads(sanitized)
        
        # Check that the content is preserved correctly
        assert parsed["title"] == "Mevo Concept Testing & Price Elasticity (Strategic Targets)"
        assert "Mixed-methods quantitative survey" in parsed["description"]
        assert len(parsed["sections"]) == 1
        assert parsed["sections"][0]["id"] == 1
        assert parsed["sections"][0]["title"] == "Sample Plan"
        assert len(parsed["sections"][0]["questions"]) == 1
        
        question = parsed["sections"][0]["questions"][0]
        assert question["text"] == "Please confirm you currently reside in the United States."
        assert question["type"] == "single_choice"
        assert "Yes, I currently reside in the United States" in question["options"]


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])