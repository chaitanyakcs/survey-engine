#!/usr/bin/env python3
"""
Debug script to test JSON extraction patterns
"""
import re
import json

# Sample content that might be generated (based on the logs showing 24,745 characters)
sample_content = '''
{
  "title": "Market Research Survey",
  "description": "Comprehensive market research study",
  "sections": [
    {
      "id": 1,
      "title": "Demographics",
      "description": "Basic demographic information",
      "questions": [
        {
          "id": "q1",
          "text": "What is your age?",
          "type": "single_choice",
          "options": ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"],
          "required": true
        },
        {
          "id": "q2", 
          "text": "What is your annual household income?",
          "type": "single_choice",
          "options": ["Under $50k", "$50k-$75k", "$75k-$100k", "$100k-$150k", "$150k+"],
          "required": true
        }
      ]
    }
  ]
}
'''

def test_patterns():
    """Test the current extraction patterns"""
    print("=== TESTING CURRENT PATTERNS ===")
    
    patterns = [
        ("Complete ID+Text objects", r'\{\s*"id"\s*:\s*"([^"]*)"[^}]*"text"\s*:\s*"([^"]*)"[^}]*\}'),
        ("Complete Text+ID objects", r'\{\s*"text"\s*:\s*"([^"]*)"[^}]*"id"\s*:\s*"([^"]*)"[^}]*\}'),
        ("Partial ID+Text patterns", r'"id"\s*:\s*"([^"]*)"[^,}]*,?[^,}]*"text"\s*:\s*"([^"]*)"'),
        ("Partial Text+ID patterns", r'"text"\s*:\s*"([^"]*)"[^,}]*,?[^,}]*"id"\s*:\s*"([^"]*)"'),
        ("Flexible ID+Text", r'"id"\s*:\s*"([^"]*)"[^}]*?"text"\s*:\s*"([^"]*)"'),
        ("Flexible Text+ID", r'"text"\s*:\s*"([^"]*)"[^}]*?"id"\s*:\s*"([^"]*)"'),
        ("Text only patterns", r'"text"\s*:\s*"([^"]*)"'),
    ]
    
    for pattern_name, pattern in patterns:
        matches = list(re.finditer(pattern, sample_content, re.DOTALL))
        print(f"{pattern_name}: {len(matches)} matches")
        for i, match in enumerate(matches[:2]):  # Show first 2
            print(f"  Match {i+1}: {match.group(0)[:100]}...")
        print()

def test_improved_patterns():
    """Test improved patterns that should work better"""
    print("=== TESTING IMPROVED PATTERNS ===")
    
    # More flexible patterns that should catch the actual format
    improved_patterns = [
        ("Question objects (any order)", r'\{\s*[^}]*"id"\s*:\s*"([^"]*)"[^}]*"text"\s*:\s*"([^"]*)"[^}]*\}'),
        ("Question objects (text first)", r'\{\s*[^}]*"text"\s*:\s*"([^"]*)"[^}]*"id"\s*:\s*"([^"]*)"[^}]*\}'),
        ("Any text field", r'"text"\s*:\s*"([^"]*)"'),
        ("Any id field", r'"id"\s*:\s*"([^"]*)"'),
    ]
    
    for pattern_name, pattern in improved_patterns:
        matches = list(re.finditer(pattern, sample_content, re.DOTALL))
        print(f"{pattern_name}: {len(matches)} matches")
        for i, match in enumerate(matches[:2]):  # Show first 2
            print(f"  Match {i+1}: {match.group(0)[:100]}...")
        print()

def test_direct_json():
    """Test direct JSON parsing"""
    print("=== TESTING DIRECT JSON PARSING ===")
    try:
        result = json.loads(sample_content)
        print("✅ Direct JSON parsing succeeded!")
        print(f"Title: {result.get('title')}")
        print(f"Sections: {len(result.get('sections', []))}")
        for section in result.get('sections', []):
            print(f"  Section: {section.get('title')} - {len(section.get('questions', []))} questions")
    except json.JSONDecodeError as e:
        print(f"❌ Direct JSON parsing failed: {e}")

if __name__ == "__main__":
    test_patterns()
    test_improved_patterns()
    test_direct_json()

