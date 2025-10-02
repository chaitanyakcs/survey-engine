"""
Comprehensive test suite for output parsing and validation
Focuses on parsing LLM responses and validating survey structures
"""
import pytest
import json
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List

from src.services.validation_service import ValidationService
from src.utils.survey_utils import extract_all_questions, get_questions_count, validate_survey_json


class TestOutputParsing:
    """Test parsing of LLM responses into survey structures"""

    @pytest.fixture
    def validation_service(self):
        """Create ValidationService instance for testing"""
        return ValidationService()

    @pytest.fixture
    def sample_llm_response(self):
        """Sample LLM response for testing"""
        return {
            "title": "Customer Satisfaction Survey",
            "description": "A comprehensive survey to measure customer satisfaction",
            "sections": [
                {
                    "id": 1,
                    "title": "Demographics",
                    "description": "Basic demographic information",
                    "questions": [
                        {
                            "id": "q1",
                            "text": "What is your age group?",
                            "type": "multiple_choice",
                            "options": ["18-24", "25-34", "35-44", "45+"],
                            "required": True,
                            "validation": "single_select:required"
                        },
                        {
                            "id": "q2",
                            "text": "What is your gender?",
                            "type": "multiple_choice",
                            "options": ["Male", "Female", "Other", "Prefer not to say"],
                            "required": False,
                            "validation": "single_select"
                        }
                    ]
                },
                {
                    "id": 2,
                    "title": "Satisfaction",
                    "description": "Customer satisfaction questions",
                    "questions": [
                        {
                            "id": "q3",
                            "text": "How satisfied are you with our service?",
                            "type": "scale",
                            "options": ["1", "2", "3", "4", "5"],
                            "required": True,
                            "validation": "scale:min=1;max=5"
                        },
                        {
                            "id": "q4",
                            "text": "What could we improve?",
                            "type": "text",
                            "required": False,
                            "validation": "open_text:max_chars=500"
                        }
                    ]
                }
            ],
            "metadata": {
                "estimated_time": 5,
                "methodology_tags": ["satisfaction", "demographics"],
                "target_responses": 100,
                "quality_score": 0.85
            }
        }

    def test_parse_valid_json_response(self, validation_service, sample_llm_response):
        """Test parsing of valid JSON response"""
        json_response = json.dumps(sample_llm_response)
        
        parsed, errors = validation_service.parse_survey_response(json_response)
        
        assert parsed is not None, f"Valid JSON should parse successfully: {errors}"
        assert len(errors) == 0, f"Valid JSON should have no errors: {errors}"
        assert parsed["title"] == sample_llm_response["title"]
        assert len(parsed["sections"]) == 2

    def test_parse_invalid_json_response(self, validation_service):
        """Test parsing of invalid JSON response"""
        invalid_json = "This is not valid JSON"
        
        parsed, errors = validation_service.parse_survey_response(invalid_json)
        
        assert parsed is None, "Invalid JSON should return None"
        assert len(errors) > 0, "Invalid JSON should have errors"
        assert "JSON" in errors[0], "Error should mention JSON parsing"

    def test_parse_malformed_json_response(self, validation_service):
        """Test parsing of malformed JSON response"""
        malformed_json = '{"title": "Test", "sections": [{"id": 1, "questions": [{"id": "q1"}]}]'
        
        parsed, errors = validation_service.parse_survey_response(malformed_json)
        
        # Should handle gracefully - either parse or have specific errors
        if parsed is not None:
            assert isinstance(parsed, dict), "Parsed response should be a dictionary"
        else:
            assert len(errors) > 0, "Should have errors for malformed JSON"

    def test_parse_response_with_missing_required_fields(self, validation_service):
        """Test parsing of response with missing required fields"""
        incomplete_response = {
            "title": "Test Survey"
            # Missing sections, description, etc.
        }
        
        json_response = json.dumps(incomplete_response)
        parsed, errors = validation_service.parse_survey_response(json_response)
        
        # Should parse but have validation errors
        assert parsed is not None, "Should parse even with missing fields"
        assert len(errors) > 0, "Should have validation errors for missing fields"

    def test_parse_response_with_invalid_question_types(self, validation_service):
        """Test parsing of response with invalid question types"""
        invalid_response = {
            "title": "Test Survey",
            "sections": [
                {
                    "id": 1,
                    "title": "Test Section",
                    "questions": [
                        {
                            "id": "q1",
                            "text": "Test question?",
                            "type": "invalid_type",
                            "required": True
                        }
                    ]
                }
            ]
        }
        
        json_response = json.dumps(invalid_response)
        parsed, errors = validation_service.parse_survey_response(json_response)
        
        assert parsed is not None, "Should parse even with invalid question types"
        assert len(errors) > 0, "Should have validation errors for invalid question types"

    def test_parse_response_with_new_question_types(self, validation_service):
        """Test parsing of response with new question types"""
        new_types_response = {
            "title": "Advanced Survey",
            "sections": [
                {
                    "id": 1,
                    "title": "Advanced Questions",
                    "questions": [
                        {
                            "id": "q1",
                            "text": "Rate these attributes: Quality, Price, Service",
                            "type": "matrix_likert",
                            "attributes": ["Quality", "Price", "Service"],
                            "options": ["Poor", "Fair", "Good", "Excellent"],
                            "required": True,
                            "validation": "matrix_likert:required"
                        },
                        {
                            "id": "q2",
                            "text": "Allocate 100 points among these features",
                            "type": "constant_sum",
                            "options": ["Feature A", "Feature B", "Feature C"],
                            "total_points": 100,
                            "required": True,
                            "validation": "constant_sum:total=100"
                        },
                        {
                            "id": "q3",
                            "text": "Rate these products on these attributes",
                            "type": "numeric_grid",
                            "rows": ["Product A", "Product B"],
                            "columns": ["Quality", "Price"],
                            "required": True,
                            "validation": "numeric_grid:required"
                        },
                        {
                            "id": "q4",
                            "text": "What is the maximum price you would pay?",
                            "type": "numeric_open",
                            "currency": "USD",
                            "required": True,
                            "validation": "currency:required; min=0"
                        }
                    ]
                }
            ]
        }
        
        json_response = json.dumps(new_types_response)
        parsed, errors = validation_service.parse_survey_response(json_response)
        
        assert parsed is not None, f"New question types should parse: {errors}"
        assert len(errors) == 0, f"New question types should be valid: {errors}"

    def test_parse_van_westendorp_response(self, validation_service):
        """Test parsing of Van Westendorp response"""
        van_westendorp_response = {
            "title": "Price Sensitivity Survey",
            "sections": [
                {
                    "id": 1,
                    "title": "Price Sensitivity",
                    "questions": [
                        {
                            "id": "q1",
                            "text": "At what price would you consider the product so expensive that you would not consider buying it?",
                            "type": "numeric_open",
                            "currency": "USD",
                            "required": True,
                            "validation": "currency:required; min=0",
                            "methodology": "van_westendorp"
                        },
                        {
                            "id": "q2",
                            "text": "At what price would you consider the product so inexpensive that you would question its quality?",
                            "type": "numeric_open",
                            "currency": "USD",
                            "required": True,
                            "validation": "currency:required; min=0",
                            "methodology": "van_westendorp"
                        },
                        {
                            "id": "q3",
                            "text": "At what price would you consider the product expensive, but you would still consider buying it?",
                            "type": "numeric_open",
                            "currency": "USD",
                            "required": True,
                            "validation": "currency:required; min=0",
                            "methodology": "van_westendorp"
                        },
                        {
                            "id": "q4",
                            "text": "At what price would you consider the product a bargain—a great buy for the money?",
                            "type": "numeric_open",
                            "currency": "USD",
                            "required": True,
                            "validation": "currency:required; min=0",
                            "methodology": "van_westendorp"
                        }
                    ]
                }
            ]
        }
        
        json_response = json.dumps(van_westendorp_response)
        parsed, errors = validation_service.parse_survey_response(json_response)
        
        assert parsed is not None, f"Van Westendorp should parse: {errors}"
        assert len(errors) == 0, f"Van Westendorp should be valid: {errors}"
        
        # Verify all 4 Van Westendorp questions are present
        questions = []
        for section in parsed["sections"]:
            questions.extend(section["questions"])
        
        van_westendorp_questions = [q for q in questions if q.get("methodology") == "van_westendorp"]
        assert len(van_westendorp_questions) == 4, "Should have exactly 4 Van Westendorp questions"

    def test_parse_response_with_validation_errors(self, validation_service):
        """Test parsing of response with validation errors"""
        error_response = {
            "title": "Test Survey",
            "sections": [
                {
                    "id": 1,
                    "title": "Test Section",
                    "questions": [
                        {
                            "id": "q1",
                            "text": "Test question?",
                            "type": "multiple_choice",
                            "options": [],  # Empty options for required question
                            "required": True
                        },
                        {
                            "id": "q2",
                            "text": "Test question 2?",
                            "type": "scale",
                            "options": ["1", "2", "3"],  # Missing validation
                            "required": True
                        }
                    ]
                }
            ]
        }
        
        json_response = json.dumps(error_response)
        parsed, errors = validation_service.parse_survey_response(json_response)
        
        assert parsed is not None, "Should parse even with validation errors"
        assert len(errors) > 0, "Should have validation errors"
        
        # Check that specific errors are identified
        error_text = " ".join(errors).lower()
        assert "options" in error_text or "validation" in error_text, "Should identify specific validation issues"


