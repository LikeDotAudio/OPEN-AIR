import os
import re

def clean_name(name):
    # Remove XXX placeholders
    name = re.sub(r'X{2,}', '', name)
    # Replace spaces and dashes with underscores
    name = name.replace(' ', '_').replace('-', '_')
    # Remove leading/trailing underscores
    name = name.strip('_')
    # Replace multiple underscores with one
    name = re.sub(r'_+', '_', name)
    return name

def remove_redundant(name, parent_context, is_folder=False):
    redundant_words = ['Manager', 'Builder', 'Worker', 'Data', 'Object']
    
    # If it's a file, remove prefixes
    if not is_folder:
        if parent_context == 'managers' and name.lower().startswith('manager_'):
            name = name[8:]
        elif parent_context == 'workers' and name.lower().startswith('worker_'):
            name = name[7:]
        
        # Specific redundant prefixes like 'worker_importer_' in 'workers/importers'
        if 'importers' in parent_context and name.lower().startswith('worker_importer_'):
            name = name[16:]
        if 'importers' in parent_context and name.lower().startswith('worker_'):
            name = name[7:]
            
    # Remove noise words if they are redundant with parent context
    # This is tricky. Let's do some common ones.
    for word in redundant_words:
        if word.lower() in parent_context.lower():
            # If parent folder already has the word, remove it from the name
            # But only if it's not the ONLY word in the name
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            new_name = pattern.sub('', name)
            new_name = new_name.replace('__', '_').strip('_')
            if new_name and not new_name.startswith('.'):
                 name = new_name
                 
    return name

def get_new_path(old_path):
    parts = old_path.split('/')
    new_parts = []
    
    for i, part in enumerate(parts):
        if part == '':
            new_parts.append('')
            continue
            
        # Split extension
        name_part, ext = os.path.splitext(part)
        cleaned = clean_name(name_part)
        
        if i == 0 and part in ['managers', 'workers']:
            new_parts.append(part)
            continue

        # Special case for 'manager' folder in Splinker
        if part == 'manager' and 'Splinker' in parts:
            cleaned = 'core'
            ext = '' # It's a folder
        
        # Special case for 'SPLINKER - early thigns - archive'
        if 'SPLINKER' in part and 'early' in part and 'archive' in part:
             cleaned = 'splinker_archive'
             ext = ''

        # Remove redundant prefixes
        if i > 0:
            if parts[0] == 'managers':
                if cleaned.lower().startswith('manager_'):
                    cleaned = cleaned[8:]
            elif parts[0] == 'workers':
                if cleaned.lower().startswith('worker_importer_'):
                    cleaned = cleaned[16:]
                elif cleaned.lower().startswith('worker_'):
                    cleaned = cleaned[7:]

        # Specific noise words removal if they are not the only word
        if len(cleaned.split('_')) > 1:
            for word in ['Manager', 'Builder', 'Worker', 'Data']:
                if word.lower() in cleaned.lower():
                    # Only remove if it's a separate component
                    pattern = re.compile(rf'_?{word}_?', re.IGNORECASE)
                    test_new = pattern.sub('_', cleaned).strip('_')
                    if test_new:
                        cleaned = test_new

        # Final cleanup for the part
        cleaned = cleaned.replace('__', '_').strip('_')
        if not cleaned: 
            cleaned = clean_name(name_part)
            
        new_parts.append(cleaned + ext)
    
    return '/'.join(new_parts)

import json

def generate_full_mapping(root_dir):
    mapping = {}
    
    # Use find to get all files and folders
    # Exclude .git
    import subprocess
    cmd = ["find", ".", "-not", "-path", "*/.*"]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=root_dir)
    paths = result.stdout.splitlines()
    
    # Sort paths by depth (deepest first for files, shallowest first for folders?)
    # Actually, if we rename a parent folder, the child paths change.
    # So we should rename from leaf to root? Or use 'git mv' which handles it?
    # Better to rename from leaf to root.
    paths.sort(key=lambda x: x.count('/'), reverse=True)
    
    for path in paths:
        if path == '.': continue
        old_path = path.lstrip('./')
        new_path = get_new_path(old_path)
        
        if old_path != new_path:
            mapping[old_path] = new_path
            
    return mapping

if __name__ == "__main__":
    full_mapping = generate_full_mapping("/home/anthony/Documents/OPEN-AIR")
    # Save to file
    with open("rename_mapping.json", "w") as f:
        json.dump(full_mapping, f, indent=4)
    print(f"Generated mapping with {len(full_mapping)} entries.")
