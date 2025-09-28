#!/usr/bin/env python3
"""
Comprehensive test suite for the new SOTA prompt system
Tests all major functionality and edge cases
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from src.services.prompt_service import PromptService
from src.services.prompt_builder import PromptBuilder, RAGContext, SectionManager, OutputFormatter

def test_prompt_builder_components():
    """Test individual components of the PromptBuilder"""
    print("🧪 Testing PromptBuilder components...")

    # Test SectionManager
    section_manager = SectionManager()

    # Test system role section
    role_section = section_manager.build_system_role_section()
    assert "Expert Survey Designer" in role_section.content[0]
    assert role_section.order == 1
    print("✅ System role section test passed")

    # Test RAG context section
    rag_context = RAGContext(
        example_count=3,
        avg_quality_score=0.89,
        methodology_tags=["van_westendorp", "conjoint"],
        similarity_scores=[0.92, 0.87, 0.83]
    )
    rag_section = section_manager.build_rag_context_section(rag_context)
    assert "Based on 3 high-quality similar surveys" in rag_section.content[1]
    assert "0.89" in rag_section.content[2]  # avg quality score
    print("✅ RAG context section test passed")

    # Test JSON requirements section
    json_section = OutputFormatter.get_json_requirements_section()
    assert "MANDATORY: Generate survey using SECTIONS format" in json_section.content[1]
    assert json_section.order == 6
    print("✅ JSON requirements section test passed")

def test_rag_context_conversion():
    """Test conversion of golden examples to RAG context"""
    print("🧪 Testing RAG context conversion...")

    prompt_service = PromptService()

    # Test with various golden examples
    golden_examples = [
        {
            "quality_score": 0.95,
            "methodology_tags": ["van_westendorp", "pricing"],
            "similarity": 0.92
        },
        {
            "quality_score": 0.87,
            "methodology_tags": ["conjoint", "choice_modeling"],
            "similarity": 0.85
        },
        {
            "quality_score": 0.91,
            "methodology_tags": ["nps"],
            "similarity": 0.78
        }
    ]

    rag_context = prompt_service._convert_golden_examples_to_rag_context(golden_examples)

    assert rag_context is not None
    assert rag_context.example_count == 3
    assert abs(rag_context.avg_quality_score - 0.91) < 0.01  # (0.95 + 0.87 + 0.91) / 3
    assert "van_westendorp" in rag_context.methodology_tags
    assert "conjoint" in rag_context.methodology_tags
    assert len(rag_context.similarity_scores) == 3
    print("✅ RAG context conversion test passed")

def test_prompt_length_reduction():
    """Test that new prompts are significantly shorter"""
    print("🧪 Testing prompt length reduction...")

    prompt_service = PromptService()

    context = {
        "rfq_details": {
            "title": "Market Research Study",
            "text": "We need comprehensive market research for our new product line including consumer preferences, pricing sensitivity, and competitive analysis.",
            "category": "Consumer Goods",
            "segment": "Premium Market",
            "goal": "Product Launch",
            "methodology_tags": ["van_westendorp", "conjoint", "nps"]
        }
    }

    # Large set of golden examples (like production)
    golden_examples = [
        {
            "rfq_text": f"Research study {i}",
            "quality_score": 0.85 + (i * 0.01),
            "methodology_tags": ["van_westendorp", "pricing"],
            "similarity": 0.9 - (i * 0.02),
            "survey_json": {
                "title": f"Survey {i}",
                "questions": [{"id": f"q{j}", "text": f"Question {j}"} for j in range(1, 11)]
            }
        } for i in range(5)  # 5 examples
    ]

    prompt = prompt_service.create_survey_prompt(
        rfq_text=context["rfq_details"]["text"],
        context=context,
        golden_examples=golden_examples,
        methodology_blocks=[]
    )

    # Should be much shorter than old 25k+ character prompts
    assert len(prompt) < 6000, f"Prompt too long: {len(prompt)} chars"
    assert len(prompt) > 2000, f"Prompt too short: {len(prompt)} chars"

    # Should contain RAG summary, not full examples
    assert "CONTEXTUAL KNOWLEDGE:" in prompt
    assert "Based on 5 high-quality similar surveys" in prompt
    assert "survey_json" not in prompt  # No raw JSON in prompt

    print(f"✅ Prompt length test passed: {len(prompt)} chars (within optimal range)")

def test_json_format_consolidation():
    """Test that JSON formatting requirements are consolidated"""
    print("🧪 Testing JSON format consolidation...")

    prompt_service = PromptService()

    context = {"rfq_details": {"text": "Simple test"}}
    prompt = prompt_service.create_survey_prompt("test", context, [], [])

    # Count occurrences of key formatting terms
    critical_count = prompt.count("CRITICAL")
    mandatory_count = prompt.count("MANDATORY")
    json_count = prompt.count("JSON")

    # Should have significantly fewer redundant warnings
    assert critical_count <= 5, f"Too many CRITICAL warnings: {critical_count}"
    assert mandatory_count <= 4, f"Too many MANDATORY warnings: {mandatory_count}"

    # Should have consolidated JSON requirements section
    assert "JSON FORMATTING RULES:" in prompt
    assert "REQUIRED JSON STRUCTURE:" in prompt

    print(f"✅ JSON consolidation test passed: {critical_count} CRITICAL, {mandatory_count} MANDATORY warnings")

def test_methodology_integration():
    """Test methodology tag integration"""
    print("🧪 Testing methodology integration...")

    prompt_service = PromptService()

    context = {
        "rfq_details": {
            "text": "Pricing research study",
            "methodology_tags": ["van_westendorp", "conjoint"]
        }
    }

    golden_examples = [
        {
            "methodology_tags": ["nps", "pricing"],
            "quality_score": 0.9,
            "similarity": 0.8
        }
    ]

    prompt = prompt_service.create_survey_prompt("test", context, golden_examples, [])

    # Should extract and combine methodology tags (this is the core functionality)
    methodology_tags = prompt_service._extract_methodology_tags(context, golden_examples)
    assert "van_westendorp" in methodology_tags
    assert "conjoint" in methodology_tags
    assert "nps" in methodology_tags
    assert "pricing" in methodology_tags

    # RAG context should include methodology information
    rag_context = prompt_service._convert_golden_examples_to_rag_context(golden_examples)
    assert "nps" in rag_context.methodology_tags
    assert "pricing" in rag_context.methodology_tags

    print("✅ Methodology integration test passed")

def test_edge_cases():
    """Test edge cases and error handling"""
    print("🧪 Testing edge cases...")

    prompt_service = PromptService()

    # Test with empty golden examples
    prompt = prompt_service.create_survey_prompt("test", {}, [], [])
    assert len(prompt) > 1000  # Should still generate valid prompt
    print("✅ Empty golden examples test passed")

    # Test with no methodology tags
    context = {"rfq_details": {"text": "Simple test"}}
    prompt = prompt_service.create_survey_prompt("test", context, [], [])
    assert "SECTIONS format" in prompt  # Core requirements should be present
    print("✅ No methodology tags test passed")

    # Test RAG context with no examples
    rag_context = prompt_service._convert_golden_examples_to_rag_context([])
    assert rag_context is None
    print("✅ Empty RAG context test passed")

def run_comprehensive_tests():
    """Run all comprehensive tests"""
    print("🚀 Starting comprehensive SOTA prompt system tests...\n")

    tests = [
        test_prompt_builder_components,
        test_rag_context_conversion,
        test_prompt_length_reduction,
        test_json_format_consolidation,
        test_methodology_integration,
        test_edge_cases
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} FAILED: {e}")
            failed += 1
        print()

    print(f"📊 Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All comprehensive tests PASSED!")
        return True
    else:
        print("❌ Some tests FAILED!")
        return False

if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)