# CleanupUtilities/Clear_flamegraph.py
# Author: Anthony Peter Kuzub
# Version: 20260323.Standalone.1
#
# Description: Standalone maintenance script to wipe the OPEN-AIR Flame Graph data.

import os
import shutil
import logging

# Configure standard logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("FlameGraphCleanup")

def cleanup_flamegraph():
    """Purges the flame graph data files."""
    project_root = os.getcwd()
    target = os.path.join(project_root, "oaDataLogs", "FlameGraph")
    
    logger.info(f"📡📤📤 [CLEAR_FLAMEGRAPH] Starting Flame Graph cleanup...")
    
    if os.path.exists(target):
        items_purged = 0
        for filename in os.listdir(target):
            file_path = os.path.join(target, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    logger.info(f"  Deleting flamegraph file: {file_path}")
                    os.unlink(file_path)
                    items_purged += 1
                elif os.path.isdir(file_path):
                    logger.info(f"  Deleting flamegraph directory: {file_path}")
                    shutil.rmtree(file_path)
                    items_purged += 1
            except Exception as e:
                logger.error(f"   ⚠️ Failed to delete {file_path}. Reason: {e}")
        
        if items_purged > 0:
            logger.info(f"   ✅ Purged {items_purged} items from: {os.path.relpath(target, project_root)}")
        else:
            logger.info(f"   ℹ️ {os.path.relpath(target, project_root)} was already empty.")
    else:
        logger.warning(f"   ⚠️ Directory not found: {os.path.relpath(target, project_root)}")

if __name__ == "__main__":
    cleanup_flamegraph()
