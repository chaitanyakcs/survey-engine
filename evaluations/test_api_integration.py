#!/usr/bin/env python3
"""
Test API Integration with Advanced Evaluators
Verify that the API endpoints return advanced evaluation results
"""

import asyncio
import json
import sys
import requests
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

def test_api_integration():
    """
    Test that the API integration works with advanced evaluators
    """
    
    print("🌐 Testing API Integration with Advanced Evaluators")
    print("=" * 60)
    
    # Test survey data
    test_survey_data = {
        "title": "B2B Software Pricing Strategy Survey",
        "description": "Understanding pricing preferences and decision criteria for B2B software solutions",
        "questions": [
            {"id": "q1", "text": "What is your role in software purchasing decisions?", "type": "multiple_choice"},
            {"id": "q2", "text": "Don't you think expensive software is better?", "type": "rating"},
            {"id": "q3", "text": "How important are price and features in your selection?", "type": "rating"},
            {"id": "q4", "text": "What challenges do you face when evaluating software?", "type": "text"},
        ],
        "metadata": {
            "methodology": ["Van Westendorp PSM"]
        }
    }
    
    api_base_url = "http://localhost:8000"  # Adjust if different
    
    try:
        print("📡 Sending test evaluation request to API...")
        
        # Test the evaluation endpoint
        response = requests.post(
            f"{api_base_url}/pillar-scores/evaluate",
            json=test_survey_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print("\\n✅ API INTEGRATION SUCCESSFUL!")
            print(f"📊 Overall Grade: {result.get('overall_grade', 'N/A')}")
            print(f"🎯 Overall Score: {result.get('weighted_score', 0):.2f}")
            print()
            
            print("📊 PILLAR BREAKDOWN:")
            for pillar in result.get('pillar_breakdown', []):
                print(f"   {pillar['display_name']}: {pillar['score']:.2f} (Grade: {pillar['grade']})")
            print()
            
            print("💡 RECOMMENDATIONS RECEIVED:")
            recommendations = result.get('recommendations', [])
            for i, rec in enumerate(recommendations[:5], 1):  # Show first 5
                print(f"   {i}. {rec}")
            print()
            
            print("📈 EVALUATION SUMMARY:")
            summary = result.get('summary', 'No summary available')
            print(f"   {summary}")
            print()
            
            # Check for advanced evaluation indicators
            if "Advanced Chain-of-Thought Analysis" in summary:
                print("🚀 ADVANCED EVALUATION CONFIRMED!")
                print("   ✅ Chain-of-thought reasoning active")
                print("   ✅ Enhanced recommendations available")
                
                if "objectives extracted" in summary:
                    print("   ✅ Semantic RFQ analysis working")
                if "biases detected" in summary:
                    print("   ✅ Advanced bias detection active")
                if "Confidence:" in summary:
                    print("   ✅ Confidence scoring available")
                
                return "advanced"
            elif "Fallback mode active" in summary:
                print("⚠️  ADVANCED EVALUATION IN FALLBACK MODE")
                print("   • Advanced evaluators loaded but using fallback logic")
                print("   • This is expected without LLM API tokens")
                return "fallback"
            else:
                print("⚠️  LEGACY EVALUATION DETECTED")
                print("   • API is using old PillarScoringService")
                print("   • Advanced evaluators not integrated properly")
                return "legacy"
                
        else:
            print(f"❌ API REQUEST FAILED: {response.status_code}")
            print(f"Response: {response.text}")
            return "failed"
            
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Cannot connect to API server")
        print("   Make sure the server is running on http://localhost:8000")
        print("   Try running: uvicorn src.main:app --reload")
        return "connection_error"
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT ERROR: API request took too long")
        return "timeout"
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return "error"

def test_pillar_rules_endpoint():
    """
    Test the pillar rules summary endpoint
    """
    
    print("\\n🔍 Testing Pillar Rules Summary Endpoint...")
    
    try:
        response = requests.get(
            "http://localhost:8000/pillar-scores/rules/summary",
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Rules Summary: {result.get('total_rules', 0)} total rules across {result.get('total_pillars', 0)} pillars")
            return True
        else:
            print(f"⚠️  Rules endpoint returned: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"⚠️  Rules endpoint error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing API Integration - Advanced Evaluator Connection")
    print("Testing that the API serves advanced evaluation results to the UI")
    print()
    
    # Test main evaluation
    evaluation_result = test_api_integration()
    
    # Test rules endpoint
    rules_working = test_pillar_rules_endpoint()
    
    print("\\n" + "=" * 60)
    print("🎯 API INTEGRATION TEST SUMMARY")
    
    if evaluation_result == "advanced":
        print("✅ PERFECT: Advanced evaluators fully integrated into API")
        print("   🎉 UI will receive sophisticated chain-of-thought analysis")
        print("   💡 Users get specific actionable recommendations")
        print("   📊 Confidence scores and detailed metadata available")
    elif evaluation_result == "fallback":
        print("✅ GOOD: Advanced evaluators integrated, running in fallback mode")
        print("   🔄 Still significantly better than legacy system")
        print("   📈 Add LLM API tokens for full chain-of-thought reasoning")
    elif evaluation_result == "legacy":
        print("❌ ISSUE: API still using legacy evaluation system")
        print("   🔧 Check advanced evaluator imports in pillar_scores.py")
        print("   📋 May need to restart API server to load new code")
    elif evaluation_result == "connection_error":
        print("❌ SETUP: API server not running")
        print("   🚀 Start server with: uvicorn src.main:app --reload")
    else:
        print(f"❌ ERROR: Integration test failed ({evaluation_result})")
    
    print("\\nNext: Test in your UI by generating a survey and checking pillar scores!")