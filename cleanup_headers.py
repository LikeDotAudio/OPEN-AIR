# cleanup_headers.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: cleanup_headers.py

import os
import re
import sys

def cleanup_file(file_path):
    print(f"Cleaning {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if not lines:
        return

    # Extract info from old header
    author = "Anthony Peter Kuzub" # Default
    version = "1.0.0" # Default
    description = ""
    
    # Noise patterns
    noise_patterns = [
    ]

    # Try to find existing info in the first few lines
    for line in lines[:50]:
        if line.startswith('#'):
            if 'Author:' in line:
                author = line.split('Author:', 1)[1].strip()
            elif 'Version' in line:
                v_match = re.search(r'Version[:\s]+([\w\.]+)', line)
                if v_match:
                    version = v_match.group(1)
            elif 'Description:' in line:
                description = line.split('Description:', 1)[1].strip()
            elif not description and len(line.strip('#').strip()) > 30:
                content = line.strip('#').strip()
                    if not content.startswith("---") and not content.endswith("---"):
                        description = content

    # Clean description
    if description.startswith("Description:"):
        description = description[len("Description:"):].strip()

    # Mandated header
    rel_path = os.path.relpath(file_path, "/home/anthony/Documents/OPEN-AIR")
    new_header = [
        f"# {rel_path}\n",
        f"# Author: {author}\n",
        f"# Version: {version}\n",
        "#\n",
        f"# Description: {description if description else 'No description available.'}\n",
        "\n"
    ]

    # Process remaining lines
    new_lines = []
    
    # Commented out code pattern
    code_pattern = re.compile(r'^\s*#\s*(def|if|class|for|while|try|except|with|return|import|from|elif|else|finally)\b')

    # Skip old header
    # We want to skip everything until we find real code or a "Standard Debug Logging" section
    code_start_index = 0
    in_initial_comments = True
    for i, line in enumerate(lines):
        # Skip leading whitespace
        if not line.strip():
            continue
            
        if line.startswith('#'):
            # If it's a logging section marker, we start here
            if "--- Standard Debug Logging Setup ---" in line:
                code_start_index = i
                break
            # If it's something that looks like actual documentation for the first function, we might want to keep it
            # But usually it's better to just skip all top comments
            continue
        else:
            # Found first non-comment line
            code_start_index = i
            break

    # Add the rest of the lines, filtering for noise and commented-out code
    for line in lines[code_start_index:]:
        # Remove noise lines even in the body if they appear
        if any(noise in line for noise in noise_patterns):
            continue
        
        # Remove commented out code
        if code_pattern.match(line):
            continue
            
        new_lines.append(line)

    # Combine
    final_content = "".join(new_header) + "".join(new_lines)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(final_content)

if __name__ == "__main__":
    files = sys.stdin.read().splitlines()
    for f in files:
        if os.path.exists(f) and f.endswith('.py'):
            cleanup_file(f)
