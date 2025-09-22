#!/usr/bin/env python3
"""
Fix server restart issues by addressing database migrations and resource management
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration_fix():
    """Run the duplicate rules migration fix"""
    logger.info("🔧 Running migration fix for duplicate rules...")
    
    try:
        # Run the migration
        result = subprocess.run([
            "psql", 
            os.getenv("DATABASE_URL", "postgresql://postgres:tLUyiANweqFgCQglIczDMqagjstLWWNM@postgres.railway.internal:5432/railway"),
            "-f", "migrations/015_fix_duplicate_rules.sql"
        ], capture_output=True, text=True, check=True)
        
        logger.info("✅ Migration fix completed successfully")
        logger.info(f"Migration output: {result.stdout}")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Migration fix failed: {e}")
        logger.error(f"Error output: {e.stderr}")
        return False

def optimize_model_loading():
    """Optimize model loading to prevent memory issues"""
    logger.info("🔧 Optimizing model loading...")
    
    # Create an optimized model preloader
    optimized_preloader = """
#!/usr/bin/env python3
import os
import sys
import asyncio
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import settings
from src.services.embedding_service import EmbeddingService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global model instance to prevent multiple loading
_embedding_service = None

async def get_embedding_service():
    global _embedding_service
    if _embedding_service is None:
        logger.info("🔄 Loading embedding model (first time only)...")
        _embedding_service = EmbeddingService()
        await _embedding_service.preload_model()
        logger.info("✅ Embedding model loaded successfully")
    return _embedding_service

async def preload_models():
    try:
        # Only load once
        await get_embedding_service()
        
        # Test with minimal text
        service = await get_embedding_service()
        test_embedding = await service.get_embedding("test")
        logger.info(f"✅ Model test successful, dimension: {len(test_embedding)}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Model loading failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(preload_models())
    sys.exit(0 if success else 1)
"""
    
    with open("preload_models_optimized.py", "w") as f:
        f.write(optimized_preloader)
    
    # Make it executable
    os.chmod("preload_models_optimized.py", 0o755)
    
    logger.info("✅ Optimized model preloader created")
    return True

def create_restart_monitor():
    """Create a restart monitor script"""
    logger.info("🔧 Creating restart monitor...")
    
    monitor_script = """#!/bin/bash
# Restart monitor for Survey Engine
# This script monitors the application and restarts it if it crashes

LOG_FILE="/app/restart_monitor.log"
MAX_RESTARTS=5
RESTART_COUNT=0

log_with_timestamp() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_with_timestamp "Starting restart monitor..."

while [ $RESTART_COUNT -lt $MAX_RESTARTS ]; do
    log_with_timestamp "Starting Survey Engine (attempt $((RESTART_COUNT + 1))/$MAX_RESTARTS)..."
    
    # Start the application
    ./start.sh both &
    APP_PID=$!
    
    # Wait for the application to exit
    wait $APP_PID
    EXIT_CODE=$?
    
    log_with_timestamp "Application exited with code $EXIT_CODE"
    
    if [ $EXIT_CODE -eq 0 ]; then
        log_with_timestamp "Application exited normally, stopping monitor"
        break
    else
        RESTART_COUNT=$((RESTART_COUNT + 1))
        if [ $RESTART_COUNT -lt $MAX_RESTARTS ]; then
            log_with_timestamp "Application crashed, restarting in 10 seconds..."
            sleep 10
        else
            log_with_timestamp "Maximum restart attempts reached, stopping monitor"
            break
        fi
    fi
done

log_with_timestamp "Restart monitor stopped"
"""
    
    with open("restart_monitor.sh", "w") as f:
        f.write(monitor_script)
    
    os.chmod("restart_monitor.sh", 0o755)
    logger.info("✅ Restart monitor created")
    return True

def main():
    """Main fix function"""
    logger.info("🚀 Starting server restart fixes...")
    
    # Step 1: Fix database migrations
    if not run_migration_fix():
        logger.error("❌ Failed to fix database migrations")
        return False
    
    # Step 2: Optimize model loading
    if not optimize_model_loading():
        logger.error("❌ Failed to optimize model loading")
        return False
    
    # Step 3: Create restart monitor
    if not create_restart_monitor():
        logger.error("❌ Failed to create restart monitor")
        return False
    
    logger.info("✅ All fixes completed successfully!")
    logger.info("📋 Next steps:")
    logger.info("1. Deploy the updated code")
    logger.info("2. Run: ./restart_monitor.sh")
    logger.info("3. Monitor the logs for stability")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
