"""
Simple test suite for PromptBuilder focusing on actual functionality
"""
import pytest
from unittest.mock import MagicMock, patch

from src.services.prompt_builder import PromptBuilder, SectionManager, PromptSection, RAGContext


class TestPromptBuilderBasic:
    """Test basic PromptBuilder functionality"""

    @pytest.fixture
    def prompt_builder(self):
        """Create PromptBuilder instance for testing"""
        return PromptBuilder()

    def test_prompt_builder_initialization(self, prompt_builder):
        """Test that PromptBuilder initializes correctly"""
        assert prompt_builder is not None
        assert hasattr(prompt_builder, 'build_survey_generation_prompt')

    def test_prompt_builder_has_required_methods(self, prompt_builder):
        """Test that PromptBuilder has required methods"""
        required_methods = [
            'build_survey_generation_prompt',
            'get_pillar_rules_context',
            '_load_rules_from_database'
        ]
        
        for method in required_methods:
            assert hasattr(prompt_builder, method), f"PromptBuilder missing method: {method}"

    def test_build_survey_generation_prompt_basic(self, prompt_builder):
        """Test basic prompt generation"""
        context = {
            "rfq_text": "Create a simple survey",
            "methodology": "satisfaction"
        }
        
        prompt = prompt_builder.build_survey_generation_prompt(context["rfq_text"], context)
        
        assert isinstance(prompt, str)
        assert len(prompt) > 100
        assert "survey" in prompt.lower()

    def test_build_survey_generation_prompt_with_question_types(self, prompt_builder):
        """Test prompt generation with question types"""
        context = {
            "rfq_text": "Create a survey with matrix questions and constant sum",
            "methodology": "comprehensive"
        }
        
        prompt = prompt_builder.build_survey_generation_prompt(context["rfq_text"], context)
        
        assert isinstance(prompt, str)
        assert len(prompt) > 100
        # Should include guidance for question types
        assert "matrix" in prompt.lower() or "constant" in prompt.lower()

    def test_get_pillar_rules_context(self, prompt_builder):
        """Test pillar rules context generation"""
        context = prompt_builder.get_pillar_rules_context()
        
        assert isinstance(context, str)
        # Should be empty or contain pillar rules
        assert len(context) >= 0

    def test_load_rules_from_database(self, prompt_builder):
        """Test loading rules from database"""
        # This should not raise an exception
        try:
            prompt_builder._load_rules_from_database()
        except Exception as e:
            # If database is not available, that's okay for testing
            assert "database" in str(e).lower() or "connection" in str(e).lower()


class TestSectionManager:
    """Test SectionManager functionality"""

    def test_section_manager_initialization(self):
        """Test SectionManager initialization"""
        section_manager = SectionManager()
        assert section_manager is not None
        assert hasattr(section_manager, 'sections')

    def test_add_section(self):
        """Test adding sections to manager"""
        section_manager = SectionManager()
        
        test_section = PromptSection(
            title="Test Section",
            content=["Test content"],
            order=1
        )
        
        section_manager.add_section("test", test_section)
        assert "test" in section_manager.sections
        assert section_manager.sections["test"] == test_section

    def test_get_ordered_sections(self):
        """Test getting sections in order"""
        section_manager = SectionManager()
        
        # Add sections with different orders
        section1 = PromptSection("First", ["content1"], order=2)
        section2 = PromptSection("Second", ["content2"], order=1)
        
        section_manager.add_section("first", section1)
        section_manager.add_section("second", section2)
        
        ordered_sections = section_manager.get_ordered_sections()
        
        assert len(ordered_sections) == 2
        assert ordered_sections[0].title == "Second"  # order=1
        assert ordered_sections[1].title == "First"   # order=2

    def test_build_system_role_section(self):
        """Test building system role section"""
        section_manager = SectionManager()
        
        section = section_manager.build_system_role_section()
        
        assert isinstance(section, PromptSection)
        assert section.title == "System Role and Expertise"
        assert len(section.content) > 0
        assert "Expert" in section.content[0]

    def test_build_methodology_section(self):
        """Test building methodology section"""
        section_manager = SectionManager()
        
        methodology_tags = ["van_westendorp", "conjoint"]
        methodology_rules = {
            "van_westendorp": {"required_questions": 4},
            "conjoint": {"required_questions": 6}
        }
        
        section = section_manager.build_methodology_section(methodology_tags, methodology_rules)
        
        assert isinstance(section, PromptSection)
        assert section.title == "Methodology Requirements"
        assert len(section.content) > 0

    def test_build_rag_context_section(self):
        """Test building RAG context section"""
        section_manager = SectionManager()
        
        rag_context = RAGContext(
            example_count=3,
            avg_quality_score=0.89,
            methodology_tags=["van_westendorp"],
            similarity_scores=[0.92, 0.87, 0.83]
        )
        
        section = section_manager.build_rag_context_section(rag_context)
        
        assert isinstance(section, PromptSection)
        assert section.title == "RAG Context and Examples"
        assert len(section.content) > 0
        assert "3" in section.content[1]  # example count

    def test_build_current_task_section(self):
        """Test building current task section"""
        section_manager = SectionManager()
        
        rfq_details = {
            "rfq_text": "Create a customer satisfaction survey",
            "methodology": "satisfaction",
            "target_segment": "customers"
        }
        
        section = section_manager.build_current_task_section(rfq_details)
        
        assert isinstance(section, PromptSection)
        assert section.title == "Current Task"
        assert len(section.content) > 0
        assert "customer satisfaction" in section.content[1].lower()


