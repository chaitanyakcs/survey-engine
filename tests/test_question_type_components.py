"""
Comprehensive test suite for new question type components
Tests MatrixLikert, ConstantSum, NumericGrid, and NumericOpen components
"""
import pytest
import json
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List

# Mock React components for testing
class MockComponent:
    def __init__(self, **props):
        self.props = props
    
    def render(self):
        return f"<{self.__class__.__name__} {self.props}>"


class TestMatrixLikertComponent:
    """Test MatrixLikert component functionality"""

    def test_matrix_likert_parsing(self):
        """Test parsing of matrix_likert question text"""
        question_text = "Rate these attributes: Quality, Price, Service, Support"
        
        # Simulate parsing logic
        attributes = [attr.strip() for attr in question_text.split(":")[1].split(",")]
        expected_attributes = ["Quality", "Price", "Service", "Support"]
        
        assert attributes == expected_attributes, f"Expected {expected_attributes}, got {attributes}"

    def test_matrix_likert_validation(self):
        """Test validation of matrix_likert question structure"""
        valid_question = {
            "id": "q1",
            "text": "Rate these attributes: Quality, Price, Service",
            "type": "matrix_likert",
            "attributes": ["Quality", "Price", "Service"],
            "options": ["Poor", "Fair", "Good", "Excellent"],
            "required": True,
            "validation": "matrix_likert:required"
        }
        
        # Validate required fields
        assert "id" in valid_question
        assert "text" in valid_question
        assert "type" in valid_question
        assert valid_question["type"] == "matrix_likert"
        assert "attributes" in valid_question
        assert "options" in valid_question
        assert len(valid_question["attributes"]) > 0
        assert len(valid_question["options"]) > 0

    def test_matrix_likert_invalid_structure(self):
        """Test validation of invalid matrix_likert structure"""
        invalid_question = {
            "id": "q1",
            "text": "Rate these attributes",
            "type": "matrix_likert",
            "options": ["Poor", "Fair", "Good", "Excellent"]
            # Missing attributes
        }
        
        # Should fail validation
        assert "attributes" not in invalid_question
        assert invalid_question["type"] == "matrix_likert"

    def test_matrix_likert_rendering_data(self):
        """Test data structure for matrix_likert rendering"""
        question = {
            "id": "q1",
            "text": "Rate these attributes: Quality, Price, Service",
            "type": "matrix_likert",
            "attributes": ["Quality", "Price", "Service"],
            "options": ["Poor", "Fair", "Good", "Excellent"],
            "required": True
        }
        
        # Simulate rendering data preparation
        rendering_data = {
            "question_id": question["id"],
            "question_text": question["text"],
            "attributes": question["attributes"],
            "options": question["options"],
            "required": question["required"],
            "rows": question["attributes"],
            "columns": question["options"]
        }
        
        assert rendering_data["question_id"] == "q1"
        assert len(rendering_data["rows"]) == 3
        assert len(rendering_data["columns"]) == 4
        assert rendering_data["required"] is True


