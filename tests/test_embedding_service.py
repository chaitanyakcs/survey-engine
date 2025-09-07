import pytest
import asyncio
from unittest.mock import patch, MagicMock
from src.services.embedding_service import EmbeddingService

# Configure pytest for async tests
pytestmark = pytest.mark.asyncio


class TestEmbeddingService:
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing"""
        with patch('src.services.embedding_service.settings') as mock:
            mock.embedding_model = "all-MiniLM-L6-v2"
            mock.replicate_api_token = "test_token"
            yield mock
    
    def test_should_use_replicate(self, mock_settings):
        """Test _should_use_replicate detection logic"""
        # Test cases that should use Replicate
        replicate_cases = [
            "text-embedding-ada-002",
            "nateraw/bge-large-en-v1.5", 
            "replicate:some-model",
            "sentence-transformers/all-mpnet-base-v2"
        ]
        
        for model_name in replicate_cases:
            mock_settings.embedding_model = model_name
            service = EmbeddingService()
            assert service._should_use_replicate() == True, f"Should use Replicate for {model_name}"
        
        # Test cases that should use SentenceTransformers
        local_cases = [
            "all-MiniLM-L6-v2",
            "distilbert-base-nli-mean-tokens",
            "paraphrase-MiniLM-L6-v2"
        ]
        
        for model_name in local_cases:
            mock_settings.embedding_model = model_name
            service = EmbeddingService()
            assert service._should_use_replicate() == False, f"Should use local for {model_name}"
    
    @patch('src.services.embedding_service.SentenceTransformer')
    def test_local_embedding_initialization(self, mock_st, mock_settings):
        """Test initialization with local SentenceTransformers model"""
        mock_settings.embedding_model = "all-MiniLM-L6-v2"
        
        service = EmbeddingService()
        
        assert service.use_replicate == False
        mock_st.assert_called_once_with("all-MiniLM-L6-v2")
    
    @patch('src.services.embedding_service.replicate')
    def test_replicate_embedding_initialization(self, mock_replicate, mock_settings):
        """Test initialization with Replicate model"""
        mock_settings.embedding_model = "nateraw/bge-large-en-v1.5"
        
        service = EmbeddingService()
        
        assert service.use_replicate == True
        assert mock_replicate.api_token == "test_token"
    
    def test_replicate_initialization_without_token(self, mock_settings):
        """Test that initialization fails without Replicate token"""
        mock_settings.embedding_model = "nateraw/bge-large-en-v1.5"
        mock_settings.replicate_api_token = None
        
        with pytest.raises(ValueError, match="REPLICATE_API_TOKEN is required"):
            EmbeddingService()
    
    @patch('src.services.embedding_service.SentenceTransformer')
    async def test_get_embedding_local(self, mock_st, mock_settings):
        """Test getting embedding from local model"""
        mock_settings.embedding_model = "all-MiniLM-L6-v2"
        
        # Mock the encode method to return fake embeddings
        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
        mock_st.return_value = mock_model
        
        service = EmbeddingService()
        
        # Mock the actual async execution
        with patch.object(service, '_get_sentence_transformer_embedding', return_value=[0.1, 0.2, 0.3]) as mock_method:
            embedding = await service.get_embedding("test text")
            assert embedding == [0.1, 0.2, 0.3]
            mock_method.assert_called_once_with("test text")
    
    @patch('src.services.embedding_service.replicate')
    async def test_get_embedding_replicate(self, mock_replicate, mock_settings):
        """Test getting embedding from Replicate API"""
        mock_settings.embedding_model = "nateraw/bge-large-en-v1.5"
        
        # Create a proper coroutine mock
        async def mock_async_run(*args, **kwargs):
            return [0.4, 0.5, 0.6]
        
        mock_replicate.async_run = mock_async_run
        
        service = EmbeddingService()
        embedding = await service.get_embedding("test text")
        
        assert embedding == [0.4, 0.5, 0.6]
    
    @patch('src.services.embedding_service.replicate')
    async def test_replicate_fallback_on_error(self, mock_replicate, mock_settings):
        """Test fallback to sentence transformers when Replicate fails"""
        mock_settings.embedding_model = "nateraw/bge-large-en-v1.5"
        
        # Mock replicate to fail
        mock_replicate.async_run.side_effect = Exception("API Error")
        
        service = EmbeddingService()
        
        # Mock the fallback method
        with patch.object(service, '_get_sentence_transformer_embedding', return_value=[0.7, 0.8, 0.9]) as mock_fallback:
            embedding = await service.get_embedding("test text")
            
            assert embedding == [0.7, 0.8, 0.9]
            mock_fallback.assert_called_once_with("test text")


if __name__ == "__main__":
    pytest.main([__file__])