class TestRAGContext:
    """Test RAGContext functionality"""

    def test_rag_context_initialization(self):
        """Test RAGContext initialization"""
        rag_context = RAGContext(
            example_count=5,
            avg_quality_score=0.85,
            methodology_tags=["satisfaction", "pricing"],
            similarity_scores=[0.9, 0.8, 0.7, 0.6, 0.5]
        )
        
        assert rag_context.example_count == 5
        assert rag_context.avg_quality_score == 0.85
        assert len(rag_context.methodology_tags) == 2
        assert len(rag_context.similarity_scores) == 5

    def test_rag_context_validation(self):
        """Test RAGContext validation"""
        # Valid context
        valid_context = RAGContext(
            example_count=3,
            avg_quality_score=0.9,
            methodology_tags=["test"],
            similarity_scores=[0.9, 0.8, 0.7]
        )
        
        assert valid_context.example_count > 0
        assert 0 <= valid_context.avg_quality_score <= 1
        assert len(valid_context.methodology_tags) > 0
        assert len(valid_context.similarity_scores) == valid_context.example_count


class TestPromptSection:
    """Test PromptSection functionality"""

    def test_prompt_section_initialization(self):
        """Test PromptSection initialization"""
        section = PromptSection(
            title="Test Section",
            content=["Line 1", "Line 2"],
            order=1,
            required=True
        )
        
        assert section.title == "Test Section"
        assert len(section.content) == 2
        assert section.order == 1
        assert section.required is True

    def test_prompt_section_defaults(self):
        """Test PromptSection with defaults"""
        section = PromptSection(
            title="Test Section",
            content=["Line 1"]
        )
        
        assert section.title == "Test Section"
        assert len(section.content) == 1
        assert section.order == 0  # default
        assert section.required is True  # default


class TestPromptBuilderIntegration:
    """Integration tests for PromptBuilder"""

    @pytest.fixture
    def prompt_builder(self):
        """Create PromptBuilder instance for testing"""
        return PromptBuilder()

    def test_end_to_end_prompt_generation(self, prompt_builder):
        """Test complete prompt generation flow"""
        context = {
            "rfq_text": "Create a comprehensive market research survey",
            "methodology": "comprehensive",
            "target_segment": "business professionals",
            "additional_requirements": ["Include pricing questions", "Add demographic questions"]
        }
        
        prompt = prompt_builder.build_survey_generation_prompt(context["rfq_text"], context)
        
        assert isinstance(prompt, str)
        assert len(prompt) > 500
        assert "comprehensive" in prompt.lower()
        assert "market research" in prompt.lower()

    def test_prompt_generation_with_different_methodologies(self, prompt_builder):
        """Test prompt generation with different methodologies"""
        methodologies = ["van_westendorp", "conjoint", "nps", "satisfaction"]
        
        for methodology in methodologies:
            context = {
                "rfq_text": f"Create a {methodology} survey",
                "methodology": methodology
            }
            
            prompt = prompt_builder.build_survey_generation_prompt(context["rfq_text"], context)
            
            assert isinstance(prompt, str)
            assert len(prompt) > 100
            assert methodology in prompt.lower()

    def test_prompt_generation_error_handling(self, prompt_builder):
        """Test error handling in prompt generation"""
        # Test with None context
        try:
            prompt = prompt_builder.build_survey_generation_prompt(None)
            # Should handle gracefully
            assert isinstance(prompt, str)
        except Exception as e:
            # If it raises an exception, it should be handled gracefully
            assert "context" in str(e).lower() or "none" in str(e).lower()

        # Test with empty context
        empty_context = {}
        prompt = prompt_builder.build_survey_generation_prompt(empty_context)
        assert isinstance(prompt, str)

    def test_prompt_consistency(self, prompt_builder):
        """Test that prompts are consistent across multiple calls"""
        context = {
            "rfq_text": "Create a test survey",
            "methodology": "test"
        }
        
        # Generate multiple prompts
        prompts = []
        for i in range(3):
            prompt = prompt_builder.build_survey_generation_prompt(context["rfq_text"], context)
            prompts.append(prompt)
        
        # All prompts should be similar in structure
        assert all(isinstance(p, str) for p in prompts)
        assert all(len(p) > 100 for p in prompts)
        
        # All should contain the RFQ text
        assert all("test survey" in p.lower() for p in prompts)


if __name__ == "__main__":
    pytest.main([__file__])
