#!/usr/bin/env python3
"""
Script to test Anthropic models with correct parameters
"""

import replicate
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_anthropic_models():
    """Test Anthropic models with correct parameters"""
    
    # Set up Replicate API token
    api_token = os.getenv('REPLICATE_API_TOKEN')
    if not api_token:
        print("❌ REPLICATE_API_TOKEN not found in environment")
        return
    
    replicate.api_token = api_token
    
    print("🔍 Testing Anthropic models with correct parameters...")
    print("=" * 60)
    
    # Test Anthropic models
    anthropic_models = [
        "anthropic/claude-4-sonnet",
        "anthropic/claude-3.7-sonnet", 
        "anthropic/claude-3.5-haiku",
        "anthropic/claude-3.5-sonnet"
    ]
    
    working_models = []
    
    for model in anthropic_models:
        try:
            model_info = replicate.models.get(model)
            print(f"✅ {model} - Found")
            print(f"   Description: {model_info.description[:100]}..." if model_info.description else "   No description")
            working_models.append(model)
        except Exception as e:
            print(f"❌ {model} - Error: {str(e)}")
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY - Working Anthropic models:")
    for model in working_models:
        print(f"  ✅ {model}")
    
    print(f"\nTotal working Anthropic models: {len(working_models)}")
    
    # Test generation with correct parameters (min 1024 tokens)
    if working_models:
        print(f"\n🧪 Testing generation with {working_models[0]}...")
        try:
            # Test with correct parameters
            output = replicate.run(
                working_models[0],
                input={
                    "prompt": "Hello, how are you?",
                    "max_tokens": 1024
                }
            )
            print(f"✅ Generation test successful!")
            print(f"   Output: {str(output)[:100]}...")
        except Exception as e:
            print(f"❌ Generation test failed: {str(e)}")

if __name__ == "__main__":
    test_anthropic_models()
