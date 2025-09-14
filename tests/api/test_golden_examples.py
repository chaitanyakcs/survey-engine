"""
Standardized tests for Golden Examples API endpoints
"""
import pytest
from tests.base import BaseAPITest, TestDataFactory


@pytest.mark.api
class TestGoldenExamplesAPI(BaseAPITest):
    """Test suite for Golden Examples API endpoints"""
    
    def test_get_golden_examples_success(self):
        """Test successful retrieval of golden examples"""
        client = self.create_test_client()
        
        # Mock service response
        with patch('src.services.golden_service.GoldenService.get_all_golden_pairs') as mock_get_all:
            mock_data = [
                self.create_mock_golden_pair(id="1"),
                self.create_mock_golden_pair(id="2", title="Another Golden Pair")
            ]
            mock_get_all.return_value = mock_data
            
            response = client.get("/api/v1/golden-pairs/")
            
            self.assert_response_structure(response, 200, ["id", "title", "rfq_text"])
            data = response.json()
            assert len(data) == 2
            assert data[0]["id"] == "1"
            assert data[1]["title"] == "Another Golden Pair"
    
    def test_get_golden_examples_empty(self):
        """Test retrieval when no golden examples exist"""
        client = self.create_test_client()
        
        with patch('src.services.golden_service.GoldenService.get_all_golden_pairs') as mock_get_all:
            mock_get_all.return_value = []
            
            response = client.get("/api/v1/golden-pairs/")
            
            self.assert_response_structure(response, 200)
            assert response.json() == []
    
    def test_get_golden_example_by_id_success(self):
        """Test successful retrieval of specific golden example"""
        client = self.create_test_client()
        
        with patch('src.services.golden_service.GoldenService.get_golden_pair_by_id') as mock_get_by_id:
            mock_data = self.create_mock_golden_pair(id="test_123")
            mock_get_by_id.return_value = mock_data
            
            response = client.get("/api/v1/golden-pairs/test_123")
            
            self.assert_response_structure(response, 200, ["id", "title", "rfq_text", "survey_json"])
            data = response.json()
            assert data["id"] == "test_123"
    
    def test_get_golden_example_by_id_not_found(self):
        """Test retrieval of non-existent golden example"""
        client = self.create_test_client()
        
        with patch('src.services.golden_service.GoldenService.get_golden_pair_by_id') as mock_get_by_id:
            mock_get_by_id.return_value = None
            
            response = client.get("/api/v1/golden-pairs/nonexistent")
            
            self.assert_response_structure(response, 404)
            assert "not found" in response.json()["detail"].lower()
    
    def test_create_golden_example_success(self):
        """Test successful creation of golden example"""
        client = self.create_test_client()
        
        with patch('src.services.golden_service.GoldenService.create_golden_pair') as mock_create:
            mock_response = self.create_mock_golden_pair(id="new_123")
            mock_create.return_value = mock_response
            
            payload = {
                "title": "New Golden Pair",
                "rfq_text": "Test RFQ for pricing research",
                "survey_json": {"questions": []},
                "methodology_tags": ["van_westendorp"],
                "industry_category": "consumer_goods",
                "research_goal": "pricing_research",
                "quality_score": 0.85
            }
            
            response = client.post("/api/v1/golden-pairs/", json=payload)
            
            self.assert_response_structure(response, 200, ["id", "title"])
            data = response.json()
            assert data["title"] == "New Golden Pair"
            mock_create.assert_called_once()
    
    def test_create_golden_example_validation_error(self):
        """Test creation with invalid data"""
        client = self.create_test_client()
        
        # Test empty title
        payload = {
            "title": "",  # Invalid: empty title
            "rfq_text": "Test RFQ",
            "survey_json": {"questions": []}
        }
        
        response = client.post("/api/v1/golden-pairs/", json=payload)
        self.assert_response_structure(response, 422)
    
    def test_create_golden_example_missing_required_fields(self):
        """Test creation with missing required fields"""
        client = self.create_test_client()
        
        # Test missing rfq_text
        payload = {
            "title": "Test Survey",
            "survey_json": {"questions": []}
            # Missing rfq_text
        }
        
        response = client.post("/api/v1/golden-pairs/", json=payload)
        self.assert_response_structure(response, 422)
    
    def test_update_golden_example_success(self):
        """Test successful update of golden example"""
        client = self.create_test_client()
        
        with patch('src.services.golden_service.GoldenService.update_golden_pair') as mock_update:
            mock_response = self.create_mock_golden_pair(
                id="test_123",
                title="Updated Golden Pair"
            )
            mock_update.return_value = mock_response
            
            payload = {
                "title": "Updated Golden Pair",
                "rfq_text": "Updated RFQ text",
                "survey_json": {"questions": []},
                "methodology_tags": ["maxdiff"],
                "industry_category": "technology",
                "research_goal": "feature_prioritization",
                "quality_score": 0.95
            }
            
            response = client.put("/api/v1/golden-pairs/test_123", json=payload)
            
            self.assert_response_structure(response, 200, ["id", "title"])
            data = response.json()
            assert data["title"] == "Updated Golden Pair"
            mock_update.assert_called_once()
    
    def test_update_golden_example_not_found(self):
        """Test update of non-existent golden example"""
        client = self.create_test_client()
        
        with patch('src.services.golden_service.GoldenService.update_golden_pair') as mock_update:
            mock_update.return_value = None
            
            payload = {
                "title": "Updated Golden Pair",
                "rfq_text": "Updated RFQ text",
                "survey_json": {"questions": []}
            }
            
            response = client.put("/api/v1/golden-pairs/nonexistent", json=payload)
            
            self.assert_response_structure(response, 404)
            assert "not found" in response.json()["detail"].lower()
    
    def test_delete_golden_example_success(self):
        """Test successful deletion of golden example"""
        client = self.create_test_client()
        
        with patch('src.services.golden_service.GoldenService.delete_golden_pair') as mock_delete:
            mock_delete.return_value = True
            
            response = client.delete("/api/v1/golden-pairs/test_123")
            
            self.assert_response_structure(response, 200)
            data = response.json()
            assert "deleted successfully" in data["message"]
            mock_delete.assert_called_once_with("test_123")
    
    def test_delete_golden_example_not_found(self):
        """Test deletion of non-existent golden example"""
        client = self.create_test_client()
        
        with patch('src.services.golden_service.GoldenService.delete_golden_pair') as mock_delete:
            mock_delete.return_value = False
            
            response = client.delete("/api/v1/golden-pairs/nonexistent")
            
            self.assert_response_structure(response, 404)
            assert "not found" in response.json()["detail"].lower()
    
    def test_parse_document_success(self):
        """Test successful document parsing"""
        client = self.create_test_client()
        
        with patch('src.services.document_parser.DocumentParser.parse_document') as mock_parse:
            mock_parse.return_value = {
                "extracted_text": "Sample extracted text from DOCX",
                "survey_data": {
                    "questions": [
                        TestDataFactory.create_question("single_choice")
                    ]
                }
            }
            
            files = {
                "file": (
                    "test.docx",
                    b"mock docx content",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            }
            
            response = client.post("/api/v1/golden-pairs/parse-document", files=files)
            
            self.assert_response_structure(response, 200, ["extracted_text", "survey_data"])
            data = response.json()
            assert "Sample extracted text from DOCX" in data["extracted_text"]
            assert len(data["survey_data"]["questions"]) == 1
    
    def test_parse_document_invalid_file_type(self):
        """Test document parsing with invalid file type"""
        client = self.create_test_client()
        
        files = {
            "file": ("test.txt", b"plain text content", "text/plain")
        }
        
        response = client.post("/api/v1/golden-pairs/parse-document", files=files)
        
        self.assert_response_structure(response, 422)
        assert "DOCX" in response.json()["detail"]
    
    def test_parse_document_parsing_error(self):
        """Test document parsing with parsing error"""
        client = self.create_test_client()
        
        with patch('src.services.document_parser.DocumentParser.parse_document') as mock_parse:
            mock_parse.side_effect = Exception("Parsing failed")
            
            files = {
                "file": (
                    "test.docx",
                    b"corrupted docx content",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            }
            
            response = client.post("/api/v1/golden-pairs/parse-document", files=files)
            
            self.assert_response_structure(response, 500)
            assert "Failed to parse document" in response.json()["detail"]
    
    def test_golden_examples_pagination(self):
        """Test golden examples with pagination parameters"""
        client = self.create_test_client()
        
        with patch('src.services.golden_service.GoldenService.get_all_golden_pairs') as mock_get_all:
            mock_data = [self.create_mock_golden_pair(id=f"id_{i}") for i in range(5)]
            mock_get_all.return_value = mock_data
            
            # Test with limit parameter
            response = client.get("/api/v1/golden-pairs/?limit=3")
            
            self.assert_response_structure(response, 200)
            # Note: Actual pagination implementation would need to be added to the service
    
    def test_golden_examples_filtering(self):
        """Test golden examples with filtering parameters"""
        client = self.create_test_client()
        
        with patch('src.services.golden_service.GoldenService.get_all_golden_pairs') as mock_get_all:
            mock_data = [
                self.create_mock_golden_pair(
                    id="1",
                    methodology_tags=["van_westendorp"],
                    industry_category="consumer_goods"
                ),
                self.create_mock_golden_pair(
                    id="2",
                    methodology_tags=["conjoint"],
                    industry_category="technology"
                )
            ]
            mock_get_all.return_value = mock_data
            
            # Test with methodology filter
            response = client.get("/api/v1/golden-pairs/?methodology=van_westendorp")
            
            self.assert_response_structure(response, 200)
            # Note: Actual filtering implementation would need to be added to the service


if __name__ == "__main__":
    pytest.main([__file__])
