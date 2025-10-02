"""
Comprehensive test suite for PromptBuilder service focusing on system prompt generation
and output parsing for all question types including the new ones.
"""
import pytest
import json
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List

from src.services.prompt_builder import PromptBuilder


class TestPromptBuilderSystemPrompt:
    """Test system prompt generation for all question types"""

    @pytest.fixture
    def prompt_builder(self):
        """Create PromptBuilder instance for testing"""
        return PromptBuilder()

    @pytest.fixture
    def sample_rfq_context(self):
        """Sample RFQ context for testing"""
        return {
            "rfq_text": "Create a comprehensive market research survey for a new software product",
            "survey_id": "test_survey_123",
            "workflow_id": "test_workflow_456",
            "methodology": "comprehensive",
            "target_segment": "business professionals"
        }

    @pytest.fixture
    def all_question_types_context(self):
        """Context that should generate all question types"""
        return {
            "rfq_text": "Create a survey with all question types: multiple choice, text, scale, ranking, matrix, constant sum, numeric grid, and numeric open",
            "methodology": "comprehensive",
            "target_segment": "general population"
        }

    def test_system_prompt_includes_all_question_types(self, prompt_builder, all_question_types_context):
        """Test that system prompt includes guidance for all question types"""
        prompt = prompt_builder.build_survey_generation_prompt(all_question_types_context)
        
        # Check for all question types in the prompt
        question_types = [
            "multiple_choice", "single_select", "multiple_select",
            "text", "open_text", "textarea",
            "scale", "likert", "rating",
            "ranking", "rank_order",
            "matrix_likert", "matrix_rating",
            "constant_sum", "point_allocation",
            "numeric_grid", "grid_rating",
            "numeric_open", "currency_input"
        ]
        
        for qtype in question_types:
            assert qtype in prompt.lower(), f"Question type '{qtype}' not found in system prompt"

    def test_system_prompt_includes_question_type_guidelines(self, prompt_builder, all_question_types_context):
        """Test that system prompt includes specific guidelines for each question type"""
        prompt = prompt_builder.build_survey_generation_prompt(all_question_types_context)
        
        # Check for specific guidelines
        guidelines = [
            "matrix_likert: comma-separated attributes as rows",
            "constant_sum: point allocation with validation",
            "numeric_grid: numeric inputs in grid format",
            "numeric_open: currency-aware numeric input",
            "van westendorp: four specific pricing questions"
        ]
        
        for guideline in guidelines:
            assert guideline.lower() in prompt.lower(), f"Guideline '{guideline}' not found in system prompt"

    def test_system_prompt_includes_json_schema(self, prompt_builder, sample_rfq_context):
        """Test that system prompt includes comprehensive JSON schema"""
        prompt = prompt_builder.build_survey_generation_prompt(sample_rfq_context)
        
        # Check for JSON structure requirements
        json_requirements = [
            "sections",
            "questions",
            "id",
            "text",
            "type",
            "options",
            "required",
            "validation",
            "methodology"
        ]
        
        for requirement in json_requirements:
            assert requirement in prompt, f"JSON requirement '{requirement}' not found in system prompt"

    def test_system_prompt_includes_validation_rules(self, prompt_builder, sample_rfq_context):
        """Test that system prompt includes validation rules for all question types"""
        prompt = prompt_builder.build_survey_generation_prompt(sample_rfq_context)
        
        # Check for validation patterns
        validation_patterns = [
            "single_select:required",
            "multi_select:min=1",
            "scale:min=1;max=10",
            "currency:required; min=0",
            "ranking:rank_all",
            "constant_sum:total=100"
        ]
        
        for pattern in validation_patterns:
            assert pattern in prompt, f"Validation pattern '{pattern}' not found in system prompt"

    def test_system_prompt_includes_methodology_guidance(self, prompt_builder, sample_rfq_context):
        """Test that system prompt includes methodology-specific guidance"""
        prompt = prompt_builder.build_survey_generation_prompt(sample_rfq_context)
        
        # Check for methodology guidance
        methodology_guidance = [
            "van westendorp",
            "conjoint analysis",
            "maxdiff",
            "nps",
            "satisfaction",
            "pricing research"
        ]
        
        for methodology in methodology_guidance:
            assert methodology.lower() in prompt.lower(), f"Methodology '{methodology}' not found in system prompt"

    def test_system_prompt_question_type_examples(self, prompt_builder, all_question_types_context):
        """Test that system prompt includes examples for each question type"""
        prompt = prompt_builder.build_survey_generation_prompt(all_question_types_context)
        
        # Check for example patterns
        example_patterns = [
            "example:",
            "for matrix_likert:",
            "for constant_sum:",
            "for numeric_grid:",
            "for numeric_open:",
            "json example:"
        ]
        
        for pattern in example_patterns:
            assert pattern.lower() in prompt.lower(), f"Example pattern '{pattern}' not found in system prompt"

    def test_system_prompt_handles_van_westendorp_specifically(self, prompt_builder):
        """Test that Van Westendorp questions get specific guidance"""
        context = {
            "rfq_text": "Create a Van Westendorp Price Sensitivity Meter survey",
            "methodology": "van_westendorp"
        }
        
        prompt = prompt_builder.build_survey_generation_prompt(context)
        
        # Check for Van Westendorp specific content
        van_westendorp_content = [
            "so expensive that you would not consider buying",
            "so inexpensive that you would question its quality",
            "expensive, but you would still consider buying",
            "bargain—a great buy for the money",
            "numeric_open",
            "currency validation"
        ]
        
        for content in van_westendorp_content:
            assert content.lower() in prompt.lower(), f"Van Westendorp content '{content}' not found in system prompt"

    def test_system_prompt_handles_matrix_questions(self, prompt_builder):
        """Test that matrix questions get specific guidance"""
        context = {
            "rfq_text": "Create a matrix rating survey for product attributes",
            "methodology": "matrix_rating"
        }
        
        prompt = prompt_builder.build_survey_generation_prompt(context)
        
        # Check for matrix specific content
        matrix_content = [
            "matrix_likert",
            "comma-separated attributes",
            "rows and columns",
            "radio buttons",
            "table format"
        ]
        
        for content in matrix_content:
            assert content.lower() in prompt.lower(), f"Matrix content '{content}' not found in system prompt"

    def test_system_prompt_handles_constant_sum_questions(self, prompt_builder):
        """Test that constant sum questions get specific guidance"""
        context = {
            "rfq_text": "Create a constant sum point allocation survey",
            "methodology": "constant_sum"
        }
        
        prompt = prompt_builder.build_survey_generation_prompt(context)
        
        # Check for constant sum specific content
        constant_sum_content = [
            "constant_sum",
            "point allocation",
            "total must equal",
            "real-time validation",
            "helper functions"
        ]
        
        for content in constant_sum_content:
            assert content.lower() in prompt.lower(), f"Constant sum content '{content}' not found in system prompt"

    def test_system_prompt_handles_numeric_questions(self, prompt_builder):
        """Test that numeric questions get specific guidance"""
        context = {
            "rfq_text": "Create numeric grid and numeric open questions",
            "methodology": "numeric_questions"
        }
        
        prompt = prompt_builder.build_survey_generation_prompt(context)
        
        # Check for numeric specific content
        numeric_content = [
            "numeric_grid",
            "numeric_open",
            "textbox for numbers",
            "currency input",
            "numeric validation"
        ]
        
        for content in numeric_content:
            assert content.lower() in prompt.lower(), f"Numeric content '{content}' not found in system prompt"


