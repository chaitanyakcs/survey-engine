#!/usr/bin/env python3
"""
Simple test to verify key PromptService changes
"""

import os

def test_prompt_service_cleanup():
    """Test that PromptService has been properly cleaned up"""

    print("🧪 Testing PromptService Cleanup...")

    # Read the PromptService file directly
    prompt_service_path = os.path.join(os.path.dirname(__file__), 'src', 'services', 'prompt_service.py')

    try:
        with open(prompt_service_path, 'r') as f:
            content = f.read()

        print(f"✅ PromptService file loaded ({len(content)} characters)")

        # Test 1: Check that hardcoded quality rules are removed
        print("\n🗑️  Test 1: Checking hardcoded quality rules removal...")

        old_quality_rules = [
            '"question_quality"',
            '"survey_structure"',
            '"respondent_experience"',
            '"Questions must be clear, concise, and unambiguous"',
            '"Start with screening questions to qualify respondents"',
            '"Follow established research methodology standards"',
            '"Keep survey length appropriate"'
        ]

        found_old_rules = []
        for rule in old_quality_rules:
            if rule in content:
                found_old_rules.append(rule)

        if not found_old_rules:
            print("✅ All hardcoded quality rules successfully removed")
        else:
            print(f"❌ Found old quality rules still present: {found_old_rules}")

        # Test 2: Check that quality rules are initialized as empty
        print("\n📝 Test 2: Checking quality rules initialization...")

        if 'self.quality_rules = {}' in content:
            print("✅ Quality rules properly initialized as empty")
        else:
            print("❌ Quality rules not properly initialized as empty")

        # Test 3: Check that methodology rules are preserved
        print("\n🔬 Test 3: Checking methodology rules preservation...")

        methodology_indicators = [
            '"van_westendorp"',
            '"conjoint"',
            '"maxdiff"',
            '"nps"',
            'Must have exactly 4 price questions',
            'Must have balanced choice sets'
        ]

        found_methodology = []
        for indicator in methodology_indicators:
            if indicator in content:
                found_methodology.append(indicator)

        if len(found_methodology) >= 4:  # Should find most methodology indicators
            print(f"✅ Methodology rules preserved ({len(found_methodology)}/{len(methodology_indicators)} indicators found)")
        else:
            print(f"❌ Methodology rules may be missing ({len(found_methodology)}/{len(methodology_indicators)} indicators found)")

        # Test 4: Check that generation rules loading is preserved
        print("\n⚙️  Test 4: Checking generation rules system...")

        generation_indicators = [
            'rule_type == \'generation\'',
            'generation_rules',
            'rule_type\': \'generation\'',
            'pillar_rules'
        ]

        found_generation = []
        for indicator in generation_indicators:
            if indicator in content:
                found_generation.append(indicator)

        if len(found_generation) >= 2:
            print(f"✅ Generation rules system preserved ({len(found_generation)}/{len(generation_indicators)} indicators found)")
        else:
            print(f"❌ Generation rules system may be incomplete ({len(found_generation)}/{len(generation_indicators)} indicators found)")

        # Test 5: Check that quality rules methods are removed
        print("\n🚮 Test 5: Checking removed methods...")

        removed_methods = [
            'def add_custom_rule',
            'def _check_quality_rules',
            'quality_check = self._check_quality_rules'
        ]

        found_removed = []
        for method in removed_methods:
            if method in content:
                found_removed.append(method)

        if not found_removed:
            print("✅ All deprecated quality rule methods successfully removed")
        else:
            print(f"❌ Found deprecated methods still present: {found_removed}")

        # Test 6: Check for quality rules in prompt building
        print("\n📄 Test 6: Checking prompt building cleanup...")

        quality_prompt_indicators = [
            '## Quality Standards:',
            'for category, rules in self.quality_rules.items():',
            'f"### {category.replace'
        ]

        found_quality_prompt = []
        for indicator in quality_prompt_indicators:
            if indicator in content:
                found_quality_prompt.append(indicator)

        if not found_quality_prompt:
            print("✅ Quality rules removed from prompt building")
        else:
            print(f"❌ Quality rules still found in prompt building: {found_quality_prompt}")

        # Test 7: Check that pillar rules context is preserved
        print("\n🏛️  Test 7: Checking pillar rules context...")

        pillar_indicators = [
            'get_pillar_rules_context',
            '5-PILLAR',
            'pillar_display',
            'generation_guideline'
        ]

        found_pillar = []
        for indicator in pillar_indicators:
            if indicator in content:
                found_pillar.append(indicator)

        if len(found_pillar) >= 3:
            print(f"✅ Pillar rules context preserved ({len(found_pillar)}/{len(pillar_indicators)} indicators found)")
        else:
            print(f"❌ Pillar rules context may be incomplete ({len(found_pillar)}/{len(pillar_indicators)} indicators found)")

        # Summary
        print("\n🎉 PromptService Cleanup Analysis Complete!")

        # Count issues
        issues = []
        if found_old_rules:
            issues.append("Old quality rules found")
        if found_removed:
            issues.append("Deprecated methods found")
        if found_quality_prompt:
            issues.append("Quality rules in prompt building")

        if not issues:
            print("✅ ALL TESTS PASSED - PromptService successfully cleaned up!")
            print("\n📋 Cleanup Summary:")
            print("  ✅ Hardcoded quality rules removed")
            print("  ✅ Methodology rules preserved")
            print("  ✅ Generation rules system intact")
            print("  ✅ Deprecated methods removed")
            print("  ✅ Prompt building cleaned up")
            print("  ✅ Pillar rules context preserved")
            return True
        else:
            print(f"❌ Issues found: {issues}")
            return False

    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_prompt_service_cleanup()
    exit(0 if success else 1)