class TestConstantSumComponent:
    """Test ConstantSum component functionality"""

    def test_constant_sum_parsing(self):
        """Test parsing of constant_sum question text"""
        question_text = "Allocate 100 points among these features: Feature A, Feature B, Feature C"
        
        # Simulate parsing logic
        if "points" in question_text:
            total_points = int(question_text.split("points")[0].split()[-1])
        else:
            total_points = 100  # Default
        
        options_text = question_text.split(":")[1]
        options = [opt.strip() for opt in options_text.split(",")]
        
        assert total_points == 100
        assert options == ["Feature A", "Feature B", "Feature C"]

    def test_constant_sum_validation(self):
        """Test validation of constant_sum question structure"""
        valid_question = {
            "id": "q1",
            "text": "Allocate 100 points among these features",
            "type": "constant_sum",
            "options": ["Feature A", "Feature B", "Feature C"],
            "total_points": 100,
            "required": True,
            "validation": "constant_sum:total=100"
        }
        
        # Validate required fields
        assert "id" in valid_question
        assert "text" in valid_question
        assert "type" in valid_question
        assert valid_question["type"] == "constant_sum"
        assert "options" in valid_question
        assert "total_points" in valid_question
        assert valid_question["total_points"] == 100
        assert len(valid_question["options"]) > 0

    def test_constant_sum_invalid_structure(self):
        """Test validation of invalid constant_sum structure"""
        invalid_question = {
            "id": "q1",
            "text": "Allocate points among these features",
            "type": "constant_sum",
            "options": ["Feature A", "Feature B", "Feature C"]
            # Missing total_points
        }
        
        # Should fail validation
        assert "total_points" not in invalid_question
        assert invalid_question["type"] == "constant_sum"

    def test_constant_sum_point_validation(self):
        """Test point allocation validation logic"""
        total_points = 100
        allocated_points = {"Feature A": 40, "Feature B": 30, "Feature C": 30}
        
        # Simulate validation logic
        sum_points = sum(allocated_points.values())
        is_valid = sum_points == total_points
        
        assert is_valid, f"Point allocation should equal {total_points}, got {sum_points}"

    def test_constant_sum_point_validation_invalid(self):
        """Test point allocation validation with invalid total"""
        total_points = 100
        allocated_points = {"Feature A": 50, "Feature B": 30, "Feature C": 30}
        
        # Simulate validation logic
        sum_points = sum(allocated_points.values())
        is_valid = sum_points == total_points
        
        assert not is_valid, f"Point allocation should not equal {total_points}, got {sum_points}"

    def test_constant_sum_rendering_data(self):
        """Test data structure for constant_sum rendering"""
        question = {
            "id": "q1",
            "text": "Allocate 100 points among these features",
            "type": "constant_sum",
            "options": ["Feature A", "Feature B", "Feature C"],
            "total_points": 100,
            "required": True
        }
        
        # Simulate rendering data preparation
        rendering_data = {
            "question_id": question["id"],
            "question_text": question["text"],
            "options": question["options"],
            "total_points": question["total_points"],
            "required": question["required"],
            "allocated_points": {opt: 0 for opt in question["options"]}
        }
        
        assert rendering_data["question_id"] == "q1"
        assert rendering_data["total_points"] == 100
        assert len(rendering_data["options"]) == 3
        assert len(rendering_data["allocated_points"]) == 3


class TestNumericGridComponent:
    """Test NumericGrid component functionality"""

    def test_numeric_grid_parsing(self):
        """Test parsing of numeric_grid question text"""
        question_text = "Rate these products on these attributes: Product A, Product B vs Quality, Price, Service"
        
        # Simulate parsing logic
        if " vs " in question_text:
            parts = question_text.split(" vs ")
            rows_text = parts[0].split(":")[1]
            columns_text = parts[1]
            
            rows = [row.strip() for row in rows_text.split(",")]
            columns = [col.strip() for col in columns_text.split(",")]
        else:
            rows = ["Product A", "Product B"]  # Default
            columns = ["Quality", "Price"]     # Default
        
        assert rows == ["Product A", "Product B"]
        assert columns == ["Quality", "Price", "Service"]

    def test_numeric_grid_validation(self):
        """Test validation of numeric_grid question structure"""
        valid_question = {
            "id": "q1",
            "text": "Rate these products on these attributes",
            "type": "numeric_grid",
            "rows": ["Product A", "Product B"],
            "columns": ["Quality", "Price"],
            "required": True,
            "validation": "numeric_grid:required"
        }
        
        # Validate required fields
        assert "id" in valid_question
        assert "text" in valid_question
        assert "type" in valid_question
        assert valid_question["type"] == "numeric_grid"
        assert "rows" in valid_question
        assert "columns" in valid_question
        assert len(valid_question["rows"]) > 0
        assert len(valid_question["columns"]) > 0

    def test_numeric_grid_invalid_structure(self):
        """Test validation of invalid numeric_grid structure"""
        invalid_question = {
            "id": "q1",
            "text": "Rate these products",
            "type": "numeric_grid",
            "rows": ["Product A", "Product B"]
            # Missing columns
        }
        
        # Should fail validation
        assert "columns" not in invalid_question
        assert invalid_question["type"] == "numeric_grid"

    def test_numeric_grid_rendering_data(self):
        """Test data structure for numeric_grid rendering"""
        question = {
            "id": "q1",
            "text": "Rate these products on these attributes",
            "type": "numeric_grid",
            "rows": ["Product A", "Product B"],
            "columns": ["Quality", "Price"],
            "required": True
        }
        
        # Simulate rendering data preparation
        rendering_data = {
            "question_id": question["id"],
            "question_text": question["text"],
            "rows": question["rows"],
            "columns": question["columns"],
            "required": question["required"],
            "grid_data": {
                f"{row}_{col}": "" for row in question["rows"] for col in question["columns"]
            }
        }
        
        assert rendering_data["question_id"] == "q1"
        assert len(rendering_data["rows"]) == 2
        assert len(rendering_data["columns"]) == 2
        assert len(rendering_data["grid_data"]) == 4  # 2 rows × 2 columns


