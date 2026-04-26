# oaTests/Workers/CleanupApps/Clear_logs.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import os
import shutil


def cleanup_logs(report_path):
    """
    Finalizes the report generation by confirming the file location
    and purging the source log directories that have now been ingested.
    """
    if report_path:
        # Corrected f-string formatting for multi-line output
        print("✨ The report was generated perfectly, and is stored here:")
        print(f"   📍 {os.path.realpath(report_path)}")

    project_root = os.getcwd()
    # ⚡ NEW REQUIREMENT: Purge EVERYTHING inside oaDataLogs
    log_root = os.path.join(project_root, "oaDataLogs")

    print("📡📤📤 [CLEAR_LOGS] Starting master log sweeper (Purging oaDataLogs)...")

    if os.path.exists(log_root):
        items_purged = 0
        for filename in os.listdir(log_root):
            file_path = os.path.join(log_root, filename)
            # Skip the hidden .gitkeep or similar if they exist, or just nuke it all
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    print(f"  Deleting log file: {file_path}")
                    os.unlink(file_path)
                    items_purged += 1
                elif os.path.isdir(file_path):
                    print(f"  Deleting log directory: {file_path}")
                    shutil.rmtree(file_path)
                    items_purged += 1
            except Exception as e:
                print(f"   ⚠️ Failed to delete {file_path}. Reason: {e}")

        if items_purged > 0:
            print(f"   ✅ Purged {items_purged} top-level items and all their contents from: {os.path.relpath(log_root, project_root)}")
        else:
            print(f"   ℹ️ {os.path.relpath(log_root, project_root)} was already empty.")
    else:
        print(f"   ⚠️ Log directory not found: {os.path.relpath(log_root, project_root)}")

    print("📡📤📤 [CLEAR_LOGS] Log cleanup complete.")

if __name__ == "__main__":
    # If run directly, we'll perform the cleanup without the specific report path message.
    cleanup_logs(None)