class TestSurveyValidation:
    """Test validation of survey structures"""

    @pytest.fixture
    def validation_service(self):
        """Create ValidationService instance for testing"""
        return ValidationService()

    @pytest.fixture
    def valid_survey(self):
        """Valid survey for testing"""
        return {
            "title": "Valid Survey",
            "description": "A valid survey for testing",
            "sections": [
                {
                    "id": 1,
                    "title": "Section 1",
                    "description": "First section",
                    "questions": [
                        {
                            "id": "q1",
                            "text": "What is your age?",
                            "type": "multiple_choice",
                            "options": ["18-24", "25-34", "35+"],
                            "required": True,
                            "validation": "single_select:required"
                        }
                    ]
                }
            ],
            "metadata": {
                "estimated_time": 5,
                "methodology_tags": ["demographics"],
                "target_responses": 100,
                "quality_score": 0.8
            }
        }

    def test_validate_complete_survey(self, validation_service, valid_survey):
        """Test validation of complete survey"""
        is_valid, errors = validation_service.validate_survey_structure(valid_survey)
        
        assert is_valid, f"Valid survey should pass validation: {errors}"
        assert len(errors) == 0, f"Valid survey should have no errors: {errors}"

    def test_validate_survey_missing_title(self, validation_service):
        """Test validation of survey missing title"""
        invalid_survey = {
            "description": "Survey without title",
            "sections": []
        }
        
        is_valid, errors = validation_service.validate_survey_structure(invalid_survey)
        
        assert not is_valid, "Survey without title should fail validation"
        assert len(errors) > 0, "Should have validation errors"
        assert any("title" in error.lower() for error in errors), "Should mention missing title"

    def test_validate_survey_missing_sections(self, validation_service):
        """Test validation of survey missing sections"""
        invalid_survey = {
            "title": "Survey without sections",
            "description": "This survey has no sections"
        }
        
        is_valid, errors = validation_service.validate_survey_structure(invalid_survey)
        
        assert not is_valid, "Survey without sections should fail validation"
        assert len(errors) > 0, "Should have validation errors"
        assert any("sections" in error.lower() for error in errors), "Should mention missing sections"

    def test_validate_survey_empty_sections(self, validation_service):
        """Test validation of survey with empty sections"""
        invalid_survey = {
            "title": "Survey with empty sections",
            "sections": [
                {
                    "id": 1,
                    "title": "Empty Section",
                    "questions": []
                }
            ]
        }
        
        is_valid, errors = validation_service.validate_survey_structure(invalid_survey)
        
        assert not is_valid, "Survey with empty sections should fail validation"
        assert len(errors) > 0, "Should have validation errors"
        assert any("questions" in error.lower() for error in errors), "Should mention empty questions"

    def test_validate_question_structure(self, validation_service):
        """Test validation of individual question structures"""
        valid_question = {
            "id": "q1",
            "text": "What is your age?",
            "type": "multiple_choice",
            "options": ["18-24", "25-34", "35+"],
            "required": True,
            "validation": "single_select:required"
        }
        
        is_valid, error = validation_service.validate_question_structure(valid_question)
        assert is_valid, f"Valid question should pass: {error}"
        assert error is None, "Valid question should have no error"

    def test_validate_question_missing_id(self, validation_service):
        """Test validation of question missing ID"""
        invalid_question = {
            "text": "What is your age?",
            "type": "multiple_choice",
            "options": ["18-24", "25-34", "35+"],
            "required": True
        }
        
        is_valid, error = validation_service.validate_question_structure(invalid_question)
        assert not is_valid, "Question without ID should fail validation"
        assert "id" in error.lower(), "Should mention missing ID"

    def test_validate_question_missing_text(self, validation_service):
        """Test validation of question missing text"""
        invalid_question = {
            "id": "q1",
            "type": "multiple_choice",
            "options": ["18-24", "25-34", "35+"],
            "required": True
        }
        
        is_valid, error = validation_service.validate_question_structure(invalid_question)
        assert not is_valid, "Question without text should fail validation"
        assert "text" in error.lower(), "Should mention missing text"

    def test_validate_question_missing_type(self, validation_service):
        """Test validation of question missing type"""
        invalid_question = {
            "id": "q1",
            "text": "What is your age?",
            "options": ["18-24", "25-34", "35+"],
            "required": True
        }
        
        is_valid, error = validation_service.validate_question_structure(invalid_question)
        assert not is_valid, "Question without type should fail validation"
        assert "type" in error.lower(), "Should mention missing type"

    def test_validate_question_invalid_type(self, validation_service):
        """Test validation of question with invalid type"""
        invalid_question = {
            "id": "q1",
            "text": "What is your age?",
            "type": "invalid_type",
            "options": ["18-24", "25-34", "35+"],
            "required": True
        }
        
        is_valid, error = validation_service.validate_question_structure(invalid_question)
        assert not is_valid, "Question with invalid type should fail validation"
        assert "type" in error.lower(), "Should mention invalid type"

    def test_validate_question_missing_options_for_multiple_choice(self, validation_service):
        """Test validation of multiple choice question missing options"""
        invalid_question = {
            "id": "q1",
            "text": "What is your age?",
            "type": "multiple_choice",
            "required": True
        }
        
        is_valid, error = validation_service.validate_question_structure(invalid_question)
        assert not is_valid, "Multiple choice without options should fail validation"
        assert "options" in error.lower(), "Should mention missing options"

    def test_validate_question_empty_options_for_multiple_choice(self, validation_service):
        """Test validation of multiple choice question with empty options"""
        invalid_question = {
            "id": "q1",
            "text": "What is your age?",
            "type": "multiple_choice",
            "options": [],
            "required": True
        }
        
        is_valid, error = validation_service.validate_question_structure(invalid_question)
        assert not is_valid, "Multiple choice with empty options should fail validation"
        assert "options" in error.lower(), "Should mention empty options"

    def test_validate_matrix_likert_question(self, validation_service):
        """Test validation of matrix_likert question"""
        valid_matrix = {
            "id": "q1",
            "text": "Rate these attributes: Quality, Price, Service",
            "type": "matrix_likert",
            "attributes": ["Quality", "Price", "Service"],
            "options": ["Poor", "Fair", "Good", "Excellent"],
            "required": True,
            "validation": "matrix_likert:required"
        }
        
        is_valid, error = validation_service.validate_question_structure(valid_matrix)
        assert is_valid, f"Valid matrix_likert should pass: {error}"

    def test_validate_matrix_likert_missing_attributes(self, validation_service):
        """Test validation of matrix_likert question missing attributes"""
        invalid_matrix = {
            "id": "q1",
            "text": "Rate these attributes",
            "type": "matrix_likert",
            "options": ["Poor", "Fair", "Good", "Excellent"],
            "required": True
        }
        
        is_valid, error = validation_service.validate_question_structure(invalid_matrix)
        assert not is_valid, "Matrix_likert without attributes should fail validation"
        assert "attributes" in error.lower(), "Should mention missing attributes"

    def test_validate_constant_sum_question(self, validation_service):
        """Test validation of constant_sum question"""
        valid_constant_sum = {
            "id": "q1",
            "text": "Allocate 100 points among these features",
            "type": "constant_sum",
            "options": ["Feature A", "Feature B", "Feature C"],
            "total_points": 100,
            "required": True,
            "validation": "constant_sum:total=100"
        }
        
        is_valid, error = validation_service.validate_question_structure(valid_constant_sum)
        assert is_valid, f"Valid constant_sum should pass: {error}"

    def test_validate_constant_sum_missing_total_points(self, validation_service):
        """Test validation of constant_sum question missing total_points"""
        invalid_constant_sum = {
            "id": "q1",
            "text": "Allocate points among these features",
            "type": "constant_sum",
            "options": ["Feature A", "Feature B", "Feature C"],
            "required": True
        }
        
        is_valid, error = validation_service.validate_question_structure(invalid_constant_sum)
        assert not is_valid, "Constant_sum without total_points should fail validation"
        assert "total_points" in error.lower(), "Should mention missing total_points"

    def test_validate_numeric_grid_question(self, validation_service):
        """Test validation of numeric_grid question"""
        valid_numeric_grid = {
            "id": "q1",
            "text": "Rate these products on these attributes",
            "type": "numeric_grid",
            "rows": ["Product A", "Product B"],
            "columns": ["Quality", "Price"],
            "required": True,
            "validation": "numeric_grid:required"
        }
        
        is_valid, error = validation_service.validate_question_structure(valid_numeric_grid)
        assert is_valid, f"Valid numeric_grid should pass: {error}"

    def test_validate_numeric_grid_missing_columns(self, validation_service):
        """Test validation of numeric_grid question missing columns"""
        invalid_numeric_grid = {
            "id": "q1",
            "text": "Rate these products",
            "type": "numeric_grid",
            "rows": ["Product A", "Product B"],
            "required": True
        }
        
        is_valid, error = validation_service.validate_question_structure(invalid_numeric_grid)
        assert not is_valid, "Numeric_grid without columns should fail validation"
        assert "columns" in error.lower(), "Should mention missing columns"

    def test_validate_numeric_open_question(self, validation_service):
        """Test validation of numeric_open question"""
        valid_numeric_open = {
            "id": "q1",
            "text": "What is the maximum price you would pay?",
            "type": "numeric_open",
            "currency": "USD",
            "required": True,
            "validation": "currency:required; min=0"
        }
        
        is_valid, error = validation_service.validate_question_structure(valid_numeric_open)
        assert is_valid, f"Valid numeric_open should pass: {error}"

    def test_validate_van_westendorp_questions(self, validation_service):
        """Test validation of Van Westendorp questions"""
        van_westendorp_questions = [
            {
                "id": "q1",
                "text": "At what price would you consider the product so expensive that you would not consider buying it?",
                "type": "numeric_open",
                "currency": "USD",
                "required": True,
                "validation": "currency:required; min=0",
                "methodology": "van_westendorp"
            },
            {
                "id": "q2",
                "text": "At what price would you consider the product so inexpensive that you would question its quality?",
                "type": "numeric_open",
                "currency": "USD",
                "required": True,
                "validation": "currency:required; min=0",
                "methodology": "van_westendorp"
            },
            {
                "id": "q3",
                "text": "At what price would you consider the product expensive, but you would still consider buying it?",
                "type": "numeric_open",
                "currency": "USD",
                "required": True,
                "validation": "currency:required; min=0",
                "methodology": "van_westendorp"
            },
            {
                "id": "q4",
                "text": "At what price would you consider the product a bargain—a great buy for the money?",
                "type": "numeric_open",
                "currency": "USD",
                "required": True,
                "validation": "currency:required; min=0",
                "methodology": "van_westendorp"
            }
        ]
        
        for question in van_westendorp_questions:
            is_valid, error = validation_service.validate_question_structure(question)
            assert is_valid, f"Van Westendorp question {question['id']} should pass: {error}"

    def test_validate_survey_metadata(self, validation_service):
        """Test validation of survey metadata"""
        valid_metadata = {
            "estimated_time": 10,
            "methodology_tags": ["satisfaction", "demographics"],
            "target_responses": 100,
            "quality_score": 0.85
        }
        
        is_valid, errors = validation_service.validate_survey_metadata(valid_metadata)
        assert is_valid, f"Valid metadata should pass: {errors}"
        assert len(errors) == 0, f"Valid metadata should have no errors: {errors}"

    def test_validate_survey_metadata_missing_fields(self, validation_service):
        """Test validation of survey metadata with missing fields"""
        incomplete_metadata = {
            "estimated_time": 10
            # Missing other fields
        }
        
        is_valid, errors = validation_service.validate_survey_metadata(incomplete_metadata)
        assert not is_valid, "Incomplete metadata should fail validation"
        assert len(errors) > 0, "Should have validation errors for missing fields"


