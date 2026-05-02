import os
import re

# List of subfolders and the patterns to fix
reorg_folders = {
    "oaGui/Managers/layout": r"from \.layout\.",
    "oaGui/Managers/grid": r"from \.grid\.",
    "oaGui/Managers/lifecycle": r"from \.lifecycle\.",
    "oaGui/Managers/refresh": r"from \.refresh\.",
    "oaGui/Managers/display": r"from \.display\.",
    "oaGui/Managers/assembler": r"from \.assembler\.",
    "oaGui/Managers/tabs": r"from \.tabs\.",
    "oaGui/Managers/bootstrap": r"from \.bootstrap\.",
    "oaGui/FileReaders/scanner": r"from \.scanner\.",
    "oaGui/FileReaders/loader": r"from \.loader\.",
}

def fix_internal_imports(folder_path, pattern):
    if not os.path.exists(folder_path): return
    
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                new_content = re.sub(pattern, "from .", content)
                
                if new_content != content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Fixed internal imports in: {file_path}")

def main():
    for folder, pattern in reorg_folders.items():
        fix_internal_imports(folder, pattern)

if __name__ == "__main__":
    main()
