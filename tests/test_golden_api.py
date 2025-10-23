import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.main import app

client = TestClient(app)


class TestGoldenExamplesAPI:
    """Test suite for Golden Examples API endpoints"""
    
    def test_get_golden_examples(self):
        """Test GET /api/v1/golden-pairs/ endpoint"""
        with patch('src.services.golden_service.GoldenService.get_all_golden_pairs') as mock_get_all:
            mock_get_all.return_value = [
                {
                    "id": "1",
                    "title": "Test Golden Pair",
                    "rfq_text": "Test RFQ",
                    "survey_json": {"questions": []},
                    "methodology_tags": ["vw"],
                    "industry_category": "tech",
                    "research_goal": "pricing",
                    "quality_score": 0.9,
                    "created_at": "2024-01-01T00:00:00Z"
                }
            ]
            
            response = client.get("/api/v1/golden-pairs/")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["title"] == "Test Golden Pair"
            assert data[0]["methodology_tags"] == ["vw"]
    
    def test_get_golden_example_by_id(self):
        """Test GET /api/v1/golden-pairs/{id} endpoint"""
        with patch('src.services.golden_service.GoldenService.get_golden_pair_by_id') as mock_get_by_id:
            mock_get_by_id.return_value = {
                "id": "1",
                "title": "Test Golden Pair",
                "rfq_text": "Test RFQ",
                "survey_json": {"questions": []},
                "methodology_tags": ["vw"],
                "industry_category": "tech",
                "research_goal": "pricing",
                "quality_score": 0.9
            }
            
            response = client.get("/api/v1/golden-pairs/1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "1"
            assert data["title"] == "Test Golden Pair"
    
    def test_get_golden_example_not_found(self):
        """Test GET /api/v1/golden-pairs/{id} with non-existent ID"""
        with patch('src.services.golden_service.GoldenService.get_golden_pair_by_id') as mock_get_by_id:
            mock_get_by_id.return_value = None
            
            response = client.get("/api/v1/golden-pairs/999")
            
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()
    
    def test_create_golden_example(self):
        """Test POST /api/v1/golden-pairs/ endpoint"""
        with patch('src.services.golden_service.GoldenService.create_golden_pair') as mock_create:
            mock_create.return_value = {
                "id": "1",
                "title": "New Golden Pair",
                "rfq_text": "New RFQ",
                "survey_json": {"questions": []},
                "methodology_tags": ["conjoint"],
                "industry_category": "retail",
                "research_goal": "feature_prioritization",
                "quality_score": 0.85
            }
            
            payload = {
                "title": "New Golden Pair",
                "rfq_text": "New RFQ",
                "survey_json": {"questions": []},
                "methodology_tags": ["conjoint"],
                "industry_category": "retail",
                "research_goal": "feature_prioritization",
                "quality_score": 0.85
            }
            
            response = client.post("/api/v1/golden-pairs/", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "New Golden Pair"
            assert data["methodology_tags"] == ["conjoint"]
    
    def test_create_golden_example_with_empty_title_handling(self):
        """Test POST /api/v1/golden-pairs/ with empty title - should generate fallback title"""
        with patch('src.services.embedding_service.EmbeddingService.is_ready', return_value=True), \
             patch('src.services.model_loader.BackgroundModelLoader.is_ready', return_value=True), \
             patch('src.services.golden_service.GoldenService.create_golden_pair') as mock_create:
            # Create a mock object that behaves like a GoldenRFQSurveyPair
            mock_golden_pair = MagicMock()
            mock_golden_pair.id = "1"
            mock_golden_pair.title = "General Survey Survey"  # Fallback title generated
            mock_golden_pair.rfq_text = "Test RFQ"
            mock_golden_pair.survey_json = {"questions": []}
            mock_golden_pair.methodology_tags = []
            mock_golden_pair.industry_category = None
            mock_golden_pair.research_goal = None
            mock_golden_pair.quality_score = 0.85
            mock_golden_pair.usage_count = 0
            mock_create.return_value = mock_golden_pair
            
            payload = {
                "title": "",  # Empty title
                "rfq_text": "Test RFQ",
                "survey_json": {"questions": []},  # No title in survey JSON either
                "methodology_tags": None,
                "industry_category": None,
                "research_goal": None,
                "quality_score": 0.85
            }
            
            response = client.post("/api/v1/golden-pairs/", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            # Should not be empty or "Untitled Survey"
            assert data["title"] is not None
            assert data["title"] != ""
            assert data["title"] != "Untitled Survey"
    
    def test_create_golden_example_with_survey_title(self):
        """Test POST /api/v1/golden-pairs/ with title in survey JSON"""
        with patch('src.services.embedding_service.EmbeddingService.is_ready', return_value=True), \
             patch('src.services.model_loader.BackgroundModelLoader.is_ready', return_value=True), \
             patch('src.services.golden_service.GoldenService.create_golden_pair') as mock_create:
            # Create a mock object that behaves like a GoldenRFQSurveyPair
            mock_golden_pair = MagicMock()
            mock_golden_pair.id = "1"
            mock_golden_pair.title = "Survey Title from JSON"
            mock_golden_pair.rfq_text = "Test RFQ"
            mock_golden_pair.survey_json = {"title": "Survey Title from JSON", "questions": []}
            mock_golden_pair.methodology_tags = ["van_westendorp"]
            mock_golden_pair.industry_category = "tech"
            mock_golden_pair.research_goal = "pricing"
            mock_golden_pair.quality_score = 0.85
            mock_golden_pair.usage_count = 0
            mock_create.return_value = mock_golden_pair
            
            payload = {
                "title": None,  # No golden pair title
                "rfq_text": "Test RFQ",
                "survey_json": {"title": "Survey Title from JSON", "questions": []},
                "methodology_tags": ["van_westendorp"],
                "industry_category": "tech",
                "research_goal": "pricing",
                "quality_score": 0.85
            }
            
            response = client.post("/api/v1/golden-pairs/", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Survey Title from JSON"
    
    def test_create_golden_example_with_industry_methodology_fallback(self):
        """Test POST /api/v1/golden-pairs/ with industry and methodology for fallback title"""
        with patch('src.services.embedding_service.EmbeddingService.is_ready', return_value=True), \
             patch('src.services.model_loader.BackgroundModelLoader.is_ready', return_value=True), \
             patch('src.services.golden_service.GoldenService.create_golden_pair') as mock_create:
            # Create a mock object that behaves like a GoldenRFQSurveyPair
            mock_golden_pair = MagicMock()
            mock_golden_pair.id = "1"
            mock_golden_pair.title = "Healthcare van_westendorp Survey"
            mock_golden_pair.rfq_text = "Test RFQ"
            mock_golden_pair.survey_json = {"questions": []}
            mock_golden_pair.methodology_tags = ["van_westendorp"]
            mock_golden_pair.industry_category = "Healthcare"
            mock_golden_pair.research_goal = "pricing"
            mock_golden_pair.quality_score = 0.85
            mock_golden_pair.usage_count = 0
            mock_create.return_value = mock_golden_pair
            
            payload = {
                "title": None,  # No golden pair title
                "rfq_text": "Test RFQ",
                "survey_json": {"questions": []},  # No title in survey JSON
                "methodology_tags": ["van_westendorp"],
                "industry_category": "Healthcare",
                "research_goal": "pricing",
                "quality_score": 0.85
            }
            
            response = client.post("/api/v1/golden-pairs/", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            # Should generate meaningful fallback title
            assert "Healthcare" in data["title"]
            assert "van_westendorp" in data["title"]
            assert "Survey" in data["title"]

    def test_create_golden_example_validation_error(self):
        """Test POST /api/v1/golden-pairs/ with invalid data - should still work with our new handling"""
        payload = {
            "title": "",  # Empty title - should be handled gracefully now
            "rfq_text": "Test RFQ",
            "survey_json": {"questions": []}
        }
        
        with patch('src.services.embedding_service.EmbeddingService.is_ready', return_value=True), \
             patch('src.services.model_loader.BackgroundModelLoader.is_ready', return_value=True), \
             patch('src.services.golden_service.GoldenService.create_golden_pair') as mock_create:
            # Create a mock object that behaves like a GoldenRFQSurveyPair
            mock_golden_pair = MagicMock()
            mock_golden_pair.id = "1"
            mock_golden_pair.title = "General Survey Survey"  # Fallback title
            mock_golden_pair.rfq_text = "Test RFQ"
            mock_golden_pair.survey_json = {"questions": []}
            mock_golden_pair.methodology_tags = []
            mock_golden_pair.industry_category = None
            mock_golden_pair.research_goal = None
            mock_golden_pair.quality_score = 0.85
            mock_golden_pair.usage_count = 0
            mock_create.return_value = mock_golden_pair
            
            response = client.post("/api/v1/golden-pairs/", json=payload)
            
            assert response.status_code == 200  # Should succeed with fallback title
            data = response.json()
            assert data["title"] is not None
            assert data["title"] != ""
    
    def test_update_golden_example(self):
        """Test PUT /api/v1/golden-pairs/{id} endpoint"""
        with patch('src.services.golden_service.GoldenService.update_golden_pair') as mock_update:
            mock_update.return_value = {
                "id": "1",
                "title": "Updated Golden Pair",
                "rfq_text": "Updated RFQ",
                "survey_json": {"questions": []},
                "methodology_tags": ["maxdiff"],
                "industry_category": "finance",
                "research_goal": "brand_perception",
                "quality_score": 0.95
            }
            
            payload = {
                "title": "Updated Golden Pair",
                "rfq_text": "Updated RFQ",
                "survey_json": {"questions": []},
                "methodology_tags": ["maxdiff"],
                "industry_category": "finance",
                "research_goal": "brand_perception",
                "quality_score": 0.95
            }
            
            response = client.put("/api/v1/golden-pairs/1", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Updated Golden Pair"
            assert data["methodology_tags"] == ["maxdiff"]
    
    def test_delete_golden_example(self):
        """Test DELETE /api/v1/golden-pairs/{id} endpoint"""
        with patch('src.services.golden_service.GoldenService.delete_golden_pair') as mock_delete:
            mock_delete.return_value = True
            
            response = client.delete("/api/v1/golden-pairs/1")
            
            assert response.status_code == 200
            assert response.json()["message"] == "Golden pair deleted successfully"
    
    def test_delete_golden_example_not_found(self):
        """Test DELETE /api/v1/golden-pairs/{id} with non-existent ID"""
        with patch('src.services.golden_service.GoldenService.delete_golden_pair') as mock_delete:
            mock_delete.return_value = False
            
            response = client.delete("/api/v1/golden-pairs/999")
            
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()
    
    def test_parse_document_endpoint(self):
        """Test POST /api/v1/golden-pairs/parse-document endpoint"""
        with patch('src.services.document_parser.DocumentParser.parse_document') as mock_parse:
            mock_parse.return_value = {
                "extracted_text": "Sample extracted text from DOCX",
                "survey_data": {
                    "questions": [
                        {"text": "What is your age?", "type": "single_choice", "options": ["18-24", "25-34"]}
                    ]
                }
            }
            
            # Create a mock file
            files = {"file": ("test.docx", b"mock docx content", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            
            response = client.post("/api/v1/golden-pairs/parse-document", files=files)
            
            assert response.status_code == 200
            data = response.json()
            assert "extracted_text" in data
            assert "survey_data" in data
            assert len(data["survey_data"]["questions"]) == 1
    
    def test_parse_document_invalid_file_type(self):
        """Test POST /api/v1/golden-pairs/parse-document with invalid file type"""
        files = {"file": ("test.txt", b"plain text content", "text/plain")}
        
        response = client.post("/api/v1/golden-pairs/parse-document", files=files)
        
        assert response.status_code == 422
        assert "DOCX" in response.json()["detail"]
    
    def test_parse_document_parsing_error(self):
        """Test POST /api/v1/golden-pairs/parse-document with parsing error"""
        with patch('src.services.document_parser.DocumentParser.parse_document') as mock_parse:
            mock_parse.side_effect = Exception("Parsing failed")
            
            files = {"file": ("test.docx", b"corrupted docx content", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            
            response = client.post("/api/v1/golden-pairs/parse-document", files=files)
            
            assert response.status_code == 500
            assert "Failed to parse document" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__])

