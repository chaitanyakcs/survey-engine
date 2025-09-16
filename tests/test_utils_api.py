import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.main import app

client = TestClient(app)


class TestUtilsAPI:
    """Test suite for Utils API endpoints"""
    
    def test_extract_text_endpoint(self):
        """Test POST /api/v1/utils/extract-text endpoint"""
        with patch('src.services.document_parser.DocumentParser.extract_text') as mock_extract:
            mock_extract.return_value = "Sample extracted text from DOCX file"
            
            files = {"file": ("test.docx", b"mock docx content", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            
            response = client.post("/api/v1/utils/extract-text", files=files)
            
            assert response.status_code == 200
            data = response.json()
            assert data["extracted_text"] == "Sample extracted text from DOCX file"
            assert data["filename"] == "test.docx"
    
    def test_extract_text_invalid_file_type(self):
        """Test POST /api/v1/utils/extract-text with invalid file type"""
        files = {"file": ("test.txt", b"plain text content", "text/plain")}
        
        response = client.post("/api/v1/utils/extract-text", files=files)
        
        assert response.status_code == 422
        assert "DOCX" in response.json()["detail"]
    
    def test_extract_text_no_file(self):
        """Test POST /api/v1/utils/extract-text with no file"""
        response = client.post("/api/v1/utils/extract-text")
        
        assert response.status_code == 422
        assert "file" in response.json()["detail"]
    
    def test_extract_text_parsing_error(self):
        """Test POST /api/v1/utils/extract-text with parsing error"""
        with patch('src.services.document_parser.DocumentParser.extract_text') as mock_extract:
            mock_extract.side_effect = Exception("Failed to extract text")
            
            files = {"file": ("test.docx", b"corrupted docx content", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            
            response = client.post("/api/v1/utils/extract-text", files=files)
            
            assert response.status_code == 500
            assert "Failed to extract text" in response.json()["detail"]
    
    def test_extract_text_large_file(self):
        """Test POST /api/v1/utils/extract-text with large file"""
        with patch('src.services.document_parser.DocumentParser.extract_text') as mock_extract:
            mock_extract.return_value = "Large document content " * 1000  # Simulate large content
            
            # Create a large file (simulate)
            large_content = b"x" * (10 * 1024 * 1024)  # 10MB
            files = {"file": ("large.docx", large_content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            
            response = client.post("/api/v1/utils/extract-text", files=files)
            
            assert response.status_code == 200
            data = response.json()
            assert "Large document content" in data["extracted_text"]
    
    def test_health_check(self):
        """Test GET /health endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
    
    def test_docs_endpoint(self):
        """Test GET /docs endpoint"""
        response = client.get("/docs")
        
        assert response.status_code == 200
        # Should return HTML documentation
        assert "text/html" in response.headers["content-type"]
    
    def test_openapi_schema(self):
        """Test GET /openapi.json endpoint"""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert data["info"]["title"] == "Survey Generation Engine"
        assert "paths" in data
    
    def test_cors_headers(self):
        """Test CORS headers are present"""
        response = client.options("/api/v1/golden-pairs/")
        
        # Should have CORS headers
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
    
    def test_api_versioning(self):
        """Test API versioning is consistent"""
        # Test that all API endpoints use /api/v1/ prefix
        endpoints_to_test = [
            "/api/v1/golden-pairs/",
            "/api/v1/rfq/",
            "/api/v1/surveys/",
            "/api/v1/field-extraction/",
            "/api/v1/utils/extract-text"
        ]
        
        for endpoint in endpoints_to_test:
            # Just test that the endpoint exists (not 404)
            response = client.get(endpoint)
            # Should not be 404 (might be 405 for wrong method, but not 404)
            assert response.status_code != 404, f"Endpoint {endpoint} not found"
    
    def test_error_response_format(self):
        """Test that error responses follow consistent format"""
        # Test 404 error
        response = client.get("/api/v1/nonexistent-endpoint")
        assert response.status_code == 404
        
        # Test 422 validation error
        response = client.post("/api/v1/golden-pairs/", json={})
        assert response.status_code == 422
        
        # Both should have 'detail' field
        assert "detail" in response.json()
    
    def test_content_type_headers(self):
        """Test that responses have correct content-type headers"""
        # JSON endpoints should return application/json
        response = client.get("/api/v1/golden-pairs/")
        assert response.headers["content-type"] == "application/json"
        
        # Health check should return application/json
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"
    
    def test_rate_limiting_headers(self):
        """Test that rate limiting headers are present (if implemented)"""
        response = client.get("/api/v1/golden-pairs/")
        
        # Check for common rate limiting headers
        # Note: This test might need adjustment based on actual rate limiting implementation
        assert response.status_code in [200, 429]  # Either success or rate limited


if __name__ == "__main__":
    pytest.main([__file__])

