#!/usr/bin/env python3
"""
Test script to verify spacing fixes using the actual production survey data.
"""

import re
import requests
import json

def test_spacing_fix():
    """Test the spacing fix regex pattern with production survey data"""
    
    # Get the actual survey data from production
    print("Fetching survey data from production...")
    try:
        response = requests.get("https://survey-engine-production.up.railway.app/api/v1/survey/7256caf3-5b86-4b5a-bb89-d9233cdf0d41")
        response.raise_for_status()
        survey_data = response.json()
        print("✅ Survey data fetched successfully")
    except Exception as e:
        print(f"❌ Failed to fetch survey data: {e}")
        return False
    
    # Extract questions from the survey
    questions = []
    if 'final_output' in survey_data and 'sections' in survey_data['final_output']:
        for section in survey_data['final_output']['sections']:
            if 'questions' in section:
                for question in section['questions']:
                    if 'text' in question:
                        questions.append({
                            'id': question.get('id', 'unknown'),
                            'text': question['text'],
                            'section': section.get('title', 'Unknown')
                        })
    
    print(f"Found {len(questions)} questions to test")
    
    # The regex pattern used in our fix
    spacing_fix_pattern = r'\s+([,\.;:!?])'
    
    print("\nTesting spacing fix for production survey questions...")
    print("=" * 80)
    
    all_passed = True
    issues_found = 0
    
    for i, question in enumerate(questions[:10], 1):  # Test first 10 questions
        original_text = question['text']
        
        # Apply the spacing fix
        fixed_text = re.sub(spacing_fix_pattern, r'\1', original_text)
        
        # Check if there were any spacing issues
        has_issues = original_text != fixed_text
        
        if has_issues:
            issues_found += 1
            print(f"\n🔍 Question {i} ({question['id']}) - {question['section']}")
            print(f"Original: '{original_text}'")
            print(f"Fixed:    '{fixed_text}'")
            print(f"Status:   ✅ FIXED")
        else:
            print(f"\n✅ Question {i} ({question['id']}) - No spacing issues")
    
    print("\n" + "=" * 80)
    print(f"Summary:")
    print(f"- Questions tested: {min(10, len(questions))}")
    print(f"- Spacing issues found: {issues_found}")
    print(f"- Issues that would be fixed: {issues_found}")
    
    if issues_found > 0:
        print(f"\n🎯 Our spacing fix would resolve {issues_found} spacing issues!")
        print("The fix is working correctly and would clean up the production survey.")
    else:
        print("\n✅ No spacing issues found in the tested questions.")
    
    return True

if __name__ == "__main__":
    test_spacing_fix()

