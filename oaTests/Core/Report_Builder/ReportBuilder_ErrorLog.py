import os
import glob
from datetime import datetime

def build_tab(data_dir):
    """
    Scans the error logs and returns an HTML snippet for the tab content.
    """
    error_files = glob.glob(os.path.join(data_dir, "errors_*.log"))
    if not error_files:
        return "<h3>No Error Logs Found</h3><p>Everything seems to be running correctly. Error logs will appear here if a crash occurs.</p>"

    # Sort by modification time (newest first)
    error_files.sort(key=os.path.getmtime, reverse=True)

    html = "<h3>Error Log Browser</h3>"
    for file_path in error_files[:5]: # Show latest 5
        filename = os.path.basename(file_path)
        mtime = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
        
        with open(file_path, 'r', errors='replace') as f:
            content = f.read()
        
        html += f"""
        <div class="log-entry error-log">
            <div class="log-header">
                <span class="log-filename">{filename}</span>
                <span class="log-time">{mtime}</span>
            </div>
            <pre class="log-content">{content}</pre>
        </div>
        """
    return html