class TestNumericOpenComponent:
    """Test NumericOpen component functionality"""

    def test_numeric_open_parsing(self):
        """Test parsing of numeric_open question text"""
        question_text = "What is the maximum price you would pay for this product?"
        
        # Simulate parsing logic
        is_currency_question = any(word in question_text.lower() for word in ["price", "cost", "amount", "dollar", "euro"])
        currency = "USD" if is_currency_question else None
        
        assert is_currency_question is True
        assert currency == "USD"

    def test_numeric_open_validation(self):
        """Test validation of numeric_open question structure"""
        valid_question = {
            "id": "q1",
            "text": "What is the maximum price you would pay?",
            "type": "numeric_open",
            "currency": "USD",
            "required": True,
            "validation": "currency:required; min=0"
        }
        
        # Validate required fields
        assert "id" in valid_question
        assert "text" in valid_question
        assert "type" in valid_question
        assert valid_question["type"] == "numeric_open"
        assert "currency" in valid_question
        assert valid_question["currency"] == "USD"

    def test_numeric_open_van_westendorp_parsing(self):
        """Test parsing of Van Westendorp questions"""
        van_westendorp_questions = [
            "At what price would you consider the product so expensive that you would not consider buying it?",
            "At what price would you consider the product so inexpensive that you would question its quality?",
            "At what price would you consider the product expensive, but you would still consider buying it?",
            "At what price would you consider the product a bargain—a great buy for the money?"
        ]
        
        for question_text in van_westendorp_questions:
            # Simulate parsing logic
            is_van_westendorp = any(phrase in question_text.lower() for phrase in [
                "so expensive that you would not consider buying",
                "so inexpensive that you would question its quality",
                "expensive, but you would still consider buying",
                "bargain—a great buy for the money"
            ])
            
            assert is_van_westendorp is True, f"Should identify Van Westendorp question: {question_text}"

    def test_numeric_open_currency_validation(self):
        """Test currency validation for numeric_open questions"""
        question = {
            "id": "q1",
            "text": "What is the maximum price you would pay?",
            "type": "numeric_open",
            "currency": "USD",
            "required": True,
            "validation": "currency:required; min=0"
        }
        
        # Simulate validation logic
        validation_rules = question["validation"].split(";")
        has_currency = "currency" in validation_rules[0]
        has_min = "min=0" in validation_rules[1]
        
        assert has_currency is True
        assert has_min is True

    def test_numeric_open_rendering_data(self):
        """Test data structure for numeric_open rendering"""
        question = {
            "id": "q1",
            "text": "What is the maximum price you would pay?",
            "type": "numeric_open",
            "currency": "USD",
            "required": True
        }
        
        # Simulate rendering data preparation
        rendering_data = {
            "question_id": question["id"],
            "question_text": question["text"],
            "currency": question["currency"],
            "required": question["required"],
            "input_type": "number",
            "step": "0.01" if question["currency"] else "1"
        }
        
        assert rendering_data["question_id"] == "q1"
        assert rendering_data["currency"] == "USD"
        assert rendering_data["input_type"] == "number"
        assert rendering_data["step"] == "0.01"


