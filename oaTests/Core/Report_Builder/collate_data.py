import os

def collate_extra_tabs(project_root):
    """
    Collates specialized report tabs (Audits, Logs, etc.) 
    by calling their respective builder modules.
    """
    try:
        from oaTests.Core.Report_Builder import ReportBuilder_Audits, ReportBuilder_ChangeLog, ReportBuilder_ErrorLog, ReportBuilder_RunLog
        
        audit_html = ReportBuilder_Audits.build_tab(os.path.join(project_root, "oaDataAudits"))
        changelog_html = ReportBuilder_ChangeLog.build_tab(os.path.join(project_root, "oaDataLogs", "ChangeLog"))
        error_html = ReportBuilder_ErrorLog.build_tab(os.path.join(project_root, "oaDataLogs", "Errors"))
        runlog_html = ReportBuilder_RunLog.build_tab(os.path.join(project_root, "oaDataLogs", "ApplicationRunLog"))
        
        return {
            "audit": audit_html,
            "changelog": changelog_html,
            "error": error_html,
            "runlog": runlog_html
        }
    except Exception as e:
        print(f"⚠️ Error during data collation: {e}")
        err_msg = f"<p>Error loading tab: {e}</p>"
        return {
            "audit": err_msg,
            "changelog": err_msg,
            "error": err_msg,
            "runlog": err_msg
        }
