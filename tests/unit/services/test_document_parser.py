"""
Comprehensive test suite for DocumentParser
"""
import pytest
import json
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock, mock_open
from io import BytesIO

# Mock external dependencies
import sys
sys.modules['docx'] = MagicMock()
sys.modules['replicate'] = MagicMock()

from src.services.document_parser import DocumentParser, DocumentParsingError


class TestDocumentParser:
    """Test suite for DocumentParser core functionality"""

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
    def document_parser(self, mock_settings, mock_db_session):
        """Create DocumentParser instance with mocked dependencies"""
        return DocumentParser(db_session=mock_db_session)

    @pytest.fixture
    def sample_docx_content(self):
        """Sample DOCX file content as bytes"""
        return b"mock_docx_content_for_testing"

    @pytest.fixture
    def sample_extracted_text(self):
        """Sample extracted text from DOCX"""
        return """
        Survey Requirements Document

        Title: Customer Satisfaction Survey

        Objective: Measure customer satisfaction with our new mobile application

        Target Audience: Mobile app users aged 18-65

        Questions:
        1. How satisfied are you with the app interface?
        2. How likely are you to recommend this app to others?
        3. What features would you like to see improved?

        Methodology: Standard satisfaction survey with NPS component

        Sample Size: 500 respondents
        Timeline: 2 weeks
        """

    @pytest.fixture
    def sample_rfq_extracted_text(self):
        """Sample RFQ document text"""
        return """
        RFQ: Product Feature Research Study

        Company Background: TechCorp is a leading software company developing productivity tools.

        Business Problem: We need to prioritize which features to develop for our next product release.

        Research Objectives:
        - Understand which features customers value most
        - Determine willingness to pay for premium features
        - Identify usage patterns and preferences

        Target Audience: Small business owners, 25-50 years old, currently using productivity software

        Methodology: Conjoint analysis to understand feature trade-offs

        Sample Plan: n=300, LOI 15 minutes, recruit through email list

        Required Sections: Screener, Feature Evaluation, Demographics
        """

    @pytest.fixture
    def sample_survey_json_response(self):
        """Sample valid survey JSON response from LLM"""
        return {
            "raw_output": {
                "document_text": "Sample document text",
                "extraction_timestamp": "2024-01-01T00:00:00Z",
                "source_file": None,
                "error": None
            },
            "final_output": {
                "title": "Customer Satisfaction Survey",
                "description": "Survey to measure customer satisfaction",
                "metadata": {
                    "quality_score": 0.9,
                    "estimated_time": 10,
                    "methodology_tags": ["satisfaction", "nps"],
                    "target_responses": 500,
                    "source_file": None
                },
                "questions": [
                    {
                        "id": "q1",
                        "text": "How satisfied are you with the app interface?",
                        "type": "scale",
                        "options": ["Very Dissatisfied", "Dissatisfied", "Neutral", "Satisfied", "Very Satisfied"],
                        "required": True,
                        "validation": "single_select",
                        "methodology": "satisfaction",
                        "routing": None
                    },
                    {
                        "id": "q2",
                        "text": "How likely are you to recommend this app?",
                        "type": "scale",
                        "options": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
                        "required": True,
                        "validation": "single_select",
                        "methodology": "nps",
                        "routing": None
                    }
                ],
                "parsing_issues": []
            }
        }

    @pytest.fixture
    def sample_rfq_analysis_response(self):
        """Sample RFQ analysis response from LLM"""
        return {
            "confidence": 0.85,
            "identified_sections": {
                "objectives": {
                    "confidence": 0.9,
                    "source_text": "Understand which features customers value most",
                    "source_section": "Research Objectives",
                    "extracted_data": [
                        "Understand which features customers value most",
                        "Determine willingness to pay for premium features"
                    ]
                },
                "business_context": {
                    "confidence": 0.8,
                    "source_text": "TechCorp is a leading software company",
                    "source_section": "Company Background",
                    "extracted_data": "TechCorp is a leading software company developing productivity tools"
                }
            },
            "extracted_entities": {
                "stakeholders": ["small business owners"],
                "industries": ["technology", "software"],
                "research_types": ["feature research", "pricing study"],
                "methodologies": ["conjoint analysis"]
            },
            "field_mappings": [
                {
                    "field": "title",
                    "value": "Product Feature Research Study",
                    "confidence": 0.95,
                    "source": "RFQ: Product Feature Research Study",
                    "reasoning": "Clear title in document header",
                    "priority": "critical"
                },
                {
                    "field": "company_product_background",
                    "value": "TechCorp is a leading software company developing productivity tools.",
                    "confidence": 0.85,
                    "source": "Company Background: TechCorp is a leading software company...",
                    "reasoning": "Company background section with clear business context",
                    "priority": "critical"
                },
                {
                    "field": "primary_method",
                    "value": "conjoint",
                    "confidence": 0.90,
                    "source": "Methodology: Conjoint analysis to understand feature trade-offs",
                    "reasoning": "Explicit mention of conjoint analysis methodology",
                    "priority": "high"
                }
            ]
        }

    def test_init_with_valid_api_token(self, mock_settings, mock_db_session):
        """Test DocumentParser initialization with valid API token"""
        parser = DocumentParser(db_session=mock_db_session)
        assert parser.db_session == mock_db_session
        assert parser.model == "test/model"

    def test_init_without_api_token(self, mock_db_session):
        """Test DocumentParser initialization without API token"""
        with patch('src.services.document_parser.settings') as mock_settings:
            mock_settings.replicate_api_token = None

            with pytest.raises(Exception):  # Should raise UserFriendlyError
                DocumentParser(db_session=mock_db_session)

    def test_extract_text_from_docx_success(self, document_parser, sample_docx_content):
        """Test successful text extraction from DOCX"""
        # Mock the Document class and its methods
        mock_doc = MagicMock()
        mock_paragraph1 = MagicMock()
        mock_paragraph1.text = "Title: Test Survey"
        mock_paragraph2 = MagicMock()
        mock_paragraph2.text = "Description: This is a test survey"
        mock_paragraph3 = MagicMock()
        mock_paragraph3.text = ""  # Empty paragraph should be skipped

        mock_doc.paragraphs = [mock_paragraph1, mock_paragraph2, mock_paragraph3]
        mock_doc.tables = []  # No tables for this test

        with patch('src.services.document_parser.Document', return_value=mock_doc):
            result = document_parser.extract_text_from_docx(sample_docx_content)

        expected_text = "Title: Test Survey\nDescription: This is a test survey"
        assert result == expected_text

    def test_extract_text_from_docx_with_tables(self, document_parser, sample_docx_content):
        """Test text extraction from DOCX with tables"""
        # Mock document with tables
        mock_doc = MagicMock()
        mock_doc.paragraphs = []

        # Mock table structure
        mock_table = MagicMock()
        mock_row = MagicMock()
        mock_cell1 = MagicMock()
        mock_cell1.text = "Question"
        mock_cell2 = MagicMock()
        mock_cell2.text = "Type"
        mock_row.cells = [mock_cell1, mock_cell2]
        mock_table.rows = [mock_row]
        mock_doc.tables = [mock_table]

        with patch('src.services.document_parser.Document', return_value=mock_doc):
            result = document_parser.extract_text_from_docx(sample_docx_content)

        assert "Question | Type" in result

    def test_extract_text_from_docx_failure(self, document_parser, sample_docx_content):
        """Test text extraction failure handling"""
        with patch('src.services.document_parser.Document', side_effect=Exception("Invalid DOCX")):
            with pytest.raises(DocumentParsingError) as exc_info:
                document_parser.extract_text_from_docx(sample_docx_content)

            assert "Failed to extract text from document" in str(exc_info.value)

    def test_create_conversion_prompt(self, document_parser, sample_extracted_text):
        """Test creation of survey conversion prompt"""
        prompt = document_parser.create_conversion_prompt(sample_extracted_text)

        # Verify prompt structure
        assert isinstance(prompt, str)
        assert len(prompt) > 1000

        # Verify key components
        assert "expert survey methodologist" in prompt.lower()
        assert sample_extracted_text in prompt
        assert "JSON" in prompt
        assert "REQUIRED JSON SCHEMA" in prompt
        assert "METHODOLOGY DETECTION HINTS" in prompt

        # Verify methodology hints included
        assert "Van Westendorp" in prompt
        assert "Gabor-Granger" in prompt
        assert "Conjoint" in prompt
        assert "MaxDiff" in prompt

    @pytest.mark.asyncio
    async def test_convert_to_json_success(self, document_parser, sample_extracted_text, sample_survey_json_response):
        """Test successful document to JSON conversion"""
        mock_response = [json.dumps(sample_survey_json_response)]

        with patch('src.services.document_parser.replicate') as mock_replicate:
            mock_replicate.async_run.return_value = mock_response

            result = await document_parser.convert_to_json(sample_extracted_text)

            # Verify result structure
            assert "raw_output" in result
            assert "final_output" in result
            assert result["final_output"]["title"] == "Customer Satisfaction Survey"
            assert len(result["final_output"]["questions"]) == 2

            # Verify replicate was called
            mock_replicate.async_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_convert_to_json_invalid_json_response(self, document_parser, sample_extracted_text):
        """Test handling of invalid JSON response"""
        mock_response = ["This is not valid JSON"]

        with patch('src.services.document_parser.replicate') as mock_replicate:
            mock_replicate.async_run.return_value = mock_response

            result = await document_parser.convert_to_json(sample_extracted_text)

            # Should return fallback response
            assert "raw_output" in result
            assert "final_output" in result
            assert result["final_output"]["title"] == "Document Parse Error"
            assert "error" in result["raw_output"]

    @pytest.mark.asyncio
    async def test_convert_to_json_api_failure(self, document_parser, sample_extracted_text):
        """Test handling of API failure"""
        with patch('src.services.document_parser.replicate') as mock_replicate:
            mock_replicate.async_run.side_effect = Exception("API Error")

            result = await document_parser.convert_to_json(sample_extracted_text)

            # Should return fallback response with error
            assert "raw_output" in result
            assert "final_output" in result
            assert "API Error" in result["raw_output"]["error"]

    @pytest.mark.asyncio
    async def test_convert_to_json_markdown_extraction(self, document_parser, sample_extracted_text):
        """Test JSON extraction from markdown code blocks"""
        # Response with JSON in markdown
        markdown_response = f'''Here's the extracted survey:
        ```json
        {json.dumps({"title": "Test Survey", "questions": []})}
        ```
        '''

        with patch('src.services.document_parser.replicate') as mock_replicate:
            mock_replicate.async_run.return_value = [markdown_response]

            result = await document_parser.convert_to_json(sample_extracted_text)

            # Should extract JSON from markdown
            assert result["title"] == "Test Survey"
            assert "questions" in result

    def test_validate_survey_json_success(self, document_parser, sample_survey_json_response):
        """Test successful survey JSON validation"""
        result = document_parser.validate_survey_json(sample_survey_json_response)

        # Should return validated structure
        assert "raw_output" in result
        assert "final_output" in result
        assert result["final_output"]["title"] == "Customer Satisfaction Survey"

    def test_validate_survey_json_legacy_format(self, document_parser):
        """Test validation of legacy format survey"""
        legacy_survey = {
            "title": "Legacy Survey",
            "description": "Test survey",
            "questions": [
                {
                    "id": "q1",
                    "text": "Test question",
                    "type": "text",
                    "required": True
                }
            ]
        }

        # Mock SurveyCreate validation
        with patch('src.services.document_parser.SurveyCreate') as mock_survey:
            mock_survey.return_value.model_dump.return_value = legacy_survey

            result = document_parser.validate_survey_json(legacy_survey)

            assert result["title"] == "Legacy Survey"

    def test_validate_survey_json_validation_error(self, document_parser):
        """Test handling of validation errors"""
        invalid_survey = {"invalid": "structure"}

        with patch('src.services.document_parser.SurveyCreate', side_effect=Exception("Validation failed")):
            with pytest.raises(DocumentParsingError):
                document_parser.validate_survey_json(invalid_survey)

    def test_create_rfq_extraction_prompt(self, document_parser, sample_rfq_extracted_text):
        """Test creation of RFQ extraction prompt"""
        prompt = document_parser.create_rfq_extraction_prompt(sample_rfq_extracted_text)

        # Verify prompt structure
        assert isinstance(prompt, str)
        assert len(prompt) > 2000

        # Verify key components
        assert "expert research consultant" in prompt.lower()
        assert sample_rfq_extracted_text in prompt
        assert "FIELD PRIORITIZATION" in prompt
        assert "CRITICAL FIELDS" in prompt
        assert "CONFIDENCE SCORING GUIDELINES" in prompt

        # Verify field-specific guidance
        assert "TITLE (Critical)" in prompt
        assert "COMPANY_PRODUCT_BACKGROUND" in prompt
        assert "METHODOLOGY DETECTION" in prompt

        # Verify expected JSON structure
        assert "field_mappings" in prompt
        assert "confidence" in prompt
        assert "identified_sections" in prompt

    @pytest.mark.asyncio
    async def test_extract_rfq_data_success(self, document_parser, sample_rfq_extracted_text, sample_rfq_analysis_response):
        """Test successful RFQ data extraction"""
        mock_response = [json.dumps(sample_rfq_analysis_response)]

        with patch('src.services.document_parser.replicate') as mock_replicate:
            mock_replicate.async_run.return_value = mock_response

            result = await document_parser.extract_rfq_data(sample_rfq_extracted_text)

            # Verify result structure
            assert result["confidence"] == 0.85
            assert "identified_sections" in result
            assert "field_mappings" in result
            assert len(result["field_mappings"]) == 3

            # Verify specific mappings
            title_mapping = next((m for m in result["field_mappings"] if m["field"] == "title"), None)
            assert title_mapping is not None
            assert title_mapping["value"] == "Product Feature Research Study"
            assert title_mapping["confidence"] == 0.95

    @pytest.mark.asyncio
    async def test_extract_rfq_data_invalid_json(self, document_parser, sample_rfq_extracted_text):
        """Test RFQ extraction with invalid JSON response"""
        mock_response = ["Invalid JSON response"]

        with patch('src.services.document_parser.replicate') as mock_replicate:
            mock_replicate.async_run.return_value = mock_response

            result = await document_parser.extract_rfq_data(sample_rfq_extracted_text)

            # Should return fallback structure
            assert result["confidence"] == 0.1
            assert "field_mappings" in result
            assert result["field_mappings"] == []
            assert "parsing_error" in result

    @pytest.mark.asyncio
    async def test_extract_rfq_data_api_failure(self, document_parser, sample_rfq_extracted_text):
        """Test RFQ extraction with API failure"""
        with patch('src.services.document_parser.replicate') as mock_replicate:
            mock_replicate.async_run.side_effect = Exception("API failed")

            result = await document_parser.extract_rfq_data(sample_rfq_extracted_text)

            # Should return error structure
            assert result["confidence"] == 0.0
            assert "extraction_error" in result
            assert "API failed" in result["extraction_error"]

    @pytest.mark.asyncio
    async def test_parse_document_for_rfq_success(self, document_parser, sample_docx_content, sample_rfq_analysis_response):
        """Test complete RFQ document parsing workflow"""
        # Mock text extraction
        with patch.object(document_parser, 'extract_text_from_docx', return_value="Sample RFQ text"):
            # Mock RFQ data extraction
            with patch.object(document_parser, 'extract_rfq_data', new_callable=AsyncMock, return_value=sample_rfq_analysis_response):
                result = await document_parser.parse_document_for_rfq(sample_docx_content, "test.docx")

                # Verify result structure
                assert "document_content" in result
                assert "rfq_analysis" in result
                assert result["processing_status"] == "completed"
                assert result["errors"] == []

                # Verify document content
                doc_content = result["document_content"]
                assert doc_content["raw_text"] == "Sample RFQ text"
                assert doc_content["filename"] == "test.docx"
                assert doc_content["word_count"] == 3

    @pytest.mark.asyncio
    async def test_parse_document_for_rfq_empty_text(self, document_parser, sample_docx_content):
        """Test RFQ parsing with empty document text"""
        with patch.object(document_parser, 'extract_text_from_docx', return_value=""):
            with pytest.raises(DocumentParsingError) as exc_info:
                await document_parser.parse_document_for_rfq(sample_docx_content)

            assert "No text content found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_parse_document_success(self, document_parser, sample_docx_content, sample_survey_json_response):
        """Test complete document parsing workflow"""
        # Mock text extraction
        with patch.object(document_parser, 'extract_text_from_docx', return_value="Sample survey text"):
            # Mock JSON conversion
            with patch.object(document_parser, 'convert_to_json', new_callable=AsyncMock, return_value=sample_survey_json_response):
                # Mock validation
                with patch.object(document_parser, 'validate_survey_json', return_value=sample_survey_json_response):
                    result = await document_parser.parse_document(sample_docx_content)

                    # Verify result
                    assert "raw_output" in result
                    assert "final_output" in result
                    assert result["final_output"]["title"] == "Customer Satisfaction Survey"

    @pytest.mark.asyncio
    async def test_parse_document_empty_text(self, document_parser, sample_docx_content):
        """Test document parsing with empty text"""
        with patch.object(document_parser, 'extract_text_from_docx', return_value=""):
            with pytest.raises(DocumentParsingError) as exc_info:
                await document_parser.parse_document(sample_docx_content)

            assert "No text content found" in str(exc_info.value)


