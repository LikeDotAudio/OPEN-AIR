# Report_Builder/collate_data.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import os


def collate_extra_tabs(project_root):
    """
    Collates specialized report tabs (Audits, Logs, etc.) 
    by calling their respective builder modules.
    """
    try:
        from oaTests.FileWriters import (
            ReportBuilder_Audits,
            ReportBuilder_BugLog,
            ReportBuilder_ChangeLog,
            ReportBuilder_Dependencies,
            ReportBuilder_ErrorLog,
            ReportBuilder_FlameGraph,
            ReportBuilder_RunLog,
        )

        audit_html = ReportBuilder_Audits.build_tab(os.path.join(project_root, "oaDataLogs/Audits"))
        changelog_html = ReportBuilder_ChangeLog.build_tab(os.path.join(project_root, "oaDataLogs", "ChangeLog"))
        error_html = ReportBuilder_ErrorLog.build_tab(os.path.join(project_root, "oaDataLogs", "Errors"))
        runlog_html = ReportBuilder_RunLog.build_tab(os.path.join(project_root, "oaDataLogs", "ApplicationRunLog"))
        buglog_html = ReportBuilder_BugLog.build_tab(os.path.join(project_root, "oaDataLogs", "BugLog"))
        flamegraph_html = ReportBuilder_FlameGraph.build_tab(project_root)
        dependencies_html = ReportBuilder_Dependencies.build_tab()

        return {
            "audit": audit_html,
            "changelog": changelog_html,
            "error": error_html,
            "runlog": runlog_html,
            "buglog": buglog_html,
            "flamegraph": flamegraph_html,
            "dependencies": dependencies_html
        }
    except Exception as e:
        print(f"⚠️ Error during data collation: {e}")
        err_message = f"<p>Error loading tab: {e}</p>"
        return {
            "audit": err_message,
            "changelog": err_message,
            "error": err_message,
            "runlog": err_message
        }
