"""
Comprehensive test suite for GenerationService
"""
import pytest
import json
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from pydantic import ValidationError

# Mock external dependencies before importing the service
import sys
sys.modules['replicate'] = MagicMock()

from src.services.generation_service import GenerationService
from src.utils.error_messages import UserFriendlyError


class TestGenerationService:
    """Test suite for GenerationService core functionality"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return MagicMock()

    @pytest.fixture
    def mock_settings(self):
        """Mock settings with proper API configuration"""
        with patch('src.services.generation_service.settings') as mock:
            mock.replicate_api_token = "test_token_123"
            mock.generation_model = "test/model"
            yield mock

    @pytest.fixture
    def mock_prompt_service(self):
        """Mock PromptService"""
        with patch('src.services.generation_service.PromptService') as mock:
            mock_instance = MagicMock()
            mock_instance.build_golden_enhanced_prompt.return_value = "Test prompt for generation"
            mock.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def mock_llm_audit_service(self):
        """Mock LLMAuditService"""
        with patch('src.services.generation_service.LLMAuditService') as mock:
            mock_instance = MagicMock()
            mock_instance.log_llm_interaction = MagicMock()
            mock.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def generation_service(self, mock_db_session, mock_settings, mock_prompt_service, mock_llm_audit_service):
        """Create GenerationService instance with mocked dependencies"""
        return GenerationService(db_session=mock_db_session)

    @pytest.fixture
    def sample_context(self):
        """Sample context for survey generation"""
        return {
            "rfq_text": "Create a customer satisfaction survey for our software product",
            "survey_id": "test_survey_123",
            "workflow_id": "test_workflow_456",
            "rfq_id": "test_rfq_789"
        }

    @pytest.fixture
    def sample_golden_examples(self):
        """Sample golden examples for testing"""
        return [
            {
                "id": "golden_1",
                "rfq_text": "Customer satisfaction survey",
                "survey_json": {
                    "title": "Customer Satisfaction Survey",
                    "sections": [
                        {
                            "id": 1,
                            "title": "Satisfaction Questions",
                            "questions": [
                                {
                                    "id": "q1",
                                    "text": "How satisfied are you?",
                                    "type": "scale",
                                    "required": True
                                }
                            ]
                        }
                    ]
                },
                "methodology_tags": ["satisfaction"],
                "quality_score": 0.9
            }
        ]

    @pytest.fixture
    def sample_methodology_blocks(self):
        """Sample methodology blocks for testing"""
        return [
            {
                "methodology": "nps",
                "description": "Net Promoter Score methodology",
                "required_questions": 2,
                "validation_rules": ["Must use 0-10 scale"]
            }
        ]

    def test_init_with_valid_api_token(self, mock_db_session, mock_settings):
        """Test GenerationService initialization with valid API token"""
        service = GenerationService(db_session=mock_db_session)
        assert service.db_session == mock_db_session
        assert service.model == "test/model"
        assert service.prompt_service is not None
        assert service.replicate_client is not None

    def test_init_without_api_token(self, mock_db_session):
        """Test GenerationService initialization fails without API token"""
        with patch('src.services.generation_service.settings') as mock_settings:
            mock_settings.replicate_api_token = None

            with pytest.raises(UserFriendlyError) as exc_info:
                GenerationService(db_session=mock_db_session)

            assert "AI service not configured" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_generate_survey_success(self, generation_service, sample_context,
                                         sample_golden_examples, sample_methodology_blocks):
        """Test successful survey generation"""
        # Mock the replicate.async_run response
        mock_response = [
            '{"title": "Customer Satisfaction Survey", "sections": [',
            '{"id": 1, "title": "Questions", "questions": [',
            '{"id": "q1", "text": "How satisfied are you?", "type": "scale", "required": true}',
            ']}]}'
        ]

        with patch('src.services.generation_service.replicate') as mock_replicate:
            mock_replicate.async_run.return_value = mock_response

            result = await generation_service.generate_survey(
                context=sample_context,
                golden_examples=sample_golden_examples,
                methodology_blocks=sample_methodology_blocks
            )

            # Verify the result structure
            assert "survey" in result
            assert "pillar_scores" in result
            assert result["survey"]["title"] == "Customer Satisfaction Survey"
            assert len(result["survey"]["sections"]) == 1
            assert result["pillar_scores"]["overall_grade"] == "B"

            # Verify replicate was called with correct parameters
            mock_replicate.async_run.assert_called_once()
            call_args = mock_replicate.async_run.call_args
            assert "prompt" in call_args[1]["input"]
            assert call_args[1]["input"]["temperature"] == 0.7

    @pytest.mark.asyncio
    async def test_generate_survey_api_failure(self, generation_service, sample_context,
                                             sample_golden_examples, sample_methodology_blocks):
        """Test survey generation with API failure"""
        with patch('src.services.generation_service.replicate') as mock_replicate:
            mock_replicate.async_run.side_effect = Exception("API call failed")

            with pytest.raises(Exception) as exc_info:
                await generation_service.generate_survey(
                    context=sample_context,
                    golden_examples=sample_golden_examples,
                    methodology_blocks=sample_methodology_blocks
                )

            assert "API call failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_survey_authentication_error(self, generation_service, sample_context,
                                                      sample_golden_examples, sample_methodology_blocks):
        """Test survey generation with authentication error"""
        with patch('src.services.generation_service.replicate') as mock_replicate:
            mock_replicate.async_run.side_effect = Exception("authentication failed")

            with pytest.raises(UserFriendlyError) as exc_info:
                await generation_service.generate_survey(
                    context=sample_context,
                    golden_examples=sample_golden_examples,
                    methodology_blocks=sample_methodology_blocks
                )

            assert "AI service not configured" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_generate_survey_empty_response(self, generation_service, sample_context,
                                                sample_golden_examples, sample_methodology_blocks):
        """Test survey generation with empty response"""
        with patch('src.services.generation_service.replicate') as mock_replicate:
            mock_replicate.async_run.return_value = ""

            with pytest.raises(Exception) as exc_info:
                await generation_service.generate_survey(
                    context=sample_context,
                    golden_examples=sample_golden_examples,
                    methodology_blocks=sample_methodology_blocks
                )

            assert "empty or invalid response" in str(exc_info.value)

    def test_extract_survey_json_valid_json(self, generation_service):
        """Test JSON extraction with valid JSON"""
        valid_json = '{"title": "Test Survey", "sections": []}'
        result = generation_service._extract_survey_json(valid_json)

        assert result["title"] == "Test Survey"
        assert result["sections"] == []

    def test_extract_survey_json_with_markdown(self, generation_service):
        """Test JSON extraction from markdown code blocks"""
        markdown_response = '''Here's your survey:
        ```json
        {"title": "Test Survey", "sections": []}
        ```
        '''
        result = generation_service._extract_survey_json(markdown_response)

        assert result["title"] == "Test Survey"
        assert result["sections"] == []

    def test_extract_survey_json_malformed(self, generation_service):
        """Test JSON extraction with malformed JSON"""
        malformed_json = '{"title": "Test Survey", "sections": [}'  # Missing closing bracket

        # Should use fallback extraction methods
        result = generation_service._extract_survey_json(malformed_json)

        # Should return a minimal valid survey
        assert "title" in result
        assert "sections" in result
        assert isinstance(result["sections"], list)

    def test_extract_survey_json_no_json(self, generation_service):
        """Test JSON extraction with no JSON content"""
        no_json_response = "This is just text without any JSON"

        result = generation_service._extract_survey_json(no_json_response)

        # Should create minimal survey
        assert result["title"] == "Generated Survey"
        assert result["sections"] == []

    def test_validate_and_fix_survey_structure(self, generation_service):
        """Test survey structure validation and fixing"""
        # Test with missing basic fields
        survey = {}
        generation_service._validate_and_fix_survey_structure(survey)

        assert survey["title"] == "Generated Survey"
        assert survey["description"] == "AI-generated survey"
        assert "sections" in survey
        assert survey["estimated_time"] == 5

    def test_validate_and_fix_legacy_questions_format(self, generation_service):
        """Test conversion from legacy questions format to sections"""
        survey = {
            "title": "Test Survey",
            "questions": [
                {"id": "q1", "text": "Test question", "type": "text", "required": True}
            ]
        }

        generation_service._validate_and_fix_survey_structure(survey)

        assert "sections" in survey
        assert "questions" not in survey
        assert len(survey["sections"]) == 1
        assert survey["sections"][0]["title"] == "Survey Questions"
        assert len(survey["sections"][0]["questions"]) == 1

    def test_consolidate_sections_many_single_questions(self, generation_service):
        """Test section consolidation with many single-question sections"""
        sections = [
            {"id": 1, "title": f"Section {i}", "questions": [{"id": f"q{i}", "text": f"Question {i}"}]}
            for i in range(1, 6)  # 5 single-question sections
        ]

        result = generation_service._consolidate_sections(sections)

        # Should consolidate into fewer sections
        assert len(result) < len(sections)
        # Total questions should remain the same
        total_questions = sum(len(section.get("questions", [])) for section in result)
        assert total_questions == 5

    def test_group_questions_into_sections_few_questions(self, generation_service):
        """Test question grouping with few questions"""
        questions = [
            {"id": "q1", "text": "How old are you?", "category": "demographics"},
            {"id": "q2", "text": "What is your income?", "category": "demographics"}
        ]

        result = generation_service._group_questions_into_sections(questions)

        # Few questions should go into one section
        assert len(result) == 1
        assert result[0]["title"] == "Survey Questions"
        assert len(result[0]["questions"]) == 2

    def test_group_questions_into_sections_by_category(self, generation_service):
        """Test question grouping by category"""
        questions = [
            {"id": "q1", "text": "How old are you?", "category": "demographics"},
            {"id": "q2", "text": "What is your income?", "category": "demographics"},
            {"id": "q3", "text": "How satisfied are you?", "category": "satisfaction"},
            {"id": "q4", "text": "Would you recommend us?", "category": "satisfaction"},
            {"id": "q5", "text": "What features do you prefer?", "category": "preferences"}
        ]

        # Mock the question text analysis
        result = generation_service._group_questions_into_sections(questions)

        # Should create separate sections for categories with 2+ questions
        section_titles = [section["title"] for section in result]
        assert "Demographics" in section_titles or "Background & Experience" in section_titles
        assert "Satisfaction & Rating" in section_titles

        assert result["confidence_score"] == 0.5

        # Should extract some questions
        if result["sections"]:
            assert len(result["sections"][0]["questions"]) > 0

    def test_extract_questions_from_text_force_comprehensive(self, generation_service):
        """Test comprehensive question extraction with force method"""
        text = '''
        {"id": "q1", "text": "How satisfied are you with our service?", "type": "scale", "required": true}
        {"id": "q2", "text": "What is your age?", "type": "text", "required": true}
        '''

        result = generation_service._extract_questions_from_text_force(text)

        assert len(result) == 2
        assert result[0]["id"] == "q1"
        assert result[0]["text"] == "How satisfied are you with our service?"
        assert result[1]["id"] == "q2"
        assert result[1]["text"] == "What is your age?"

    def test_texts_similar(self, generation_service):
        """Test text similarity detection"""
        text1 = "How satisfied are you with our service?"
        text2 = "How satisfied are you with our product?"
        text3 = "What is your favorite color?"

        # Similar texts
        assert generation_service._texts_similar(text1, text2, threshold=0.6)

        # Different texts
        assert not generation_service._texts_similar(text1, text3, threshold=0.6)

        # Edge cases
        assert not generation_service._texts_similar("", text1)
        assert not generation_service._texts_similar(text1, "")

    @pytest.mark.asyncio
    async def test_store_system_prompt_audit(self, generation_service):
        """Test system prompt audit storage"""
        # Mock the database models
        with patch('src.services.generation_service.SystemPromptAudit') as mock_audit:
            mock_audit_instance = MagicMock()
            mock_audit.return_value = mock_audit_instance

            await generation_service._store_system_prompt_audit(
                survey_id="test_survey",
                rfq_id="test_rfq",
                system_prompt="Test prompt",
                generation_context={"test": "context"}
            )

            # Verify audit record was created and committed
            generation_service.db_session.add.assert_called_once_with(mock_audit_instance)
            generation_service.db_session.commit.assert_called_once()

    def test_calculate_pillar_grade(self, generation_service):
        """Test pillar grade calculation"""
        assert generation_service._calculate_pillar_grade(0.95) == "A"
        assert generation_service._calculate_pillar_grade(0.85) == "B"
        assert generation_service._calculate_pillar_grade(0.75) == "C"
        assert generation_service._calculate_pillar_grade(0.65) == "D"
        assert generation_service._calculate_pillar_grade(0.55) == "F"

    def test_compile_recommendations(self, generation_service):
        """Test recommendation compilation"""
        pillar_scores = [
            MagicMock(recommendations=["Improve question clarity", "Add more options"]),
            MagicMock(recommendations=["Improve question clarity", "Reduce survey length"]),
            MagicMock(recommendations=["Add demographic questions"])
        ]

        result = generation_service._compile_recommendations(pillar_scores)

        # Should remove duplicates while preserving order
        assert "Improve question clarity" in result
        assert "Add more options" in result
        assert "Reduce survey length" in result
        assert "Add demographic questions" in result
        assert len([r for r in result if r == "Improve question clarity"]) == 1  # No duplicates

    def test_balanced_json_extraction_simple(self, generation_service):
        """Test balanced JSON extraction with simple valid JSON"""
        json_text = '{"title": "Test", "sections": []}'
        result = generation_service._extract_balanced_json_robust(json_text)

        assert result["title"] == "Test"
        assert result["sections"] == []

    def test_balanced_json_extraction_nested(self, generation_service):
        """Test balanced JSON extraction with nested structures"""
        json_text = '{"title": "Test", "sections": [{"id": 1, "questions": [{"id": "q1", "text": "Question"}]}]}'
        result = generation_service._extract_balanced_json_robust(json_text)

        assert result["title"] == "Test"
        assert len(result["sections"]) == 1
        assert result["sections"][0]["id"] == 1

    def test_balanced_json_extraction_with_strings(self, generation_service):
        """Test balanced JSON extraction with quoted strings containing braces"""
        json_text = '{"title": "Test {with braces}", "description": "Contains } and { characters"}'
        result = generation_service._extract_balanced_json_robust(json_text)

        assert result["title"] == "Test {with braces}"
        assert result["description"] == "Contains } and { characters"

    def test_repair_json_simple_fixes(self, generation_service):
        """Test simple JSON repair functionality"""
        # Test missing comma repair
        broken_json = '{"title": "Test"\n"description": "Test desc"}'
        repaired = generation_service._repair_json_simple(broken_json)

        if repaired:  # Only test if repair was attempted
            result = json.loads(repaired)
            assert result["title"] == "Test"
            assert result["description"] == "Test desc"

    @pytest.mark.asyncio
    async def test_advanced_evaluation_fallback(self, generation_service, sample_context):
        """Test advanced evaluation with fallback to pillar-scores API"""
        survey_data = {"title": "Test Survey", "sections": []}

        # Mock the evaluation to return proper format
        with patch.object(generation_service, '_call_pillar_scores_api') as mock_api:
            mock_api.return_value = {
                "overall_grade": "B",
                "weighted_score": 0.8,
                "total_score": 0.8,
                "summary": "Good survey",
                "pillar_breakdown": [],
                "recommendations": []
            }

            result = await generation_service._evaluate_with_advanced_system(survey_data, "test rfq")

            assert result["overall_grade"] == "B"
            assert result["weighted_score"] == 0.8
            mock_api.assert_called_once()


class TestGenerationServiceIntegration:
    """Integration tests for GenerationService with real-world scenarios"""

    @pytest.fixture
    def integration_service(self, mock_settings):
        """Create service for integration testing"""
        with patch('src.services.generation_service.LLMAuditService'), \
             patch('src.services.generation_service.PromptService'):
            return GenerationService(db_session=MagicMock())

    @pytest.mark.asyncio
    async def test_full_generation_workflow(self, integration_service):
        """Test complete generation workflow from context to final survey"""
        context = {
            "rfq_text": "Create a customer satisfaction survey for software",
            "survey_id": "integration_test",
            "workflow_id": "workflow_integration"
        }
        golden_examples = []
        methodology_blocks = []

        # Mock a realistic response
        realistic_response = '''{
            "title": "Customer Satisfaction Survey",
            "description": "Survey to measure customer satisfaction with our software",
            "sections": [
                {
                    "id": 1,
                    "title": "Satisfaction Questions",
                    "description": "Core satisfaction measurement",
                    "questions": [
                        {
                            "id": "q1",
                            "text": "How satisfied are you with our software?",
                            "type": "scale",
                            "required": true,
                            "category": "satisfaction"
                        },
                        {
                            "id": "q2",
                            "text": "How likely are you to recommend our software?",
                            "type": "scale",
                            "required": true,
                            "category": "nps"
                        }
                    ]
                }
            ],
            "estimated_time": 5,
            "confidence_score": 0.9,
            "methodologies": ["satisfaction", "nps"],
            "golden_examples": [],
            "metadata": {"target_responses": 100, "methodology": ["satisfaction"]}
        }'''

        with patch('src.services.generation_service.replicate') as mock_replicate:
            mock_replicate.async_run.return_value = [realistic_response]

            result = await integration_service.generate_survey(
                context=context,
                golden_examples=golden_examples,
                methodology_blocks=methodology_blocks
            )

            # Verify complete workflow
            assert "survey" in result
            assert "pillar_scores" in result
            survey = result["survey"]

            # Verify survey structure
            assert survey["title"] == "Customer Satisfaction Survey"
            assert len(survey["sections"]) == 1
            assert len(survey["sections"][0]["questions"]) == 2

            # Verify questions
            questions = survey["sections"][0]["questions"]
            assert questions[0]["text"] == "How satisfied are you with our software?"
            assert questions[1]["text"] == "How likely are you to recommend our software?"

            # Verify metadata
            assert survey["estimated_time"] == 5
            assert survey["confidence_score"] == 0.9

    @pytest.mark.asyncio
    async def test_empty_survey_rejection(self, generation_service):
        """Test that empty surveys are rejected during validation"""
        # Create an empty survey structure
        empty_survey = {
            "title": "Empty Survey",
            "description": "This survey has no questions",
            "sections": []  # Empty sections array
        }
        
        # Attempt to validate and fix structure - should raise ValueError
        with pytest.raises(ValueError, match="Generated survey is empty"):
            generation_service._validate_and_fix_survey_structure(empty_survey)
    
    @pytest.mark.asyncio
    async def test_empty_survey_with_empty_sections(self, generation_service):
        """Test that surveys with sections but no questions are rejected"""
        # Create a survey with sections but no questions
        empty_survey = {
            "title": "Empty Survey",
            "description": "This survey has sections but no questions",
            "sections": [
                {
                    "id": 1,
                    "title": "Section 1",
                    "description": "Empty section",
                    "questions": []  # Empty questions array
                },
                {
                    "id": 2,
                    "title": "Section 2",
                    "description": "Another empty section",
                    "questions": []  # Empty questions array
                }
            ]
        }
        
        # Attempt to validate and fix structure - should raise ValueError
        with pytest.raises(ValueError, match="Generated survey is empty"):
            generation_service._validate_and_fix_survey_structure(empty_survey)
    
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, integration_service):
        """Test error recovery and fallback mechanisms"""
        context = {"rfq_text": "Test survey"}

        # Test with completely invalid response
        with patch('src.services.generation_service.replicate') as mock_replicate:
            mock_replicate.async_run.return_value = ["Invalid response that is not JSON"]

            result = await integration_service.generate_survey(
                context=context,
                golden_examples=[],
                methodology_blocks=[]
            )

            # Should still produce a valid result with fallback
            assert "survey" in result
            assert "pillar_scores" in result
            survey = result["survey"]

            # Verify fallback survey structure
            assert survey["title"] == "Generated Survey"
            assert "sections" in survey
            assert isinstance(survey["sections"], list)


class TestGenerationServicePerformance:
    """Performance and load testing for GenerationService"""

    @pytest.fixture
    def performance_service(self, mock_settings):
        """Create service for performance testing"""
        with patch('src.services.generation_service.LLMAuditService'), \
             patch('src.services.generation_service.PromptService'):
            return GenerationService(db_session=MagicMock())

    def test_json_extraction_performance(self, performance_service):
        """Test JSON extraction performance with large responses"""
        # Create a large JSON response
        large_sections = []
        for i in range(50):  # 50 sections
            questions = []
            for j in range(20):  # 20 questions per section
                questions.append({
                    "id": f"q{i}_{j}",
                    "text": f"Question {i}_{j} with some longer text to make it realistic",
                    "type": "scale",
                    "required": True
                })
            large_sections.append({
                "id": i + 1,
                "title": f"Section {i + 1}",
                "questions": questions
            })

        large_json = json.dumps({
            "title": "Large Performance Test Survey",
            "sections": large_sections
        })

        # Test extraction performance
        import time
        start_time = time.time()
        result = performance_service._extract_survey_json(large_json)
        extraction_time = time.time() - start_time

        # Verify extraction worked and was reasonably fast (< 1 second)
        assert result["title"] == "Large Performance Test Survey"
        assert len(result["sections"]) == 50
        assert extraction_time < 1.0, f"JSON extraction took too long: {extraction_time}s"

    def test_section_consolidation_performance(self, performance_service):
        """Test section consolidation performance with many sections"""
        # Create many single-question sections
        sections = []
        for i in range(100):
            sections.append({
                "id": i + 1,
                "title": f"Section {i + 1}",
                "questions": [{"id": f"q{i}", "text": f"Question {i}"}]
            })

        import time
        start_time = time.time()
        result = performance_service._consolidate_sections(sections)
        consolidation_time = time.time() - start_time

        # Verify consolidation worked and was fast
        assert len(result) < len(sections)  # Should consolidate
        assert consolidation_time < 0.5, f"Section consolidation took too long: {consolidation_time}s"

        # Verify all questions preserved
        total_questions_before = sum(len(s.get("questions", [])) for s in sections)
        total_questions_after = sum(len(s.get("questions", [])) for s in result)
        assert total_questions_before == total_questions_after