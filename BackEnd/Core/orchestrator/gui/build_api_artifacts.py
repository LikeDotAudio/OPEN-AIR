#!/usr/bin/env python3
import os
import json
import urllib.request

# BackEnd/Core/orchestrator/gui/ -> repo root is four levels up.
REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")
)
script_dir = os.path.join(REPO_ROOT, "FrontEnd")

def generate_api_tree():
    """Generate the static /api/tree JSON file from the Gui_Frames folder"""
    print("🌳 Generating static /api/tree JSON from Gui_Frames...")
    gui_frames_path = os.path.join(script_dir, "Gui_Frames")
    
    def get_directory_tree(path, base_path):
        name = os.path.basename(path)
        children = []
        if os.path.isdir(path):
            entries = sorted(os.listdir(path))
            for entry in entries:
                if entry.startswith('.') or entry.startswith('__'):
                    continue
                full_path = os.path.join(path, entry)
                if os.path.isdir(full_path):
                    children.append(get_directory_tree(full_path, base_path))
                elif entry.endswith('.json'):
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = json.load(f)
                    except Exception as e:
                        content = {"error": f"Could not parse JSON: {e}"}
                    
                    rel_path = os.path.relpath(full_path, base_path)
                    rel_path_str = "/" + rel_path.replace("\\", "/")
                    children.append({
                        "name": entry,
                        "type": "file",
                        "content": content,
                        "path": rel_path_str
                    })
        return {
            "name": name,
            "type": "directory",
            "children": children
        }
    
    if os.path.exists(gui_frames_path):
        tree = get_directory_tree(gui_frames_path, gui_frames_path)
        api_dir = os.path.join(script_dir, "api")
        os.makedirs(api_dir, exist_ok=True)
        with open(os.path.join(api_dir, "tree.json"), 'w', encoding='utf-8') as f:
            json.dump(tree, f, separators=(',', ':'))
        print("✅ Static /api/tree.json generated successfully.")
    else:
        print("⚠️ Gui_Frames directory not found in FrontEnd, skipping tree generation.")

def generate_api_grabbag():
    print("🎒 Generating static /api/grabbag JSON from local backend...")
    try:
        req = urllib.request.Request("http://localhost:8000/api/grabbag")
        with urllib.request.urlopen(req, timeout=5) as response:
            data = response.read()
            api_dir = os.path.join(script_dir, "api")
            os.makedirs(api_dir, exist_ok=True)
            with open(os.path.join(api_dir, "grabbag"), "wb") as f:
                f.write(data)
        print("✅ Static /api/grabbag generated successfully.")
    except Exception as e:
        print(f"⚠️ Could not fetch /api/grabbag (Backend likely not running): {e}")

if __name__ == "__main__":
    generate_api_tree()
    generate_api_grabbag()
