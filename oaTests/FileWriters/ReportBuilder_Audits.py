# Report_Builder/ReportBuilder_Audits.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import glob
import html
import os
from datetime import datetime


def build_tab(data_dir):
    """
    Scans the audits directory and returns an HTML snippet for the tab content.
    """
    audit_files = glob.glob(os.path.join(data_dir, "*.md")) + glob.glob(os.path.join(data_dir, "*.txt"))
    if not audit_files:
        return "<h3>No Audit Reports Found</h3><p>Run an audit command to generate reports.</p>"

    # Sort by modification time (newest first)
    audit_files.sort(key=os.path.getmtime, reverse=True)

    tab_html = "<h3>Latest Audit Reports</h3>"
    for file_path in audit_files[:5]: # Show latest 5
        filename = os.path.basename(file_path)
        mtime = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')

        with open(file_path, encoding="utf-8") as f:
            # ⚡ OPTIMIZATION: Limit read to 100KB per file
            content = f.read(100000)
            if f.read(1): # Check if there's more
                content += "\n\n... (Report Truncated for Performance) ..."

        escaped_content = html.escape(content)

        tab_html += f"""
        <div class="log-entry">
            <div class="log-header">
                <span class="log-filename">{filename}</span>
                <span class="log-time">{mtime}</span>
            </div>
            <div class="markdown-content" style="padding: 15px; background: #1a1a1a; color: #ccc;">{escaped_content}</div>
        </div>
        """
    return tab_html
