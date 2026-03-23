# Report_Builder/clear_logs.py
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
        print(f"\n✨ The report was generated perfectly, and is stored here:")
        print(f"   📍 {os.path.realpath(report_path)}")

    project_root = os.getcwd()
    targets = [
        os.path.join(project_root, "oaDataAudits"),
        os.path.join(project_root, "oaDataLogs", "ApplicationRunLog"),
        os.path.join(project_root, "oaDataLogs", "BugLog"),
        os.path.join(project_root, "oaDataLogs", "ChangeLog"),
        os.path.join(project_root, "oaDataLogs", "Errors")
    ]

    print(f"\n🧹 Starting report sweeper (Log Cleanup)...")

    for target in targets:
        if os.path.exists(target):
            # We want to delete the CONTENTS, so we list files and subdirs
            files_purged = 0
            for filename in os.listdir(target):
                file_path = os.path.join(target, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                        files_purged += 1
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                        files_purged += 1
                except Exception as e:
                    print(f"   ⚠️ Failed to delete {file_path}. Reason: {e}")
            
            if files_purged > 0:
                print(f"   ✅ Purged {files_purged} items from: {os.path.relpath(target, project_root)}")
            else:
                print(f"   ℹ️ {os.path.relpath(target, project_root)} was already empty.")
        else:
            print(f"   ⚠️ Directory not found: {os.path.relpath(target, project_root)}")

    print(f"🏁 Log cleanup complete.\n")

if __name__ == "__main__":
    # If run directly, we'll perform the cleanup without the specific report path message.
    cleanup_logs(None)
