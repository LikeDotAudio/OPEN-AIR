import os
import ast
from collections import defaultdict

project_root = "/home/anthony/Documents/OPEN-AIR"
output_file = os.path.join(project_root, "assets/Documentation/Audits/Bad_Class_Objects_Audit.md")

# Thresholds
GOD_CLASS_METHODS = 15
GOD_CLASS_ATTRS = 10
TRAIN_WRECK_DEPTH = 3

class ClassStructureVisitor(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        self.issues = []
        self.current_class = None
        self.class_methods = []
        self.class_attrs = set()
        self.method_var_usage = defaultdict(set)

    def visit_ClassDef(self, node):
        old_class = self.current_class
        self.current_class = node.name
        self.class_methods = []
        self.class_attrs = set()
        self.method_var_usage = defaultdict(set)

        # 1. SRP Name Check
        bad_words = ["Manager", "Processor", "Super", "And", "Controller", "Helper"]
        for word in bad_words:
            if word.lower() in node.name.lower():
                self.issues.append({
                    "line": node.lineno,
                    "type": "SRP Violation (Naming)",
                    "detail": f"Class '{node.name}' uses noise word '{word}' indicating mixed responsibilities.",
                    "snippet": f"class {node.name}:"
                })

        self.generic_visit(node)

        # 2. God Class Check
        method_count = len([n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))])
        if method_count > GOD_CLASS_METHODS:
            self.issues.append({
                "line": node.lineno,
                "type": "God Class (Size)",
                "detail": f"Class '{node.name}' has {method_count} methods (Threshold: {GOD_CLASS_METHODS}).",
                "snippet": f"class {node.name}:"
            })

        # 3. Cohesion Check (Simple heuristic)
        if len(self.class_attrs) > 5 and method_count > 5:
            # Check for methods that use a disjoint set of attributes
            # (Skipping detailed graph analysis for brevity, using a count heuristic)
            uncohesive_methods = 0
            for m, attrs in self.method_var_usage.items():
                if len(attrs) == 0: uncohesive_methods += 1
            
            if uncohesive_methods > method_count / 2:
                self.issues.append({
                    "line": node.lineno,
                    "type": "Low Cohesion",
                    "detail": f"Class '{node.name}' has {uncohesive_methods} methods that do not use any instance variables.",
                    "snippet": f"class {node.name}:"
                })

        self.current_class = old_class

    def visit_Attribute(self, node):
        # Detect instance variable usage
        if isinstance(node.value, ast.Name) and node.value.id == "self":
            if self.current_class:
                self.class_attrs.add(node.attr)
                # Find current method
                for parent in reversed(self.stack):
                    if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        self.method_var_usage[parent.name].add(node.attr)
                        break
        
        # 4. Law of Demeter (Train Wreck)
        depth = self.get_attribute_depth(node)
        if depth >= TRAIN_WRECK_DEPTH:
            self.issues.append({
                "line": node.lineno,
                "type": "Law of Demeter (Train Wreck)",
                "detail": f"Chain of {depth} calls/attributes violates encapsulation.",
                "snippet": "..." # Snippet added in post-processing
            })
        
        self.generic_visit(node)

    def get_attribute_depth(self, node):
        depth = 0
        curr = node
        while isinstance(curr, ast.Attribute):
            depth += 1
            curr = curr.value
        return depth

    def visit(self, node):
        if not hasattr(self, 'stack'): self.stack = []
        self.stack.append(node)
        super().visit(node)
        self.stack.pop()

def analyze_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)
        visitor = ClassStructureVisitor(filepath)
        visitor.visit(tree)
        
        # Add snippets
        lines = source.splitlines()
        for issue in visitor.issues:
            if issue["snippet"] == "...":
                issue["snippet"] = lines[issue["line"]-1].strip()
        
        return visitor.issues
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
    f.write("# Clean Code Audit: Class & Object Structure Report\n\n")
    f.write("## Executive Summary\n")
    total_violations = sum(len(f["issues"]) for f in all_results)
    f.write(f"Analyzed codebase for God Classes, SRP violations, Low Cohesion, and Law of Demeter violations.\n")
    f.write(f"- **Files with Issues**: {len(all_results)}\n")
    f.write(f"- **Total Violations**: {total_violations}\n\n")

    f.write("## Top Offenders\n\n")
    all_results.sort(key=lambda x: len(x["issues"]), reverse=True)

    for item in all_results[:30]:
        f.write(f"### {item['file']}\n")
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
