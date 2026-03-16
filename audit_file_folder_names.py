import os
import re
from collections import defaultdict

project_root = "/home/anthony/Documents/OPEN-AIR"
output_file = os.path.join(project_root, "assets/Documentation/Audits/Bad_File_Folder_Names_Audit.md")

# Configuration for Bad Naming
NOISE_WORDS = ["Data", "Info", "Object", "Manager", "Builder", "Worker"]
REDUNDANT_PATTERNS = [r"manager_", r"worker_", r"gui_"]
FORBIDDEN_CHARS = [r" ", r"-", r"\.", r"\(", r"\)"] # Files should use underscores

# Configuration for Containerization
FILE_COUNT_THRESHOLD = 15 # A folder with more than 15 files might need sub-containers

def analyze_file_naming(root, files, dirs):
    issues = []
    rel_root = os.path.relpath(root, project_root)
    
    # Check folder name
    folder_name = os.path.basename(root)
    if folder_name and folder_name != "." and folder_name != "..":
        for word in NOISE_WORDS:
            if word.lower() in folder_name.lower() and folder_name != word:
                issues.append({
                    "path": rel_root,
                    "type": "Noise Word in Folder Name",
                    "detail": f"Folder '{folder_name}' contains redundant word '{word}'."
                })

    # Check file naming and containerization
    py_files = [f for f in files if f.endswith(".py") and not f.startswith("__")]
    if len(py_files) > FILE_COUNT_THRESHOLD:
        issues.append({
            "path": rel_root,
            "type": "Flat Directory (Over-coupling)",
            "detail": f"Directory contains {len(py_files)} Python files. Consider grouping into sub-containers (e.g., 'core/', 'utils/', 'ui/')."
        })

    for file in files:
        if file.startswith("__"): continue
        rel_file_path = os.path.join(rel_root, file)
        
        # 1. Noise Words
        for word in NOISE_WORDS:
            if word.lower() in file.lower() and not file.startswith(word.lower()):
                issues.append({
                    "path": rel_file_path,
                    "type": "Noise Word in File Name",
                    "detail": f"File '{file}' contains redundant word '{word}'."
                })
        
        # 2. Meaningless Distinctions (Redundant Prefixes)
        for pattern in REDUNDANT_PATTERNS:
            if file.lower().startswith(pattern) and len(file.split(pattern)) > 1:
                # If the folder name already implies this, it's redundant
                if pattern.strip("_") in rel_root.lower():
                    issues.append({
                        "path": rel_file_path,
                        "type": "Redundant Prefix",
                        "detail": f"File '{file}' uses prefix '{pattern}' already implied by its parent directory."
                    })

        # 3. Non-standard characters (except for specific non-code assets)
        if file.endswith((".py", ".json", ".md")):
            for char in FORBIDDEN_CHARS:
                if re.search(char, file.replace(".py", "").replace(".json", "").replace(".md", "")):
                    issues.append({
                        "path": rel_file_path,
                        "type": "Naming Convention Violation",
                        "detail": f"File '{file}' uses non-standard characters (should use underscores)."
                    })

    return issues

def find_scattered_alike_files(all_files):
    # Find files with similar names across different directories
    file_map = defaultdict(list)
    for f in all_files:
        name = os.path.basename(f)
        if name.startswith("__") or not name.endswith(".py"): continue
        file_map[name].append(f)
    
    scattered = []
    for name, paths in file_map.items():
        if len(paths) > 1:
            scattered.append({
                "name": name,
                "paths": [os.path.relpath(p, project_root) for p in paths]
            })
    return scattered

all_results = []
all_file_paths = []

for root, dirs, files in os.walk(project_root):
    if any(ignore in root for ignore in [".git", "__pycache__", "DATA", ".crawler", "node_modules"]):
        continue
    
    all_results.extend(analyze_file_naming(root, files, dirs))
    for f in files:
        all_file_paths.append(os.path.join(root, f))

scattered_files = find_scattered_alike_files(all_file_paths)

# Generate Report
with open(output_file, "w", encoding="utf-8") as f:
    f.write("# Clean Code Audit: Bad File/Folder Naming & Containerization Report\n\n")
    
    f.write("## Executive Summary\n")
    f.write("Analyzed the project structure for intention-revealing names, noise words, redundant prefixes, and flat directories.\n")
    f.write(f"- **Naming Violations Identified**: {len(all_results)}\n")
    f.write(f"- **Scattered Alike Files (Duplication risk)**: {len(scattered_files)}\n\n")
    
    f.write("## Top Offenders (Flat Directories & Over-coupling)\n\n")
    flat_dirs = [r for r in all_results if r["type"] == "Flat Directory (Over-coupling)"]
    for r in flat_dirs:
        f.write(f"### `{r['path']}`\n- {r['detail']}\n\n")

    f.write("## Naming Violations\n\n")
    # Group by type
    grouped = defaultdict(list)
    for r in all_results:
        if r["type"] != "Flat Directory (Over-coupling)":
            grouped[r["type"]].append(r)
            
    for issue_type, issues in grouped.items():
        f.write(f"### {issue_type}\n")
        # Limit to top 15 for readability
        for iss in issues[:15]:
            f.write(f"- `{iss['path']}`: {iss['detail']}\n")
        if len(issues) > 15:
            f.write(f"- ... and {len(issues) - 15} more.\n")
        f.write("\n")

    f.write("## Scattered Alike Files (Conceptual Affinity Issues)\n")
    f.write("These files share the exact same name but are located in different directories. This often indicates a failure to containerize shared logic or a violation of conceptual affinity.\n\n")
    for s in scattered_files:
        f.write(f"### `{s['name']}`\n")
        for p in s["paths"]:
            f.write(f"- `{p}`\n")
        f.write("\n")

print(f"Audit complete. Results written to {output_file}")
