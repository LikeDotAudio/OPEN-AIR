# CleanupUtilities/DeleteCache.py
# Author: Anthony Peter Kuzub
# Version: 20260321.CacheClear.1
#
# Description: Master Cache Purge Script.

import os
import shutil
import logging
import sys
from pathlib import Path

LOCAL_DEBUG = True    # Set to False in production, True for dev on this file

# Configure standard logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("CachePurge")

def purge_cache():
    """
    Deletes the local cache and running state files.
    Excludes log directories handled by clear_logs.py.
    """
    # oaTests/Core/CleanupUtilities/DeleteCache.py -> project_root
    current_script_dir = Path(__file__).resolve().parent
    project_root = current_script_dir.parents[2]
    
    # Target non-log data directories
    data_dirs = [
        project_root / "oaDataCache",
        project_root / "oaDataRunningFiles",
        project_root / ".pytest_cache" / "oaDataState",
        project_root / "DATA" # Legacy compatibility
    ]

    if LOCAL_DEBUG: logger.info("🧹 Starting local cache and state purge...")

    for data_dir in data_dirs:
        if data_dir.exists():
            if LOCAL_DEBUG: logger.info(f"🗑️  Nuking: {data_dir.name}")
            try:
                # To delete CONTENTS and not the dir itself, we iterate
                files_purged = 0
                for item in data_dir.iterdir():
                    try:
                        if item.is_file() or item.is_symlink():
                            item.unlink()
                            files_purged += 1
                        elif item.is_dir():
                            shutil.rmtree(item)
                            files_purged += 1
                    except Exception as e:
                        logger.error(f"  └─ ❌ Failed to delete {item.name}: {e}")
                
                if LOCAL_DEBUG: 
                    if files_purged > 0:
                        logger.info(f"  └─ 💥 Purged {files_purged} items from {data_dir.name}.")
                    else:
                        logger.info(f"  └─ ℹ️ {data_dir.name} was already empty.")
            except Exception as e:
                logger.error(f"  └─ ❌ Failed to access {data_dir.name}: {e}")
        else:
            if LOCAL_DEBUG: logger.info(f"  └─ 🤷 {data_dir.name} directory not found.")

    # Recreate structure via path_initializer to ensure sanity
    if LOCAL_DEBUG: logger.info("🌱 Re-initializing directory structure integrity...")
    try:
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        from oaOchestration.Core.path_initializer import initialize_paths
        initialize_paths()
        if LOCAL_DEBUG: logger.info("✨ Directory structure integrity verified.")
    except Exception as e:
        logger.error(f"❌ Failed to initialize paths: {e}")

    if LOCAL_DEBUG: logger.info("✅ Cache purge complete.")

if __name__ == "__main__":
    purge_cache()
