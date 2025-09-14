import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from src.main import app

client = TestClient(app)


class TestSurveyGenerationAPI:
    """Test suite for Survey Generation API endpoints"""
    
    def test_submit_rfq(self):
        """Test POST /api/v1/rfq/ endpoint"""
        with patch('src.services.generation_service.GenerationService.generate_survey') as mock_generate:
            mock_generate.return_value = {
                "survey_id": "survey_123",
                "workflow_id": "workflow_456",
                "status": "started",
                "message": "Survey generation started"
            }
            
            payload = {
                "description": "We need a survey for pricing research on coffee machines",
                "title": "Coffee Machine Pricing Survey"
            }
            
            response = client.post("/api/v1/rfq/", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert data["survey_id"] == "survey_123"
            assert data["status"] == "started"
    
    def test_submit_rfq_validation_error(self):
        """Test POST /api/v1/rfq/ with invalid data"""
        payload = {
            "description": "",  # Empty description should fail
            "title": "Test Survey"
        }
        
        response = client.post("/api/v1/rfq/", json=payload)
        
        assert response.status_code == 422  # Validation error
    
    def test_get_survey_status(self):
        """Test GET /api/v1/survey/{id}/status endpoint"""
        with patch('src.services.generation_service.GenerationService.get_survey_status') as mock_status:
            mock_status.return_value = {
                "survey_id": "survey_123",
                "status": "completed",
                "progress": 100,
                "current_step": "finalized",
                "message": "Survey generation completed"
            }
            
            response = client.get("/api/v1/survey/survey_123/status")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert data["progress"] == 100
    
    def test_get_survey_status_not_found(self):
        """Test GET /api/v1/survey/{id}/status with non-existent ID"""
        with patch('src.services.generation_service.GenerationService.get_survey_status') as mock_status:
            mock_status.return_value = None
            
            response = client.get("/api/v1/survey/nonexistent/status")
            
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()
    
    def test_get_survey_result(self):
        """Test GET /api/v1/survey/{id} endpoint"""
        with patch('src.services.generation_service.GenerationService.get_survey_result') as mock_result:
            mock_result.return_value = {
                "id": "survey_123",
                "title": "Coffee Machine Pricing Survey",
                "description": "A survey to understand pricing preferences for coffee machines",
                "questions": [
                    {
                        "id": "q1",
                        "text": "What is your age group?",
                        "type": "single_choice",
                        "options": ["18-24", "25-34", "35-44", "45+"],
                        "required": True,
                        "category": "demographic"
                    },
                    {
                        "id": "q2",
                        "text": "At what price would this coffee machine be too expensive?",
                        "type": "text",
                        "required": True,
                        "category": "pricing",
                        "methodology": "van_westendorp"
                    }
                ],
                "estimated_time": 15,
                "target_responses": 200,
                "metadata": {
                    "methodology": ["van_westendorp"],
                    "industry_category": "consumer_goods",
                    "research_goal": "pricing_research"
                }
            }
            
            response = client.get("/api/v1/survey/survey_123")
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "survey_123"
            assert data["title"] == "Coffee Machine Pricing Survey"
            assert len(data["questions"]) == 2
    
    def test_get_survey_result_not_found(self):
        """Test GET /api/v1/survey/{id} with non-existent ID"""
        with patch('src.services.generation_service.GenerationService.get_survey_result') as mock_result:
            mock_result.return_value = None
            
            response = client.get("/api/v1/survey/nonexistent")
            
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()
    
    def test_edit_survey(self):
        """Test PUT /api/v1/survey/{id}/edit endpoint"""
        with patch('src.services.generation_service.GenerationService.edit_survey') as mock_edit:
            mock_edit.return_value = {
                "id": "survey_123",
                "title": "Updated Coffee Machine Survey",
                "description": "Updated description",
                "questions": [],
                "estimated_time": 20,
                "target_responses": 250
            }
            
            payload = {
                "title": "Updated Coffee Machine Survey",
                "description": "Updated description",
                "questions": [],
                "estimated_time": 20,
                "target_responses": 250
            }
            
            response = client.put("/api/v1/survey/survey_123/edit", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Updated Coffee Machine Survey"
            assert data["estimated_time"] == 20
    
    def test_edit_survey_validation_error(self):
        """Test PUT /api/v1/survey/{id}/edit with invalid data"""
        payload = {
            "title": "",  # Empty title should fail
            "description": "Test description"
        }
        
        response = client.put("/api/v1/survey/survey_123/edit", json=payload)
        
        assert response.status_code == 422  # Validation error
    
    def test_get_surveys_list(self):
        """Test GET /api/v1/surveys/ endpoint"""
        with patch('src.services.generation_service.GenerationService.get_surveys') as mock_get_surveys:
            mock_get_surveys.return_value = [
                {
                    "id": "survey_1",
                    "title": "Survey 1",
                    "status": "completed",
                    "created_at": "2024-01-01T00:00:00Z"
                },
                {
                    "id": "survey_2",
                    "title": "Survey 2",
                    "status": "in_progress",
                    "created_at": "2024-01-02T00:00:00Z"
                }
            ]
            
            response = client.get("/api/v1/surveys/")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["title"] == "Survey 1"
            assert data[1]["status"] == "in_progress"
    
    def test_cancel_survey_generation(self):
        """Test POST /api/v1/survey/{id}/cancel endpoint"""
        with patch('src.services.generation_service.GenerationService.cancel_survey_generation') as mock_cancel:
            mock_cancel.return_value = {
                "survey_id": "survey_123",
                "status": "cancelled",
                "message": "Survey generation cancelled"
            }
            
            response = client.post("/api/v1/survey/survey_123/cancel")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "cancelled"
    
    def test_cancel_survey_generation_not_found(self):
        """Test POST /api/v1/survey/{id}/cancel with non-existent ID"""
        with patch('src.services.generation_service.GenerationService.cancel_survey_generation') as mock_cancel:
            mock_cancel.return_value = None
            
            response = client.post("/api/v1/survey/nonexistent/cancel")
            
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()
    
    def test_survey_generation_error_handling(self):
        """Test error handling during survey generation"""
        with patch('src.services.generation_service.GenerationService.generate_survey') as mock_generate:
            mock_generate.side_effect = Exception("Generation service unavailable")
            
            payload = {
                "description": "Test RFQ",
                "title": "Test Survey"
            }
            
            response = client.post("/api/v1/rfq/", json=payload)
            
            assert response.status_code == 500
            assert "error" in response.json()


if __name__ == "__main__":
    pytest.main([__file__])
