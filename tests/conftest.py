"""
Test configuration and fixtures for the survey-engine project
"""
import pytest
import sys
from unittest.mock import MagicMock, patch

# Mock problematic imports before they're imported
sys.modules['docx'] = MagicMock()
sys.modules['replicate'] = MagicMock()
sys.modules['sentence_transformers'] = MagicMock()
sys.modules['langchain'] = MagicMock()
sys.modules['langgraph'] = MagicMock()
sys.modules['pgvector'] = MagicMock()
sys.modules['redis'] = MagicMock()
sys.modules['faiss'] = MagicMock()

# Mock database connection
@pytest.fixture
def mock_db_session():
    """Mock database session for testing"""
    mock_session = MagicMock()
    return mock_session

# Mock settings
@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    with patch('src.config.settings.settings') as mock:
        mock.database_url = "postgresql://test:test@localhost:5432/test_db"
        mock.redis_url = "redis://localhost:6379"
        mock.replicate_api_token = "test_token"
        mock.embedding_model = "all-MiniLM-L6-v2"
        mock.generation_model = "openai/gpt-4"
        mock.golden_similarity_threshold = 0.75
        mock.max_golden_examples = 3
        mock.debug = True
        mock.log_level = "DEBUG"
        yield mock

# Mock external services
@pytest.fixture
def mock_embedding_service():
    """Mock embedding service"""
    with patch('src.services.embedding_service.EmbeddingService') as mock:
        mock_instance = MagicMock()
        mock_instance.get_embedding.return_value = [0.1, 0.2, 0.3]
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_generation_service():
    """Mock generation service"""
    with patch('src.services.generation_service.GenerationService') as mock:
        mock_instance = MagicMock()
        mock_instance.generate_survey.return_value = {
            "survey_id": "test_survey_123",
            "workflow_id": "test_workflow_456",
            "status": "started"
        }
        mock_instance.get_survey_status.return_value = {
            "survey_id": "test_survey_123",
            "status": "completed",
            "progress": 100
        }
        mock_instance.get_survey_result.return_value = {
            "id": "test_survey_123",
            "title": "Test Survey",
            "questions": []
        }
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_golden_service():
    """Mock golden service"""
    with patch('src.services.golden_service.GoldenService') as mock:
        mock_instance = MagicMock()
        mock_instance.get_all_golden_pairs.return_value = []
        mock_instance.get_golden_pair_by_id.return_value = None
        mock_instance.create_golden_pair.return_value = {
            "id": "1",
            "title": "Test Golden Pair"
        }
        mock_instance.update_golden_pair.return_value = {
            "id": "1",
            "title": "Updated Golden Pair"
        }
        mock_instance.delete_golden_pair.return_value = True
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_document_parser():
    """Mock document parser"""
    with patch('src.services.document_parser.DocumentParser') as mock:
        mock_instance = MagicMock()
        mock_instance.extract_text.return_value = "Extracted text from document"
        mock_instance.parse_document.return_value = {
            "extracted_text": "Extracted text from document",
            "survey_data": {"questions": []}
        }
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_field_extraction_service():
    """Mock field extraction service"""
    with patch('src.services.field_extraction_service.FieldExtractionService') as mock:
        mock_instance = MagicMock()
        mock_instance.extract_fields.return_value = {
            "methodology_tags": ["basic_survey"],
            "industry_category": "general",
            "research_goal": "general_research",
            "quality_score": 0.8,
            "suggested_title": "Test Survey",
            "confidence_score": 0.7,
            "reasoning": {},
            "parsing_issues": []
        }
        mock.return_value = mock_instance
        yield mock_instance

