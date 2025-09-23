#!/usr/bin/env python3
"""
Debug script to test JSON parsing from LLM responses
"""

import re
import json

def test_json_extraction():
    # Sample response from the logs - this is the truncated version
    response_content = """```json
{
    "pillar_scores": {
        "content_validity": 0.85,
        "methodological_rigor": 0.78,
        "clarity_comprehensibility": 0.82,
        "structural_coherence": 0.80,
        "deployment_readiness": 0.88
    },
    "weighted_score": 0.82,
    "overall_grade": "B+",
    "detailed_analysis": {
        "content_validity": {
            "score": 0.85,
            "strengths": ["Covers all primary research objectives", "Questions align well with RFQ requirements"],
            "wea..."""
    
    print("Testing JSON extraction with truncated response...")
    print(f"Response content length: {len(response_content)}")
    print(f"Response starts with: {response_content[:50]}")
    print(f"Response ends with: {response_content[-50:]}")
    
    # Test the regex pattern
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_content, re.DOTALL)
    print(f"Regex match found: {json_match is not None}")
    
    if json_match:
        print(f"Captured group length: {len(json_match.group(1))}")
        print(f"Captured group: {json_match.group(1)[:100]}...")
        try:
            result = json.loads(json_match.group(1))
            print("✅ JSON parsing successful!")
            print(f"Pillar scores: {result.get('pillar_scores', {})}")
            return result
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            print(f"Captured content: {json_match.group(1)}")
    
    # Test alternative approach
    print("\nTesting alternative approach...")
    start_idx = response_content.find('{')
    if start_idx != -1:
        print(f"Found opening brace at index: {start_idx}")
        
        # Find balanced braces
        brace_count = 0
        end_idx = start_idx
        
        for i in range(start_idx, len(response_content)):
            char = response_content[i]
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i + 1
                    break
        
        print(f"Found closing brace at index: {end_idx}")
        print(f"Brace count balanced: {brace_count == 0}")
        
        if brace_count == 0:
            json_str = response_content[start_idx:end_idx]
            print(f"Extracted JSON string length: {len(json_str)}")
            try:
                result = json.loads(json_str)
                print("✅ Alternative JSON parsing successful!")
                return result
            except json.JSONDecodeError as e:
                print(f"❌ Alternative JSON parsing failed: {e}")
                print(f"JSON string: {json_str[:200]}...")
    
    print("\nTesting with complete JSON...")
    # Test with complete JSON
    complete_response = """```json
{
    "pillar_scores": {
        "content_validity": 0.85,
        "methodological_rigor": 0.78,
        "clarity_comprehensibility": 0.82,
        "structural_coherence": 0.80,
        "deployment_readiness": 0.88
    },
    "weighted_score": 0.82,
    "overall_grade": "B+",
    "detailed_analysis": {
        "content_validity": {
            "score": 0.85,
            "strengths": ["Covers all primary research objectives", "Questions align well with RFQ requirements"],
            "weaknesses": ["Some questions could be more specific"]
        }
    }
}
```"""
    
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', complete_response, re.DOTALL)
    print(f"Complete response regex match found: {json_match is not None}")
    
    if json_match:
        try:
            result = json.loads(json_match.group(1))
            print("✅ Complete JSON parsing successful!")
            print(f"Pillar scores: {result.get('pillar_scores', {})}")
            return result
        except json.JSONDecodeError as e:
            print(f"❌ Complete JSON parsing failed: {e}")

if __name__ == "__main__":
    test_json_extraction()