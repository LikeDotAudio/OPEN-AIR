# .gemini/TempScripts/fix_commas.py
import os
import re
import sys

def fix_commas(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    changed = False
    in_all = False
    for i in range(len(lines)):
        line = lines[i]
        if "__all__ = [" in line:
            in_all = True
            continue
        if in_all and "]" in line:
            in_all = False
            continue
        
        if in_all:
            # If it's a string line and doesn't end with a comma
            if re.match(r'^    ["\'][^"\']+["\']\s*$', line):
                lines[i] = line.rstrip() + ",\n"
                changed = True
    
    if changed:
        print(f"Fixed commas in: {file_path}")
        with open(file_path, 'w') as f:
            f.writelines(lines)

if __name__ == "__main__":
    import glob
    files = glob.glob("**/Entry.py", recursive=True)
    for f in files:
        fix_commas(f)
