# Audit Tools/audit_bad_functions.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import os
import ast

project_root = "."
output_file = os.path.join(project_root, "oaDataAudits/Documentation/Audits/Bad_Functions_Audit.md")

# Configuration for "Bad Function" detection
MAX_ARGS = 3 # Ideal is 0, avoid 3+
MAX_LINES = 40 # Heuristic for "doing too much"
MAX_NESTING = 3 # Indent level should not be > 1 or 2

def get_nesting_depth(node):
    max_depth = 0
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.Match)):
            max_depth = max(max_depth, 1 + get_nesting_depth(child))
        else:
            max_depth = max(max_depth, get_nesting_depth(child))
    return max_depth

def is_flag_arg(arg, default=None):
    if arg.arg.lower() in ["flag", "force", "silent"]:
        return True
    if default is not None:
        if isinstance(default, (ast.Constant, ast.NameConstant)) and isinstance(default.value, bool):
            return True
    return False

def audit_file(filepath):
    results = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)
    except Exception as e:
        return []

    lines = source.splitlines()

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_results = []
            
            # 1. Argument Count
            arg_count = len(node.args.args)
            if arg_count > MAX_ARGS:
                func_results.append(f"Too many arguments ({arg_count})")

            # 2. Function Length
            start_line = node.lineno
            end_line = getattr(node, "end_lineno", start_line)
            length = end_line - start_line
            if length > MAX_LINES:
                func_results.append(f"Excessively large ({length} lines)")

            # 3. Nesting Depth
            nesting = get_nesting_depth(node)
            if nesting >= MAX_NESTING:
                func_results.append(f"Deeply nested structure (depth {nesting})")

            # 4. Flag Arguments
            # Map defaults to args
            defaults = node.args.defaults
            args = node.args.args
            # Defaults are aligned to the end of args
            offset = len(args) - len(defaults)
            for i, arg in enumerate(args):
                default = defaults[i - offset] if i >= offset else None
                if is_flag_arg(arg, default):
                    func_results.append(f"Uses flag argument: '{arg.arg}'")

            # 5. Long If/Else chains (Heuristic)
            for body_item in node.body:
                if isinstance(body_item, ast.If):
                    if_count = 0
                    curr = body_item
                    while isinstance(curr, ast.If):
                        if_count += 1
                        if curr.orelse and len(curr.orelse) == 1 and isinstance(curr.orelse[0], ast.If):
                            curr = curr.orelse[0]
                        else:
                            break
                    if if_count > 3:
                        func_results.append(f"Long if/else/elif chain ({if_count} levels)")

            if func_results:
                results.append({
                    "file": os.path.relpath(filepath, project_root),
                    "function": node.name,
                    "line": node.lineno,
                    "issues": func_results
                })
    return results

all_results = []
for root, dirs, files in os.walk(project_root):
    if any(ignore in root for ignore in [".git", ".venv", "__pycache__", ".gemini", "node_modules", "DATA", ".crawler"]):
        continue
    for file in files:
        if file.endswith(".py"):
            filepath = os.path.join(root, file)
            all_results.extend(audit_file(filepath))

# Update the file
if os.path.exists(output_file):
    with open(output_file, "r", encoding="utf-8") as f:
        intro = f.read()
else:
    intro = "Bad functions are excessively large and try to accomplish too much, resulting in muddled intent and ambiguity of purpose..."

# Split intro if it already has audit findings
if "--- AUDIT RESULTS ---" in intro:
    intro = intro.split("--- AUDIT RESULTS ---")[0]

with open(output_file, "w", encoding="utf-8") as f:
    f.write(intro.strip() + "\n\n")
    f.write("--- AUDIT RESULTS ---\n")
    f.write("The following functions violate clean code principles (too many arguments, too large, deep nesting, or flag arguments):\n\n")
    
    # Group by file
    from collections import defaultdict
    grouped = defaultdict(list)
    for r in all_results:
        grouped[r['file']].append(r)
        
    for file, items in sorted(grouped.items()):
        f.write(f"File: {file}\n")
        for item in items:
            f.write(f"  - Function: {item['function']} (Line {item['line']})\n")
            for issue in item['issues']:
                f.write(f"    * {issue}\n")
        f.write("\n")

print(f"Audit complete. {len(all_results)} problematic functions found.")
