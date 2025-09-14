"""
Standardized tests for Survey Generation API endpoints
"""
import pytest
from unittest.mock import patch
from tests.base import BaseAPITest, TestDataFactory


@pytest.mark.api
class TestSurveyGenerationAPI(BaseAPITest):
    """Test suite for Survey Generation API endpoints"""
    
    def test_submit_rfq_success(self):
        """Test successful RFQ submission"""
        client = self.create_test_client()
        
        with patch('src.services.generation_service.GenerationService.generate_survey') as mock_generate:
            mock_generate.return_value = {
                "survey_id": "survey_123",
                "workflow_id": "workflow_456",
                "status": "started",
                "message": "Survey generation started"
            }
            
            payload = self.create_mock_rfq_request()
            response = client.post("/api/v1/rfq/", json=payload)
            
            self.assert_response_structure(response, 200, ["survey_id", "workflow_id", "status"])
            data = response.json()
            assert data["survey_id"] == "survey_123"
            assert data["status"] == "started"
            mock_generate.assert_called_once()
    
    def test_submit_rfq_validation_error(self):
        """Test RFQ submission with invalid data"""
        client = self.create_test_client()
        
        # Test empty description
        payload = {
            "description": "",  # Invalid: empty description
            "title": "Test Survey"
        }
        
        response = client.post("/api/v1/rfq/", json=payload)
        self.assert_response_structure(response, 422)
    
    def test_submit_rfq_missing_required_fields(self):
        """Test RFQ submission with missing required fields"""
        client = self.create_test_client()
        
        # Test missing description
        payload = {
            "title": "Test Survey"
            # Missing description
        }
        
        response = client.post("/api/v1/rfq/", json=payload)
        self.assert_response_structure(response, 422)
    
    def test_get_survey_status_success(self):
        """Test successful survey status retrieval"""
        client = self.create_test_client()
        
        with patch('src.services.generation_service.GenerationService.get_survey_status') as mock_status:
            mock_status.return_value = {
                "survey_id": "survey_123",
                "status": "completed",
                "progress": 100,
                "current_step": "finalized",
                "message": "Survey generation completed"
            }
            
            response = client.get("/api/v1/survey/survey_123/status")
            
            self.assert_response_structure(response, 200, ["survey_id", "status", "progress"])
            data = response.json()
            assert data["status"] == "completed"
            assert data["progress"] == 100
    
    def test_get_survey_status_not_found(self):
        """Test survey status retrieval for non-existent survey"""
        client = self.create_test_client()
        
        with patch('src.services.generation_service.GenerationService.get_survey_status') as mock_status:
            mock_status.return_value = None
            
            response = client.get("/api/v1/survey/nonexistent/status")
            
            self.assert_response_structure(response, 404)
            assert "not found" in response.json()["detail"].lower()
    
    def test_get_survey_result_success(self):
        """Test successful survey result retrieval"""
        client = self.create_test_client()
        
        with patch('src.services.generation_service.GenerationService.get_survey_result') as mock_result:
            mock_survey = self.create_mock_survey(id="survey_123")
            mock_result.return_value = mock_survey
            
            response = client.get("/api/v1/survey/survey_123")
            
            self.assert_response_structure(response, 200, ["id", "title", "questions"])
            data = response.json()
            assert data["id"] == "survey_123"
            assert len(data["questions"]) == 2
    
    def test_get_survey_result_not_found(self):
        """Test survey result retrieval for non-existent survey"""
        client = self.create_test_client()
        
        with patch('src.services.generation_service.GenerationService.get_survey_result') as mock_result:
            mock_result.return_value = None
            
            response = client.get("/api/v1/survey/nonexistent")
            
            self.assert_response_structure(response, 404)
            assert "not found" in response.json()["detail"].lower()
    
    def test_edit_survey_success(self):
        """Test successful survey editing"""
        client = self.create_test_client()
        
        with patch('src.services.generation_service.GenerationService.edit_survey') as mock_edit:
            mock_response = self.create_mock_survey(
                id="survey_123",
                title="Updated Survey",
                estimated_time=20
            )
            mock_edit.return_value = mock_response
            
            payload = {
                "title": "Updated Survey",
                "description": "Updated description",
                "questions": [],
                "estimated_time": 20,
                "target_responses": 250
            }
            
            response = client.put("/api/v1/survey/survey_123/edit", json=payload)
            
            self.assert_response_structure(response, 200, ["id", "title"])
            data = response.json()
            assert data["title"] == "Updated Survey"
            assert data["estimated_time"] == 20
            mock_edit.assert_called_once()
    
    def test_edit_survey_validation_error(self):
        """Test survey editing with invalid data"""
        client = self.create_test_client()
        
        # Test empty title
        payload = {
            "title": "",  # Invalid: empty title
            "description": "Test description"
        }
        
        response = client.put("/api/v1/survey/survey_123/edit", json=payload)
        self.assert_response_structure(response, 422)
    
    def test_edit_survey_not_found(self):
        """Test editing non-existent survey"""
        client = self.create_test_client()
        
        with patch('src.services.generation_service.GenerationService.edit_survey') as mock_edit:
            mock_edit.return_value = None
            
            payload = {
                "title": "Updated Survey",
                "description": "Updated description"
            }
            
            response = client.put("/api/v1/survey/nonexistent/edit", json=payload)
            
            self.assert_response_structure(response, 404)
            assert "not found" in response.json()["detail"].lower()
    
    def test_get_surveys_list_success(self):
        """Test successful surveys list retrieval"""
        client = self.create_test_client()
        
        with patch('src.services.generation_service.GenerationService.get_surveys') as mock_get_surveys:
            mock_surveys = [
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
            mock_get_surveys.return_value = mock_surveys
            
            response = client.get("/api/v1/surveys/")
            
            self.assert_response_structure(response, 200)
            data = response.json()
            assert len(data) == 2
            assert data[0]["title"] == "Survey 1"
            assert data[1]["status"] == "in_progress"
    
    def test_get_surveys_list_empty(self):
        """Test surveys list retrieval when no surveys exist"""
        client = self.create_test_client()
        
        with patch('src.services.generation_service.GenerationService.get_surveys') as mock_get_surveys:
            mock_get_surveys.return_value = []
            
            response = client.get("/api/v1/surveys/")
            
            self.assert_response_structure(response, 200)
            assert response.json() == []
    
    def test_cancel_survey_generation_success(self):
        """Test successful survey generation cancellation"""
        client = self.create_test_client()
        
        with patch('src.services.generation_service.GenerationService.cancel_survey_generation') as mock_cancel:
            mock_cancel.return_value = {
                "survey_id": "survey_123",
                "status": "cancelled",
                "message": "Survey generation cancelled"
            }
            
            response = client.post("/api/v1/survey/survey_123/cancel")
            
            self.assert_response_structure(response, 200, ["survey_id", "status"])
            data = response.json()
            assert data["status"] == "cancelled"
            mock_cancel.assert_called_once_with("survey_123")
    
    def test_cancel_survey_generation_not_found(self):
        """Test cancellation of non-existent survey"""
        client = self.create_test_client()
        
        with patch('src.services.generation_service.GenerationService.cancel_survey_generation') as mock_cancel:
            mock_cancel.return_value = None
            
            response = client.post("/api/v1/survey/nonexistent/cancel")
            
            self.assert_response_structure(response, 404)
            assert "not found" in response.json()["detail"].lower()
    
    def test_survey_generation_error_handling(self):
        """Test error handling during survey generation"""
        client = self.create_test_client()
        
        with patch('src.services.generation_service.GenerationService.generate_survey') as mock_generate:
            mock_generate.side_effect = Exception("Generation service unavailable")
            
            payload = self.create_mock_rfq_request()
            response = client.post("/api/v1/rfq/", json=payload)
            
            self.assert_response_structure(response, 500)
            assert "error" in response.json()
    
    def test_survey_generation_timeout(self):
        """Test survey generation timeout handling"""
        client = self.create_test_client()
        
        with patch('src.services.generation_service.GenerationService.generate_survey') as mock_generate:
            mock_generate.side_effect = TimeoutError("Generation timeout")
            
            payload = self.create_mock_rfq_request()
            response = client.post("/api/v1/rfq/", json=payload)
            
            self.assert_response_structure(response, 500)
            assert "timeout" in response.json()["error"].lower()
    
    def test_survey_generation_progress_tracking(self):
        """Test survey generation progress tracking"""
        client = self.create_test_client()
        
        # Test different progress states
        progress_states = [
            {"status": "started", "progress": 0, "current_step": "initializing"},
            {"status": "in_progress", "progress": 50, "current_step": "generating_questions"},
            {"status": "in_progress", "progress": 90, "current_step": "finalizing"},
            {"status": "completed", "progress": 100, "current_step": "finalized"}
        ]
        
        with patch('src.services.generation_service.GenerationService.get_survey_status') as mock_status:
            for state in progress_states:
                mock_status.return_value = {
                    "survey_id": "survey_123",
                    **state,
                    "message": f"Survey generation {state['status']}"
                }
                
                response = client.get("/api/v1/survey/survey_123/status")
                
                self.assert_response_structure(response, 200, ["status", "progress", "current_step"])
                data = response.json()
                assert data["status"] == state["status"]
                assert data["progress"] == state["progress"]
                assert data["current_step"] == state["current_step"]
    
    def test_survey_generation_with_different_methodologies(self):
        """Test survey generation with different methodology requirements"""
        client = self.create_test_client()
        
        test_cases = [
            {
                "rfq": "We need a Van Westendorp pricing study for coffee machines",
                "expected_methodology": ["van_westendorp"]
            },
            {
                "rfq": "We need a conjoint analysis for software features",
                "expected_methodology": ["conjoint_analysis"]
            },
            {
                "rfq": "We need a MaxDiff study for brand preferences",
                "expected_methodology": ["maxdiff"]
            }
        ]
        
        with patch('src.services.generation_service.GenerationService.generate_survey') as mock_generate:
            for case in test_cases:
                mock_generate.return_value = {
                    "survey_id": f"survey_{case['expected_methodology'][0]}",
                    "workflow_id": "workflow_123",
                    "status": "started"
                }
                
                payload = {
                    "description": case["rfq"],
                    "title": f"Test {case['expected_methodology'][0]} Survey"
                }
                
                response = client.post("/api/v1/rfq/", json=payload)
                
                self.assert_response_structure(response, 200)
                # Note: Actual methodology validation would need to be implemented in the service


if __name__ == "__main__":
    pytest.main([__file__])
