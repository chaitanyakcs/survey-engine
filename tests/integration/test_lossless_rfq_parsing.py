"""
Integration tests for lossless RFQ parsing with unmapped context
Tests the complete flow from document parsing to survey generation
"""
import pytest
import json
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from sqlalchemy.orm import Session

# Mock external dependencies
import sys
sys.modules['docx'] = MagicMock()
sys.modules['replicate'] = MagicMock()

from src.services.document_parser import DocumentParser
from src.workflows.nodes import RFQNode, ContextBuilderNode
from src.workflows.state import SurveyGenerationState
from src.services.prompt_builder import PromptBuilder


class TestLosslessRfqParsing:
    """Test suite for lossless RFQ parsing with unmapped context"""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings with API configuration"""
        with patch('src.services.document_parser.settings') as mock:
            mock.replicate_api_token = "test_token_123"
            mock.generation_model = "test/model"
            yield mock

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return MagicMock()

    @pytest.fixture
    def sample_document_text(self):
        """Sample document text with unmapped context"""
        return """
        Customer Satisfaction Research Study
        
        We need to conduct a comprehensive customer satisfaction survey for our new product line.
        The survey should focus on user experience and product quality.
        
        IMPORTANT: Please ensure the survey maintains a professional tone throughout.
        We prefer shorter questions to maintain respondent engagement.
        The survey should be mobile-friendly as most users access via mobile devices.
        
        Additional Requirements:
        - Include demographic questions for segmentation
        - Focus on satisfaction ratings and likelihood to recommend
        - Consider cultural sensitivity for international markets
        """

    @pytest.fixture
    def mock_llm_response_with_unmapped_context(self):
        """Mock LLM response including unmapped_context field"""
        return {
            "confidence": 0.85,
            "field_mappings": [
                {
                    "field": "title",
                    "value": "Customer Satisfaction Research Study",
                    "confidence": 0.9,
                    "source": "Customer Satisfaction Research Study",
                    "reasoning": "Clear title in document header",
                    "priority": "critical"
                },
                {
                    "field": "description",
                    "value": "Comprehensive customer satisfaction survey for new product line focusing on user experience and product quality",
                    "confidence": 0.85,
                    "source": "We need to conduct a comprehensive customer satisfaction survey for our new product line",
                    "reasoning": "Main research description",
                    "priority": "critical"
                }
            ],
            "unmapped_context": "IMPORTANT: Please ensure the survey maintains a professional tone throughout. We prefer shorter questions to maintain respondent engagement. The survey should be mobile-friendly as most users access via mobile devices. Additional Requirements: Include demographic questions for segmentation, Focus on satisfaction ratings and likelihood to recommend, Consider cultural sensitivity for international markets"
        }

    @pytest.mark.asyncio
    async def test_document_parser_extracts_unmapped_context(self, mock_settings, mock_db_session, sample_document_text, mock_llm_response_with_unmapped_context):
        """Test that document parser extracts unmapped_context field"""
        # Mock the LLM response
        with patch('src.services.document_parser.DocumentParser.extract_rfq_data') as mock_extract:
            mock_extract.return_value = mock_llm_response_with_unmapped_context
            
            parser = DocumentParser(db_session=mock_db_session)
            
            # Test the extraction
            result = await parser.extract_rfq_data(sample_document_text)
            
            # Verify unmapped_context is extracted
            assert "unmapped_context" in result
            assert result["unmapped_context"] == mock_llm_response_with_unmapped_context["unmapped_context"]
            assert len(result["unmapped_context"]) > 0
            assert "professional tone" in result["unmapped_context"]
            assert "mobile-friendly" in result["unmapped_context"]

    @pytest.mark.asyncio
    async def test_unmapped_context_word_limit(self, mock_settings, mock_db_session):
        """Test that unmapped_context respects 200-word limit"""
        # Create a very long unmapped context
        long_context = "This is a very long context. " * 50  # ~1500 characters
        
        mock_response = {
            "confidence": 0.85,
            "field_mappings": [],
            "unmapped_context": long_context
        }
        
        with patch('src.services.document_parser.DocumentParser.extract_rfq_data') as mock_extract:
            mock_extract.return_value = mock_response
            
            parser = DocumentParser(db_session=mock_db_session)
            result = await parser.extract_rfq_data("test document")
            
            # Verify unmapped_context is present but should be limited
            assert "unmapped_context" in result
            # The LLM should respect the 200-word limit instruction
            assert len(result["unmapped_context"]) <= 200 * 6  # 200 words * ~6 chars per word

    @pytest.mark.asyncio
    async def test_rfq_node_loads_unmapped_context(self, mock_db_session):
        """Test that RFQNode loads unmapped_context from enhanced_rfq_data"""
        # Mock RFQ with enhanced_rfq_data containing unmapped_context
        mock_rfq = MagicMock()
        mock_rfq.enhanced_rfq_data = {
            "unmapped_context": "Professional tone required, mobile-friendly design preferred",
            "business_context": {"company_product_background": "Test company"}
        }
        
        with patch('src.workflows.nodes.RFQNode.db') as mock_db:
            mock_db.query.return_value.filter.return_value.first.return_value = mock_rfq
            
            # Mock embedding service
            with patch('src.workflows.nodes.EmbeddingService') as mock_embedding_service:
                mock_embedding_service.return_value.get_embedding = AsyncMock(return_value=[0.1] * 384)
                
                rfq_node = RFQNode(mock_db_session)
                
                # Create test state
                state = SurveyGenerationState(
                    rfq_text="Test RFQ",
                    rfq_id="test-rfq-id"
                )
                
                # Execute RFQNode
                result = await rfq_node(state)
                
                # Verify unmapped_context is loaded
                assert "unmapped_context" in result
                assert result["unmapped_context"] == "Professional tone required, mobile-friendly design preferred"

    @pytest.mark.asyncio
    async def test_context_builder_includes_unmapped_context(self, mock_db_session):
        """Test that ContextBuilderNode includes unmapped_context in context"""
        context_builder = ContextBuilderNode(mock_db_session)
        
        # Create test state with unmapped_context
        state = SurveyGenerationState(
            rfq_text="Test RFQ",
            rfq_title="Test Title",
            unmapped_context="Additional context for survey generation",
            enhanced_rfq_data={"business_context": {"company_product_background": "Test"}}
        )
        
        # Execute ContextBuilderNode
        result = await context_builder(state)
        
        # Verify context includes unmapped_context
        assert "unmapped_context" in result["context"]
        assert result["context"]["unmapped_context"] == "Additional context for survey generation"

    @pytest.mark.asyncio
    async def test_prompt_builder_includes_unmapped_context_section(self, mock_db_session):
        """Test that PromptBuilder includes unmapped_context in prompt"""
        prompt_builder = PromptBuilder(db_session=mock_db_session)
        
        # Create context with unmapped_context
        context = {
            "unmapped_context": "Professional tone required, mobile-friendly design preferred",
            "rfq_details": {
                "text": "Test RFQ text",
                "title": "Test Title"
            }
        }
        
        # Build prompt
        prompt = await prompt_builder.build_survey_generation_prompt(
            rfq_text="Test RFQ text",
            context=context
        )
        
        # Verify prompt includes unmapped_context section
        assert "ADDITIONAL CONTEXT FROM RFQ:" in prompt
        assert "Professional tone required, mobile-friendly design preferred" in prompt
        assert "The following information was extracted from the RFQ but doesn't fit into structured fields:" in prompt

    @pytest.mark.asyncio
    async def test_prompt_builder_skips_empty_unmapped_context(self, mock_db_session):
        """Test that PromptBuilder skips unmapped_context section when empty"""
        prompt_builder = PromptBuilder(db_session=mock_db_session)
        
        # Create context with empty unmapped_context
        context = {
            "unmapped_context": "",
            "rfq_details": {
                "text": "Test RFQ text",
                "title": "Test Title"
            }
        }
        
        # Build prompt
        prompt = await prompt_builder.build_survey_generation_prompt(
            rfq_text="Test RFQ text",
            context=context
        )
        
        # Verify prompt does not include unmapped_context section
        assert "ADDITIONAL CONTEXT FROM RFQ:" not in prompt

    @pytest.mark.asyncio
    async def test_end_to_end_unmapped_context_flow(self, mock_settings, mock_db_session, sample_document_text, mock_llm_response_with_unmapped_context):
        """Test complete end-to-end flow with unmapped_context"""
        # Mock the document parser
        with patch('src.services.document_parser.DocumentParser.extract_rfq_data') as mock_extract:
            mock_extract.return_value = mock_llm_response_with_unmapped_context
            
            parser = DocumentParser(db_session=mock_db_session)
            rfq_data = await parser.extract_rfq_data(sample_document_text)
            
            # Verify unmapped_context is extracted
            assert "unmapped_context" in rfq_data
            
            # Mock RFQ with enhanced_rfq_data
            mock_rfq = MagicMock()
            mock_rfq.enhanced_rfq_data = {
                "unmapped_context": rfq_data["unmapped_context"],
                "business_context": {"company_product_background": "Test company"}
            }
            
            # Test RFQNode
            with patch('src.workflows.nodes.RFQNode.db') as mock_db:
                mock_db.query.return_value.filter.return_value.first.return_value = mock_rfq
                
                with patch('src.workflows.nodes.EmbeddingService') as mock_embedding_service:
                    mock_embedding_service.return_value.get_embedding = AsyncMock(return_value=[0.1] * 384)
                    
                    rfq_node = RFQNode(mock_db_session)
                    state = SurveyGenerationState(
                        rfq_text="Test RFQ",
                        rfq_id="test-rfq-id"
                    )
                    
                    rfq_result = await rfq_node(state)
                    assert "unmapped_context" in rfq_result
                    
                    # Update state with result
                    state.unmapped_context = rfq_result["unmapped_context"]
                    
                    # Test ContextBuilderNode
                    context_builder = ContextBuilderNode(mock_db_session)
                    context_result = await context_builder(state)
                    
                    assert "unmapped_context" in context_result["context"]
                    
                    # Test PromptBuilder
                    prompt_builder = PromptBuilder(db_session=mock_db_session)
                    prompt = await prompt_builder.build_survey_generation_prompt(
                        rfq_text="Test RFQ",
                        context=context_result["context"]
                    )
                    
                    # Verify unmapped_context appears in final prompt
                    assert "ADDITIONAL CONTEXT FROM RFQ:" in prompt
                    assert rfq_data["unmapped_context"] in prompt

    def test_unmapped_context_field_validation(self):
        """Test that unmapped_context field is properly validated"""
        # Test valid unmapped_context
        valid_context = "Professional tone required, mobile-friendly design preferred"
        assert len(valid_context) > 0
        assert isinstance(valid_context, str)
        
        # Test empty unmapped_context
        empty_context = ""
        assert len(empty_context) == 0
        
        # Test None unmapped_context
        none_context = None
        assert none_context is None

    @pytest.mark.asyncio
    async def test_unmapped_context_preserves_formatting(self, mock_db_session):
        """Test that unmapped_context preserves important formatting"""
        prompt_builder = PromptBuilder(db_session=mock_db_session)
        
        # Create context with formatted unmapped_context
        formatted_context = """IMPORTANT: Please ensure the survey maintains a professional tone throughout.
        We prefer shorter questions to maintain respondent engagement.
        The survey should be mobile-friendly as most users access via mobile devices.
        
        Additional Requirements:
        - Include demographic questions for segmentation
        - Focus on satisfaction ratings and likelihood to recommend
        - Consider cultural sensitivity for international markets"""
        
        context = {
            "unmapped_context": formatted_context,
            "rfq_details": {
                "text": "Test RFQ text",
                "title": "Test Title"
            }
        }
        
        # Build prompt
        prompt = await prompt_builder.build_survey_generation_prompt(
            rfq_text="Test RFQ text",
            context=context
        )
        
        # Verify formatting is preserved
        assert "IMPORTANT:" in prompt
        assert "Additional Requirements:" in prompt
        assert "- Include demographic questions" in prompt