class TestPromptBuilderOutputParsing:
    """Test output parsing and validation for all question types"""

    @pytest.fixture
    def prompt_builder(self):
        """Create PromptBuilder instance for testing"""
        return PromptBuilder()

    @pytest.fixture
    def valid_survey_json(self):
        """Valid survey JSON with all question types"""
        return {
            "title": "Comprehensive Survey Test",
            "description": "Test survey with all question types",
            "sections": [
                {
                    "id": 1,
                    "title": "Basic Questions",
                    "description": "Basic question types",
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
                            "text": "Please describe your experience",
                            "type": "text",
                            "required": False,
                            "validation": "open_text:max_chars=500"
                        },
                        {
                            "id": "q3",
                            "text": "Rate your satisfaction",
                            "type": "scale",
                            "options": ["1", "2", "3", "4", "5"],
                            "required": True,
                            "validation": "scale:min=1;max=5"
                        }
                    ]
                },
                {
                    "id": 2,
                    "title": "Advanced Questions",
                    "description": "Advanced question types",
                    "questions": [
                        {
                            "id": "q4",
                            "text": "Rate these attributes: Quality, Price, Service",
                            "type": "matrix_likert",
                            "attributes": ["Quality", "Price", "Service"],
                            "options": ["Poor", "Fair", "Good", "Excellent"],
                            "required": True,
                            "validation": "matrix_likert:required"
                        },
                        {
                            "id": "q5",
                            "text": "Allocate 100 points among these features",
                            "type": "constant_sum",
                            "options": ["Feature A", "Feature B", "Feature C"],
                            "total_points": 100,
                            "required": True,
                            "validation": "constant_sum:total=100"
                        },
                        {
                            "id": "q6",
                            "text": "Rate these products on these attributes",
                            "type": "numeric_grid",
                            "rows": ["Product A", "Product B"],
                            "columns": ["Quality", "Price"],
                            "required": True,
                            "validation": "numeric_grid:required"
                        },
                        {
                            "id": "q7",
                            "text": "What is the maximum price you would pay?",
                            "type": "numeric_open",
                            "currency": "USD",
                            "required": True,
                            "validation": "currency:required; min=0"
                        }
                    ]
                }
            ],
            "metadata": {
                "estimated_time": 10,
                "methodology_tags": ["comprehensive", "all_types"],
                "target_responses": 100,
                "quality_score": 0.9
            }
        }

    def test_validate_survey_structure(self, prompt_builder, valid_survey_json):
        """Test validation of survey structure"""
        is_valid, errors = prompt_builder.validate_survey_structure(valid_survey_json)
        
        assert is_valid, f"Survey validation failed: {errors}"
        assert len(errors) == 0, f"Unexpected validation errors: {errors}"

    def test_validate_question_types(self, prompt_builder, valid_survey_json):
        """Test validation of all question types"""
        questions = []
        for section in valid_survey_json["sections"]:
            questions.extend(section["questions"])
        
        for question in questions:
            is_valid, error = prompt_builder.validate_question_structure(question)
            assert is_valid, f"Question {question['id']} validation failed: {error}"

    def test_validate_matrix_likert_questions(self, prompt_builder):
        """Test validation of matrix_likert questions"""
        valid_matrix = {
            "id": "q1",
            "text": "Rate these attributes: Quality, Price, Service",
            "type": "matrix_likert",
            "attributes": ["Quality", "Price", "Service"],
            "options": ["Poor", "Fair", "Good", "Excellent"],
            "required": True,
            "validation": "matrix_likert:required"
        }
        
        is_valid, error = prompt_builder.validate_question_structure(valid_matrix)
        assert is_valid, f"Valid matrix_likert failed: {error}"
        
        # Test invalid matrix_likert
        invalid_matrix = {
            "id": "q2",
            "text": "Rate these attributes",
            "type": "matrix_likert",
            "options": ["Poor", "Fair", "Good", "Excellent"],
            "required": True
        }
        
        is_valid, error = prompt_builder.validate_question_structure(invalid_matrix)
        assert not is_valid, "Invalid matrix_likert should fail validation"
        assert "attributes" in error.lower(), "Should mention missing attributes"

    def test_validate_constant_sum_questions(self, prompt_builder):
        """Test validation of constant_sum questions"""
        valid_constant_sum = {
            "id": "q1",
            "text": "Allocate 100 points among these features",
            "type": "constant_sum",
            "options": ["Feature A", "Feature B", "Feature C"],
            "total_points": 100,
            "required": True,
            "validation": "constant_sum:total=100"
        }
        
        is_valid, error = prompt_builder.validate_question_structure(valid_constant_sum)
        assert is_valid, f"Valid constant_sum failed: {error}"
        
        # Test invalid constant_sum
        invalid_constant_sum = {
            "id": "q2",
            "text": "Allocate points",
            "type": "constant_sum",
            "options": ["Feature A", "Feature B"],
            "required": True
        }
        
        is_valid, error = prompt_builder.validate_question_structure(invalid_constant_sum)
        assert not is_valid, "Invalid constant_sum should fail validation"
        assert "total_points" in error.lower(), "Should mention missing total_points"

    def test_validate_numeric_grid_questions(self, prompt_builder):
        """Test validation of numeric_grid questions"""
        valid_numeric_grid = {
            "id": "q1",
            "text": "Rate these products on these attributes",
            "type": "numeric_grid",
            "rows": ["Product A", "Product B"],
            "columns": ["Quality", "Price"],
            "required": True,
            "validation": "numeric_grid:required"
        }
        
        is_valid, error = prompt_builder.validate_question_structure(valid_numeric_grid)
        assert is_valid, f"Valid numeric_grid failed: {error}"
        
        # Test invalid numeric_grid
        invalid_numeric_grid = {
            "id": "q2",
            "text": "Rate these products",
            "type": "numeric_grid",
            "rows": ["Product A", "Product B"],
            "required": True
        }
        
        is_valid, error = prompt_builder.validate_question_structure(invalid_numeric_grid)
        assert not is_valid, "Invalid numeric_grid should fail validation"
        assert "columns" in error.lower(), "Should mention missing columns"

    def test_validate_numeric_open_questions(self, prompt_builder):
        """Test validation of numeric_open questions"""
        valid_numeric_open = {
            "id": "q1",
            "text": "What is the maximum price you would pay?",
            "type": "numeric_open",
            "currency": "USD",
            "required": True,
            "validation": "currency:required; min=0"
        }
        
        is_valid, error = prompt_builder.validate_question_structure(valid_numeric_open)
        assert is_valid, f"Valid numeric_open failed: {error}"

    def test_validate_van_westendorp_questions(self, prompt_builder):
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
            is_valid, error = prompt_builder.validate_question_structure(question)
            assert is_valid, f"Van Westendorp question {question['id']} failed: {error}"

    def test_parse_llm_response_valid_json(self, prompt_builder):
        """Test parsing of valid LLM response"""
        valid_response = {
            "title": "Test Survey",
            "description": "A test survey",
            "sections": [
                {
                    "id": 1,
                    "title": "Test Section",
                    "questions": [
                        {
                            "id": "q1",
                            "text": "Test question?",
                            "type": "multiple_choice",
                            "options": ["Option 1", "Option 2"],
                            "required": True
                        }
                    ]
                }
            ]
        }
        
        parsed, errors = prompt_builder.parse_llm_response(json.dumps(valid_response))
        assert parsed is not None, f"Valid JSON parsing failed: {errors}"
        assert len(errors) == 0, f"Unexpected parsing errors: {errors}"

    def test_parse_llm_response_invalid_json(self, prompt_builder):
        """Test parsing of invalid LLM response"""
        invalid_response = "This is not valid JSON"
        
        parsed, errors = prompt_builder.parse_llm_response(invalid_response)
        assert parsed is None, "Invalid JSON should return None"
        assert len(errors) > 0, "Should have parsing errors"

    def test_parse_llm_response_malformed_json(self, prompt_builder):
        """Test parsing of malformed JSON"""
        malformed_response = '{"title": "Test", "sections": [{"id": 1, "questions": [{"id": "q1"}]}]'
        
        parsed, errors = prompt_builder.parse_llm_response(malformed_response)
        # Should handle gracefully
        assert parsed is not None or len(errors) > 0, "Should either parse or have errors"

    def test_extract_questions_from_sections(self, prompt_builder, valid_survey_json):
        """Test extraction of questions from sections"""
        questions = prompt_builder.extract_questions_from_sections(valid_survey_json["sections"])
        
        assert len(questions) == 7, f"Expected 7 questions, got {len(questions)}"
        
        # Check that all question types are present
        question_types = [q["type"] for q in questions]
        expected_types = ["multiple_choice", "text", "scale", "matrix_likert", "constant_sum", "numeric_grid", "numeric_open"]
        
        for expected_type in expected_types:
            assert expected_type in question_types, f"Question type {expected_type} not found in extracted questions"

    def test_validate_survey_metadata(self, prompt_builder, valid_survey_json):
        """Test validation of survey metadata"""
        is_valid, errors = prompt_builder.validate_survey_metadata(valid_survey_json.get("metadata", {}))
        
        assert is_valid, f"Metadata validation failed: {errors}"
        assert len(errors) == 0, f"Unexpected metadata errors: {errors}"

    def test_validate_survey_metadata_missing_fields(self, prompt_builder):
        """Test validation of survey metadata with missing fields"""
        incomplete_metadata = {
            "estimated_time": 10
            # Missing other required fields
        }
        
        is_valid, errors = prompt_builder.validate_survey_metadata(incomplete_metadata)
        assert not is_valid, "Incomplete metadata should fail validation"
        assert len(errors) > 0, "Should have validation errors for missing fields"


