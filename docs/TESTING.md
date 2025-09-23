# 🧪 Survey Engine Testing Guide

This document provides comprehensive guidance for testing the Survey Engine project using our standardized testing framework.

## 📋 Test Structure

```
tests/
├── base.py                    # Base test classes and utilities
├── conftest.py               # Pytest configuration and fixtures
├── api/                      # API endpoint tests
│   ├── test_golden_examples.py
│   ├── test_survey_generation.py
│   ├── test_field_extraction.py
│   └── test_utils.py
├── unit/                     # Unit tests (to be created)
├── integration/              # Integration tests (to be created)
└── fixtures/                 # Test data fixtures (to be created)
```

## 🚀 Quick Start

### Running Tests

```bash
# Run all tests
python3 tests/run_tests.py

# Run specific test types
python3 tests/run_tests.py --type api
python3 tests/run_tests.py --type unit
python3 tests/run_tests.py --type integration

# Run with coverage
python3 tests/run_tests.py --coverage

# Run with verbose output
python3 tests/run_tests.py --verbose

# Run specific test markers
python3 tests/run_tests.py --markers "api and not slow"

# Run in parallel
python3 tests/run_tests.py --parallel 4
```

### Using pytest directly

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/api/test_golden_examples.py

# Run specific test method
pytest tests/api/test_golden_examples.py::TestGoldenExamplesAPI::test_get_golden_examples

# Run with coverage
pytest --cov=src --cov-report=html

# Run with specific markers
pytest -m "api and not slow"
```

## 🏗️ Test Framework Components

### Base Test Classes

#### `BaseAPITest`
- **Purpose**: Base class for API endpoint tests
- **Features**:
  - Automatic mock setup for external dependencies
  - Common assertion utilities
  - Test data factories
  - Response structure validation

#### `BaseServiceTest`
- **Purpose**: Base class for service layer tests
- **Features**:
  - Service-specific mock setup
  - Service response validation
  - Dependency injection testing

#### `BaseComponentTest`
- **Purpose**: Base class for React component tests
- **Features**:
  - Component prop mocking
  - Rendering assertions
  - User interaction testing

### Test Data Factory

The `TestDataFactory` class provides standardized methods for creating test data:

```python
# Create different question types
question = TestDataFactory.create_question("single_choice")
question = TestDataFactory.create_question("van_westendorp")

# Create methodology tags
tags = TestDataFactory.create_methodology_tags("van_westendorp")

# Create industry categories
industry = TestDataFactory.create_industry_category("tech")

# Create research goals
goal = TestDataFactory.create_research_goal("pricing")
```

## 📊 Test Categories

### API Tests (`tests/api/`)

Test all REST API endpoints with comprehensive coverage:

- **Golden Examples API**: CRUD operations, document parsing
- **Survey Generation API**: RFQ submission, status tracking, result retrieval
- **Field Extraction API**: Intelligent field extraction, validation
- **Utils API**: Text extraction, health checks, documentation

**Key Features**:
- ✅ Success and error scenarios
- ✅ Input validation testing
- ✅ Authentication and authorization
- ✅ Response structure validation
- ✅ Error handling and edge cases

### Unit Tests (`tests/unit/`)

Test individual components in isolation:

- **Service Layer**: Business logic, data processing
- **Utility Functions**: Helper functions, validators
- **Data Models**: Pydantic models, database models
- **Helper Classes**: Configuration, error handling

### Integration Tests (`tests/integration/`)

Test component interactions:

- **Database Integration**: Real database operations
- **External API Integration**: Third-party service calls
- **End-to-End Workflows**: Complete user journeys
- **Performance Testing**: Load and stress testing

## 🎯 Test Standards

### Naming Conventions

- **Test Files**: `test_*.py`
- **Test Classes**: `Test*`
- **Test Methods**: `test_*`
- **Fixtures**: `*_fixture` or `mock_*`

### Test Method Structure

```python
def test_feature_behavior_condition(self):
    """Test description explaining what is being tested"""
    # Arrange - Setup test data and mocks
    client = self.create_test_client()
    mock_data = self.create_mock_data()
    
    # Act - Execute the functionality
    response = client.post("/api/endpoint", json=mock_data)
    
    # Assert - Verify the results
    self.assert_response_structure(response, 200, ["field1", "field2"])
    assert response.json()["field1"] == "expected_value"
```

### Assertion Patterns

```python
# Response structure validation
self.assert_response_structure(response, 200, ["required_field"])

# Service response validation
self.assert_service_response(response, dict, ["field1", "field2"])

# Component rendering validation
self.assert_component_renders(component, ["Expected Text", element])
```

## 🔧 Configuration

### Pytest Configuration (`pytest.ini`)

- **Test Discovery**: Automatic test file discovery
- **Markers**: Categorize tests by type and speed
- **Warnings**: Filter out common warnings
- **Async Support**: Automatic async test handling

### Environment Setup

Tests automatically mock external dependencies:
- Database connections
- Redis cache
- External APIs (Replicate, OpenAI)
- File system operations

## 📈 Coverage Goals

| Component | Target Coverage | Current Status |
|-----------|----------------|----------------|
| API Endpoints | 90%+ | 🟡 In Progress |
| Service Layer | 85%+ | 🟡 In Progress |
| Utility Functions | 95%+ | 🟡 In Progress |
| Frontend Components | 80%+ | 🔴 Not Started |
| Integration Tests | 70%+ | 🔴 Not Started |

## 🚨 Common Issues and Solutions

### Import Errors
```bash
# If you get import errors, ensure you're in the project root
cd /path/to/survey-engine
python3 -m pytest tests/
```

### Mock Issues
```python
# Ensure mocks are properly patched
with patch('src.services.service_name.ServiceClass.method') as mock_method:
    mock_method.return_value = expected_value
    # Your test code here
```

### Database Issues
```python
# Use the base test class which handles database mocking
class TestMyAPI(BaseAPITest):
    def test_my_endpoint(self):
        # Database is automatically mocked
        pass
```

## 🔄 Continuous Integration

### GitHub Actions (Recommended)

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: pip install -r requirements-docker.txt
      - name: Run tests
        run: python3 tests/run_tests.py --coverage
```

## 📚 Best Practices

1. **Test Isolation**: Each test should be independent
2. **Descriptive Names**: Test names should explain what is being tested
3. **Arrange-Act-Assert**: Follow the AAA pattern
4. **Mock External Dependencies**: Don't rely on external services
5. **Test Edge Cases**: Include error scenarios and boundary conditions
6. **Keep Tests Fast**: Unit tests should run quickly
7. **Maintain Test Data**: Use factories for consistent test data
8. **Document Complex Tests**: Add comments for complex test scenarios

## 🎉 Success Metrics

- **Test Coverage**: >85% overall
- **Test Speed**: <30 seconds for full suite
- **Test Reliability**: <1% flaky tests
- **Test Maintainability**: Easy to add new tests
- **Test Documentation**: Clear and comprehensive

---

**Happy Testing! 🧪✨**