class TestDocumentParserIntegration:
    """Integration tests for DocumentParser with realistic scenarios"""

    @pytest.fixture
    def integration_parser(self, mock_settings):
        """Create parser for integration testing"""
        return DocumentParser(db_session=MagicMock())

    @pytest.mark.asyncio
    async def test_full_survey_parsing_workflow(self, integration_parser):
        """Test complete survey parsing from DOCX to validated JSON"""
        # Mock a realistic DOCX extraction
        realistic_text = """
        Customer Satisfaction Survey

        We want to understand how satisfied our customers are with our mobile application.

        Target Audience: Mobile app users aged 18-65

        Questions:
        1. How satisfied are you with the overall app experience? (Scale: Very Dissatisfied to Very Satisfied)
        2. How likely are you to recommend our app to friends? (Scale: 0-10)
        3. What is your favorite feature in the app? (Open text)
        4. How often do you use the app? (Multiple choice: Daily, Weekly, Monthly, Rarely)
        5. What improvements would you suggest? (Open text)

        Sample size: 1000 respondents
        Timeline: 3 weeks
        """

        # Mock realistic LLM response
        realistic_response = {
            "raw_output": {
                "document_text": realistic_text,
                "extraction_timestamp": "2024-01-01T00:00:00Z",
                "source_file": None,
                "error": None
            },
            "final_output": {
                "title": "Customer Satisfaction Survey",
                "description": "Survey to understand customer satisfaction with mobile application",
                "metadata": {
                    "quality_score": 0.9,
                    "estimated_time": 8,
                    "methodology_tags": ["satisfaction", "nps"],
                    "target_responses": 1000,
                    "source_file": None
                },
                "questions": [
                    {
                        "id": "q1",
                        "text": "How satisfied are you with the overall app experience?",
                        "type": "scale",
                        "options": ["Very Dissatisfied", "Dissatisfied", "Neutral", "Satisfied", "Very Satisfied"],
                        "required": True,
                        "validation": "single_select",
                        "methodology": "satisfaction",
                        "routing": None
                    },
                    {
                        "id": "q2",
                        "text": "How likely are you to recommend our app to friends?",
                        "type": "scale",
                        "options": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
                        "required": True,
                        "validation": "single_select",
                        "methodology": "nps",
                        "routing": None
                    },
                    {
                        "id": "q3",
                        "text": "What is your favorite feature in the app?",
                        "type": "text",
                        "options": [],
                        "required": False,
                        "validation": None,
                        "methodology": None,
                        "routing": None
                    },
                    {
                        "id": "q4",
                        "text": "How often do you use the app?",
                        "type": "multiple_choice",
                        "options": ["Daily", "Weekly", "Monthly", "Rarely"],
                        "required": True,
                        "validation": "single_select",
                        "methodology": None,
                        "routing": None
                    },
                    {
                        "id": "q5",
                        "text": "What improvements would you suggest?",
                        "type": "text",
                        "options": [],
                        "required": False,
                        "validation": None,
                        "methodology": None,
                        "routing": None
                    }
                ],
                "parsing_issues": []
            }
        }

        with patch.object(integration_parser, 'extract_text_from_docx', return_value=realistic_text):
            with patch('src.services.document_parser.replicate') as mock_replicate:
                mock_replicate.async_run.return_value = [json.dumps(realistic_response)]

                result = await integration_parser.parse_document(b"mock_docx_content")

                # Verify complete workflow
                assert "final_output" in result
                survey = result["final_output"]

                # Verify survey structure
                assert survey["title"] == "Customer Satisfaction Survey"
                assert len(survey["questions"]) == 5
                assert survey["metadata"]["estimated_time"] == 8

                # Verify question types
                questions = survey["questions"]
                assert questions[0]["type"] == "scale"  # Satisfaction
                assert questions[1]["type"] == "scale"  # NPS
                assert questions[2]["type"] == "text"   # Open text
                assert questions[3]["type"] == "multiple_choice"  # Usage frequency
                assert questions[4]["type"] == "text"   # Suggestions

    @pytest.mark.asyncio
    async def test_full_rfq_parsing_workflow(self, integration_parser):
        """Test complete RFQ parsing from DOCX to field mappings"""
        realistic_rfq_text = """
        RFQ: E-commerce User Experience Research

        Company: ShopTech Solutions - Leading e-commerce platform provider

        Background: We provide e-commerce solutions to mid-market retailers and need to understand
        how to improve our checkout process to reduce cart abandonment.

        Business Problem: Cart abandonment rate is 68%, above industry average. Need to identify
        friction points in checkout process and prioritize improvements.

        Research Objectives:
        - Identify main reasons for cart abandonment
        - Test new checkout flow designs
        - Understand payment method preferences
        - Measure impact of design changes on conversion

        Target Audience: Online shoppers who have abandoned carts in the last 30 days
        - Age: 25-55
        - Income: $40K+
        - Purchase frequency: At least monthly online purchases

        Methodology: User testing with A/B testing component

        Sample Requirements:
        - n=200 for user testing
        - n=1000 for A/B test
        - LOI: 20 minutes for user testing
        - Recruit from customer database

        Required Sections:
        - Screener (purchase behavior, demographics)
        - Current checkout experience evaluation
        - New design testing
        - Payment preferences
        - Post-test survey

        Timeline: 4 weeks
        Budget: $50,000
        """

        realistic_rfq_response = {
            "confidence": 0.9,
            "identified_sections": {
                "objectives": {
                    "confidence": 0.95,
                    "source_text": "Identify main reasons for cart abandonment, Test new checkout flow designs",
                    "source_section": "Research Objectives",
                    "extracted_data": [
                        "Identify main reasons for cart abandonment",
                        "Test new checkout flow designs",
                        "Understand payment method preferences",
                        "Measure impact of design changes on conversion"
                    ]
                },
                "business_context": {
                    "confidence": 0.9,
                    "source_text": "ShopTech Solutions - Leading e-commerce platform provider",
                    "source_section": "Company",
                    "extracted_data": "ShopTech Solutions provides e-commerce solutions to mid-market retailers"
                }
            },
            "extracted_entities": {
                "stakeholders": ["online shoppers", "retailers"],
                "industries": ["e-commerce", "retail"],
                "research_types": ["user experience", "user testing", "a/b testing"],
                "methodologies": ["user testing", "a/b testing"]
            },
            "field_mappings": [
                {
                    "field": "title",
                    "value": "E-commerce User Experience Research",
                    "confidence": 0.95,
                    "source": "RFQ: E-commerce User Experience Research",
                    "reasoning": "Clear title in document header",
                    "priority": "critical"
                },
                {
                    "field": "company_product_background",
                    "value": "ShopTech Solutions - Leading e-commerce platform provider offering solutions to mid-market retailers",
                    "confidence": 0.9,
                    "source": "Company: ShopTech Solutions - Leading e-commerce platform provider",
                    "reasoning": "Company background section with clear business context",
                    "priority": "critical"
                },
                {
                    "field": "business_problem",
                    "value": "Cart abandonment rate is 68%, above industry average. Need to identify friction points in checkout process.",
                    "confidence": 0.85,
                    "source": "Business Problem: Cart abandonment rate is 68%...",
                    "reasoning": "Clear problem statement in business context",
                    "priority": "high"
                },
                {
                    "field": "research_audience",
                    "value": "Online shoppers who have abandoned carts, age 25-55, income $40K+, monthly online purchases",
                    "confidence": 0.8,
                    "source": "Target Audience: Online shoppers who have abandoned carts in the last 30 days",
                    "reasoning": "Detailed audience description with demographics",
                    "priority": "medium"
                },
                {
                    "field": "sample_plan",
                    "value": "n=200 for user testing, n=1000 for A/B test, LOI 20 minutes, recruit from customer database",
                    "confidence": 0.85,
                    "source": "Sample Requirements: n=200 for user testing, n=1000 for A/B test...",
                    "reasoning": "Detailed sampling specifications",
                    "priority": "medium"
                },
                {
                    "field": "required_sections",
                    "value": ["Screener", "Current checkout experience evaluation", "New design testing", "Payment preferences", "Post-test survey"],
                    "confidence": 0.8,
                    "source": "Required Sections: Screener (purchase behavior, demographics)...",
                    "reasoning": "Explicit section requirements listed",
                    "priority": "medium"
                }
            ]
        }

        with patch.object(integration_parser, 'extract_text_from_docx', return_value=realistic_rfq_text):
            with patch('src.services.document_parser.replicate') as mock_replicate:
                mock_replicate.async_run.return_value = [json.dumps(realistic_rfq_response)]

                result = await integration_parser.parse_document_for_rfq(b"mock_docx_content", "ecommerce_rfq.docx")

                # Verify complete RFQ workflow
                assert result["processing_status"] == "completed"
                assert result["errors"] == []

                # Verify document content
                doc_content = result["document_content"]
                assert doc_content["filename"] == "ecommerce_rfq.docx"
                assert "ShopTech Solutions" in doc_content["raw_text"]

                # Verify RFQ analysis
                rfq_analysis = result["rfq_analysis"]
                assert rfq_analysis["confidence"] == 0.9
                assert len(rfq_analysis["field_mappings"]) == 6

                # Verify specific high-confidence mappings
                title_mapping = next((m for m in rfq_analysis["field_mappings"] if m["field"] == "title"), None)
                assert title_mapping["confidence"] == 0.95
                assert "E-commerce User Experience Research" in title_mapping["value"]

                company_mapping = next((m for m in rfq_analysis["field_mappings"] if m["field"] == "company_product_background"), None)
                assert company_mapping["confidence"] == 0.9
                assert "ShopTech Solutions" in company_mapping["value"]