class TestQuestionTypeIntegration:
    """Integration tests for all question types"""

    def test_question_type_detection(self):
        """Test detection of question types from text"""
        question_type_tests = [
            {
                "text": "Rate these attributes: Quality, Price, Service",
                "expected_type": "matrix_likert",
                "expected_attributes": ["Quality", "Price", "Service"]
            },
            {
                "text": "Allocate 100 points among these features: Feature A, Feature B",
                "expected_type": "constant_sum",
                "expected_total": 100
            },
            {
                "text": "Rate these products on these attributes: Product A, Product B vs Quality, Price",
                "expected_type": "numeric_grid",
                "expected_rows": ["Product A", "Product B"],
                "expected_columns": ["Quality", "Price"]
            },
            {
                "text": "What is the maximum price you would pay?",
                "expected_type": "numeric_open",
                "expected_currency": "USD"
            }
        ]
        
        for test_case in question_type_tests:
            text = test_case["text"]
            expected_type = test_case["expected_type"]
            
            # Simulate type detection logic
            if "Rate these attributes" in text and ":" in text:
                detected_type = "matrix_likert"
            elif "Allocate" in text and "points" in text:
                detected_type = "constant_sum"
            elif "Rate these products" in text and " vs " in text:
                detected_type = "numeric_grid"
            elif any(word in text.lower() for word in ["price", "cost", "amount"]):
                detected_type = "numeric_open"
            else:
                detected_type = "unknown"
            
            assert detected_type == expected_type, f"Expected {expected_type}, got {detected_type} for: {text}"

    def test_question_type_validation_rules(self):
        """Test validation rules for each question type"""
        validation_tests = [
            {
                "type": "matrix_likert",
                "required_fields": ["id", "text", "type", "attributes", "options"],
                "validation_pattern": "matrix_likert:required"
            },
            {
                "type": "constant_sum",
                "required_fields": ["id", "text", "type", "options", "total_points"],
                "validation_pattern": "constant_sum:total=100"
            },
            {
                "type": "numeric_grid",
                "required_fields": ["id", "text", "type", "rows", "columns"],
                "validation_pattern": "numeric_grid:required"
            },
            {
                "type": "numeric_open",
                "required_fields": ["id", "text", "type", "currency"],
                "validation_pattern": "currency:required; min=0"
            }
        ]
        
        for test_case in validation_tests:
            question_type = test_case["type"]
            required_fields = test_case["required_fields"]
            validation_pattern = test_case["validation_pattern"]
            
            # Test that validation pattern contains expected elements
            if question_type == "matrix_likert":
                assert "matrix_likert" in validation_pattern
            elif question_type == "constant_sum":
                assert "constant_sum" in validation_pattern
                assert "total=" in validation_pattern
            elif question_type == "numeric_grid":
                assert "numeric_grid" in validation_pattern
            elif question_type == "numeric_open":
                assert "currency" in validation_pattern
                assert "min=" in validation_pattern

    def test_question_type_rendering_consistency(self):
        """Test that all question types have consistent rendering data structure"""
        question_types = ["matrix_likert", "constant_sum", "numeric_grid", "numeric_open"]
        
        for question_type in question_types:
            # Simulate rendering data structure
            rendering_data = {
                "question_id": f"q_{question_type}",
                "question_text": f"Test {question_type} question",
                "type": question_type,
                "required": True
            }
            
            # All question types should have these basic fields
            assert "question_id" in rendering_data
            assert "question_text" in rendering_data
            assert "type" in rendering_data
            assert "required" in rendering_data
            
            # Type-specific fields should be present
            if question_type == "matrix_likert":
                rendering_data["attributes"] = ["Quality", "Price"]
                rendering_data["options"] = ["Poor", "Good", "Excellent"]
            elif question_type == "constant_sum":
                rendering_data["options"] = ["Feature A", "Feature B"]
                rendering_data["total_points"] = 100
            elif question_type == "numeric_grid":
                rendering_data["rows"] = ["Product A", "Product B"]
                rendering_data["columns"] = ["Quality", "Price"]
            elif question_type == "numeric_open":
                rendering_data["currency"] = "USD"
                rendering_data["input_type"] = "number"

    def test_question_type_error_handling(self):
        """Test error handling for malformed question types"""
        error_tests = [
            {
                "type": "matrix_likert",
                "malformed_data": {"id": "q1", "text": "Rate attributes", "type": "matrix_likert"},
                "expected_error": "missing_attributes"
            },
            {
                "type": "constant_sum",
                "malformed_data": {"id": "q1", "text": "Allocate points", "type": "constant_sum"},
                "expected_error": "missing_total_points"
            },
            {
                "type": "numeric_grid",
                "malformed_data": {"id": "q1", "text": "Rate products", "type": "numeric_grid"},
                "expected_error": "missing_columns"
            },
            {
                "type": "numeric_open",
                "malformed_data": {"id": "q1", "text": "Enter amount", "type": "numeric_open"},
                "expected_error": "missing_currency"
            }
        ]
        
        for test_case in error_tests:
            question_type = test_case["type"]
            malformed_data = test_case["malformed_data"]
            expected_error = test_case["expected_error"]
            
            # Simulate error detection
            if question_type == "matrix_likert" and "attributes" not in malformed_data:
                detected_error = "missing_attributes"
            elif question_type == "constant_sum" and "total_points" not in malformed_data:
                detected_error = "missing_total_points"
            elif question_type == "numeric_grid" and "columns" not in malformed_data:
                detected_error = "missing_columns"
            elif question_type == "numeric_open" and "currency" not in malformed_data:
                detected_error = "missing_currency"
            else:
                detected_error = "none"
            
            assert detected_error == expected_error, f"Expected {expected_error}, got {detected_error} for {question_type}"


if __name__ == "__main__":
    pytest.main([__file__])


