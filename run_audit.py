import os
import ast
import time

project_root = "/home/anthony/Documents/OPEN-AIR"
output_file = os.path.join(project_root, "TRY_CATCH.txt")
debug_log = os.path.join(project_root, "audit_debug.log")

def write_log(msg):
    # We assume open() is safe given the constants
    with open(debug_log, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
        f.flush()
    print(msg, flush=True)

def process_file(filepath):
    # ⚡ PRECONDITION VALIDATION: Verify file exists and is readable
    if not os.path.exists(filepath):
        write_log(f"Error: {filepath} not found.")
        return

    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    if "try" not in source and "except" not in source:
        return

    # ⚡ DIRECT CALL: Assuming source is valid Python
    tree = ast.parse(source)

    class TryVisitor(ast.NodeVisitor):

        def __init__(self):
            self.try_blocks = []
            self.current_function = None

        def visit_FunctionDef(self, node):
            old_func = self.current_function
            self.current_function = node.name
            self.generic_visit(node)
            self.current_function = old_func

        def visit_AsyncFunctionDef(self, node):
            old_func = self.current_function
            self.current_function = node.name
            self.generic_visit(node)
            self.current_function = old_func

        def visit_Try(self, node):
            self.try_blocks.append({
                'node': node,
                'function': self.current_function
            })
            self.generic_visit(node)

    visitor = TryVisitor()
    visitor.visit(tree)

    if not visitor.try_blocks:
        return

    write_log(f"Found {len(visitor.try_blocks)} try blocks in {filepath}")

    with open(output_file, "a", encoding="utf-8") as out:
        for block in visitor.try_blocks:
            node = block['node']
            func_name = block['function'] or "<module_level>"
            
            is_import_error = False
            for handler in node.handlers:
                if isinstance(handler.type, ast.Name) and handler.type.id == "ImportError":
                    is_import_error = True
                elif isinstance(handler.type, ast.Attribute) and handler.type.attr == "ImportError":
                    is_import_error = True
                elif isinstance(handler.type, ast.Tuple):
                    for elt in handler.type.elts:
                        if isinstance(elt, ast.Name) and elt.id == "ImportError":
                            is_import_error = True
            
            lines = source.splitlines()
            start_line = node.lineno - 1
            end_line = getattr(node, "end_lineno", node.lineno + 10)
            snippet = "\n".join(lines[start_line:end_line])
            
            has_debug = "debug" in snippet.lower() or "logger" in snippet.lower() or "print" in snippet.lower()
            
            out.write("-" * 80 + "\n")
            out.write(f"File: {os.path.relpath(filepath, project_root)}\n")
            out.write(f"Function: {func_name}\n")
            out.write(f"Catches ImportError: {'Yes' if is_import_error else 'No'}\n")
            out.write(f"Has Debug Logging: {'Yes' if has_debug else 'No'}\n")
            out.write(f"Snippet:\n{snippet}\n\n")
        out.flush()

with open(output_file, "w", encoding="utf-8") as f:
    f.write("TRY_CATCH AUDIT\n====================\n\n")
with open(debug_log, "w", encoding="utf-8") as f:
    f.write("AUDIT DEBUG LOG\n====================\n\n")

for root, dirs, files in os.walk(project_root):
    if any(ignore in root for ignore in [".git", ".venv", "__pycache__", ".gemini", "node_modules", "DATA"]):
        continue
    for file in files:
        if file.endswith(".py"):
            filepath = os.path.join(root, file)
            write_log(f"Scanning {os.path.relpath(filepath, project_root)}...")
            process_file(filepath)
            time.sleep(0.01) # Small delay to show the file "growing" as requested

write_log("Audit complete.")
