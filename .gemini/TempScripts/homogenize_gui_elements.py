# .gemini/TempScripts/homogenize_gui_elements.py
import os
import shutil
from pathlib import Path

project_root = Path("/home/anthony/Documents/OPEN-AIR")
gui_elements_core = project_root / "oaGuiElements" / "Core"

def read_file(path):
    with open(path) as f: return f.read()

def write_file(path, content):
    with open(path, 'w') as f: f.write(content)

# We'll collect all mapping changes: old_import -> new_import
import_replacements = {}

sample_files = list(gui_elements_core.rglob("sample.json"))

for sample_file in sample_files:
    element_dir = sample_file.parent
    if element_dir.name == "Assets":
        element_dir = element_dir.parent

    category = element_dir.parent.name
    element_name = element_dir.name

    if category == "Core" or element_name == "Core":
        continue

    print(f"Processing: {category}/{element_name}")

    core_dir = element_dir / "Core"
    interface_dir = element_dir / "Interface"
    assets_dir = element_dir / "Assets"

    core_dir.mkdir(exist_ok=True)
    interface_dir.mkdir(exist_ok=True)
    assets_dir.mkdir(exist_ok=True)

    (core_dir / "__init__.py").touch()
    (interface_dir / "__init__.py").touch()

    if sample_file.parent != assets_dir:
        shutil.move(str(sample_file), str(assets_dir / "sample.json"))

    for py_file in list(element_dir.glob("*.py")):
        if py_file.name == "__init__.py": continue

        module_name = py_file.stem

        if py_file.name.endswith("_editor.py"):
            shutil.move(str(py_file), str(interface_dir / py_file.name))
            old_mod = f"oaGuiElements.Core.{category}.{element_name}.{module_name}"
            new_mod = f"oaGuiElements.Core.{category}.{element_name}.Interface.{module_name}"
            import_replacements[old_mod] = new_mod
        else:
            dest_file = core_dir / py_file.name
            shutil.move(str(py_file), str(dest_file))
            old_mod = f"oaGuiElements.Core.{category}.{element_name}.{module_name}"
            new_mod = f"oaGuiElements.Core.{category}.{element_name}.Core.{module_name}"
            import_replacements[old_mod] = new_mod

    # Generate bespoke editor
    editor_file = interface_dir / f"{element_name}_editor.py"
    if not editor_file.exists():
        class_name = "".join(x.capitalize() for x in element_name.split("_")) + "Editor"
        editor_content = f'''# oaGuiElements/Core/{category}/{element_name}/Interface/{element_name}_editor.py
# Author: Gemini CLI
# Version: 20260417.1.0
# Description: Bespoke editor for {element_name}.

import tkinter as tk
from tkinter import ttk

class {class_name}:
    """Standalone editor for {element_name} configuration."""

    def __init__(self, parent, config_data, on_save_callback):
        self.parent = parent
        self.current_config = config_data.copy() if config_data else {{}}
        self.on_save = on_save_callback

        self.window = tk.Toplevel(parent)
        self.window.title(f"Editor: {{self.current_config.get('path', '{element_name}')}}")
        self.window.geometry("500x600")
        self.window.configure(bg="#1e1e1e")
        self.window.transient(parent)
        self.window.grab_set()

        self._build_ui()

    def _build_ui(self):
        header = tk.Frame(self.window, bg="#333333", height=40)
        header.pack(side="top", fill="x")
        tk.Label(header, text="{element_name.replace('_', ' ').upper()} EDITOR", bg="#333333", fg="white", 
                 font=("Arial", 10, "bold")).pack(side="left", padx=10, pady=10)

        container = tk.Frame(self.window, bg="#1e1e1e")
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        tk.Label(container, text="Bespoke properties for {element_name} will appear here.", bg="#1e1e1e", fg="white").pack(pady=20)
        
        row = tk.Frame(container, bg="#1e1e1e")
        row.pack(fill="x", pady=5)
        tk.Label(row, text="Label", bg="#1e1e1e", fg="#dcdcdc", width=15, anchor="w").pack(side="left")
        var = tk.StringVar(value=str(self.current_config.get("label", "")))
        entry = tk.Entry(row, textvariable=var, bg="#2d2d2d", fg="white", insertbackground="white", relief="flat")
        entry.pack(side="left", fill="x", expand=True, padx=5)
        var.trace_add("write", lambda *a: self.current_config.update({{"label": var.get()}}))

        footer = tk.Frame(self.window, bg="#333333", height=50)
        footer.pack(side="bottom", fill="x")

        tk.Button(footer, text="SAVE", bg="#4CAF50", fg="white", 
                  font=("Arial", 9, "bold"), relief="flat", width=12,
                  command=self._on_save).pack(side="right", padx=10, pady=10)
        
        tk.Button(footer, text="DISCARD", bg="#f44336", fg="white", 
                  font=("Arial", 9, "bold"), relief="flat", width=12,
                  command=self.window.destroy).pack(side="right", padx=10, pady=10)

    def _on_save(self):
        if self.on_save:
            self.on_save(self.current_config)
        self.window.destroy()

    @staticmethod
    def launch(parent, config_data, on_save_callback):
        return {class_name}(parent, config_data, on_save_callback)
'''
        write_file(str(editor_file), editor_content)

# Global refactor of imports
all_py_files = []
for root, dirs, files in os.walk(project_root):
    if ".venv" in root or ".git" in root or "__pycache__" in root or "oaData" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            all_py_files.append(Path(root) / file)

for py_file in all_py_files:
    try:
        content = read_file(py_file)
        new_content = content
        for old_mod, new_mod in import_replacements.items():
            new_content = new_content.replace(old_mod, new_mod)
        if new_content != content:
            write_file(str(py_file), new_content)
            print(f"Updated imports in {py_file.relative_to(project_root)}")
    except Exception:
        pass

print("Homogenization complete.")
