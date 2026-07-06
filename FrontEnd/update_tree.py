import os
import json

script_dir = "/home/anthony/Documents/OPEN-AIR/FrontEnd"
gui_frames_path = os.path.join(script_dir, "Gui_Frames")

def get_directory_tree(path, base_path):
    name = os.path.basename(path)
    children = []
    if os.path.isdir(path):
        for entry in sorted(os.listdir(path)):
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                children.append(get_directory_tree(full_path, base_path))
            else:
                if entry.endswith('.json'):
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

tree = get_directory_tree(gui_frames_path, gui_frames_path)
api_dir = os.path.join(script_dir, "api")
os.makedirs(api_dir, exist_ok=True)
with open(os.path.join(api_dir, "tree.json"), 'w', encoding='utf-8') as f:
    json.dump(tree, f, indent=2)
print("Static /api/tree.json generated successfully.")
