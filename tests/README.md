# Survey Engine Test Suite

## Overview

This directory contains comprehensive tests for the survey engine, focusing on system prompt generation and output parsing. The test suite has been cleaned up and hardened to ensure robust functionality.

## Test Structure

### Core Test Files

1. **`test_prompt_builder_comprehensive.py`** - Comprehensive tests for system prompt generation
   - Tests all question types including new ones (matrix_likert, constant_sum, numeric_grid, numeric_open)
   - Validates prompt structure and content
   - Tests methodology-specific guidance
   - Performance and consistency tests

2. **`test_output_parsing_comprehensive.py`** - Robust tests for output parsing and validation
   - Tests parsing of LLM responses
   - Validates survey structures
   - Tests all question types
   - Error handling and recovery tests

3. **`test_question_type_components.py`** - Tests for new question type components
   - MatrixLikert component tests
   - ConstantSum component tests
   - NumericGrid component tests
   - NumericOpen component tests
   - Integration tests for all question types

4. **`test_prompt_service.py`** - Existing prompt service tests (maintained)
5. **`test_survey_parsing.py`** - Existing survey parsing tests (maintained)

### Test Runner

- **`run_comprehensive_tests.py`** - Comprehensive test runner with multiple modes:
  - `all` - Run all tests
  - `critical` - Run only critical tests
  - `performance` - Run performance tests

### Configuration

- **`pytest.ini`** - Pytest configuration with markers and settings
- **`conftest.py`** - Shared test fixtures and configuration

## Test Categories

### Critical Tests (Must Pass)
- System prompt generation for all question types
- Output parsing and validation
- Question type component functionality
- Van Westendorp question handling
- Matrix question parsing

### Performance Tests
- Large prompt generation performance
- Response parsing performance
- Memory usage during testing

### Integration Tests
- End-to-end prompt generation and parsing
- Question type detection and validation
- Error handling and recovery

## Running Tests

### Run All Tests
```bash
python3 tests/run_comprehensive_tests.py all
```

### Run Critical Tests Only
```bash
python3 tests/run_comprehensive_tests.py critical
```

### Run Performance Tests
```bash
python3 tests/run_comprehensive_tests.py performance
```

### Run Specific Test File
```bash
python3 -m pytest tests/test_prompt_builder_comprehensive.py -v
```

### Run Specific Test Class
```bash
python3 -m pytest tests/test_question_type_components.py::TestMatrixLikertComponent -v
```

## Test Coverage

### System Prompt Generation
- ✅ All question types included in prompts
- ✅ Methodology-specific guidance
- ✅ JSON schema requirements
- ✅ Validation rules for all types
- ✅ Van Westendorp specific content
- ✅ Matrix question guidance
- ✅ Constant sum guidance
- ✅ Numeric question guidance

### Output Parsing
- ✅ Valid JSON parsing
- ✅ Invalid JSON handling
- ✅ Malformed data recovery
- ✅ Question type validation
- ✅ Survey structure validation
- ✅ Metadata validation

### Question Type Components
- ✅ MatrixLikert parsing and validation
- ✅ ConstantSum point allocation
- ✅ NumericGrid structure validation
- ✅ NumericOpen currency handling
- ✅ Van Westendorp question detection
- ✅ Error handling for malformed data

## Cleanup Completed

### Removed Outdated Files
- `test_cleaned_prompt_service.py`
- `test_comprehensive_prompt_system.py`
- `test_new_prompt_system.py`
- `test_actual_control_chars.py`
- `test_actual_production.py`
- `test_full_extraction.py`
- `test_large_response.py`
- `test_generation_rules.py`
- `test_evaluation_no_retry.py`
- `test_rfq_generation.py`
- All `debug_*.py` files
- `simple_prompt_test.py`
- `simple_test_rules.py`

### Maintained Important Files
- `test_prompt_service.py` - Core prompt service tests
- `test_survey_parsing.py` - Survey parsing tests
- `test_generation_service.py` - Generation service tests
- `test_validation_service.py` - Validation service tests

## Test Quality Improvements

1. **Comprehensive Coverage** - Tests cover all new question types and functionality
2. **Error Handling** - Robust error handling and recovery testing
3. **Performance** - Performance testing for large inputs
4. **Integration** - End-to-end testing scenarios
5. **Maintainability** - Clean, well-organized test structure
6. **Documentation** - Clear test descriptions and documentation

## Future Enhancements

1. **Coverage Reporting** - Add code coverage reporting
2. **Parallel Testing** - Implement parallel test execution
3. **CI/CD Integration** - Automated test running in CI/CD
4. **Load Testing** - Add load testing for high-volume scenarios
5. **Mock Services** - Enhanced mocking for external dependencies

## Dependencies

- pytest >= 6.0
- pytest-mock
- pytest-cov (optional)
- pytest-xdist (optional, for parallel execution)

## Notes

- All tests are designed to run independently
- Tests use mocks for external dependencies
- Performance tests have time limits to prevent hanging
- Error messages are descriptive for easy debugging
- Tests are organized by functionality for easy maintenance


