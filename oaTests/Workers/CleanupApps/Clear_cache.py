import sys
import os
    project_root = current_script_dir.parents[2]
    
            sys.path.insert(0, str(project_root))

import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# oaTests/Workers/CleanupApps/Clear_cache.py
# Author: Anthony Peter Kuzub
# Version: 20260323.CacheClear.1
#
# Description: Master Cache Purge Script.

import shutil
import logging
from pathlib import Path

LOCAL_DEBUG = True


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
    # Current script: project_root/oaTests/Workers/CleanupApps/Clear_cache.py
    current_script_dir = Path(__file__).resolve().parent
    # Target non-log data directories
    data_dirs = [
        project_root / "oaDataCache",
        project_root / "oaDataRunningFiles",
        project_root / ".pytest_cache" / "oaDataState",
        project_root / "DATA" # Legacy compatibility
    ]

    matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"📡📤📤 [CLEAR_CACHE] Starting local cache and state purge...", "INFO")

    for data_dir in data_dirs:
        if data_dir.exists():
            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"🗑️  Nuking: {data_dir.name}", "INFO")
            try:
                # To delete CONTENTS and not the dir itself, we iterate
                items_purged = 0
                for item in data_dir.iterdir():
                    try:
                        if item.is_file() or item.is_symlink():
                            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"  Deleting cache file: {item}", "INFO")
                            item.unlink()
                            items_purged += 1
                        elif item.is_dir():
                            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"  Deleting cache directory: {item}", "INFO")
                            shutil.rmtree(item)
                            items_purged += 1
                    except Exception as e:
                        logger.error(f"  └─ ❌ Failed to delete {item.name}: {e}")
                
                if LOCAL_DEBUG: 
                    if items_purged > 0:
                        matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"  └─ 💥 Purged {items_purged} items from {data_dir.name}.", "INFO")
                    else:
                        matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"  └─ ℹ️ {data_dir.name} was already empty.", "INFO")
            except Exception as e:
                logger.error(f"  └─ ❌ Failed to access {data_dir.name}: {e}")
        else:
            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"  └─ 🤷 {data_dir.name} directory not found.", "INFO")

    # Recreate structure via path_initializer to ensure sanity
    matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🌱 Re-initializing directory structure integrity...", "INFO")
    try:
        if str(project_root) not in sys.path:
        from oaOchestration.Core.path_initializer import initialize_paths
        initialize_paths()
        matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "✨ Directory structure integrity verified.", "INFO")
    except Exception as e:
        logger.error(f"❌ Failed to initialize paths: {e}")

    matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "📡📤📤 [CLEAR_CACHE] Cache purge complete.", "INFO")

if __name__ == "__main__":
    purge_cache()