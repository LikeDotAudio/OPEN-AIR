import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# oaTests/Workers/CleanupApps/Clear_audits.py
# Author: Anthony Peter Kuzub
# Version: 20260323.2030.1
#
# Description: Maintenance script to purge all system audit logs.

import os
import shutil
import logging

# Configure standard logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("AuditCleanup")

def cleanup_audits():
    """Purges all files from the audit data directory."""
    project_root = os.getcwd()
    target = os.path.join(project_root, "oaDataAudits")
    
    matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"📡📤📤 [CLEAR_AUDITS] Starting System Audit cleanup...", "INFO")
    
    if os.path.exists(target):
        items_purged = 0
        try:
            for filename in os.listdir(target):
                file_path = os.path.join(target, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"  Deleting audit file: {file_path}", "INFO")
                        os.unlink(file_path)
                        items_purged += 1
                    elif os.path.isdir(file_path):
                        matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"  Deleting audit directory: {file_path}", "INFO")
                        shutil.rmtree(file_path)
                        items_purged += 1
                except Exception as e:
                    logger.error(f"   ⚠️ Failed to delete {file_path}. Reason: {e}")
            
            if items_purged > 0:
                matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"   ✅ Purged {items_purged} items from: {os.path.relpath(target, project_root)}", "INFO")
            else:
                matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"   ℹ️ {os.path.relpath(target, project_root)} was already empty.", "INFO")
        except Exception as e:
            logger.error(f"   💥 CRITICAL: Could not access audit directory: {e}")
    else:
        logger.warning(f"   ⚠️ Directory not found: {os.path.relpath(target, project_root)}")

    matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"📡📤📤 [CLEAR_AUDITS] System Audit cleanup complete.", "INFO")

if __name__ == "__main__":
    cleanup_audits()
