#!/usr/bin/env python3
"""
Debug script to see what the actual LLM content looks like
"""
import asyncio
import logging
import os
import sys
from unittest.mock import MagicMock, AsyncMock, patch

# Add the src directory to the path
sys.path.insert(0, 'src')

from src.services.generation_service import GenerationService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_real_content():
    """Debug what the actual LLM content looks like"""
    
    # Create a mock database session
    mock_db = MagicMock()
    mock_connection_manager = MagicMock()
    
    # Create the service
    service = GenerationService(
        db_session=mock_db,
        workflow_id="test-workflow-123",
        connection_manager=mock_connection_manager
    )
    
    # Mock the WebSocket client
    service.ws_client = MagicMock()
    service.ws_client.send_progress_update = AsyncMock()
    
    try:
        logger.info("🚀 Testing with real Replicate API...")
        
        # Test the sync fallback method with a simple prompt
        result = await service._generate_with_sync_fallback("Generate a comprehensive survey about customer satisfaction with 25 questions. Return ONLY valid JSON format with no markdown, no explanations, no additional text. Start with { and end with }.")
        
        logger.info(f"✅ Real API test completed!")
        logger.info(f"📊 Result keys: {list(result.keys())}")
        logger.info(f"📊 Survey keys: {list(result['survey'].keys())}")
        logger.info(f"📊 Sections count: {len(result['survey'].get('sections', []))}")
        
        # Show the raw response content
        if 'generation_metadata' in result:
            raw_content = result['generation_metadata'].get('raw_response', '')
            logger.info(f"🔍 Raw response content length: {len(raw_content)}")
            logger.info(f"🔍 Raw response content (first 500 chars):")
            logger.info(f"'{raw_content[:500]}'")
            logger.info(f"🔍 Raw response content (last 500 chars):")
            logger.info(f"'{raw_content[-500:]}'")
            
            # Also check if there's a different key for the response
            logger.info(f"🔍 Generation metadata keys: {list(result['generation_metadata'].keys())}")
            for key, value in result['generation_metadata'].items():
                if isinstance(value, str) and len(value) > 50:
                    logger.info(f"🔍 Key '{key}' contains: '{value[:200]}...'")
        
        # Check if there's audit data
        if 'audit_data' in result:
            logger.info(f"🔍 Audit data keys: {list(result['audit_data'].keys())}")
            for key, value in result['audit_data'].items():
                if isinstance(value, str) and len(value) > 50:
                    logger.info(f"🔍 Audit key '{key}' contains: '{value[:200]}...'")
        
        # Check all result keys for any content
        logger.info(f"🔍 All result keys: {list(result.keys())}")
        for key, value in result.items():
            if isinstance(value, dict):
                logger.info(f"🔍 Dict key '{key}' has subkeys: {list(value.keys())}")
                for subkey, subvalue in value.items():
                    if isinstance(subvalue, str) and len(subvalue) > 100:
                        logger.info(f"🔍 {key}.{subkey} contains: '{subvalue[:200]}...'")
        
        # Count total questions
        total_questions = 0
        for section in result['survey'].get('sections', []):
            questions = section.get('questions', [])
            total_questions += len(questions)
            logger.info(f"📊 Section '{section.get('title', 'Unknown')}': {len(questions)} questions")
        
        logger.info(f"📊 Total questions: {total_questions}")
        
        if total_questions > 0:
            logger.info("✅ Questions were successfully extracted!")
        else:
            logger.error("❌ No questions were extracted!")
            
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(debug_real_content())
