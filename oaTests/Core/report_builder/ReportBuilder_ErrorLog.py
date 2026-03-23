# Report_Builder/ReportBuilder_ErrorLog.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import os
import glob
import html
from datetime import datetime

def parse_log_line(line):
    """Parses a pipe-separated log line and returns a grid-aligned HTML row."""
    parts = [p.strip() for p in line.split('|')]
    
    if len(parts) < 5:
        # This handles tracebacks or multiline messages
        return f'<div class="log-line-raw" style="color: #e74c3c; padding: 2px 15px; font-size: 0.9em;">{html.escape(line)}</div>'
    
    # Extract columns
    timestamp = parts[0]
    level = parts[1]
    system = parts[2]
    element = parts[3]
    module = parts[4]
    message = " | ".join(parts[5:]) if len(parts) > 5 else ""
    
    # Assign color classes based on content
    level_class = f"log-level-{level.lower()}"
    system_class = f"log-system-{system.lower()}"
    
    return (
        f'<div class="log-line">'
        f'<span class="log-col log-timestamp">{html.escape(timestamp)}</span>'
        f'<span class="log-col log-type {level_class}">{html.escape(level)}</span>'
        f'<span class="log-col log-system {system_class}">{html.escape(system)}</span>'
        f'<span class="log-col log-element">{html.escape(element)}</span>'
        f'<span class="log-col log-module" title="{html.escape(module)}">{html.escape(module)}</span>'
        f'<span class="log-col log-col-message log-message">{html.escape(message)}</span>'
        f'</div>'
    )

def build_tab(data_dir):
    """
    Scans the error logs and returns an HTML snippet for the tab content.
    """
    error_files = glob.glob(os.path.join(data_dir, "errors_*.log"))
    if not error_files:
        return "<h3>No Error Logs Found</h3><p>Everything seems to be running correctly. Error logs will appear here if a crash occurs.</p>"

    # Sort by modification time (newest first)
    error_files.sort(key=os.path.getmtime, reverse=True)

    tab_html = """
    <h3>Error Log Browser</h3>
    <div class="log-controls">
        <input type="text" class="log-search" placeholder="Search error messages..." onkeyup="filterLogs('ErrorLogs')">
        <select class="log-filter-select filter-level" onchange="filterLogs('ErrorLogs')">
            <option value="">All Levels</option>
            <option value="WARNING">WARNING</option>
            <option value="ERROR">ERROR</option>
            <option value="CRITICAL">CRITICAL</option>
        </select>
        <select class="log-filter-select filter-system" onchange="filterLogs('ErrorLogs')">
            <option value="">All Systems</option>
            <option value="CORE">CORE</option>
            <option value="UI">UI</option>
            <option value="SUP">SUP</option>
        </select>
        <select class="log-filter-select filter-element" onchange="filterLogs('ErrorLogs')">
            <option value="">All Elements</option>
            <option value="BUILDER">BUILDER</option>
            <option value="ROUTER">ROUTER</option>
            <option value="DATA">DATA</option>
            <option value="COMM">COMM</option>
            <option value="SYSTEM">SYSTEM</option>
            <option value="MIDI">MIDI</option>
            <option value="OSC">OSC</option>
            <option value="SNMP">SNMP</option>
        </select>
        <input type="text" class="log-search filter-module" style="flex-grow: 0; min-width: 150px;" placeholder="Filter Module..." onkeyup="filterLogs('ErrorLogs')">
    </div>
    """
    for file_path in error_files[:5]: # Show latest 5
        filename = os.path.basename(file_path)
        mtime = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
        
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        
        processed_lines = "".join([parse_log_line(line) for line in lines])
        
        tab_html += f"""
        <div class="log-entry error-log">
            <div class="log-header">
                <span class="log-filename">{filename}</span>
                <span class="log-time">{mtime}</span>
            </div>
            <div class="log-content-scrollable">
                <div class="log-table-header">
                    <span>Time</span>
                    <span>Type</span>
                    <span>System</span>
                    <span>Element</span>
                    <span>Module</span>
                    <span>Message</span>
                </div>
                {processed_lines}
            </div>
        </div>
        """
    return tab_html
