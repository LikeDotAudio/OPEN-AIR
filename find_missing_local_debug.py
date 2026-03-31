import os
import re

def check_file(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Check if LOCAL_DEBUG is used as a whole word (not in a string literal)
    # This is a bit complex for a simple regex, but we'll try:
    # Match \bLOCAL_DEBUG\b but not if it's inside quotes or is part of a definition/import.
    
    has_use = re.search(r'\bLOCAL_DEBUG\b', content)
    if not has_use:
        return False
    
    # Check if it's defined: LOCAL_DEBUG = or LOCAL_DEBUG=
    has_definition = re.search(r'\bLOCAL_DEBUG\s*=', content)
    
    # Check if it's imported: from ... import LOCAL_DEBUG or import ... LOCAL_DEBUG
    has_import = re.search(r'import\s+.*LOCAL_DEBUG', content)
    
    # Also check for 'patch' which we saw in tests
    has_patch = re.search(r"patch\(.*LOCAL_DEBUG", content)
    
    # If it's used but not defined or imported (and not just patched in a test)
    if has_use and not has_definition and not has_import and not has_patch:
        # Check if it's only in comments
        lines = content.splitlines()
        for line in lines:
            stripped = line.strip()
            if not stripped.startswith('#') and re.search(r'\bLOCAL_DEBUG\b', line):
                # Double check if this line is an assignment or import (in case regex failed)
                if not re.search(r'\bLOCAL_DEBUG\s*=', line) and not re.search(r'import\s+.*LOCAL_DEBUG', line):
                    return True
    return False

for root, dirs, files in os.walk('.'):
    if '.git' in dirs: dirs.remove('.git')
    for file in files:
        if file.endswith('.py'):
            file_path = os.path.join(root, file)
            if check_file(file_path):
                print(file_path)
