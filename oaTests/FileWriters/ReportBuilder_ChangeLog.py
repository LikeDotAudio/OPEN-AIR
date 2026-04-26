# Report_Builder/ReportBuilder_ChangeLog.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import os


def build_tab(data_dir):
    """
    Reads the main CHANGELOG.md and returns an HTML snippet for the tab content.
    """
    changelog_path = os.path.join(data_dir, "CHANGELOG.md")
    if not os.path.exists(changelog_path):
        return "<h3>No Change Logs Found</h3><p>Ensure CHANGELOG.md exists in the data directory.</p>"

    from collections import deque
    try:
        with open(changelog_path) as f:
            # Use deque to efficiently keep only the last 1000 lines
            lines = deque(f, maxlen=1000)
            content = "".join(lines)
    except Exception as e:
        return f"<h3>Error Reading Change Log</h3><p>{e}</p>"

    html = f"""
    <h3>Latest Change Logs</h3>
    <div class="log-entry">
        <div class="log-header">
            <span class="log-filename">CHANGELOG.md</span>
        </div>
        <pre class="log-content">{content}</pre>
    </div>
    """
    return html
