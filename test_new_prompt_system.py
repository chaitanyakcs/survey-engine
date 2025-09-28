#!/usr/bin/env python3
"""
Test the new SOTA prompt system
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from src.services.prompt_service import PromptService
from src.services.prompt_builder import RAGContext

def test_new_prompt_system():
    """Test the new modular prompt system"""
    print("🧪 Testing new SOTA prompt system...")

    # Create prompt service
    prompt_service = PromptService()

    # Sample context
    context = {
        "rfq_details": {
            "title": "Coffee Machine Research",
            "text": "We need to understand consumer preferences for premium coffee machines in the $500-2000 price range. Focus on brand preference, feature importance, and price sensitivity.",
            "category": "Consumer Electronics",
            "segment": "Premium Coffee Enthusiasts",
            "goal": "Market Research",
            "methodology_tags": ["van_westendorp", "conjoint"]
        }
    }

    # Sample golden examples (these would normally come from RAG)
    golden_examples = [
        {
            "rfq_text": "Coffee machine market research",
            "quality_score": 0.92,
            "methodology_tags": ["van_westendorp", "pricing"],
            "similarity": 0.85,
            "survey_json": {"title": "Sample Survey", "questions": []}
        },
        {
            "rfq_text": "Premium appliance research",
            "quality_score": 0.88,
            "methodology_tags": ["conjoint"],
            "similarity": 0.78,
            "survey_json": {"title": "Another Survey", "questions": []}
        }
    ]

    methodology_blocks = []

    # Test new system
    print("📝 Generating prompt with new system...")
    prompt = prompt_service.create_survey_prompt(
        rfq_text=context["rfq_details"]["text"],
        context=context,
        golden_examples=golden_examples,
        methodology_blocks=methodology_blocks
    )

    print(f"✅ Prompt generated successfully!")
    print(f"📏 Prompt length: {len(prompt)} characters")

    # Check for key improvements
    improvements = []

    if "CONTEXTUAL KNOWLEDGE:" in prompt:
        improvements.append("✅ RAG context summary (not full examples)")

    if prompt.count("CRITICAL") < 5:
        improvements.append("✅ Reduced redundant CRITICAL warnings")

    if "Based on 2 high-quality similar surveys" in prompt:
        improvements.append("✅ Golden examples converted to context")

    if len(prompt) < 15000:  # Should be much shorter than old 25k+ char prompts
        improvements.append("✅ Significantly shorter prompt")

    if "JSON FORMATTING RULES:" in prompt:
        improvements.append("✅ Consolidated formatting requirements")

    print(f"\n🎯 Improvements detected: {len(improvements)}/5")
    for improvement in improvements:
        print(f"  {improvement}")

    # Show sample of the prompt
    print(f"\n📄 Prompt preview (first 500 chars):")
    print(f"{prompt[:500]}...")

    print(f"\n🔚 Prompt ending (last 200 chars):")
    print(f"...{prompt[-200:]}")

    return len(improvements) >= 4  # Should have most improvements

if __name__ == "__main__":
    success = test_new_prompt_system()
    if success:
        print("\n🎉 New prompt system test PASSED!")
    else:
        print("\n❌ New prompt system test FAILED!")
        sys.exit(1)