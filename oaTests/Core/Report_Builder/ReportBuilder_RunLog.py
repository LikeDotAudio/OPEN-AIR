import os
import glob
from datetime import datetime

def build_tab(data_dir):
    """
    Scans the application run logs and returns an HTML snippet for the tab content.
    """
    log_files = glob.glob(os.path.join(data_dir, "Application_*.log"))
    if not log_files:
        return "<h3>No Application Run Logs Found</h3><p>Application logs will appear here after the system is launched.</p>"

    # Sort by modification time (newest first)
    log_files.sort(key=os.path.getmtime, reverse=True)

    html = "<h3>Application Run Log Browser</h3>"
    for file_path in log_files[:5]: # Show latest 5
        filename = os.path.basename(file_path)
        mtime = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
        
        with open(file_path, 'r', errors='replace') as f:
            # For run logs, usually only show the last 1000 lines if they are huge
            content = f.read()
            lines = content.splitlines()
            if len(lines) > 1000:
                content = "... [truncated] ...\n" + "\n".join(lines[-1000:])
        
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
