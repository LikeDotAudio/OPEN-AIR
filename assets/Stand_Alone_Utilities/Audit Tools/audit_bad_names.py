import os
import ast
import re

project_root = "/home/anthony/Documents/OPEN-AIR"
output_file = os.path.join(project_root, "assets/Documentation/Audits/Bad_Names_Audit.md")

# Configuration
NOISE_WORDS = ["Data", "Info", "Variable", "List", "String"]
EXCLUDED_NUMBERS = [0, 1, -1, 0.0, 1.0, -1.0, 0.5, 2] # 2 is common for bitwise or simple logic

def is_constant_name(name):
    return name.isupper() and len(name) > 1

def analyze_naming(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)
    except Exception as e:
        return []

    issues = []
    lines = source.splitlines()

    class NamingVisitor(ast.NodeVisitor):
        def __init__(self):
            self.in_loop = False

        def visit_For(self, node):
            old_loop = self.in_loop
            self.in_loop = True
            self.generic_visit(node)
            self.in_loop = old_loop

        def visit_Name(self, node):
            # Short Variables
            if isinstance(node.ctx, ast.Store):
                if len(node.id) <= 2 and not self.in_loop and not node.id.startswith("_"):
                    issues.append({
                        "line": node.lineno,
                        "type": "Short Variable Name",
                        "detail": f"Variable '{node.id}' is too short for its scope.",
                        "snippet": lines[node.lineno-1].strip()
                    })
                
                # Noise Words
                for word in NOISE_WORDS:
                    if word.lower() in node.id.lower() and not is_constant_name(node.id):
                        issues.append({
                            "line": node.lineno,
                            "type": "Noise Word",
                            "detail": f"Variable '{node.id}' contains redundant word '{word}'.",
                            "snippet": lines[node.lineno-1].strip()
                        })

                # Prefixes
                if node.id.startswith(("m_", "s_", "i_", "f_")):
                    issues.append({
                        "line": node.lineno,
                        "type": "Encoding/Prefix",
                        "detail": f"Variable '{node.id}' uses legacy prefix.",
                        "snippet": lines[node.lineno-1].strip()
                    })

        def visit_Constant(self, node):
            # Magic Numbers
            if isinstance(node.value, (int, float)) and node.value not in EXCLUDED_NUMBERS:
                # Check if it's part of a constant assignment
                parent = self.get_parent_assignment(node)
                if parent and not is_constant_name(parent):
                    issues.append({
                        "line": node.lineno,
                        "type": "Magic Number",
                        "detail": f"Literal '{node.value}' should be a named constant.",
                        "snippet": lines[node.lineno-1].strip()
                    })

        def get_parent_assignment(self, node):
            # Simple heuristic to see if this constant is being assigned to a non-UPPER_CASE variable
            for p in ast.walk(tree):
                if isinstance(p, ast.Assign):
                    for target in p.targets:
                        if isinstance(target, ast.Name) and ast.dump(p.value).find(ast.dump(node)) != -1:
                            return target.id
            return None

        def visit_FunctionDef(self, node):
            # Function Naming (Verb Check - Heuristic)
            common_verbs = ["get", "set", "update", "create", "delete", "handle", "on_", "build", "process", "run", "add", "remove", "is_", "has_"]
            if not any(node.name.lower().startswith(v) for v in common_verbs) and not node.name.startswith("_"):
                issues.append({
                    "line": node.lineno,
                    "type": "Function Naming",
                    "detail": f"Function '{node.name}' may not be a verb phrase.",
                    "snippet": lines[node.lineno-1].strip()
                })
            self.generic_visit(node)

    visitor = NamingVisitor()
    visitor.visit(tree)
    return issues

all_issues = []
for root, dirs, files in os.walk(project_root):
    if any(ignore in root for ignore in [".git", "__pycache__", "DATA", ".crawler", "node_modules"]):
        continue
    for file in files:
        if file.endswith(".py"):
            filepath = os.path.join(root, file)
            file_issues = analyze_naming(filepath)
            if file_issues:
                all_issues.append({
                    "file": os.path.relpath(filepath, project_root),
                    "issues": file_issues
                })

# Generate Report
with open(output_file, "w", encoding="utf-8") as f:
    f.write("# Clean Code Audit: Bad Naming Report\n\n")
    f.write("## Executive Summary\n")
    total_violations = sum(len(f["issues"]) for f in all_issues)
    f.write(f"Analyzed codebase for magic numbers, short variables, noise words, and poor function names.\n")
    f.write(f"- **Files with Issues**: {len(all_issues)}\n")
    f.write(f"- **Total Violations**: {total_violations}\n\n")

    f.write("## Top Offenders\n\n")
    all_issues.sort(key=lambda x: len(x["issues"]), reverse=True)

    for item in all_issues[:30]:
        f.write(f"### {item['file']}\n")
        # Group issues by type
        from collections import defaultdict
        grouped = defaultdict(list)
        for issue in item["issues"]:
            grouped[issue["type"]].append(issue)
        
        for issue_type, issues in grouped.items():
            f.write(f"#### {issue_type}\n")
            for iss in issues[:10]: # Limit per file
                f.write(f"- Line {iss['line']}: {iss['detail']}\n")
                f.write(f"  `{iss['snippet']}`\n")
            if len(issues) > 10:
                f.write(f"- ... and {len(issues) - 10} more.\n")
        f.write("\n---\n")

print(f"Audit complete. Results written to {output_file}")
