# oaTests/Workers/CleanupApps/Clear_reports.py
# Author: Anthony Peter Kuzub
# Version: 20260323.2045.1
#
# Description: Maintenance script to purge old reports while preserving the latest one.

import os
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
    project_root = os.getcwd()
    target = os.path.join(project_root, "oaReports")
    
    logger.info(f"📡📤📤 [CLEAR_REPORTS] Starting Reports cleanup...")
    
    if not os.path.exists(target):
        logger.warning(f"   ⚠️ Directory not found: {os.path.relpath(target, project_root)}")
        return

    try:
        # Get all files in the directory with their full paths
        files = [os.path.join(target, f) for f in os.listdir(target) 
                 if os.path.isfile(os.path.join(target, f))]
        
        if not files:
            logger.info(f"   ℹ️ {os.path.relpath(target, project_root)} is already empty.")
            return

        # Sort files by modification time (newest first)
        files.sort(key=os.path.getmtime, reverse=True)
        
        latest_report = files[0]
        old_reports = files[1:]
        
        logger.info(f"   💎 Preserving latest report: {os.path.basename(latest_report)}")
        
        files_purged = 0
        for file_path in old_reports:
            try:
                logger.info(f"  Deleting old report: {file_path}")
                os.unlink(file_path)
                files_purged += 1
            except Exception as e:
                logger.error(f"   ⚠️ Failed to delete {file_path}. Reason: {e}")
        
        # Also handle subdirectories if any (nuke them all)
        for item in os.listdir(target):
            item_path = os.path.join(target, item)
            if os.path.isdir(item_path):
                try:
                    logger.info(f"  Deleting old report directory: {item_path}")
                    shutil.rmtree(item_path)
                    files_purged += 1
                except Exception as e:
                    logger.error(f"   ⚠️ Failed to delete directory {item_path}. Reason: {e}")

        if files_purged > 0:
            logger.info(f"   ✅ Purged {files_purged} old items from: {os.path.relpath(target, project_root)}")
        else:
            logger.info("   ℹ️ No old reports required purging.")

    except Exception as e:
        logger.error(f"   💥 CRITICAL: Error during report cleanup: {e}")

if __name__ == "__main__":
    cleanup_reports()
