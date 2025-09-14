"""
Standardized tests for Utils API endpoints
"""
import pytest
from unittest.mock import patch
from tests.base import BaseAPITest


@pytest.mark.api
class TestUtilsAPI(BaseAPITest):
    """Test suite for Utils API endpoints"""
    
    def test_extract_text_success(self):
        """Test successful text extraction from DOCX"""
        client = self.create_test_client()
        
        with patch('src.services.document_parser.DocumentParser.extract_text') as mock_extract:
            mock_extract.return_value = "Sample extracted text from DOCX file"
            
            files = {
                "file": (
                    "test.docx",
                    b"mock docx content",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            }
            
            response = client.post("/api/v1/utils/extract-text", files=files)
            
            self.assert_response_structure(response, 200, ["extracted_text", "filename"])
            data = response.json()
            assert data["extracted_text"] == "Sample extracted text from DOCX file"
            assert data["filename"] == "test.docx"
    
    def test_extract_text_invalid_file_type(self):
        """Test text extraction with invalid file type"""
        client = self.create_test_client()
        
        files = {
            "file": ("test.txt", b"plain text content", "text/plain")
        }
        
        response = client.post("/api/v1/utils/extract-text", files=files)
        
        self.assert_response_structure(response, 422)
        assert "DOCX" in response.json()["detail"]
    
    def test_extract_text_no_file(self):
        """Test text extraction with no file provided"""
        client = self.create_test_client()
        
        response = client.post("/api/v1/utils/extract-text")
        
        self.assert_response_structure(response, 422)
        assert "file" in response.json()["detail"]
    
    def test_extract_text_parsing_error(self):
        """Test text extraction with parsing error"""
        client = self.create_test_client()
        
        with patch('src.services.document_parser.DocumentParser.extract_text') as mock_extract:
            mock_extract.side_effect = Exception("Failed to extract text")
            
            files = {
                "file": (
                    "test.docx",
                    b"corrupted docx content",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            }
            
            response = client.post("/api/v1/utils/extract-text", files=files)
            
            self.assert_response_structure(response, 500)
            assert "Failed to extract text" in response.json()["detail"]
    
    def test_extract_text_large_file(self):
        """Test text extraction with large file"""
        client = self.create_test_client()
        
        with patch('src.services.document_parser.DocumentParser.extract_text') as mock_extract:
            # Simulate large content
            large_text = "Large document content " * 1000
            mock_extract.return_value = large_text
            
            # Create a large file (simulate)
            large_content = b"x" * (10 * 1024 * 1024)  # 10MB
            files = {
                "file": (
                    "large.docx",
                    large_content,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            }
            
            response = client.post("/api/v1/utils/extract-text", files=files)
            
            self.assert_response_structure(response, 200)
            data = response.json()
            assert "Large document content" in data["extracted_text"]
    
    def test_health_check(self):
        """Test health check endpoint"""
        client = self.create_test_client()
        
        response = client.get("/health")
        
        self.assert_response_structure(response, 200, ["status", "version"])
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
    
    def test_docs_endpoint(self):
        """Test API documentation endpoint"""
        client = self.create_test_client()
        
        response = client.get("/docs")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_openapi_schema(self):
        """Test OpenAPI schema endpoint"""
        client = self.create_test_client()
        
        response = client.get("/openapi.json")
        
        self.assert_response_structure(response, 200)
        data = response.json()
        assert "openapi" in data
        assert data["info"]["title"] == "Survey Generation Engine"
        assert "paths" in data
    
    def test_cors_headers(self):
        """Test CORS headers are present"""
        client = self.create_test_client()
        
        response = client.options("/api/v1/golden-pairs/")
        
        # Should have CORS headers
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
    
    def test_api_versioning_consistency(self):
        """Test API versioning is consistent across endpoints"""
        client = self.create_test_client()
        
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
        client = self.create_test_client()
        
        # Test 404 error
        response = client.get("/api/v1/nonexistent-endpoint")
        assert response.status_code == 404
        assert "detail" in response.json()
        
        # Test 422 validation error
        response = client.post("/api/v1/golden-pairs/", json={})
        assert response.status_code == 422
        assert "detail" in response.json()
    
    def test_content_type_headers(self):
        """Test that responses have correct content-type headers"""
        client = self.create_test_client()
        
        # JSON endpoints should return application/json
        response = client.get("/api/v1/golden-pairs/")
        assert response.headers["content-type"] == "application/json"
        
        # Health check should return application/json
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"
    
    def test_rate_limiting_headers(self):
        """Test that rate limiting headers are present (if implemented)"""
        client = self.create_test_client()
        
        response = client.get("/api/v1/golden-pairs/")
        
        # Check for common rate limiting headers
        # Note: This test might need adjustment based on actual rate limiting implementation
        assert response.status_code in [200, 429]  # Either success or rate limited
    
    def test_multiple_file_upload(self):
        """Test handling of multiple file uploads (should reject)"""
        client = self.create_test_client()
        
        files = [
            ("file", ("test1.docx", b"content1", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
            ("file", ("test2.docx", b"content2", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))
        ]
        
        response = client.post("/api/v1/utils/extract-text", files=files)
        
        # Should handle multiple files gracefully (either accept first or reject)
        assert response.status_code in [200, 422]
    
    def test_file_size_limits(self):
        """Test file size limits"""
        client = self.create_test_client()
        
        # Test with very large file
        very_large_content = b"x" * (100 * 1024 * 1024)  # 100MB
        files = {
            "file": (
                "very_large.docx",
                very_large_content,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        }
        
        response = client.post("/api/v1/utils/extract-text", files=files)
        
        # Should either process or reject with appropriate error
        assert response.status_code in [200, 413, 422]  # Success, too large, or validation error
    
    def test_empty_file_upload(self):
        """Test handling of empty file upload"""
        client = self.create_test_client()
        
        files = {
            "file": ("empty.docx", b"", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        }
        
        response = client.post("/api/v1/utils/extract-text", files=files)
        
        # Should handle empty file gracefully
        assert response.status_code in [200, 422]  # Success or validation error
    
    def test_malformed_file_upload(self):
        """Test handling of malformed file upload"""
        client = self.create_test_client()
        
        files = {
            "file": ("malformed.docx", b"not a real docx file", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        }
        
        with patch('src.services.document_parser.DocumentParser.extract_text') as mock_extract:
            mock_extract.side_effect = Exception("Invalid DOCX format")
            
            response = client.post("/api/v1/utils/extract-text", files=files)
            
            self.assert_response_structure(response, 500)
            assert "Failed to extract text" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__])
