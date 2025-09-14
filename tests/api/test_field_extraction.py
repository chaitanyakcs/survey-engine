"""
Standardized tests for Field Extraction API endpoints
"""
import pytest
from unittest.mock import patch
from tests.base import BaseAPITest, TestDataFactory


@pytest.mark.api
class TestFieldExtractionAPI(BaseAPITest):
    """Test suite for Field Extraction API endpoints"""
    
    def test_extract_fields_success(self):
        """Test successful field extraction"""
        client = self.create_test_client()
        
        with patch('src.services.field_extraction_service.FieldExtractionService.extract_fields') as mock_extract:
            mock_extract.return_value = {
                "methodology_tags": ["van_westendorp", "conjoint"],
                "industry_category": "consumer_goods",
                "research_goal": "pricing_research",
                "quality_score": 0.85,
                "suggested_title": "Coffee Machine Pricing Study",
                "confidence_score": 0.9,
                "reasoning": {
                    "methodology_detection": "Detected pricing questions and choice-based questions",
                    "industry_classification": "Consumer goods based on product type and pricing focus",
                    "research_goal": "Clear focus on pricing optimization and feature preferences"
                },
                "parsing_issues": []
            }
            
            payload = {
                "workflow_id": "workflow_123",
                "rfq_text": "We need a survey for coffee machine pricing research targeting consumers aged 25-45",
                "survey_json": {
                    "questions": [
                        TestDataFactory.create_question("van_westendorp"),
                        TestDataFactory.create_question("multiple_choice")
                    ]
                }
            }
            
            response = client.post("/api/v1/field-extraction/", json=payload)
            
            self.assert_response_structure(response, 200, [
                "methodology_tags", "industry_category", "research_goal", 
                "quality_score", "suggested_title", "confidence_score"
            ])
            data = response.json()
            assert "van_westendorp" in data["methodology_tags"]
            assert data["industry_category"] == "consumer_goods"
            assert data["quality_score"] == 0.85
    
    def test_extract_fields_validation_error(self):
        """Test field extraction with invalid data"""
        client = self.create_test_client()
        
        # Test empty workflow_id
        payload = {
            "workflow_id": "",  # Invalid: empty workflow_id
            "rfq_text": "Test RFQ",
            "survey_json": {"questions": []}
        }
        
        response = client.post("/api/v1/field-extraction/", json=payload)
        self.assert_response_structure(response, 422)
    
    def test_extract_fields_missing_rfq_text(self):
        """Test field extraction with missing RFQ text"""
        client = self.create_test_client()
        
        payload = {
            "workflow_id": "workflow_123",
            "rfq_text": "",  # Invalid: empty RFQ text
            "survey_json": {"questions": []}
        }
        
        response = client.post("/api/v1/field-extraction/", json=payload)
        self.assert_response_structure(response, 422)
    
    def test_extract_fields_invalid_survey_json(self):
        """Test field extraction with invalid survey JSON"""
        client = self.create_test_client()
        
        payload = {
            "workflow_id": "workflow_123",
            "rfq_text": "Test RFQ text",
            "survey_json": "invalid_json"  # Should be a dict, not string
        }
        
        response = client.post("/api/v1/field-extraction/", json=payload)
        self.assert_response_structure(response, 422)
    
    def test_extract_fields_service_error(self):
        """Test field extraction with service error"""
        client = self.create_test_client()
        
        with patch('src.services.field_extraction_service.FieldExtractionService.extract_fields') as mock_extract:
            mock_extract.side_effect = Exception("Field extraction service unavailable")
            
            payload = {
                "workflow_id": "workflow_123",
                "rfq_text": "Test RFQ text",
                "survey_json": {"questions": []}
            }
            
            response = client.post("/api/v1/field-extraction/", json=payload)
            
            self.assert_response_structure(response, 500)
            assert "error" in response.json()
    
    def test_extract_fields_with_parsing_issues(self):
        """Test field extraction with parsing issues detected"""
        client = self.create_test_client()
        
        with patch('src.services.field_extraction_service.FieldExtractionService.extract_fields') as mock_extract:
            mock_extract.return_value = {
                "methodology_tags": ["basic_survey"],
                "industry_category": "general",
                "research_goal": "general_research",
                "quality_score": 0.6,
                "suggested_title": "General Survey",
                "confidence_score": 0.5,
                "reasoning": {
                    "methodology_detection": "Could not identify specific methodology",
                    "industry_classification": "Unable to determine specific industry",
                    "research_goal": "General research purpose detected"
                },
                "parsing_issues": [
                    "Survey questions lack clear methodology indicators",
                    "RFQ text is too generic for specific classification",
                    "No clear pricing or choice-based questions detected"
                ]
            }
            
            payload = {
                "workflow_id": "workflow_123",
                "rfq_text": "We need a general survey",
                "survey_json": {
                    "questions": [TestDataFactory.create_question("text")]
                }
            }
            
            response = client.post("/api/v1/field-extraction/", json=payload)
            
            self.assert_response_structure(response, 200)
            data = response.json()
            assert data["quality_score"] == 0.6
            assert len(data["parsing_issues"]) == 3
            assert "Survey questions lack clear methodology indicators" in data["parsing_issues"]
    
    def test_extract_fields_high_confidence(self):
        """Test field extraction with high confidence results"""
        client = self.create_test_client()
        
        with patch('src.services.field_extraction_service.FieldExtractionService.extract_fields') as mock_extract:
            mock_extract.return_value = {
                "methodology_tags": ["maxdiff", "conjoint_analysis"],
                "industry_category": "technology",
                "research_goal": "feature_prioritization",
                "quality_score": 0.95,
                "suggested_title": "Software Feature Prioritization Study",
                "confidence_score": 0.98,
                "reasoning": {
                    "methodology_detection": "Clear MaxDiff and Conjoint Analysis indicators found",
                    "industry_classification": "Technology sector based on software features and B2B context",
                    "research_goal": "Explicit focus on feature prioritization and trade-off analysis"
                },
                "parsing_issues": []
            }
            
            payload = {
                "workflow_id": "workflow_123",
                "rfq_text": "We need to prioritize software features for our B2B platform. Use MaxDiff methodology to understand feature importance and conjoint analysis for trade-offs.",
                "survey_json": {
                    "questions": [
                        TestDataFactory.create_question("multiple_choice", methodology="conjoint_analysis"),
                        TestDataFactory.create_question("ranking", methodology="maxdiff")
                    ]
                }
            }
            
            response = client.post("/api/v1/field-extraction/", json=payload)
            
            self.assert_response_structure(response, 200)
            data = response.json()
            assert data["quality_score"] == 0.95
            assert data["confidence_score"] == 0.98
            assert "maxdiff" in data["methodology_tags"]
            assert "conjoint_analysis" in data["methodology_tags"]
            assert data["industry_category"] == "technology"
    
    def test_extract_fields_empty_survey(self):
        """Test field extraction with empty survey"""
        client = self.create_test_client()
        
        with patch('src.services.field_extraction_service.FieldExtractionService.extract_fields') as mock_extract:
            mock_extract.return_value = {
                "methodology_tags": [],
                "industry_category": None,
                "research_goal": None,
                "quality_score": 0.0,
                "suggested_title": None,
                "confidence_score": 0.0,
                "reasoning": {
                    "methodology_detection": "No survey questions provided",
                    "industry_classification": "Cannot classify without survey content",
                    "research_goal": "Cannot determine research goal without survey questions"
                },
                "parsing_issues": [
                    "No survey questions provided for analysis",
                    "Cannot extract methodology without question content"
                ]
            }
            
            payload = {
                "workflow_id": "workflow_123",
                "rfq_text": "Test RFQ text",
                "survey_json": {"questions": []}
            }
            
            response = client.post("/api/v1/field-extraction/", json=payload)
            
            self.assert_response_structure(response, 200)
            data = response.json()
            assert data["quality_score"] == 0.0
            assert data["confidence_score"] == 0.0
            assert len(data["parsing_issues"]) == 2
    
    def test_extract_fields_different_industries(self):
        """Test field extraction for different industry categories"""
        client = self.create_test_client()
        
        test_cases = [
            {
                "rfq": "We need a survey for software feature prioritization in B2B SaaS",
                "expected_industry": "technology",
                "expected_methodology": ["conjoint_analysis", "maxdiff"]
            },
            {
                "rfq": "We need a pricing study for consumer electronics retail",
                "expected_industry": "consumer_goods",
                "expected_methodology": ["van_westendorp", "pricing"]
            },
            {
                "rfq": "We need a customer satisfaction survey for banking services",
                "expected_industry": "financial_services",
                "expected_methodology": ["satisfaction", "nps"]
            }
        ]
        
        with patch('src.services.field_extraction_service.FieldExtractionService.extract_fields') as mock_extract:
            for i, case in enumerate(test_cases):
                mock_extract.return_value = {
                    "methodology_tags": case["expected_methodology"],
                    "industry_category": case["expected_industry"],
                    "research_goal": "general_research",
                    "quality_score": 0.8,
                    "suggested_title": f"Test Survey {i+1}",
                    "confidence_score": 0.7,
                    "reasoning": {},
                    "parsing_issues": []
                }
                
                payload = {
                    "workflow_id": f"workflow_{i+1}",
                    "rfq_text": case["rfq"],
                    "survey_json": {"questions": [TestDataFactory.create_question("text")]}
                }
                
                response = client.post("/api/v1/field-extraction/", json=payload)
                
                self.assert_response_structure(response, 200)
                data = response.json()
                assert data["industry_category"] == case["expected_industry"]
                assert all(tag in data["methodology_tags"] for tag in case["expected_methodology"])
    
    def test_extract_fields_quality_score_ranges(self):
        """Test field extraction with different quality score ranges"""
        client = self.create_test_client()
        
        quality_test_cases = [
            {"score": 0.95, "description": "excellent"},
            {"score": 0.8, "description": "good"},
            {"score": 0.6, "description": "fair"},
            {"score": 0.3, "description": "poor"}
        ]
        
        with patch('src.services.field_extraction_service.FieldExtractionService.extract_fields') as mock_extract:
            for i, case in enumerate(quality_test_cases):
                mock_extract.return_value = {
                    "methodology_tags": ["basic_survey"],
                    "industry_category": "general",
                    "research_goal": "general_research",
                    "quality_score": case["score"],
                    "suggested_title": f"Test Survey {i+1}",
                    "confidence_score": case["score"],
                    "reasoning": {},
                    "parsing_issues": []
                }
                
                payload = {
                    "workflow_id": f"workflow_{i+1}",
                    "rfq_text": f"Test RFQ for {case['description']} quality survey",
                    "survey_json": {"questions": [TestDataFactory.create_question("text")]}
                }
                
                response = client.post("/api/v1/field-extraction/", json=payload)
                
                self.assert_response_structure(response, 200)
                data = response.json()
                assert data["quality_score"] == case["score"]
                assert 0.0 <= data["quality_score"] <= 1.0  # Valid range


if __name__ == "__main__":
    pytest.main([__file__])
