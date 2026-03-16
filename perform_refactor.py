import json
import os
import subprocess

def perform_renames(mapping_file):
    with open(mapping_file, 'r') as f:
        mapping = json.load(f)
    
    # Sort by depth, deepest first
    sorted_old_paths = sorted(mapping.keys(), key=lambda x: x.count('/'), reverse=True)
    
    for old_path in sorted_old_paths:
        new_path = mapping[old_path]
        if not os.path.exists(old_path):
            print(f"Skipping {old_path}, does not exist (maybe already moved)")
            continue
            
        new_dir = os.path.dirname(new_path)
        if new_dir and not os.path.exists(new_dir):
            os.makedirs(new_dir, exist_ok=True)
            
        print(f"Moving {old_path} to {new_path}")
        # Use standard mv to avoid git mv issues with non-existent targets or intermediate states
        subprocess.run(['mv', old_path, new_path])

def update_references(mapping_file):
    with open(mapping_file, 'r') as f:
        mapping = json.load(f)
    
    # Create a list of replacements
    # We should prioritize longer paths to avoid partial replacements
    replacements = []
    
    for old_path, new_path in mapping.items():
        # For Python imports
        if old_path.endswith('.py'):
            old_mod = old_path[:-3].replace('/', '.')
            new_mod = new_path[:-3].replace('/', '.')
            replacements.append((old_mod, new_mod))
            
        # For general file references (in strings, json, etc)
        replacements.append((old_path, new_path))
        
        # Also handle paths without extensions (for directories or just general references)
        old_base = old_path
        new_base = new_path
        if '.' in os.path.basename(old_path):
            old_base = os.path.splitext(old_path)[0]
            new_base = os.path.splitext(new_path)[0]
        replacements.append((old_base, new_base))

        # Add module dot notation for everything (files without ext and folders)
        old_mod_base = old_base.replace('/', '.')
        new_mod_base = new_base.replace('/', '.')
        replacements.append((old_mod_base, new_mod_base))


    # Deduplicate and sort by length (longest first)
    replacements = list(set(replacements))
    replacements.sort(key=lambda x: len(x[0]), reverse=True)
    
    # Now apply replacements to all files in the project
    # We'll use a script to avoid escaping issues with sed
    with open('replacer.py', 'w') as f:
        f.write(f"""
import os
import json

replacements = {json.dumps(replacements)}

def apply_replacements(content):
    for old, new in replacements:
        content = content.replace(old, new)
    return content

for root, dirs, files in os.walk('.'):
    if '.git' in dirs:
        dirs.remove('.git')
    for file in files:
        if file in ['rename_mapping.json', 'perform_refactor.py', 'replacer.py', 'refactor_mapping.py']:
            continue
        filepath = os.path.join(root, file)
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            new_content = apply_replacements(content)
            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Updated {{filepath}}")
        except Exception as e:
            print(f"Error processing {{filepath}}: {{e}}")
""")
    
    subprocess.run(['python3', 'replacer.py'])

if __name__ == "__main__":
    print("Performing renames...")
    perform_renames('rename_mapping.json')
    print("Updating references...")
    update_references('rename_mapping.json')
    print("Finalizing with git...")
    subprocess.run(['git', 'add', '-A'])
    print("Done.")
