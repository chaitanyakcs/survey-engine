import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from src.main import app

client = TestClient(app)


class TestFieldExtractionAPI:
    """Test suite for Field Extraction API endpoints"""
    
    def test_extract_fields(self):
        """Test POST /api/v1/field-extraction/ endpoint"""
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
                        {
                            "text": "At what price would this coffee machine be too expensive?",
                            "type": "text",
                            "category": "pricing"
                        },
                        {
                            "text": "Which features are most important to you?",
                            "type": "multiple_choice",
                            "options": ["Price", "Quality", "Design", "Brand"]
                        }
                    ]
                }
            }
            
            response = client.post("/api/v1/field-extraction/", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert data["methodology_tags"] == ["van_westendorp", "conjoint"]
            assert data["industry_category"] == "consumer_goods"
            assert data["research_goal"] == "pricing_research"
            assert data["quality_score"] == 0.85
    
    def test_extract_fields_validation_error(self):
        """Test POST /api/v1/field-extraction/ with invalid data"""
        payload = {
            "workflow_id": "",  # Empty workflow_id should fail
            "rfq_text": "Test RFQ",
            "survey_json": {"questions": []}
        }
        
        response = client.post("/api/v1/field-extraction/", json=payload)
        
        assert response.status_code == 422  # Validation error
    
    def test_extract_fields_missing_rfq_text(self):
        """Test POST /api/v1/field-extraction/ with missing RFQ text"""
        payload = {
            "workflow_id": "workflow_123",
            "rfq_text": "",  # Empty RFQ text
            "survey_json": {"questions": []}
        }
        
        response = client.post("/api/v1/field-extraction/", json=payload)
        
        assert response.status_code == 422  # Validation error
    
    def test_extract_fields_invalid_survey_json(self):
        """Test POST /api/v1/field-extraction/ with invalid survey JSON"""
        payload = {
            "workflow_id": "workflow_123",
            "rfq_text": "Test RFQ text",
            "survey_json": "invalid_json"  # Should be a dict, not string
        }
        
        response = client.post("/api/v1/field-extraction/", json=payload)
        
        assert response.status_code == 422  # Validation error
    
    def test_extract_fields_service_error(self):
        """Test POST /api/v1/field-extraction/ with service error"""
        with patch('src.services.field_extraction_service.FieldExtractionService.extract_fields') as mock_extract:
            mock_extract.side_effect = Exception("Field extraction service unavailable")
            
            payload = {
                "workflow_id": "workflow_123",
                "rfq_text": "Test RFQ text",
                "survey_json": {"questions": []}
            }
            
            response = client.post("/api/v1/field-extraction/", json=payload)
            
            assert response.status_code == 500
            assert "error" in response.json()
    
    def test_extract_fields_with_parsing_issues(self):
        """Test POST /api/v1/field-extraction/ with parsing issues detected"""
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
                    "questions": [
                        {
                            "text": "What do you think?",
                            "type": "text"
                        }
                    ]
                }
            }
            
            response = client.post("/api/v1/field-extraction/", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert data["quality_score"] == 0.6
            assert len(data["parsing_issues"]) == 3
            assert "Survey questions lack clear methodology indicators" in data["parsing_issues"]
    
    def test_extract_fields_high_confidence(self):
        """Test POST /api/v1/field-extraction/ with high confidence extraction"""
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
                        {
                            "text": "Which of these feature combinations would you prefer?",
                            "type": "choice_task",
                            "methodology": "conjoint_analysis"
                        },
                        {
                            "text": "Rank these features by importance",
                            "type": "ranking",
                            "methodology": "maxdiff"
                        }
                    ]
                }
            }
            
            response = client.post("/api/v1/field-extraction/", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert data["quality_score"] == 0.95
            assert data["confidence_score"] == 0.98
            assert "maxdiff" in data["methodology_tags"]
            assert "conjoint_analysis" in data["methodology_tags"]
            assert data["industry_category"] == "technology"
    
    def test_extract_fields_empty_survey(self):
        """Test POST /api/v1/field-extraction/ with empty survey"""
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
                "survey_json": {
                    "questions": []
                }
            }
            
            response = client.post("/api/v1/field-extraction/", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert data["quality_score"] == 0.0
            assert data["confidence_score"] == 0.0
            assert len(data["parsing_issues"]) == 2


if __name__ == "__main__":
    pytest.main([__file__])
