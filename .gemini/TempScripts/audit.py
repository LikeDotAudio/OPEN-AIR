import ast
import glob
import json
import os

TARGET_DIR = '/home/anthony/Documents/OPEN-AIR/oaGuiElements'

class ComplexityVisitor(ast.NodeVisitor):
    def __init__(self):
        self.complexity = 1
    def visit_If(self, node): self.complexity += 1; self.generic_visit(node)
    def visit_For(self, node): self.complexity += 1; self.generic_visit(node)
    def visit_While(self, node): self.complexity += 1; self.generic_visit(node)
    def visit_And(self, node): self.complexity += 1; self.generic_visit(node)
    def visit_Or(self, node): self.complexity += 1; self.generic_visit(node)
    def visit_ExceptHandler(self, node): self.complexity += 1; self.generic_visit(node)
    def visit_With(self, node): self.complexity += 1; self.generic_visit(node)
    def visit_ListComp(self, node): self.complexity += len(node.generators); self.generic_visit(node)
    def visit_DictComp(self, node): self.complexity += len(node.generators); self.generic_visit(node)
    def visit_SetComp(self, node): self.complexity += len(node.generators); self.generic_visit(node)
    def visit_GeneratorExp(self, node): self.complexity += len(node.generators); self.generic_visit(node)

def get_complexity(node):
    v = ComplexityVisitor()
    v.visit(node)
    return v.complexity

files = glob.glob(os.path.join(TARGET_DIR, '**', '*.py'), recursive=True)
rs_files = glob.glob(os.path.join(TARGET_DIR, '**', '*.rs'), recursive=True)

long_files = []
bad_functions = []

for file in files:
    try:
        with open(file, encoding='utf-8') as f:
            lines = f.readlines()
        if len(lines) > 500:
            long_files.append({"file": file.replace(TARGET_DIR, ''), "lines": len(lines)})
        source = "".join(lines)
        tree = ast.parse(source, filename=file)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = node.name
                args_count = len(node.args.args) + len(node.args.kwonlyargs)
                if node.args.vararg: args_count += 1
                if node.args.kwarg: args_count += 1

                line_count = getattr(node, 'end_lineno', node.lineno) - node.lineno + 1
                complexity = get_complexity(node)

                issues = []
                if complexity > 10: issues.append(f"Cyclomatic Complexity > 10 ({complexity})")
                if args_count > 2: issues.append(f"Argument Overload ({args_count} arguments)")
                if line_count > 50: issues.append(f"Mixed Abstraction / Long Function ({line_count} lines)")

                math_related = any(kw in name.lower() for kw in ['calc', 'math', 'balance', 'reward', 'fee', 'coord'])
                if math_related:
                    math_ops = [n for n in ast.walk(node) if isinstance(n, (ast.BinOp, ast.Compare))]
                    if math_ops:
                        issues.append(f"Arithmetic Specification Verification: Found {len(math_ops)} math ops.")
                if issues:
                    body = ""
                    if complexity > 20 or line_count > 100:
                        body = source.splitlines()[node.lineno-1:getattr(node, 'end_lineno', node.lineno)]
                        body = "\n".join(body)
                    bad_functions.append({
                        "file": file.replace(TARGET_DIR, ''),
                        "func": name,
                        "line": node.lineno,
                        "issues": issues,
                        "complexity": complexity,
                        "lines": line_count,
                        "args": args_count,
                        "body_preview": body[:500] + ("..." if len(body)>500 else "") if body else ""
                    })
    except Exception: pass

for file in rs_files:
    try:
        with open(file, encoding='utf-8') as f:
            lines = f.readlines()
        if len(lines) > 500:
            long_files.append({"file": file.replace(TARGET_DIR, ''), "lines": len(lines)})
    except: pass

bad_functions.sort(key=lambda x: x["complexity"], reverse=True)
out = {"long_files": long_files, "bad_functions": bad_functions[:20]}
print(json.dumps(out))
