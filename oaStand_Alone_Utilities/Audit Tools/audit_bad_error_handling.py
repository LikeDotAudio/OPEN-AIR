import os
import ast
import re

project_root = "."
output_file = os.path.join(project_root, "oaDataAudits/Documentation/Audits/Bad_Error_Handling_Audit.md")

def analyze_error_handling(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)
    except Exception as e:
        return []

    issues = []
    lines = source.splitlines()

    for node in ast.walk(tree):
        # 1. Catching everything (generic Exception or bare except)
        if isinstance(node, ast.Try):
            for handler in node.handlers:
                # Bare except:
                if handler.type is None:
                    # Check if it has 'pass'
                    has_pass = any(isinstance(s, ast.Pass) for s in handler.body)
                    issues.append({
                        "line": handler.lineno,
                        "type": "Bare except block",
                        "severity": "High" if has_pass else "Medium",
                        "snippet": lines[handler.lineno-1].strip()
                    })
                # Catching Exception:
                elif isinstance(handler.type, ast.Name) and handler.type.id == "Exception":
                    has_pass = any(isinstance(s, ast.Pass) for s in handler.body)
                    # Check if it logs or prints
                    has_logging = any("log" in ast.dump(s).lower() or "print" in ast.dump(s).lower() for s in handler.body)
                    if not has_logging or has_pass:
                        issues.append({
                            "line": handler.lineno,
                            "type": "Generic Exception catch without proper logging",
                            "severity": "Medium",
                            "snippet": lines[handler.lineno-1].strip()
                        })

        # 2. Returning None in suspected error contexts (heuristic)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for body_item in node.body:
                if isinstance(body_item, ast.Return) and body_item.value is None:
                    # Check if previous line was an 'if' that looks like an error check
                    issues.append({
                        "line": body_item.lineno,
                        "type": "Returning None (potential error code/null return)",
                        "severity": "Low",
                        "snippet": lines[body_item.lineno-1].strip()
                    })

    return issues

all_issues = []
for root, dirs, files in os.walk(project_root):
    if any(ignore in root for ignore in [".git", "__pycache__", "DATA"]):
        continue
    for file in files:
        if file.endswith(".py"):
            filepath = os.path.join(root, file)
            file_issues = analyze_error_handling(filepath)
            if file_issues:
                all_issues.append({
                    "file": os.path.relpath(filepath, project_root),
                    "issues": file_issues
                })

# Generate Report
with open(output_file, "w", encoding="utf-8") as f:
    f.write("# Bad Error Handling Audit Report\n\n")
    
    f.write("## Executive Summary\n")
    total_files = len(all_issues)
    total_violations = sum(len(f["issues"]) for f in all_issues)
    f.write(f"Analyzed codebase for silent failures, generic catches, and muddled error flows.\n")
    f.write(f"- **Files with Issues**: {total_files}\n")
    f.write(f"- **Total Violations**: {total_violations}\n\n")
    
    f.write("## Top Offenders (Silent Failures & Bare Excepts)\n\n")
    
    # Sort by number of issues
    all_issues.sort(key=lambda x: len(x["issues"]), reverse=True)
    
    for item in all_issues[:20]:
        f.write(f"### {item['file']}\n")
        for issue in item["issues"]:
            f.write(f"- Line {issue['line']}: **{issue['type']}** (Severity: {issue['severity']})\n")
            f.write(f"  `{issue['snippet']}`\n")
        f.write("\n")

print(f"Audit complete. Results written to {output_file}")
