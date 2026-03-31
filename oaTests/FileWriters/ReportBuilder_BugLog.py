# Report_Builder/ReportBuilder_BugLog.py
# Author: Gemini
# Version: 20260322.1430.1
#
# Description: Scans the BugLog directory for bug reports and returns HTML content.

import os
import glob
from datetime import datetime

def build_tab(data_dir):
    """
    Scans the BugLog directory and returns an HTML snippet for the tab content.
    """
    bug_files = glob.glob(os.path.join(data_dir, "bug_*.log")) + glob.glob(os.path.join(data_dir, "*.txt"))
    if not bug_files:
        return "<h3>No Bug Logs Found</h3><p>Excellent. No active bug reports in the queue.</p>"

    # Sort by modification time (newest first)
    bug_files.sort(key=os.path.getmtime, reverse=True)

    html = "<h3>Active Bug Log Queue</h3>"
    for file_path in bug_files[:5]: # Show latest 5
        filename = os.path.basename(file_path)
        mtime = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
        
        from collections import deque
        try:
            with open(file_path, 'r', errors='replace') as f:
                # Use deque to efficiently keep only the last 500 lines
                lines = deque(f, maxlen=500)
                content = "".join(lines)
                if len(lines) == 500:
                    content = "... [truncated for performance] ...\n" + content
        except Exception as e:
            content = f"Error reading log: {e}"
        
        html += f"""
        <div class="log-entry bug-log">
            <div class="log-header">
                <span class="log-filename">{filename}</span>
                <span class="log-time">{mtime}</span>
            </div>
            <pre class="log-content">{content}</pre>
        </div>
        """
    return html
