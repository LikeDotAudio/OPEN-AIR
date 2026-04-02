import os
    project_root = os.getcwd()

import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# oaTests/Workers/CleanupApps/Clear_reports.py
# Author: Anthony Peter Kuzub
# Version: 20260323.2045.1
#
# Description: Maintenance script to purge old reports while preserving the latest one.

import shutil
import logging
from pathlib import Path

# Configure standard logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("ReportCleanup")

def cleanup_reports():
    """
    Purges all files from the oaReports directory except for the most recently modified one.
    """
    target = os.path.join(project_root, "oaReports")
    
    matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"📡📤📤 [CLEAR_REPORTS] Starting Reports cleanup...", "INFO")
    
    if not os.path.exists(target):
        logger.warning(f"   ⚠️ Directory not found: {os.path.relpath(target, project_root)}")
        return

    try:
        # Get all files in the directory with their full paths
        files = [os.path.join(target, f) for f in os.listdir(target) 
                 if os.path.isfile(os.path.join(target, f))]
        
        if not files:
            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"   ℹ️ {os.path.relpath(target, project_root)} is already empty.", "INFO")
            return

        # Sort files by modification time (newest first)
        files.sort(key=os.path.getmtime, reverse=True)
        
        latest_report = files[0]
        old_reports = files[1:]
        
        matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"   💎 Preserving latest report: {os.path.basename(latest_report)}", "INFO")
        
        files_purged = 0
        for file_path in old_reports:
            try:
                matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"  Deleting old report: {file_path}", "INFO")
                os.unlink(file_path)
                files_purged += 1
            except Exception as e:
                logger.error(f"   ⚠️ Failed to delete {file_path}. Reason: {e}")
        
        # Also handle subdirectories if any (nuke them all)
        for item in os.listdir(target):
            item_path = os.path.join(target, item)
            if os.path.isdir(item_path):
                try:
                    matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"  Deleting old report directory: {item_path}", "INFO")
                    shutil.rmtree(item_path)
                    files_purged += 1
                except Exception as e:
                    logger.error(f"   ⚠️ Failed to delete directory {item_path}. Reason: {e}")

        if files_purged > 0:
            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"   ✅ Purged {files_purged} old items from: {os.path.relpath(target, project_root)}", "INFO")
        else:
            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "   ℹ️ No old reports required purging.", "INFO")

    except Exception as e:
        logger.error(f"   💥 CRITICAL: Error during report cleanup: {e}")

if __name__ == "__main__":
    cleanup_reports()