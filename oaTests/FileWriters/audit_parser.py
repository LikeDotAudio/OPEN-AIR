# Report_Builder/audit_parser.py
# Author: Anthony Peter Kuzub
# Version: 1.1.0
#
# Description: Parses Markdown-formatted audit logs into structured results.
# Refactored to preserve full audit findings 1:1.

import os
import re
import glob

def parse_audit_log(file_path):
    """
    Parses an audit log file and returns a list of result dictionaries.
    Captures full 1:1 content for reporting.
    """
    if not os.path.exists(file_path):
        return []

    with open(file_path, 'r', encoding="utf-8") as f:
        # ⚡ OPTIMIZATION: Limit read to 2MB.
        content = f.read(2000000)

    # Split by "## File: "
    sections = re.split(r'## File: ', content)
    results = []

    for section in sections[1:]: # Skip the session header
        lines = section.split('\n')
        if not lines:
            continue
        
        header_line = lines[0].strip()
        
        # Extract filename and status
        # Example: AuditArchitecture.toml (PASSED)
        match = re.search(r'^(.*?)\s*\((PASSED|FAILED|SKIPPED|ERROR|UNEXPECTED ERROR)\)', header_line)
        if match:
            name = match.group(1).strip()
            status_raw = match.group(2).upper()
            
            # Map statuses to reporting categories
            status_map = {
                "PASSED": "passed",
                "FAILED": "failed",
                "SKIPPED": "skipped",
                "ERROR": "error",
                "UNEXPECTED ERROR": "error"
            }
            status = status_map.get(status_raw, "error")
            
            # Capture EVERYTHING after the header line as the body
            # We strip the trailing separator '---' if it exists at the end
            body = "\n".join(lines[1:]).strip()
            if body.endswith('---'):
                body = body[:-3].strip()
            
            # For passed audits, the body goes to description
            # For failed/error, the body goes to cause
            description = ""
            cause = ""
            
            if status == "passed":
                description = body
            else:
                cause = body
                # Extract a short summary for the description if it's a failure
                desc_match = re.search(r'\*\*Partial Output:\*\*\s*(.*?)\s*(?:---|##|$)', section, re.DOTALL)
                if desc_match:
                    description = desc_match.group(1).strip().split('\n')[0]
                else:
                    description = f"Architectural audit failure in {name}"

            results.append({
                "name": f"Audit: {name}",
                "status": status,
                "description": description,
                "cause": cause, # Preserve raw newlines, HTML generator will handle formatting
                "duration": "N/A"
            })
    
    return results

def get_latest_audit_results(data_dir):
    # Prioritize combined session logs
    session_files = glob.glob(os.path.join(data_dir, "AuditSession_*.md"))
    if session_files:
        session_files.sort(key=os.path.getmtime, reverse=True)
        return parse_audit_log(session_files[0])

    # Fallback to individual audit files or old .txt logs
    audit_files = glob.glob(os.path.join(data_dir, "*.md")) + glob.glob(os.path.join(data_dir, "*.txt"))
    if not audit_files:
        return []
    
    # Sort by modification time (newest first)
    audit_files.sort(key=os.path.getmtime, reverse=True)
    latest_file = audit_files[0]
    
    return parse_audit_log(latest_file)
