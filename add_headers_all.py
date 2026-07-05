import os
import re
from datetime import datetime

# Define file extensions to process
extensions = ['.rs', '.py', '.html', '.css', '.proto']

# Build a list of files excluding node_modules, .git, etc.
files_to_process = []
for root, dirs, files in os.walk('/home/anthony/Documents/OPEN-AIR'):
    dirs[:] = [d for d in dirs if d not in ['node_modules', '.crawler', '.git', 'dist', 'build', 'pkg', 'target', '__pycache__']]
    for file in files:
        if any(file.endswith(ext) for ext in extensions):
            files_to_process.append(os.path.join(root, file))

date_str = datetime.now().strftime("%Y-%m-%d")
version_str = "26.07.05.1"

# Patterns for function definitions
rs_pattern = re.compile(r'^(?:pub\s+)?(?:async\s+)?fn\s+(\w+)')
py_pattern = re.compile(r'^def\s+(\w+)')

def process_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    filename = os.path.basename(file_path)
    
    # Check if header already exists
    if "Header:" in content and "Version:" in content:
        # Just update the version if it's there
        if "Version: 26.07.05.1" in content:
            new_content = content.replace("Version: 26.07.05.1", f"Version: {version_str}")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
        return

    purpose = filename + " implementation."
    description = f"Logic and implementation for {purpose}"
    
    if file_path.endswith('.rs') or file_path.endswith('.css') or file_path.endswith('.proto'):
        header = f"""/**
 * Header: {filename}
 * Purpose: {purpose}
 * Description: {description}
 * 
 * Version: {version_str}
 * Change Log:
 * - {date_str}: Initial annotation and documentation added.
 */

"""
    elif file_path.endswith('.py'):
        header = f"""# ==========================================
# Header: {filename}
# Purpose: {purpose}
# Description: {description}
# 
# Version: {version_str}
# Change Log:
# - {date_str}: Initial annotation and documentation added.
# ==========================================

"""
    elif file_path.endswith('.html'):
        header = f"""<!--
  Header: {filename}
  Purpose: {purpose}
  Description: {description}
  
  Version: {version_str}
  Change Log:
  - {date_str}: Initial annotation and documentation added.
-->

"""

    lines = content.split('\n')
    new_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Rust inline comment
        if file_path.endswith('.rs'):
            match = rs_pattern.search(line)
            if match:
                if i == 0 or not (lines[i-1].strip().startswith("//") or lines[i-1].strip().endswith("*/")):
                    new_lines.append(f"{' ' * (len(line) - len(line.lstrip()))}// Inline comment: Logic for {match.group(1)}")
                    
        # Python inline comment
        elif file_path.endswith('.py'):
            match = py_pattern.search(line)
            if match:
                if i == 0 or not (lines[i-1].strip().startswith("#")):
                    new_lines.append(f"{' ' * (len(line) - len(line.lstrip()))}# Inline comment: Logic for {match.group(1)}")

        new_lines.append(line)
        i += 1

    new_content = header + "\n".join(new_lines)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)

count = 0
for file in files_to_process:
    try:
        process_file(file)
        count += 1
    except Exception as e:
        print(f"Error processing {file}: {e}")

print(f"Processed {count} files.")
