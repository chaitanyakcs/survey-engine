#!/usr/bin/env python3
"""
Test script for LLM Audit Viewer implementation
Tests the new API endpoint and verifies data structure
"""

import requests
import json
import sys
from typing import List, Dict, Any

def test_llm_audit_endpoint(base_url: str = "http://localhost:8000", survey_id: str = None):
    """Test the LLM audit endpoint"""
    
    if not survey_id:
        print("❌ No survey ID provided. Please provide a valid survey ID.")
        print("Usage: python test_llm_audit_viewer.py <survey_id>")
        return False
    
    endpoint = f"{base_url}/api/v1/survey/{survey_id}/llm-audits"
    
    print(f"🔍 Testing LLM Audit endpoint: {endpoint}")
    
    try:
        response = requests.get(endpoint, timeout=10)
        
        if response.status_code == 200:
            audits = response.json()
            print(f"✅ Success! Found {len(audits)} LLM audit records")
            
            # Analyze the audit data
            if audits:
                print("\n📊 Audit Analysis:")
                purposes = {}
                for audit in audits:
                    purpose = audit.get('purpose', 'unknown')
                    sub_purpose = audit.get('sub_purpose', '')
                    key = f"{purpose}" + (f" ({sub_purpose})" if sub_purpose else "")
                    purposes[key] = purposes.get(key, 0) + 1
                
                for purpose, count in purposes.items():
                    print(f"  - {purpose}: {count} record(s)")
                
                # Show sample audit record structure
                sample = audits[0]
                print(f"\n📋 Sample Audit Record Structure:")
                print(f"  - ID: {sample.get('id', 'N/A')}")
                print(f"  - Purpose: {sample.get('purpose', 'N/A')}")
                print(f"  - Sub-purpose: {sample.get('sub_purpose', 'N/A')}")
                print(f"  - Model: {sample.get('model_name', 'N/A')}")
                print(f"  - Provider: {sample.get('model_provider', 'N/A')}")
                print(f"  - Success: {sample.get('success', 'N/A')}")
                print(f"  - Response Time: {sample.get('response_time_ms', 'N/A')}ms")
                print(f"  - Input Tokens: {sample.get('input_tokens', 'N/A')}")
                print(f"  - Output Tokens: {sample.get('output_tokens', 'N/A')}")
                print(f"  - Input Prompt Length: {len(sample.get('input_prompt', ''))} chars")
                print(f"  - Output Content Length: {len(sample.get('output_content', ''))} chars")
                print(f"  - Has Raw Response: {bool(sample.get('raw_response'))}")
                
                # Check for different interaction types
                has_generation = any(a.get('purpose') == 'survey_generation' for a in audits)
                has_evaluations = any(a.get('purpose') == 'evaluation' for a in audits)
                
                print(f"\n🎯 Interaction Types Found:")
                print(f"  - Survey Generation: {'✅' if has_generation else '❌'}")
                print(f"  - Evaluations: {'✅' if has_evaluations else '❌'}")
                
                if has_evaluations:
                    eval_types = set()
                    for audit in audits:
                        if audit.get('purpose') == 'evaluation':
                            eval_types.add(audit.get('sub_purpose', 'unknown'))
                    print(f"  - Evaluation Types: {', '.join(sorted(eval_types))}")
                
            else:
                print("⚠️  No audit records found for this survey")
                print("   This could mean:")
                print("   - The survey hasn't been generated yet")
                print("   - LLM audit tracking is not enabled")
                print("   - The survey ID is invalid")
            
            return True
            
        elif response.status_code == 404:
            print(f"❌ Survey not found (404): {survey_id}")
            return False
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection Error: Could not connect to {base_url}")
        print("   Make sure the backend server is running")
        return False
        
    except requests.exceptions.Timeout:
        print("❌ Timeout Error: Request took too long")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected Error: {str(e)}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_llm_audit_viewer.py <survey_id> [base_url]")
        print("Example: python test_llm_audit_viewer.py 123e4567-e89b-12d3-a456-426614174000")
        sys.exit(1)
    
    survey_id = sys.argv[1]
    base_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8000"
    
    print("🧪 LLM Audit Viewer Test")
    print("=" * 50)
    
    success = test_llm_audit_endpoint(base_url, survey_id)
    
    if success:
        print("\n✅ Test completed successfully!")
        print("\nNext steps:")
        print("1. Open the frontend application")
        print("2. Navigate to a survey")
        print("3. Click the 'View LLM Audit' button")
        print("4. Verify the modal opens with audit data")
    else:
        print("\n❌ Test failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
