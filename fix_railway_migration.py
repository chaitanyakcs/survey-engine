#!/usr/bin/env python3
"""
Script to manually fix Railway migration state
This script will mark the database as being at the latest revision
"""

import os
import sys
import subprocess
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def main():
    """Fix Railway migration state by marking it as up to date"""
    
    logger.info("🔧 Fixing Railway migration state...")
    
    # The target revision that adds the labels column
    target_revision = "8d392146a12e"
    
    try:
        # Mark the database as being at the target revision
        logger.info(f"📝 Marking database as revision: {target_revision}")
        
        result = subprocess.run(
            ["alembic", "stamp", target_revision],
            capture_output=True,
            text=True,
            cwd="/app"
        )
        
        if result.returncode == 0:
            logger.info("✅ Successfully marked database as up to date")
            logger.info(f"Output: {result.stdout}")
            return True
        else:
            logger.error(f"❌ Failed to stamp database: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error fixing migration state: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
