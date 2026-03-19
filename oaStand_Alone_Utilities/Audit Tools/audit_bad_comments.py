import os
import re
from collections import defaultdict

project_root = "."
output_file = os.path.join(project_root, "oaDataAudits/Documentation/Audits/Bad_Comments_Audit.md")

# Regex for commented-out code heuristics
CODE_RE = re.compile(r"^\s*#\s*(if|else|elif|def|class|for|while|import|from|self\.|return|yield|try|except|print\(|tk\.)\b")
# Regex for journal entries (Dates or Version/REV tags)
JOURNAL_RE = re.compile(r"(202\d-\d{2}-\d{2}|v\d+\.\d+|REV\d+|Author:|Modified:)", re.IGNORECASE)

def analyze_comments_and_formatting(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception:
        return []

    issues = []
    consecutive_empty = 0
    in_journal_block = False
    
    for i, line in enumerate(lines):
        lineno = i + 1
        stripped = line.strip()
        
        # 1. Vertical Distance / Formatting (Excessive empty lines)
        if not stripped:
            consecutive_empty += 1
            if consecutive_empty > 2:
                issues.append({
                    "line": lineno,
                    "type": "Formatting: Vertical Distance",
                    "detail": "Excessive vertical white space (more than 2 empty lines).",
                    "snippet": "[Empty Line]"
                })
        else:
            consecutive_empty = 0

        # 2. Commented-out Code
        if CODE_RE.match(line):
            # Exclude common comment patterns that might trigger false positives
            if "TODO" not in line and "FIXME" not in line:
                issues.append({
                    "line": lineno,
                    "type": "Commented-out Code",
                    "detail": "Line appears to be commented-out source code.",
                    "snippet": stripped
                })

        # 3. Journal/History Comments
        if stripped.startswith("#") and JOURNAL_RE.search(stripped):
            # Heuristic: If we see multiple date/version lines in the first 50 lines, it's a journal
            if lineno < 50:
                issues.append({
                    "line": lineno,
                    "type": "Journal/History Comment",
                    "detail": "Change log or version history found in file header.",
                    "snippet": stripped
                })

        # 4. Redundant/Obsolete (Simple heuristic: Comment is very similar to code)
        if "#" in line and not stripped.startswith("#"):
            code_part, comment_part = line.split("#", 1)
            code_part = code_part.strip().lower()
            comment_part = comment_part.strip().lower()
            # If comment just repeats a variable name or simple operation
            if len(comment_part) > 3 and comment_part in code_part:
                issues.append({
                    "line": lineno,
                    "type": "Redundant Comment",
                    "detail": "Inline comment repeats information already present in the code.",
                    "snippet": stripped
                })

    return issues

all_results = []
for root, dirs, files in os.walk(project_root):
    if any(ignore in root for ignore in [".git", "__pycache__", "DATA", ".crawler", "node_modules"]):
        continue
    for file in files:
        if file.endswith(".py"):
            filepath = os.path.join(root, file)
            file_issues = analyze_comments_and_formatting(filepath)
            if file_issues:
                all_results.append({
                    "file": os.path.relpath(filepath, project_root),
                    "issues": file_issues
                })

# Generate Report
with open(output_file, "w", encoding="utf-8") as f:
    f.write("# Clean Code Audit: Bad Comments & Formatting Report\n\n")
    f.write("## Executive Summary\n")
    total_violations = sum(len(f["issues"]) for f in all_results)
    f.write(f"Analyzed codebase for commented-out code, redundant comments, journal headers, and vertical distance issues.\n")
    f.write(f"- **Files with Issues**: {len(all_results)}\n")
    f.write(f"- **Total Violations**: {total_violations}\n\n")

    f.write("## Top Offenders\n\n")
    # Sort by number of issues
    all_results.sort(key=lambda x: len(x["issues"]), reverse=True)

    for item in all_results[:30]:
        f.write(f"### {item['file']}\n")
        # Group issues by type
        grouped = defaultdict(list)
        for issue in item["issues"]:
            grouped[issue["type"]].append(issue)
        
        for issue_type, issues in grouped.items():
            f.write(f"#### {issue_type}\n")
            for iss in issues[:10]:
                f.write(f"- Line {iss['line']}: {iss['detail']}\n")
                f.write(f"  `{iss['snippet']}`\n")
            if len(issues) > 10:
                f.write(f"- ... and {len(issues) - 10} more.\n")
        f.write("\n---\n")

print(f"Audit complete. Results written to {output_file}")
