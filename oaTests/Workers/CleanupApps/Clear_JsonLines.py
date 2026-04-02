import os
project_root = os.getcwd()

import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# oaTests/Workers/CleanupApps/Clear_JsonLines.py
# Author: Anthony Peter Kuzub
# Version: 20260328.0.1
#
# Description: Maintenance script to purge all system JSON Lines logs.

import shutil
import logging

# Configure standard logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("JsonLinesCleanup")

def cleanup_jsonlines():
    """Purges all files from the JsonLines data directory."""
    target = os.path.join(project_root, "oaDataLogs", "JsonLines")
    
    matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"📡📤📤 [CLEAR_JSONLINES] Starting JsonLines cleanup...", "INFO")
    
    if os.path.exists(target):
        items_purged = 0
        try:
            for filename in os.listdir(target):
                file_path = os.path.join(target, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"  Deleting JsonLines file: {file_path}", "INFO")
                        os.unlink(file_path)
                        items_purged += 1
                    elif os.path.isdir(file_path):
                        matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"  Deleting JsonLines directory: {file_path}", "INFO")
                        shutil.rmtree(file_path)
                        items_purged += 1
                except Exception as e:
                    logger.error(f"   ⚠️ Failed to delete {file_path}. Reason: {e}")
            
            if items_purged > 0:
                matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"   ✅ Purged {items_purged} items from: {os.path.relpath(target, project_root)}", "INFO")
            else:
                matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"   ℹ️ {os.path.relpath(target, project_root)} was already empty.", "INFO")
        except Exception as e:
            logger.error(f"   💥 CRITICAL: Could not access JsonLines directory: {e}")
    else:
        logger.warning(f"   ⚠️ Directory not found: {os.path.relpath(target, project_root)}")

    matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"📡📤📤 [CLEAR_JSONLINES] JsonLines cleanup complete.", "INFO")

if __name__ == "__main__":
    cleanup_jsonlines()