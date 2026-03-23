# Audit Tools/audit_bad_threading.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import os
import ast
from collections import defaultdict

project_root = "."
output_file = os.path.join(project_root, "oaDataAudits/Documentation/Audits/Bad_Threading_Audit.md")

class ConcurrencyVisitor(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        self.issues = []
        self.uses_threading = False
        self.current_class = None
        self.in_lock_block = False
        self.lock_start_line = 0

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name in ["threading", "multiprocessing", "asyncio", "queue"]:
                self.uses_threading = True
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module in ["threading", "multiprocessing", "asyncio", "queue"]:
            self.uses_threading = True
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        old_class = self.current_class
        self.current_class = node.name
        
        # Heuristic for SRP: Does a class with "Threading" in name have many business-logic methods?
        # Or does a business-logic class have too many locks?
        methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        lock_calls = 0
        for m in methods:
            for subnode in ast.walk(m):
                if isinstance(subnode, ast.With):
                    if self.is_lock_context(subnode):
                        lock_calls += 1
        
        if lock_calls > 3 and not any(x in node.name.lower() for x in ["worker", "bridge", "manager", "client"]):
            self.issues.append({
                "line": node.lineno,
                "type": "Mixed Responsibilities",
                "detail": f"Class '{node.name}' contains {lock_calls} locked sections but appears to be business logic.",
                "snippet": f"class {node.name}:"
            })

        self.generic_visit(node)
        self.current_class = old_class

    def is_lock_context(self, node):
        # Checks if 'with X:' uses a lock-like variable
        if isinstance(node.items[0].context_expr, ast.Attribute):
            attr = node.items[0].context_expr.attr.lower()
            if "lock" in attr or "mutex" in attr or "sema" in attr:
                return True
        elif isinstance(node.items[0].context_expr, ast.Name):
            name = node.items[0].context_expr.id.lower()
            if "lock" in name or "mutex" in name:
                return True
        return False

    def visit_With(self, node):
        if self.is_lock_context(node):
            # Check length of the 'with' block
            start = node.lineno
            end = getattr(node, "end_lineno", start)
            length = end - start
            if length > 10:
                self.issues.append({
                    "line": start,
                    "type": "Oversized Critical Section",
                    "detail": f"Locked block is {length} lines long. Minimize locks to absolute critical state changes.",
                    "snippet": "with lock: ..."
                })
            
            # Check for expensive calls inside lock
            for subnode in ast.walk(node):
                if isinstance(subnode, ast.Call):
                    if isinstance(subnode.func, ast.Attribute):
                        if subnode.func.attr in ["sleep", "run", "execute", "query", "urlopen", "read_file"]:
                            self.issues.append({
                                "line": subnode.lineno,
                                "type": "Blocking Call in Lock",
                                "detail": f"Expensive or blocking call '{subnode.func.attr}' found inside a locked section.",
                                "snippet": "with lock: ... call ..."
                            })

        self.generic_visit(node)

def analyze_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)
        visitor = ConcurrencyVisitor(filepath)
        visitor.visit(tree)
        
        # Add snippets
        lines = source.splitlines()
        for issue in visitor.issues:
            if issue["snippet"].endswith("..."):
                issue["snippet"] = lines[issue["line"]-1].strip()
        
        return visitor.issues if visitor.uses_threading else []
    except Exception:
        return []

all_results = []
for root, dirs, files in os.walk(project_root):
    if any(ignore in root for ignore in [".git", "__pycache__", "DATA", ".crawler", "node_modules"]):
        continue
    for file in files:
        if file.endswith(".py"):
            filepath = os.path.join(root, file)
            file_issues = analyze_file(filepath)
            if file_issues:
                all_results.append({
                    "file": os.path.relpath(filepath, project_root),
                    "issues": file_issues
                })

# Generate Report
with open(output_file, "w", encoding="utf-8") as f:
    f.write("# Clean Code Audit: Concurrency & Threading Report\n\n")
    f.write("## Executive Summary\n")
    total_violations = sum(len(f["issues"]) for f in all_results)
    f.write(f"Analyzed codebase for Mixed Responsibilities, Oversized Critical Sections, and Blocking Calls in Locks.\n")
    f.write(f"- **Files Using Threading/Concurrency**: {len(all_results)}\n")
    f.write(f"- **Total Violations**: {total_violations}\n\n")

    f.write("## Top Offenders\n\n")
    all_results.sort(key=lambda x: len(x["issues"]), reverse=True)

    for item in all_results[:20]:
        f.write(f"### {item['file']}\n")
        grouped = defaultdict(list)
        for issue in item["issues"]:
            grouped[issue["type"]].append(issue)
        
        for issue_type, issues in grouped.items():
            f.write(f"#### {issue_type}\n")
            for iss in issues[:10]:
                f.write(f"- Line {iss['line']}: {iss['detail']}\n")
                f.write(f"  `{iss['snippet']}`\n")
        f.write("\n---\n")

print(f"Audit complete. Results written to {output_file}")