class TestPromptBuilderIntegration:
    """Integration tests for PromptBuilder with realistic scenarios"""

    @pytest.fixture
    def prompt_builder(self):
        """Create PromptBuilder instance for testing"""
        return PromptBuilder()

    def test_end_to_end_prompt_generation_and_parsing(self, prompt_builder):
        """Test complete flow from prompt generation to response parsing"""
        # Generate system prompt
        context = {
            "rfq_text": "Create a comprehensive survey with all question types",
            "methodology": "comprehensive"
        }
        
        system_prompt = prompt_builder.build_system_prompt(context)
        assert len(system_prompt) > 1000, "System prompt should be comprehensive"
        
        # Simulate LLM response
        mock_response = {
            "title": "Comprehensive Survey",
            "description": "A survey with all question types",
            "sections": [
                {
                    "id": 1,
                    "title": "Basic Questions",
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
                "methodology_tags": ["comprehensive"],
                "target_responses": 100,
                "quality_score": 0.8
            }
        }
        
        # Parse response
        parsed, errors = prompt_builder.parse_llm_response(json.dumps(mock_response))
        assert parsed is not None, f"Response parsing failed: {errors}"
        assert len(errors) == 0, f"Unexpected parsing errors: {errors}"
        
        # Validate structure
        is_valid, validation_errors = prompt_builder.validate_survey_structure(parsed)
        assert is_valid, f"Survey validation failed: {validation_errors}"

    def test_question_type_specific_prompt_generation(self, prompt_builder):
        """Test prompt generation for specific question types"""
        question_type_tests = [
            {
                "type": "matrix_likert",
                "context": {"rfq_text": "Create a matrix rating survey", "methodology": "matrix_rating"},
                "expected_content": ["matrix_likert", "attributes", "rows", "columns"]
            },
            {
                "type": "constant_sum",
                "context": {"rfq_text": "Create a point allocation survey", "methodology": "constant_sum"},
                "expected_content": ["constant_sum", "point allocation", "total points"]
            },
            {
                "type": "numeric_grid",
                "context": {"rfq_text": "Create a numeric grid survey", "methodology": "numeric_grid"},
                "expected_content": ["numeric_grid", "rows", "columns", "numeric input"]
            },
            {
                "type": "numeric_open",
                "context": {"rfq_text": "Create a Van Westendorp survey", "methodology": "van_westendorp"},
                "expected_content": ["numeric_open", "currency", "van westendorp", "pricing"]
            }
        ]
        
        for test_case in question_type_tests:
            prompt = prompt_builder.build_survey_generation_prompt(test_case["context"])
            
            for expected_content in test_case["expected_content"]:
                assert expected_content.lower() in prompt.lower(), \
                    f"Expected content '{expected_content}' not found in prompt for {test_case['type']}"

    def test_error_handling_and_recovery(self, prompt_builder):
        """Test error handling and recovery mechanisms"""
        # Test with malformed input
        malformed_context = None
        prompt = prompt_builder.build_survey_generation_prompt(malformed_context)
        assert isinstance(prompt, str), "Should handle malformed input gracefully"
        
        # Test with empty context
        empty_context = {}
        prompt = prompt_builder.build_survey_generation_prompt(empty_context)
        assert isinstance(prompt, str), "Should handle empty context gracefully"
        
        # Test with invalid JSON parsing
        invalid_json = "invalid json {"
        parsed, errors = prompt_builder.parse_llm_response(invalid_json)
        assert parsed is None, "Should return None for invalid JSON"
        assert len(errors) > 0, "Should have errors for invalid JSON"

    def test_performance_with_large_inputs(self, prompt_builder):
        """Test performance with large inputs"""
        import time
        
        # Create large context
        large_context = {
            "rfq_text": "Create a comprehensive survey " * 100,  # Very long RFQ
            "methodology": "comprehensive",
            "target_segment": "general population",
            "additional_requirements": ["requirement"] * 50
        }
        
        start_time = time.time()
        prompt = prompt_builder.build_survey_generation_prompt(large_context)
        generation_time = time.time() - start_time
        
        assert isinstance(prompt, str), "Should generate prompt successfully"
        assert len(prompt) > 1000, "Should generate comprehensive prompt"
        assert generation_time < 2.0, f"Prompt generation took too long: {generation_time}s"

    def test_consistency_across_multiple_calls(self, prompt_builder):
        """Test that multiple calls produce consistent results"""
        context = {
            "rfq_text": "Create a survey",
            "methodology": "comprehensive"
        }
        
        # Generate multiple prompts
        prompts = []
        for i in range(5):
            prompt = prompt_builder.build_survey_generation_prompt(context)
            prompts.append(prompt)
        
        # All prompts should be similar (same structure, different details)
        assert all(isinstance(p, str) for p in prompts), "All prompts should be strings"
        assert all(len(p) > 500 for p in prompts), "All prompts should be substantial"
        
        # Check that key sections are present in all prompts
        key_sections = ["ROLE", "JSON STRUCTURE", "QUESTION TYPES"]
        for prompt in prompts:
            for section in key_sections:
                assert section in prompt, f"Key section '{section}' missing from prompt"


if __name__ == "__main__":
    pytest.main([__file__])
