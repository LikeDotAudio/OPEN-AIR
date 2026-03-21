import os
import glob
from datetime import datetime

def build_tab(data_dir):
    """
    Scans the audits directory and returns an HTML snippet for the tab content.
    """
    audit_files = glob.glob(os.path.join(data_dir, "*.md"))
    if not audit_files:
        return "<h3>No Audit Reports Found</h3><p>Run an audit command to generate reports.</p>"

    # Sort by modification time (newest first)
    audit_files.sort(key=os.path.getmtime, reverse=True)

    html = "<h3>Latest Audit Reports</h3>"
    for file_path in audit_files[:5]: # Show latest 5
        filename = os.path.basename(file_path)
        mtime = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        html += f"""
        <div class="log-entry">
            <div class="log-header">
                <span class="log-filename">{filename}</span>
                <span class="log-time">{mtime}</span>
            </div>
            <pre class="log-content">{content}</pre>
        </div>
        """
    return html
