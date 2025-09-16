"""
Base test classes and utilities for standardized testing
"""
import pytest
import json
from typing import Dict, Any, Optional
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


class BaseAPITest:
    """Base class for API tests with common utilities"""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment for each test"""
        # Mock external dependencies
        self._mock_external_services()
        yield
        # Cleanup after test
        self._cleanup_mocks()
    
    def _mock_external_services(self):
        """Mock external services and dependencies"""
        # Mock database
        self.db_patcher = patch('src.database.connection.get_db')
        self.mock_db = self.db_patcher.start()
        self.mock_db.return_value = MagicMock()
        
        # Mock Redis
        self.redis_patcher = patch('src.services.cache_service.redis_client')
        self.mock_redis = self.redis_patcher.start()
        
        # Mock external APIs
        self.replicate_patcher = patch('src.services.generation_service.replicate')
        self.mock_replicate = self.replicate_patcher.start()
        
        # Mock sentence transformers
        self.st_patcher = patch('src.services.embedding_service.SentenceTransformer')
        self.mock_st = self.st_patcher.start()
        self.mock_st.return_value.encode.return_value = [[0.1, 0.2, 0.3]]
    
    def _cleanup_mocks(self):
        """Cleanup mocks after test"""
        self.db_patcher.stop()
        self.redis_patcher.stop()
        self.replicate_patcher.stop()
        self.st_patcher.stop()
    
    def create_test_client(self) -> TestClient:
        """Create test client with mocked dependencies"""
        from src.main import app
        return TestClient(app)
    
    def assert_response_structure(self, response, expected_status: int, required_fields: list = None):
        """Assert response has expected structure"""
        assert response.status_code == expected_status
        
        if response.status_code < 400:
            data = response.json()
            if required_fields:
                for field in required_fields:
                    assert field in data, f"Missing required field: {field}"
        else:
            assert "detail" in response.json()
    
    def create_mock_golden_pair(self, **overrides) -> Dict[str, Any]:
        """Create mock golden pair data"""
        default = {
            "id": "test_id_1",
            "title": "Test Golden Pair",
            "rfq_text": "Test RFQ text for pricing research",
            "survey_json": {
                "questions": [
                    {
                        "id": "q1",
                        "text": "What is your age?",
                        "type": "single_choice",
                        "options": ["18-24", "25-34", "35-44", "45+"],
                        "required": True,
                        "category": "demographic"
                    }
                ]
            },
            "methodology_tags": ["van_westendorp"],
            "industry_category": "consumer_goods",
            "research_goal": "pricing_research",
            "quality_score": 0.85,
            "created_at": "2024-01-01T00:00:00Z"
        }
        default.update(overrides)
        return default
    
    def create_mock_survey(self, **overrides) -> Dict[str, Any]:
        """Create mock survey data"""
        default = {
            "id": "survey_123",
            "title": "Test Survey",
            "description": "A test survey for unit testing",
            "questions": [
                {
                    "id": "q1",
                    "text": "What is your age?",
                    "type": "single_choice",
                    "options": ["18-24", "25-34", "35-44", "45+"],
                    "required": True,
                    "category": "demographic"
                },
                {
                    "id": "q2",
                    "text": "How satisfied are you?",
                    "type": "rating_scale",
                    "scale_min": 1,
                    "scale_max": 5,
                    "required": True,
                    "category": "satisfaction"
                }
            ],
            "estimated_time": 10,
            "target_responses": 200,
            "metadata": {
                "methodology": ["basic_survey"],
                "industry_category": "technology",
                "research_goal": "customer_satisfaction"
            }
        }
        default.update(overrides)
        return default
    
    def create_mock_rfq_request(self, **overrides) -> Dict[str, Any]:
        """Create mock RFQ request data"""
        default = {
            "description": "We need a survey for coffee machine pricing research",
            "title": "Coffee Machine Pricing Survey"
        }
        default.update(overrides)
        return default


class BaseServiceTest:
    """Base class for service tests"""
    
    @pytest.fixture(autouse=True)
    def setup_service_test(self):
        """Setup service test environment"""
        self._mock_dependencies()
        yield
        self._cleanup_service_mocks()
    
    def _mock_dependencies(self):
        """Mock service dependencies"""
        # Mock database session
        self.db_patcher = patch('src.database.connection.get_db')
        self.mock_db = self.db_patcher.start()
        self.mock_db.return_value = MagicMock()
        
        # Mock external services
        self.redis_patcher = patch('src.services.cache_service.redis_client')
        self.mock_redis = self.redis_patcher.start()
        
        self.replicate_patcher = patch('src.services.generation_service.replicate')
        self.mock_replicate = self.replicate_patcher.start()
    
    def _cleanup_service_mocks(self):
        """Cleanup service mocks"""
        self.db_patcher.stop()
        self.redis_patcher.stop()
        self.replicate_patcher.stop()
    
    def assert_service_response(self, response, expected_type: type = None, required_fields: list = None):
        """Assert service response structure"""
        if expected_type:
            assert isinstance(response, expected_type)
        
        if required_fields and hasattr(response, '__dict__'):
            for field in required_fields:
                assert hasattr(response, field), f"Missing required field: {field}"
        elif required_fields and isinstance(response, dict):
            for field in required_fields:
                assert field in response, f"Missing required field: {field}"


class BaseComponentTest:
    """Base class for React component tests"""
    
    def create_mock_props(self, **overrides) -> Dict[str, Any]:
        """Create mock props for components"""
        return overrides
    
    def assert_component_renders(self, component, expected_elements: list):
        """Assert component renders expected elements"""
        for element in expected_elements:
            if isinstance(element, str):
                # Text content
                assert element in component.text
            elif hasattr(element, 'tagName'):
                # DOM element
                assert element in component


class TestDataFactory:
    """Factory for creating test data"""
    
    @staticmethod
    def create_question(question_type: str = "text", **overrides) -> Dict[str, Any]:
        """Create a test question"""
        base_questions = {
            "text": {
                "id": "q_text_1",
                "text": "Please provide your comments",
                "type": "text",
                "required": False,
                "category": "feedback"
            },
            "single_choice": {
                "id": "q_single_1",
                "text": "What is your age group?",
                "type": "single_choice",
                "options": ["18-24", "25-34", "35-44", "45+"],
                "required": True,
                "category": "demographic"
            },
            "multiple_choice": {
                "id": "q_multiple_1",
                "text": "Which features are important to you?",
                "type": "multiple_choice",
                "options": ["Price", "Quality", "Design", "Support"],
                "required": True,
                "category": "preferences"
            },
            "rating_scale": {
                "id": "q_rating_1",
                "text": "How satisfied are you?",
                "type": "rating_scale",
                "scale_min": 1,
                "scale_max": 5,
                "required": True,
                "category": "satisfaction"
            },
            "van_westendorp": {
                "id": "q_vw_1",
                "text": "At what price would this be too expensive?",
                "type": "text",
                "required": True,
                "category": "pricing",
                "methodology": "van_westendorp"
            }
        }
        
        question = base_questions.get(question_type, base_questions["text"]).copy()
        question.update(overrides)
        return question
    
    @staticmethod
    def create_methodology_tags(methodology: str) -> list:
        """Create methodology tags based on methodology type"""
        methodology_map = {
            "van_westendorp": ["van_westendorp", "pricing"],
            "conjoint": ["conjoint_analysis", "choice_modeling"],
            "maxdiff": ["maxdiff", "ranking"],
            "basic": ["basic_survey"],
            "mixed": ["van_westendorp", "conjoint_analysis", "maxdiff"]
        }
        return methodology_map.get(methodology, ["basic_survey"])
    
    @staticmethod
    def create_industry_category(industry: str) -> str:
        """Create industry category"""
        industry_map = {
            "tech": "technology",
            "retail": "consumer_goods",
            "finance": "financial_services",
            "healthcare": "healthcare",
            "automotive": "automotive"
        }
        return industry_map.get(industry, "general")
    
    @staticmethod
    def create_research_goal(goal: str) -> str:
        """Create research goal"""
        goal_map = {
            "pricing": "pricing_research",
            "features": "feature_prioritization",
            "satisfaction": "customer_satisfaction",
            "brand": "brand_perception",
            "general": "general_research"
        }
        return goal_map.get(goal, "general_research")

