import os
import re

mapping = {
    "oaFileHandlers.oaFileImportCSV": "oaFileHandlers.oaFileImportCSV",
    "oaFileHandlers.oaFileImportHTML": "oaFileHandlers.oaFileImportHTML",
    "oaFileHandlers.oaFileImportPDF": "oaFileHandlers.oaFileImportPDF",
    "oaFileHandlers.oaFileImportShow": "oaFileHandlers.oaFileImportShow"
}

def process_file(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    original_content = content
    
    # Update module paths with word boundaries to avoid partial matches
    for old, new in mapping.items():
        # Avoid double prefixing if it's already there
        content = re.sub(r'(?<!oaFileHandlers\.)\b' + old + r'\b', new, content)
        
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated: {file_path}")

def main():
    ignore_dirs = {'.git', '.venv', '__pycache__', '.crawler', '.pytest_cache'}
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith('oaData')]
        for file in files:
            if file.endswith('.py') or file.endswith('.md') or file.endswith('.json'):
                process_file(os.path.join(root, file))

if __name__ == "__main__":
    main()
