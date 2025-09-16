#!/usr/bin/env python3
"""
Model preloading script for Survey Engine
This script preloads all required ML models to avoid startup delays
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import settings
from src.services.embedding_service import EmbeddingService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def preload_models():
    """Preload all required models"""
    logger.info("🔄 [ModelPreloader] Starting model preloading...")
    
    try:
        # Preload embedding model
        logger.info("🔄 [ModelPreloader] Preloading embedding model...")
        embedding_service = EmbeddingService()
        await embedding_service.preload_model()
        logger.info("✅ [ModelPreloader] Embedding model preloaded successfully")
        
        # Test the model with a sample text
        logger.info("🔄 [ModelPreloader] Testing embedding model...")
        test_embedding = await embedding_service.get_embedding("test text for validation")
        logger.info(f"✅ [ModelPreloader] Embedding test successful, dimension: {len(test_embedding)}")
        
        logger.info("🎉 [ModelPreloader] All models preloaded successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ [ModelPreloader] Model preloading failed: {str(e)}")
        return False

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(preload_models())
    sys.exit(0 if success else 1)










