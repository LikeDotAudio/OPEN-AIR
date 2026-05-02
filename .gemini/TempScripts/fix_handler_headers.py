import os
import re

def process_file(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    if not lines: return
    
    changed = False
    # Only check the first 5 lines for the path comment
    for i in range(min(5, len(lines))):
        if lines[i].startswith("# oaFileHandlers."):
            lines[i] = lines[i].replace("# oaFileHandlers.", "# oaFileHandlers/")
            changed = True
            
    if changed:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"Fixed header in: {file_path}")

def main():
    for root, dirs, files in os.walk('oaFileHandlers'):
        for file in files:
            if file.endswith('.py'):
                process_file(os.path.join(root, file))

if __name__ == "__main__":
    main()
