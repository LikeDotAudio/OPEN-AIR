import os
import re
from datetime import datetime

# Read the list of files
with open("js_files_clean.txt", "r") as f:
    files = [line.strip() for line in f if line.strip()]

date_str = datetime.now().strftime("%Y-%m-%d")

function_pattern = re.compile(r'^(?:export\s+)?(?:default\s+)?(?:async\s+)?(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|[^=]*)\s*=>|let\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|[^=]*)\s*=>)', re.MULTILINE)

def process_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Skip if header already exists
    if "/**\n * Header:" in content:
        return

    filename = os.path.basename(file_path)
    purpose = filename.replace(".jsx", "").replace(".js", "") + " component or utility."
    description = f"Handles logic and rendering for {purpose}"

    header = f"""/**
 * Header: {filename}
 * Purpose: {purpose}
 * Description: {description}
 * 
 * Version: 1.0.0
 * Change Log:
 * - {date_str}: Initial annotation and documentation added.
 */

"""
    
    # Simple inline comment insertion logic
    lines = content.split('\n')
    new_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if line is a function definition
        match = function_pattern.search(line)
        if match:
            func_name = match.group(1) or match.group(2) or match.group(3)
            # Check previous line for comments
            if i == 0 or not (lines[i-1].strip().startswith("//") or lines[i-1].strip().endswith("*/")):
                if func_name:
                    new_lines.append(f"{' ' * (len(line) - len(line.lstrip()))}// Inline comment: Logic for {func_name}")
                else:
                    new_lines.append(f"{' ' * (len(line) - len(line.lstrip()))}// Inline comment: Logic for function")
        
        new_lines.append(line)
        i += 1

    new_content = header + "\n".join(new_lines)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)

count = 0
for file in files:
    try:
        process_file(file)
        count += 1
    except Exception as e:
        print(f"Error processing {file}: {e}")

print(f"Processed {count} files.")