class TestQuestionExtraction:
    """Test extraction of questions from survey structures"""

    def test_extract_all_questions_from_sections(self):
        """Test extraction of all questions from sections"""
        survey = {
            "sections": [
                {
                    "id": 1,
                    "title": "Section 1",
                    "questions": [
                        {"id": "q1", "text": "Question 1", "type": "multiple_choice"},
                        {"id": "q2", "text": "Question 2", "type": "text"}
                    ]
                },
                {
                    "id": 2,
                    "title": "Section 2",
                    "questions": [
                        {"id": "q3", "text": "Question 3", "type": "scale"}
                    ]
                }
            ]
        }
        
        questions = extract_all_questions(survey)
        assert len(questions) == 3, f"Expected 3 questions, got {len(questions)}"
        assert questions[0]["id"] == "q1"
        assert questions[1]["id"] == "q2"
        assert questions[2]["id"] == "q3"

    def test_extract_questions_from_legacy_format(self):
        """Test extraction of questions from legacy format"""
        survey = {
            "questions": [
                {"id": "q1", "text": "Question 1", "type": "multiple_choice"},
                {"id": "q2", "text": "Question 2", "type": "text"}
            ]
        }
        
        questions = extract_all_questions(survey)
        assert len(questions) == 2, f"Expected 2 questions, got {len(questions)}"
        assert questions[0]["id"] == "q1"
        assert questions[1]["id"] == "q2"

    def test_extract_questions_from_mixed_format(self):
        """Test extraction of questions from mixed format"""
        survey = {
            "sections": [
                {
                    "id": 1,
                    "title": "Section 1",
                    "questions": [
                        {"id": "q1", "text": "Question 1", "type": "multiple_choice"}
                    ]
                }
            ],
            "questions": [
                {"id": "q2", "text": "Question 2", "type": "text"}
            ]
        }
        
        questions = extract_all_questions(survey)
        assert len(questions) == 2, f"Expected 2 questions, got {len(questions)}"

    def test_extract_questions_from_empty_survey(self):
        """Test extraction of questions from empty survey"""
        survey = {}
        questions = extract_all_questions(survey)
        assert len(questions) == 0, f"Expected 0 questions, got {len(questions)}"

    def test_extract_questions_from_survey_with_empty_sections(self):
        """Test extraction of questions from survey with empty sections"""
        survey = {
            "sections": [
                {
                    "id": 1,
                    "title": "Empty Section",
                    "questions": []
                },
                {
                    "id": 2,
                    "title": "Section with Questions",
                    "questions": [
                        {"id": "q1", "text": "Question 1", "type": "multiple_choice"}
                    ]
                }
            ]
        }
        
        questions = extract_all_questions(survey)
        assert len(questions) == 1, f"Expected 1 question, got {len(questions)}"
        assert questions[0]["id"] == "q1"

    def test_get_questions_count(self):
        """Test getting questions count"""
        survey = {
            "sections": [
                {
                    "id": 1,
                    "title": "Section 1",
                    "questions": [
                        {"id": "q1", "text": "Question 1", "type": "multiple_choice"},
                        {"id": "q2", "text": "Question 2", "type": "text"}
                    ]
                },
                {
                    "id": 2,
                    "title": "Section 2",
                    "questions": [
                        {"id": "q3", "text": "Question 3", "type": "scale"}
                    ]
                }
            ]
        }
        
        count = get_questions_count(survey)
        assert count == 3, f"Expected 3 questions, got {count}"

    def test_get_questions_count_legacy_format(self):
        """Test getting questions count from legacy format"""
        survey = {
            "questions": [
                {"id": "q1", "text": "Question 1", "type": "multiple_choice"},
                {"id": "q2", "text": "Question 2", "type": "text"}
            ]
        }
        
        count = get_questions_count(survey)
        assert count == 2, f"Expected 2 questions, got {count}"

    def test_get_questions_count_empty_survey(self):
        """Test getting questions count from empty survey"""
        survey = {}
        count = get_questions_count(survey)
        assert count == 0, f"Expected 0 questions, got {count}"


