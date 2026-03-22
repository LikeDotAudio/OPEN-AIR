# deep_cleanup.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import os
import re
import pathlib

# --- Configuration ---
PATTERNS_TO_REMOVE = [
    r"#?\s*Blog: www\.Like\.audio.*",
    r"#?\s*Build Log: https://like\.audio/.*",
    r"#?\s*Source Code: https://github\.com/.*",
]

COMMENTED_CODE_PATTERNS = [
    r"^\s*#\s*(def|if|class|from|import|while|for|try|except|with|return|elif|else)\s+.*",
]

HEADER_MANDATE = """# {folder_file}
# Author: {author}
# Version: {version}
#
# Description: {description}
"""

def get_header_info(content, file_path):
    lines = content.splitlines()
    author = "Anthony Peter Kuzub" # Default
    version = "1.0.0" # Default
    description = ""
    
    # Try to extract from existing header
    header_lines = []
    for line in lines[:15]: # Look in first 15 lines
        if line.startswith("#"):
            header_lines.append(line)
        elif not line.strip():
            continue
        else:
            break
            
    for line in header_lines:
        if "Author:" in line:
            author = line.split("Author:")[1].strip()
        elif "Version:" in line:
            version = line.split("Version:")[1].strip()
        elif "Version" in line and not version or version == "1.0.0":
            # Handle "Version 20260222..."
            match = re.search(r"Version\s+([\w\.]+)", line)
            if match:
                version = match.group(1)
        elif "Description:" in line:
            description = line.split("Description:")[1].strip()
            
    if not description:
        # Try to find a description line (not author, version, blog, or file path)
        for line in header_lines:
            clean_line = line.lstrip("#").strip()
            if not clean_line: continue
            if any(x in line for x in ["Author:", "Version", "Blog:", "Source Code:", "Build Log:", "Feature Requests"]):
                continue
            if "/" in clean_line and clean_line.endswith(".py"):
                continue
            description = clean_line
            break

    if not description:
        description = "Brief summary of purpose"

    return author, version, description

def clean_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.splitlines()
    new_lines = []
    
    # Process headers for Python files
    if file_path.endswith(".py"):
        author, version, description = get_header_info(content, file_path)
        
        # Determine FolderName/FileName.py
        rel_path = os.path.relpath(file_path, os.getcwd())
        # The user wants FolderName/FileName.py, so if it's in a subfolder:
        parts = pathlib.Path(rel_path).parts
        if len(parts) > 1:
            folder_file = f"{parts[-2]}/{parts[-1]}"
        else:
            folder_file = parts[0]
            
        new_header = HEADER_MANDATE.format(
            folder_file=folder_file,
            author=author,
            version=version,
            description=description
        ).splitlines()
        
        # Find where the original header ends
        header_end_idx = 0
        for i, line in enumerate(lines):
            if line.startswith("#") or not line.strip():
                header_end_idx = i + 1
            else:
                header_end_idx = i
                break
        
        # Skip original header in the rest of processing
        remaining_lines = lines[header_end_idx:]
        new_lines.extend(new_header)
        # Add a newline after header if not present
        if remaining_lines and remaining_lines[0].strip():
             new_lines.append("")
    else:
        remaining_lines = lines

    # Clean remaining lines
    processed_lines = []
    for line in remaining_lines:
        skip = False
        for pattern in PATTERNS_TO_REMOVE:
            if re.search(pattern, line):
                skip = True
                break
        if skip: continue
        
        for pattern in COMMENTED_CODE_PATTERNS:
            if re.match(pattern, line):
                # Special case: don't remove if it's a docstring comment or something?
                # Actually user asked to remove them.
                skip = True
                break
        if skip: continue
        
        processed_lines.append(line)
        
    new_lines.extend(processed_lines)
    
    new_content = "\n".join(new_lines) + "\n"
    
    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def main():
    count = 0
    for root, dirs, files in os.walk("."):
        if ".git" in dirs:
            dirs.remove(".git")
        if "__pycache__" in dirs:
            dirs.remove("__pycache__")
            
        for file in files:
            if file.endswith((".py", ".md")):
                file_path = os.path.join(root, file)
                if clean_file(file_path):
                    count += 1
                    print(f"Cleaned: {file_path}")

    print(f"Total files cleaned: {count}")

if __name__ == "__main__":
    main()
