import os
import json
import glob

assets_dir = '/home/anthony/Documents/OPEN-AIR/oaGuiDefinitions/Assets'
files = glob.glob(os.path.join(assets_dir, '**', '*.json'), recursive=True)

unique_strings = set()

def extract_strings(obj):
    if isinstance(obj, dict):
        if 'En' in obj and isinstance(obj['En'], str):
            unique_strings.add(obj['En'])
        for v in obj.values():
            extract_strings(v)
    elif isinstance(obj, list):
        for item in obj:
            extract_strings(item)

for fpath in files:
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            extract_strings(data)
    except Exception as e:
        print(f"Error parsing {fpath}: {e}")

with open('/home/anthony/Documents/OPEN-AIR/.gemini/TempScripts/unique_strings.json', 'w', encoding='utf-8') as f:
    json.dump(list(unique_strings), f, indent=2)

print(f"Found {len(unique_strings)} unique strings.")