class TestSurveyUtilsIntegration:
    """Integration tests for survey utilities"""

    def test_validate_survey_json_complete(self):
        """Test validation of complete survey JSON"""
        survey = {
            "title": "Test Survey",
            "description": "A test survey",
            "sections": [
                {
                    "id": 1,
                    "title": "Section 1",
                    "questions": [
                        {
                            "id": "q1",
                            "text": "What is your age?",
                            "type": "multiple_choice",
                            "options": ["18-24", "25-34", "35+"],
                            "required": True
                        }
                    ]
                }
            ],
            "metadata": {
                "estimated_time": 5,
                "methodology_tags": ["demographics"],
                "target_responses": 100,
                "quality_score": 0.8
            }
        }
        
        is_valid, errors = validate_survey_json(survey)
        assert is_valid, f"Complete survey should be valid: {errors}"

    def test_validate_survey_json_incomplete(self):
        """Test validation of incomplete survey JSON"""
        survey = {
            "title": "Test Survey"
            # Missing sections, description, etc.
        }
        
        is_valid, errors = validate_survey_json(survey)
        assert not is_valid, "Incomplete survey should be invalid"
        assert len(errors) > 0, "Should have validation errors"

    def test_validate_survey_json_with_new_question_types(self):
        """Test validation of survey JSON with new question types"""
        survey = {
            "title": "Advanced Survey",
            "sections": [
                {
                    "id": 1,
                    "title": "Advanced Questions",
                    "questions": [
                        {
                            "id": "q1",
                            "text": "Rate these attributes: Quality, Price, Service",
                            "type": "matrix_likert",
                            "attributes": ["Quality", "Price", "Service"],
                            "options": ["Poor", "Fair", "Good", "Excellent"],
                            "required": True
                        },
                        {
                            "id": "q2",
                            "text": "Allocate 100 points among these features",
                            "type": "constant_sum",
                            "options": ["Feature A", "Feature B", "Feature C"],
                            "total_points": 100,
                            "required": True
                        }
                    ]
                }
            ]
        }
        
        is_valid, errors = validate_survey_json(survey)
        assert is_valid, f"Survey with new question types should be valid: {errors}"


if __name__ == "__main__":
    pytest.main([__file__])


