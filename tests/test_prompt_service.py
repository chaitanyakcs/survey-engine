"""
Comprehensive test suite for PromptService
"""
import pytest
import json
from unittest.mock import MagicMock, patch

from src.services.prompt_service import PromptService


class TestPromptService:
    """Test suite for PromptService core functionality"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        mock_session = MagicMock()
        return mock_session

    @pytest.fixture
    def mock_survey_rules(self):
        """Mock survey rules from database"""
        methodology_rules = [
            MagicMock(
                rule_type='methodology',
                category='van_westendorp',
                rule_description='Van Westendorp Price Sensitivity Meter',
                rule_content={'required_questions': 4, 'validation_rules': ['Must have exactly 4 price questions']},
                is_active=True
            ),
            MagicMock(
                rule_type='methodology',
                category='conjoint',
                rule_description='Conjoint Analysis',
                rule_content={'required_questions': 6, 'validation_rules': ['Must have balanced choice sets']},
                is_active=True
            )
        ]

        quality_rules = [
            MagicMock(
                rule_type='quality',
                category='question_quality',
                rule_content={'rule_text': 'Questions must be clear and unambiguous'},
                is_active=True
            ),
            MagicMock(
                rule_type='quality',
                category='survey_structure',
                rule_content={'rule_text': 'Start with screening questions'},
                is_active=True
            )
        ]

        pillar_rules = [
            MagicMock(
                id=1,
                rule_type='pillar',
                category='content_validity',
                rule_name='Content Validity Rule',
                rule_description='Ensure questions measure what they claim to measure',
                rule_content={
                    'priority': 'high',
                    'evaluation_criteria': ['question_relevance', 'content_accuracy']
                },
                is_active=True
            )
        ]

        system_prompt_rule = MagicMock(
            rule_type='system_prompt',
            rule_description='You are an expert survey designer with 15+ years of experience.',
            is_active=True
        )

        return methodology_rules, quality_rules, pillar_rules, system_prompt_rule

    @pytest.fixture
    def prompt_service(self, mock_db_session, mock_survey_rules):
        """Create PromptService instance with mocked database"""
        methodology_rules, quality_rules, pillar_rules, system_prompt_rule = mock_survey_rules

        # Mock the database queries
        mock_db_session.query.return_value.filter.return_value.all.side_effect = [
            methodology_rules,  # First call for methodology rules
            quality_rules,      # Second call for quality rules
            [],                 # Third call for custom rules (empty)
            pillar_rules        # Fourth call for pillar rules
        ]
        mock_db_session.query.return_value.filter.return_value.first.return_value = system_prompt_rule

        return PromptService(db_session=mock_db_session)

    @pytest.fixture
    def prompt_service_no_db(self):
        """Create PromptService instance without database (fallback mode)"""
        return PromptService(db_session=None)

    @pytest.fixture
    def sample_context(self):
        """Sample context for prompt building"""
        return {
            "rfq_text": "Create a customer satisfaction survey for our software product",
            "survey_id": "test_survey_123",
            "workflow_id": "test_workflow_456",
            "methodology": "satisfaction",
            "target_segment": "software users"
        }

    @pytest.fixture
    def sample_golden_examples(self):
        """Sample golden examples for testing"""
        return [
            {
                "id": "golden_1",
                "rfq_text": "Customer satisfaction survey for mobile app",
                "survey_json": {
                    "title": "Mobile App Satisfaction Survey",
                    "sections": [
                        {
                            "id": 1,
                            "title": "App Usage",
                            "questions": [
                                {
                                    "id": "q1",
                                    "text": "How often do you use our mobile app?",
                                    "type": "multiple_choice",
                                    "options": ["Daily", "Weekly", "Monthly", "Rarely"],
                                    "required": True
                                }
                            ]
                        }
                    ]
                },
                "methodology_tags": ["satisfaction", "usage"],
                "quality_score": 0.9
            },
            {
                "id": "golden_2",
                "rfq_text": "Product feedback survey",
                "survey_json": {
                    "title": "Product Feedback Survey",
                    "sections": [
                        {
                            "id": 1,
                            "title": "Feedback",
                            "questions": [
                                {
                                    "id": "q1",
                                    "text": "What do you like most about our product?",
                                    "type": "text",
                                    "required": False
                                }
                            ]
                        }
                    ]
                },
                "methodology_tags": ["feedback"],
                "quality_score": 0.8
            }
        ]

    @pytest.fixture
    def sample_methodology_blocks(self):
        """Sample methodology blocks for testing"""
        return [
            {
                "methodology": "van_westendorp",
                "description": "Van Westendorp Price Sensitivity Meter",
                "required_questions": 4,
                "question_templates": [
                    "At what price would this product be so expensive that you would not consider buying it?",
                    "At what price would you consider this product to be priced so low that you would feel the quality couldn't be very good?",
                    "At what price would you consider this product starting to get expensive, so that it is not out of the question, but you would have to give some thought to buying it?",
                    "At what price would you consider this product to be a bargain—a great buy for the money?"
                ]
            },
            {
                "methodology": "nps",
                "description": "Net Promoter Score",
                "required_questions": 2,
                "question_templates": [
                    "How likely are you to recommend [product/service] to a friend or colleague?",
                    "What is the primary reason for your score?"
                ]
            }
        ]

    def test_init_with_database(self, prompt_service):
        """Test PromptService initialization with database"""
        assert prompt_service.db_session is not None
        assert prompt_service.base_rules is not None
        assert len(prompt_service.methodology_rules) == 2
        assert 'van_westendorp' in prompt_service.methodology_rules
        assert 'conjoint' in prompt_service.methodology_rules
        assert len(prompt_service.quality_rules) == 2
        assert prompt_service.system_prompt == "You are an expert survey designer with 15+ years of experience."

    def test_init_without_database(self, prompt_service_no_db):
        """Test PromptService initialization without database (fallback)"""
        assert prompt_service_no_db.db_session is None
        assert prompt_service_no_db.base_rules is not None
        # Should load fallback rules
        assert 'van_westendorp' in prompt_service_no_db.methodology_rules
        assert 'conjoint' in prompt_service_no_db.methodology_rules
        assert len(prompt_service_no_db.quality_rules) > 0

    def test_load_base_rules(self, prompt_service):
        """Test loading of base system rules"""
        base_rules = prompt_service._load_base_rules()

        assert 'role' in base_rules
        assert 'expertise' in base_rules
        assert 'core_principles' in base_rules
        assert 'output_requirements' in base_rules

        assert "expert survey designer" in base_rules['role']
        assert isinstance(base_rules['expertise'], list)
        assert len(base_rules['expertise']) > 0

    def test_load_database_rules_success(self, mock_db_session, mock_survey_rules):
        """Test successful loading of rules from database"""
        methodology_rules, quality_rules, pillar_rules, system_prompt_rule = mock_survey_rules

        # Reset the mock to test the loading process
        mock_db_session.query.return_value.filter.return_value.all.side_effect = [
            methodology_rules,
            quality_rules,
            [],  # custom rules
            pillar_rules
        ]
        mock_db_session.query.return_value.filter.return_value.first.return_value = system_prompt_rule

        service = PromptService(db_session=mock_db_session)

        # Verify methodology rules loaded
        assert 'van_westendorp' in service.methodology_rules
        assert service.methodology_rules['van_westendorp']['required_questions'] == 4

        # Verify quality rules loaded
        assert 'question_quality' in service.quality_rules
        assert 'survey_structure' in service.quality_rules

        # Verify pillar rules loaded
        assert 'content_validity' in service.pillar_rules
        assert len(service.pillar_rules['content_validity']) == 1

        # Verify system prompt loaded
        assert service.system_prompt == "You are an expert survey designer with 15+ years of experience."

    def test_load_database_rules_failure(self, mock_db_session):
        """Test fallback when database loading fails"""
        # Make database query raise an exception
        mock_db_session.query.side_effect = Exception("Database connection failed")

        service = PromptService(db_session=mock_db_session)

        # Should fall back to hardcoded rules
        assert 'van_westendorp' in service.methodology_rules
        assert 'conjoint' in service.methodology_rules

    def test_build_golden_enhanced_prompt(self, prompt_service, sample_context,
                                       sample_golden_examples, sample_methodology_blocks):
        """Test building of comprehensive prompt with golden examples"""
        custom_rules = {
            "rules": ["Use clear and simple language", "Avoid leading questions"]
        }

        prompt = prompt_service.build_golden_enhanced_prompt(
            context=sample_context,
            golden_examples=sample_golden_examples,
            methodology_blocks=sample_methodology_blocks,
            custom_rules=custom_rules
        )

        # Verify prompt structure
        assert isinstance(prompt, str)
        assert len(prompt) > 1000  # Should be comprehensive

        # Verify key sections are included
        assert "ROLE AND EXPERTISE" in prompt
        assert "RFQ ANALYSIS" in prompt
        assert "GOLDEN EXAMPLES" in prompt
        assert "METHODOLOGY REQUIREMENTS" in prompt
        assert "QUALITY RULES" in prompt
        assert "OUTPUT FORMAT" in prompt

        # Verify context information included
        assert sample_context["rfq_text"] in prompt
        assert sample_context["methodology"] in prompt

        # Verify golden examples included
        assert "Mobile App Satisfaction Survey" in prompt
        assert "How often do you use our mobile app?" in prompt

        # Verify methodology blocks included
        assert "Van Westendorp Price Sensitivity Meter" in prompt
        assert "Net Promoter Score" in prompt

        # Verify custom rules included
        assert "Use clear and simple language" in prompt
        assert "Avoid leading questions" in prompt

        # Verify sections format requirement
        assert "sections" in prompt
        assert "DO NOT use a flat 'questions' array" in prompt

    def test_build_golden_enhanced_prompt_minimal(self, prompt_service):
        """Test prompt building with minimal inputs"""
        context = {"rfq_text": "Simple survey request"}

        prompt = prompt_service.build_golden_enhanced_prompt(
            context=context,
            golden_examples=[],
            methodology_blocks=[],
            custom_rules=None
        )

        # Should still generate valid prompt
        assert isinstance(prompt, str)
        assert len(prompt) > 500
        assert "Simple survey request" in prompt
        assert "ROLE AND EXPERTISE" in prompt

    def test_build_golden_enhanced_prompt_no_golden_examples(self, prompt_service, sample_context):
        """Test prompt building without golden examples"""
        prompt = prompt_service.build_golden_enhanced_prompt(
            context=sample_context,
            golden_examples=[],
            methodology_blocks=[],
            custom_rules=None
        )

        # Should include note about no examples
        assert "No golden examples available" in prompt
        assert sample_context["rfq_text"] in prompt

    def test_add_custom_rule(self, prompt_service):
        """Test adding custom rules dynamically"""
        initial_count = len(prompt_service.quality_rules.get('custom', []))

        prompt_service.add_custom_rule('custom', 'New custom rule for testing')

        # Verify rule was added
        assert 'custom' in prompt_service.quality_rules
        assert 'New custom rule for testing' in prompt_service.quality_rules['custom']
        assert len(prompt_service.quality_rules['custom']) == initial_count + 1

    def test_refresh_rules_from_database(self, prompt_service, mock_db_session, mock_survey_rules):
        """Test refreshing rules from database"""
        methodology_rules, quality_rules, pillar_rules, system_prompt_rule = mock_survey_rules

        # Add a custom rule first
        prompt_service.add_custom_rule('test', 'Test rule')
        assert 'test' in prompt_service.quality_rules

        # Reset mock for refresh
        mock_db_session.query.return_value.filter.return_value.all.side_effect = [
            methodology_rules,
            quality_rules,
            [],
            pillar_rules
        ]
        mock_db_session.query.return_value.filter.return_value.first.return_value = system_prompt_rule

        # Refresh rules
        prompt_service.refresh_rules_from_database()

        # Custom rule should be cleared and database rules reloaded
        assert 'test' not in prompt_service.quality_rules
        assert 'van_westendorp' in prompt_service.methodology_rules

    def test_get_methodology_guidelines(self, prompt_service):
        """Test retrieving specific methodology guidelines"""
        # Test existing methodology
        guidelines = prompt_service.get_methodology_guidelines('van_westendorp')
        assert guidelines is not None
        assert guidelines['required_questions'] == 4

        # Test case insensitive
        guidelines_upper = prompt_service.get_methodology_guidelines('VAN_WESTENDORP')
        assert guidelines_upper is not None

        # Test non-existing methodology
        guidelines_none = prompt_service.get_methodology_guidelines('nonexistent')
        assert guidelines_none is None

    def test_get_pillar_rules_context(self, prompt_service):
        """Test generating pillar rules context for LLM"""
        context = prompt_service.get_pillar_rules_context()

        if prompt_service.pillar_rules:
            assert isinstance(context, str)
            assert len(context) > 0
            assert "content_validity" in context
        else:
            assert context == ""

    def test_format_golden_examples(self, prompt_service, sample_golden_examples):
        """Test formatting of golden examples for prompt inclusion"""
        # This tests the internal formatting used in build_golden_enhanced_prompt
        prompt = prompt_service.build_golden_enhanced_prompt(
            context={"rfq_text": "test"},
            golden_examples=sample_golden_examples,
            methodology_blocks=[],
            custom_rules=None
        )

        # Verify proper formatting
        assert "EXAMPLE 1:" in prompt
        assert "EXAMPLE 2:" in prompt
        assert "RFQ Text:" in prompt
        assert "Generated Survey JSON:" in prompt
        assert "Methodology Tags:" in prompt
        assert "Quality Score:" in prompt

    def test_format_methodology_blocks(self, prompt_service, sample_methodology_blocks):
        """Test formatting of methodology blocks for prompt inclusion"""
        prompt = prompt_service.build_golden_enhanced_prompt(
            context={"rfq_text": "test"},
            golden_examples=[],
            methodology_blocks=sample_methodology_blocks,
            custom_rules=None
        )

        # Verify methodology block formatting
        assert "METHODOLOGY 1: van_westendorp" in prompt
        assert "METHODOLOGY 2: nps" in prompt
        assert "Required Questions: 4" in prompt
        assert "Required Questions: 2" in prompt

    def test_prompt_includes_quality_rules(self, prompt_service, sample_context):
        """Test that quality rules are properly included in prompts"""
        prompt = prompt_service.build_golden_enhanced_prompt(
            context=sample_context,
            golden_examples=[],
            methodology_blocks=[],
            custom_rules=None
        )

        # Should include quality rules from database
        assert "Questions must be clear and unambiguous" in prompt
        assert "Start with screening questions" in prompt

    def test_prompt_includes_pillar_context(self, prompt_service, sample_context):
        """Test that pillar rules context is included in prompts"""
        prompt = prompt_service.build_golden_enhanced_prompt(
            context=sample_context,
            golden_examples=[],
            methodology_blocks=[],
            custom_rules=None
        )

        # Should include pillar context if available
        pillar_context = prompt_service.get_pillar_rules_context()
        if pillar_context:
            assert "content_validity" in prompt.lower()

    def test_prompt_json_structure_requirements(self, prompt_service, sample_context):
        """Test that prompt includes proper JSON structure requirements"""
        prompt = prompt_service.build_golden_enhanced_prompt(
            context=sample_context,
            golden_examples=[],
            methodology_blocks=[],
            custom_rules=None
        )

        # Verify JSON structure requirements
        assert "sections" in prompt
        assert "DO NOT use a flat 'questions' array" in prompt
        assert "5 sections" in prompt
        assert '"id"' in prompt
        assert '"title"' in prompt
        assert '"description"' in prompt
        assert '"questions"' in prompt

    def test_empty_context_handling(self, prompt_service):
        """Test handling of empty or minimal context"""
        empty_context = {}

        prompt = prompt_service.build_golden_enhanced_prompt(
            context=empty_context,
            golden_examples=[],
            methodology_blocks=[],
            custom_rules=None
        )

        # Should still generate valid prompt
        assert isinstance(prompt, str)
        assert len(prompt) > 100
        assert "ROLE AND EXPERTISE" in prompt

    def test_large_golden_examples_handling(self, prompt_service):
        """Test handling of many golden examples"""
        # Create many golden examples
        many_examples = []
        for i in range(10):
            example = {
                "id": f"golden_{i}",
                "rfq_text": f"Test RFQ {i}",
                "survey_json": {
                    "title": f"Test Survey {i}",
                    "sections": [{"id": 1, "title": "Section", "questions": []}]
                },
                "methodology_tags": ["test"],
                "quality_score": 0.8
            }
            many_examples.append(example)

        prompt = prompt_service.build_golden_enhanced_prompt(
            context={"rfq_text": "test"},
            golden_examples=many_examples,
            methodology_blocks=[],
            custom_rules=None
        )

        # Should handle all examples
        assert "EXAMPLE 1:" in prompt
        assert "EXAMPLE 10:" in prompt
        assert len(prompt) > 5000  # Should be quite long

    def test_complex_custom_rules(self, prompt_service, sample_context):
        """Test handling of complex custom rules structure"""
        complex_rules = {
            "rules": [
                "Rule 1: Simple rule",
                "Rule 2: Another rule with details"
            ],
            "methodology_specific": {
                "van_westendorp": ["Use exact PSM wording"],
                "nps": ["Include 0-10 scale"]
            },
            "constraints": {
                "max_questions": 25,
                "min_sections": 3
            }
        }

        prompt = prompt_service.build_golden_enhanced_prompt(
            context=sample_context,
            golden_examples=[],
            methodology_blocks=[],
            custom_rules=complex_rules
        )

        # Verify complex rules are included
        assert "Rule 1: Simple rule" in prompt
        assert "Rule 2: Another rule with details" in prompt


class TestPromptServiceIntegration:
    """Integration tests for PromptService with realistic scenarios"""

    @pytest.fixture
    def integration_service(self):
        """Create service for integration testing"""
        return PromptService(db_session=None)  # Use fallback rules

    def test_van_westendorp_prompt_generation(self, integration_service):
        """Test prompt generation for Van Westendorp methodology"""
        context = {
            "rfq_text": "We need to determine optimal pricing for our new software product",
            "methodology": "van_westendorp",
            "target_segment": "small business owners"
        }

        methodology_blocks = [
            {
                "methodology": "van_westendorp",
                "description": "Van Westendorp Price Sensitivity Meter",
                "required_questions": 4
            }
        ]

        prompt = integration_service.build_golden_enhanced_prompt(
            context=context,
            golden_examples=[],
            methodology_blocks=methodology_blocks,
            custom_rules=None
        )

        # Verify Van Westendorp specific requirements
        assert "van_westendorp" in prompt.lower()
        assert "pricing" in prompt.lower()
        assert "4" in prompt  # Required questions
        assert "small business owners" in prompt

    def test_nps_survey_prompt_generation(self, integration_service):
        """Test prompt generation for NPS survey"""
        context = {
            "rfq_text": "Measure customer loyalty and likelihood to recommend our service",
            "methodology": "nps",
            "target_segment": "existing customers"
        }

        golden_examples = [
            {
                "id": "nps_example",
                "rfq_text": "NPS survey for retail store",
                "survey_json": {
                    "title": "Customer Loyalty Survey",
                    "sections": [
                        {
                            "id": 1,
                            "title": "Net Promoter Score",
                            "questions": [
                                {
                                    "id": "nps_q1",
                                    "text": "How likely are you to recommend our store to a friend or colleague?",
                                    "type": "scale",
                                    "scale_min": 0,
                                    "scale_max": 10,
                                    "required": True
                                },
                                {
                                    "id": "nps_q2",
                                    "text": "What is the primary reason for your score?",
                                    "type": "text",
                                    "required": False
                                }
                            ]
                        }
                    ]
                },
                "methodology_tags": ["nps"],
                "quality_score": 0.95
            }
        ]

        prompt = integration_service.build_golden_enhanced_prompt(
            context=context,
            golden_examples=golden_examples,
            methodology_blocks=[],
            custom_rules=None
        )

        # Verify NPS specific content
        assert "nps" in prompt.lower()
        assert "recommend" in prompt.lower()
        assert "0-10" in prompt or "0 to 10" in prompt
        assert "Customer Loyalty Survey" in prompt

    def test_multi_methodology_prompt(self, integration_service):
        """Test prompt generation with multiple methodologies"""
        context = {
            "rfq_text": "Comprehensive research including satisfaction, pricing, and feature preferences"
        }

        methodology_blocks = [
            {
                "methodology": "satisfaction",
                "description": "Customer satisfaction measurement"
            },
            {
                "methodology": "van_westendorp",
                "description": "Price sensitivity analysis"
            },
            {
                "methodology": "conjoint",
                "description": "Feature preference analysis"
            }
        ]

        prompt = integration_service.build_golden_enhanced_prompt(
            context=context,
            golden_examples=[],
            methodology_blocks=methodology_blocks,
            custom_rules=None
        )

        # Verify all methodologies included
        assert "satisfaction" in prompt.lower()
        assert "van_westendorp" in prompt.lower()
        assert "conjoint" in prompt.lower()
        assert "METHODOLOGY 1:" in prompt
        assert "METHODOLOGY 2:" in prompt
        assert "METHODOLOGY 3:" in prompt


class TestPromptServicePerformance:
    """Performance tests for PromptService"""

    @pytest.fixture
    def performance_service(self):
        """Create service for performance testing"""
        return PromptService(db_session=None)

    def test_large_prompt_generation_performance(self, performance_service):
        """Test performance with large inputs"""
        # Create large context
        large_context = {
            "rfq_text": "Large RFQ text " * 1000,  # Very long RFQ
            "methodology": "comprehensive"
        }

        # Create many golden examples
        many_examples = []
        for i in range(50):
            example = {
                "id": f"example_{i}",
                "rfq_text": f"Example RFQ {i} with detailed description " * 10,
                "survey_json": {
                    "title": f"Example Survey {i}",
                    "sections": [
                        {
                            "id": j,
                            "title": f"Section {j}",
                            "questions": [
                                {
                                    "id": f"q{j}_{k}",
                                    "text": f"Question {j}_{k} with detailed text",
                                    "type": "scale"
                                }
                                for k in range(5)
                            ]
                        }
                        for j in range(1, 6)
                    ]
                },
                "methodology_tags": ["comprehensive"],
                "quality_score": 0.8
            }
            many_examples.append(example)

        import time
        start_time = time.time()

        prompt = performance_service.build_golden_enhanced_prompt(
            context=large_context,
            golden_examples=many_examples,
            methodology_blocks=[],
            custom_rules=None
        )

        generation_time = time.time() - start_time

        # Verify prompt was generated and performance is reasonable
        assert isinstance(prompt, str)
        assert len(prompt) > 10000  # Should be very large
        assert generation_time < 5.0, f"Prompt generation took too long: {generation_time}s"

    def test_prompt_caching_behavior(self, performance_service):
        """Test that repeated calls don't degrade performance"""
        context = {"rfq_text": "Test RFQ"}
        golden_examples = [
            {
                "id": "test",
                "rfq_text": "Test",
                "survey_json": {"title": "Test", "sections": []},
                "methodology_tags": ["test"],
                "quality_score": 0.8
            }
        ]

        # Generate multiple prompts and measure timing
        times = []
        for i in range(10):
            import time
            start_time = time.time()

            prompt = performance_service.build_golden_enhanced_prompt(
                context=context,
                golden_examples=golden_examples,
                methodology_blocks=[],
                custom_rules=None
            )

            times.append(time.time() - start_time)

        # Performance should be consistent (no significant degradation)
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)

        assert max_time - min_time < avg_time * 0.5, "Performance degraded significantly across calls"
        assert avg_time < 1.0, f"Average generation time too slow: {avg_time}s"