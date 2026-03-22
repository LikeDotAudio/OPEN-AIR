# Report_Builder/audit_parser.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import os
import re
import glob

def parse_audit_log(file_path):
    """
    Parses an audit log file and returns a list of result dictionaries.
    Compatible with Markdown-formatted audit logs.
    """
    if not os.path.exists(file_path):
        return []

    with open(file_path, 'r') as f:
        content = f.read()

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
        # Regex to handle various statuses in parentheses
        match = re.search(r'^(.*?)\s*\((PASSED|FAILED|SKIPPED|ERROR|UNEXPECTED ERROR)\)', header_line)
        if match:
            name = match.group(1).strip()
            status_raw = match.group(2).upper()
            
            # Map statuses to reporting categories: passed, failed, error, skipped
            status_map = {
                "PASSED": "passed",
                "FAILED": "failed",
                "SKIPPED": "skipped",
                "ERROR": "error",
                "UNEXPECTED ERROR": "error"
            }
            status = status_map.get(status_raw, "error")
            
            # Extract description (Goal/Achievement)
            # For PASSED, it's the text following the header until the next separator
            # For FAILED, we look for error details
            
            description = ""
            cause = ""
            
            if status == "passed":
                # Find the first non-empty line after the header
                for l in lines[1:]:
                    if l.strip() and not l.strip().startswith('---'):
                        description = l.strip()
                        break
            elif status == "failed":
                # Extract error details
                error_match = re.search(r'\*\*Error Details:\*\*\s*```text\s*(.*?)\s*```', section, re.DOTALL)
                if error_match:
                    cause = error_match.group(1).strip()
                
                # Try to find partial output as description
                partial_match = re.search(r'\*\*Partial Output:\*\*\s*(.*?)\s*(?:---|##|$)', section, re.DOTALL)
                if partial_match:
                    description = partial_match.group(1).strip().split('\n')[0]
            elif status == "error":
                # Extract error message
                error_msg_match = re.search(r'\*\*Error:\*\*\s*(.*?)\s*(?:---|##|$)', section, re.DOTALL)
                if error_msg_match:
                    cause = error_msg_match.group(1).strip()
            
            if not description:
                description = f"Architectural audit for {name}"

            results.append({
                "name": f"Audit: {name}",
                "status": status,
                "description": description,
                "cause": cause.replace('\n', '<br>'),
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
