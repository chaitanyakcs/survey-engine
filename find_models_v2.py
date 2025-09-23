#!/usr/bin/env python3
"""
Script to find available models on Replicate
"""

import replicate
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def find_available_models():
    """Search for available models on Replicate"""
    
    # Set up Replicate API token
    api_token = os.getenv('REPLICATE_API_TOKEN')
    if not api_token:
        print("❌ REPLICATE_API_TOKEN not found in environment")
        return
    
    replicate.api_token = api_token
    
    print("🔍 Searching for available models on Replicate...")
    print("=" * 60)
    
    # Test some known working models
    known_models = [
        "openai/gpt-5",
        "openai/gpt-4o-mini", 
        "openai/gpt-4o",
        "meta-llama/llama-3.1-70b-instruct",
        "meta-llama/llama-3.1-8b-instruct",
        "meta-llama/llama-3.1-405b-instruct",
        "mistralai/mistral-7b-instruct-v0.1",
        "mistralai/mistral-7b-instruct-v0.2",
        "mistralai/mixtral-8x7b-instruct-v0.1",
        "anthropic/claude-3-5-sonnet",
        "anthropic/claude-3-5-haiku",
        "anthropic/claude-3-opus"
    ]
    
    working_models = []
    
    for model in known_models:
        try:
            model_info = replicate.models.get(model)
            print(f"✅ {model} - Found")
            print(f"   Description: {model_info.description[:100]}..." if model_info.description else "   No description")
            working_models.append(model)
        except Exception as e:
            print(f"❌ {model} - Not found: {str(e)}")
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY - Working models:")
    for model in working_models:
        print(f"  ✅ {model}")
    
    print(f"\nTotal working models found: {len(working_models)}")

if __name__ == "__main__":
    find_available_models()
