import os
import shutil
import glob
import re

source_modules = [
    "oaGuiBackground",
    "oaGuiSplashScreen"
]
target_module = "oaGuiElements"

conflicts = []

# 1. Move files
for src in source_modules:
    if not os.path.exists(src):
        print(f"Skipping {src}, does not exist.")
        continue
        
    for root, dirs, files in os.walk(src):
        if "__pycache__" in root: continue
        
        # Calculate target path
        rel_path = os.path.relpath(root, src)
        if rel_path == ".":
            target_dir = target_module
        else:
            target_dir = os.path.join(target_module, rel_path)
            
        os.makedirs(target_dir, exist_ok=True)
        
        for file in files:
            if file == "Entry.py" and rel_path == ".":
                # Don't overwrite the main Entry.py
                print(f"Skipping main {src}/Entry.py")
                continue
            
            src_file = os.path.join(root, file)
            tgt_file = os.path.join(target_dir, file)
            
            if not os.path.exists(tgt_file):
                shutil.move(src_file, tgt_file)
                print(f"Moved: {src_file} -> {tgt_file}")
            else:
                print(f"CONFLICT: {tgt_file} already exists. Left {src_file} in place.")
                conflicts.append((src_file, tgt_file))

# 2. Update imports globally
print("\nUpdating imports...")
all_files = glob.glob("**/*.py", recursive=True) + glob.glob("**/*.md", recursive=True) + glob.glob("**/*.json", recursive=True)

import_patterns = [
    (re.compile(r'\b' + src + r'\b'), target_module) for src in source_modules
]

for file in all_files:
    if any(ignore in file for ignore in [".git", "__pycache__", ".venv", ".gemini", "node_modules", "target"]):
        continue
        
    try:
        with open(file, "r", encoding="utf-8") as f:
            content = f.read()
            
        new_content = content
        for pattern, replacement in import_patterns:
            new_content = pattern.sub(replacement, new_content)
            
        if new_content != content:
            with open(file, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"Updated imports in: {file}")
    except Exception as e:
        pass

print("\nConsolidation complete.")
if conflicts:
    print("WARNING: The following conflicts were found and files were NOT moved:")
    for src, tgt in conflicts:
        print(f"  {src} conflicts with {tgt}")
