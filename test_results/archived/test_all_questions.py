#!/usr/bin/env python3
"""
Comprehensive test of all questions in the production survey.
"""

import re
import requests
import json

def test_all_questions():
    """Test spacing fixes on all questions in the production survey"""
    
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
    
    # Extract all questions from the survey
    all_questions = []
    if 'final_output' in survey_data and 'sections' in survey_data['final_output']:
        for section in survey_data['final_output']['sections']:
            if 'questions' in section:
                for question in section['questions']:
                    if 'text' in question:
                        all_questions.append({
                            'id': question.get('id', 'unknown'),
                            'text': question['text'],
                            'section': section.get('title', 'Unknown')
                        })
    
    print(f"Found {len(all_questions)} total questions to analyze")
    
    # The regex pattern used in our fix
    spacing_fix_pattern = r'\s+([,\.;:!?])'
    
    print("\nAnalyzing all questions for spacing issues...")
    print("=" * 80)
    
    issues_found = 0
    questions_with_issues = []
    
    for question in all_questions:
        original_text = question['text']
        fixed_text = re.sub(spacing_fix_pattern, r'\1', original_text)
        
        # Check if there were any spacing issues
        if original_text != fixed_text:
            issues_found += 1
            questions_with_issues.append({
                'id': question['id'],
                'section': question['section'],
                'original': original_text,
                'fixed': fixed_text
            })
    
    print(f"\n📊 COMPREHENSIVE ANALYSIS RESULTS:")
    print(f"Total questions analyzed: {len(all_questions)}")
    print(f"Questions with spacing issues: {issues_found}")
    print(f"Percentage with issues: {(issues_found/len(all_questions)*100):.1f}%")
    
    if issues_found > 0:
        print(f"\n🎯 Our spacing fix would resolve {issues_found} spacing issues!")
        print("\nSample of issues that would be fixed:")
        for i, issue in enumerate(questions_with_issues[:5], 1):
            print(f"\n{i}. {issue['id']} ({issue['section']})")
            print(f"   Original: '{issue['original']}'")
            print(f"   Fixed:    '{issue['fixed']}'")
        
        if len(questions_with_issues) > 5:
            print(f"\n   ... and {len(questions_with_issues) - 5} more issues")
    else:
        print("\n✅ No spacing issues found in any questions.")
    
    return True

if __name__ == "__main__":
    test_all_questions()

