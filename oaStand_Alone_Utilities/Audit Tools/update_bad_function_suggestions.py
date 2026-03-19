import os
import ast
import re

project_root = "/home/anthony/Documents/OPEN-AIR"
audit_file = os.path.join(project_root, "oaDataAudits/Documentation/Audits/Bad Functions.txt")
output_file = os.path.join(project_root, "oaDataAudits/Documentation/Audits/Bad Functions suggestions.txt")

def get_function_source(filepath, func_name, start_line):
    full_path = os.path.join(project_root, filepath)
    if not os.path.exists(full_path):
        return None
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # Heuristic: Find the end of the function using AST or matching indentation
        # For simplicity and context efficiency, we'll use a simple indentation check
        source = "".join(lines)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func_name and node.lineno == start_line:
                end_line = getattr(node, "end_lineno", len(lines))
                return "".join(lines[start_line-1:end_line])
    except:
        pass
    return None

def generate_suggestion(filepath, func_name, issues):
    strategies = []
    suggestions = []
    
    for issue in issues:
        if "Too many arguments" in issue:
            suggestions.append("Reduce parameter count by introducing a Parameter Object or Configuration DTO.")
            strategies.append("Pattern: Parameter Object. Encapsulate related arguments into a single class or dictionary to simplify the signature and improve readability.")
        if "Excessively large" in issue:
            suggestions.append("Decompose the function into smaller, private helper methods, each focusing on a single level of abstraction.")
            strategies.append("Pattern: Extract Method. Identify logical blocks within the function (initialization, processing, output) and move them into dedicated functions.")
        if "Deeply nested structure" in issue:
            suggestions.append("Flatten the logic by using Guard Clauses (early returns) and decomposing complex loops.")
            strategies.append("Strategy: Guard Clauses. Instead of nesting logic inside 'if' blocks, return early on invalid conditions to keep the primary logic path at a shallow indent level.")
        if "Uses flag argument" in issue:
            suggestions.append("Split the function into two distinct methods, or use polymorphism to handle different behaviors.")
            strategies.append("Strategy: Command/Query Separation. Boolean flags often indicate that a function is doing two things. Creating 'do_x()' and 'do_y()' is cleaner than 'do_thing(is_x=True)'.")
        if "Long if/else/elif chain" in issue:
            suggestions.append("Replace complex branching with a lookup table (dictionary) or use the Strategy Pattern.")
            strategies.append("Pattern: Strategy Pattern or Lookup Table. Replace hardcoded chains with a registry of handlers to make the system extensible without modifying the core logic.")

    return list(set(suggestions)), list(set(strategies))

# Parse the audit results
with open(audit_file, "r", encoding="utf-8") as f:
    content = f.read()

# Regex to find file and its functions
file_blocks = re.split(r'File: ', content)[1:]

all_suggestions = []

# Limit to top N most severe for the document to keep it useful and not just a dump
count = 0
for block in file_blocks:
    lines = block.strip().split('\n')
    filepath = lines[0]
    
    current_func = None
    current_line = None
    current_issues = []
    
    for line in lines[1:]:
        if line.startswith('  - Function:'):
            # Save previous if exists
            if current_func:
                all_suggestions.append((filepath, current_func, current_line, current_issues))
            
            match = re.search(r'Function: (.*?) \(Line (\d+)\)', line)
            current_func = match.group(1)
            current_line = int(match.group(2))
            current_issues = []
        elif line.startswith('    *'):
            current_issues.append(line.strip('* '))
    
    if current_func:
        all_suggestions.append((filepath, current_func, current_line, current_issues))

# Sort by severity (number of issues, then line count if possible)
all_suggestions.sort(key=lambda x: len(x[3]), reverse=True)

with open(output_file, "w", encoding="utf-8") as f:
    f.write("# OPEN-AIR Refactoring Guide: Bad Function Suggestions\n")
    f.write("This document provides specific strategies and code snippets for refactoring the most critical 'Bad Functions' in the project.\n\n")

    for filepath, func_name, line, issues in all_suggestions[:50]: # Top 50 severe
        source = get_function_source(filepath, func_name, line)
        suggestions, strategies = generate_suggestion(filepath, func_name, issues)
        
        f.write(f"## [{filepath}] {func_name}\n")
        f.write(f"**Location:** Line {line}\n")
        f.write("**Violations:**\n")
        for issue in issues:
            f.write(f"- {issue}\n")
        
        if source:
            f.write("\n### Current Code Snippet\n")
            f.write("```python\n")
            # Limit snippet length for the doc
            snippet_lines = source.splitlines()
            if len(snippet_lines) > 30:
                f.write("\n".join(snippet_lines[:15]) + "\n... [truncated] ...\n" + "\n".join(snippet_lines[-5:]) + "\n")
            else:
                f.write(source + "\n")
            f.write("```\n")
        
        f.write("\n### Refactoring Suggestions\n")
        for sug in suggestions:
            f.write(f"- {sug}\n")
            
        f.write("\n### Architectural Strategies\n")
        for strat in strategies:
            f.write(f"- {strat}\n")
            
        f.write("\n---\n\n")

print(f"Suggestions updated for top {min(50, len(all_suggestions))} functions.")
