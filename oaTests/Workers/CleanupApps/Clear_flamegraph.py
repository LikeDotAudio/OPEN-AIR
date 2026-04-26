import os

project_root = os.getcwd()

import inspect
import logging

# oaTests/Workers/CleanupApps/Clear_flamegraph.py
# Author: Anthony Peter Kuzub
# Version: 20260323.Standalone.1
#
# Description: Standalone maintenance script to wipe the OPEN-AIR Flame Graph data.
import shutil

from oaLogging.Methods.matrix_gate import matrix_log

# Configure standard logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("FlameGraphCleanup")

def cleanup_flamegraph():
    """Purges the flame graph data files."""
    target = os.path.join(project_root, "oaDataLogs", "FlameGraph")

    matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "📡📤📤 [CLEAR_FLAMEGRAPH] Starting Flame Graph cleanup...", "INFO")

    if os.path.exists(target):
        items_purged = 0
        for filename in os.listdir(target):
            file_path = os.path.join(target, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"  Deleting flamegraph file: {file_path}", "INFO")
                    os.unlink(file_path)
                    items_purged += 1
                elif os.path.isdir(file_path):
                    matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"  Deleting flamegraph directory: {file_path}", "INFO")
                    shutil.rmtree(file_path)
                    items_purged += 1
            except Exception as e:
                logger.error(f"   ⚠️ Failed to delete {file_path}. Reason: {e}")

        if items_purged > 0:
            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"   ✅ Purged {items_purged} items from: {os.path.relpath(target, project_root)}", "INFO")
        else:
            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"   ℹ️ {os.path.relpath(target, project_root)} was already empty.", "INFO")
    else:
        logger.warning(f"   ⚠️ Directory not found: {os.path.relpath(target, project_root)}")

if __name__ == "__main__":
    cleanup_flamegraph()