class TestDocumentParserPerformance:
    """Performance tests for DocumentParser"""

    @pytest.fixture
    def performance_parser(self, mock_settings):
        """Create parser for performance testing"""
        return DocumentParser(db_session=MagicMock())

    def test_text_extraction_performance(self, performance_parser):
        """Test text extraction performance with large documents"""
        # Create mock for large document
        mock_doc = MagicMock()

        # Create many paragraphs
        large_paragraphs = []
        for i in range(1000):
            mock_para = MagicMock()
            mock_para.text = f"This is paragraph {i} with some content to simulate a real document."
            large_paragraphs.append(mock_para)

        mock_doc.paragraphs = large_paragraphs
        mock_doc.tables = []

        with patch('src.services.document_parser.Document', return_value=mock_doc):
            import time
            start_time = time.time()

            result = performance_parser.extract_text_from_docx(b"large_document_content")

            extraction_time = time.time() - start_time

        # Verify extraction worked and was reasonably fast
        assert len(result) > 50000  # Should be large
        assert extraction_time < 2.0, f"Text extraction took too long: {extraction_time}s"
        assert "paragraph 0" in result
        assert "paragraph 999" in result

    @pytest.mark.asyncio
    async def test_json_parsing_performance(self, performance_parser):
        """Test JSON parsing performance with complex responses"""
        # Create large, complex JSON response
        large_sections = []
        for i in range(20):
            questions = []
            for j in range(50):
                questions.append({
                    "id": f"q{i}_{j}",
                    "text": f"Question {i}_{j}: " + "This is a longer question text " * 10,
                    "type": "scale",
                    "options": [f"Option {k}" for k in range(1, 8)],
                    "required": True,
                    "validation": "single_select",
                    "methodology": "satisfaction",
                    "routing": None
                })
            large_sections.append({
                "id": i + 1,
                "title": f"Section {i + 1}",
                "description": f"Description for section {i + 1} " * 10,
                "questions": questions
            })

        large_response = {
            "raw_output": {
                "document_text": "Large document text " * 1000,
                "extraction_timestamp": "2024-01-01T00:00:00Z",
                "source_file": None,
                "error": None
            },
            "final_output": {
                "title": "Large Performance Test Survey",
                "description": "Large survey for performance testing " * 20,
                "metadata": {
                    "quality_score": 0.8,
                    "estimated_time": 45,
                    "methodology_tags": ["satisfaction", "comprehensive"],
                    "target_responses": 1000,
                    "source_file": None
                },
                "questions": [],  # Using sections instead
                "sections": large_sections,
                "parsing_issues": []
            }
        }

        large_json_string = json.dumps(large_response)

        with patch('src.services.document_parser.replicate') as mock_replicate:
            mock_replicate.async_run.return_value = [large_json_string]

            import time
            start_time = time.time()

            result = await performance_parser.convert_to_json("Test document text")

            conversion_time = time.time() - start_time

        # Verify conversion worked and performance is acceptable
        assert "final_output" in result
        assert result["final_output"]["title"] == "Large Performance Test Survey"
        assert len(result["final_output"]["sections"]) == 20
        assert conversion_time < 1.0, f"JSON conversion took too long: {conversion_time}s"

    def test_json_extraction_robustness(self, performance_parser):
        """Test JSON extraction with various malformed inputs"""
        test_cases = [
            # Missing closing brace
            '{"title": "Test", "sections": [{"id": 1, "questions": []}',
            # Extra commas
            '{"title": "Test",, "sections": [],}',
            # Mixed quotes
            '{"title": \'Test\', "sections": []}',
            # Embedded JSON-like strings
            '{"title": "Test {with braces}", "description": "Has } and { chars"}',
            # Multiple JSON objects
            '{"first": "object"} {"second": "object"}',
        ]

        for test_input in test_cases:
            try:
                result = performance_parser._extract_survey_json(test_input)

                # Should always return some valid structure
                assert isinstance(result, dict)
                assert "title" in result or "sections" in result

            except Exception as e:
                # If extraction fails completely, should handle gracefully
                assert False, f"JSON extraction failed completely for input: {test_input[:50]}... Error: {e}"