import json
import os
import time
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler

# Paths
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
GUI_FRAMES_DIR = os.path.abspath(os.path.join(FRONTEND_DIR, "../Gui_Frames"))
PORT = 8000

def get_directory_tree(path):
    """Recursively build a dictionary representing the folder structure and JSON files."""
    tree = {"name": os.path.basename(path), "type": "directory", "children": []}
    try:
        entries = sorted(os.listdir(path))
        for entry in entries:
            # Ignore hidden files or __init__.py
            if entry.startswith('.') or entry.startswith('__'):
                continue
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                tree["children"].append(get_directory_tree(full_path))
            elif entry.endswith('.json'):
                try:
                    with open(full_path, encoding='utf-8') as f:
                        content = json.load(f)
                except Exception as e:
                    content = {"error": f"Could not parse JSON: {e}"}
                tree["children"].append({
                    "name": entry,
                    "type": "file",
                    "content": content,
                    "path": full_path.replace(GUI_FRAMES_DIR, "")
                })
    except PermissionError:
        pass
    return tree

def get_grab_bag():
    """Scan oaGuiElements for sample.json palette templates (mirrors the Python
    GrabBagLoader). Returns a flat, categorized component list for the editor."""
    root = os.path.abspath(os.path.join(FRONTEND_DIR, "..", "oaGuiElements"))
    components = []
    legends = {}  # merged enum lookups from every sample.json _LEGEND block
    for dirpath, _dirnames, filenames in os.walk(root):
        if "sample.json" not in filenames:
            continue
        full = os.path.join(dirpath, "sample.json")
        try:
            with open(full, encoding="utf-8") as f:
                content = json.load(f)
        except Exception:
            continue
        rel_parts = os.path.relpath(dirpath, root).split(os.sep)
        # Category = first meaningful folder segment (skip Core/Assets wrappers).
        meaningful = [p for p in rel_parts if p not in ("Core", "Assets", ".")]
        category = meaningful[0] if meaningful else "General"
        for key, schema in content.items():
            # _LEGEND blocks enumerate allowed enum values (visualization_types,
            # knob_styles, …). Merge them (union) into the global legends lookup.
            if key == "_LEGEND" and isinstance(schema, dict):
                for lk, lv in schema.items():
                    if isinstance(lv, list):
                        bucket = legends.setdefault(lk, [])
                        for item in lv:
                            if item not in bucket:
                                bucket.append(item)
                continue
            # Skip other non-widget entries (no "type").
            if not isinstance(schema, dict) or "type" not in schema:
                continue
            components.append({
                "name": key,
                "category": category,
                "type": schema.get("type", "unknown"),
                "schema": schema,
                "path": os.path.relpath(full, root),
            })
    components.sort(key=lambda c: (c["category"].lower(), c["name"].lower()))
    return {"components": components, "legends": legends}


class APIRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def _send_json(self, code, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        parsed_path = urllib.parse.urlparse(self.path)

        # Persist an edited GUI definition back to Gui_Frames (WYSIWYG editor save).
        if parsed_path.path == "/api/save":
            try:
                length = int(self.headers.get("Content-Length", 0))
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                rel_path = payload["path"]
                content = payload["content"]
            except Exception as e:
                self._send_json(400, {"ok": False, "error": f"Bad request: {e}"})
                return

            # Security: confine writes to Gui_Frames and to .json files only.
            clean_rel = str(rel_path).lstrip("/")
            abs_path = os.path.abspath(os.path.join(GUI_FRAMES_DIR, clean_rel))
            if not abs_path.startswith(GUI_FRAMES_DIR) or not abs_path.endswith(".json"):
                self._send_json(403, {"ok": False, "error": "Path outside Gui_Frames"})
                return

            try:
                # Timestamped .old backup before overwrite (mirrors FileWriter).
                backup_name = None
                if os.path.exists(abs_path):
                    ts = time.strftime("%Y%m%d_%H%M%S")
                    d, name = os.path.split(abs_path)
                    backup_path = os.path.join(d, f"{ts}_{name}.old")
                    with open(abs_path, "rb") as src, open(backup_path, "wb") as dst:
                        dst.write(src.read())
                    backup_name = os.path.basename(backup_path)

                with open(abs_path, "w", encoding="utf-8") as f:
                    json.dump(content, f, indent=2, ensure_ascii=False)

                self._send_json(200, {"ok": True, "saved": rel_path, "backup": backup_name})
            except Exception as e:
                self._send_json(500, {"ok": False, "error": str(e)})
            return

        self._send_json(404, {"ok": False, "error": "Unknown endpoint"})

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)

        # Serve the directory tree as JSON
        if parsed_path.path == '/api/tree':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            tree = get_directory_tree(GUI_FRAMES_DIR)
            self.wfile.write(json.dumps(tree).encode('utf-8'))
            return

        # Serve the categorized grab-bag palette for the WYSIWYG editor
        if parsed_path.path == '/api/grabbag':
            self._send_json(200, get_grab_bag())
            return

        # Serve local images from the project root
        if parsed_path.path == '/api/image':
            query = urllib.parse.parse_qs(parsed_path.query)
            image_rel_path = query.get('path', [None])[0]
            if image_rel_path:
                # Security: prevent directory traversal
                clean_rel = image_rel_path.lstrip('/')
                abs_project_root = os.path.abspath(os.path.join(FRONTEND_DIR, ".."))
                image_abs_path = os.path.abspath(os.path.join(abs_project_root, clean_rel))

                if image_abs_path.startswith(abs_project_root) and os.path.exists(image_abs_path):
                    self.send_response(200)
                    if image_abs_path.endswith('.png'): self.send_header('Content-Type', 'image/png')
                    elif image_abs_path.endswith('.jpg') or image_abs_path.endswith('.jpeg'): self.send_header('Content-Type', 'image/jpeg')
                    elif image_abs_path.endswith('.svg'): self.send_header('Content-Type', 'image/svg+xml')
                    elif image_abs_path.endswith('.gif'): self.send_header('Content-Type', 'image/gif')
                    self.end_headers()
                    with open(image_abs_path, 'rb') as f:
                        self.wfile.write(f.read())
                    return

            self.send_response(404)
            self.end_headers()
            return

        # Default to serving static files
        if parsed_path.path == '/':
            self.path = '/Core/Launch/index.html'

        return super().do_GET()

def run(server_class=HTTPServer, handler_class=APIRequestHandler, port=PORT):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"🚀 [DEPLOY] Starting Open-Air Web Server on http://localhost:{port}")
    print(f"📂 [ROUTING] Serving frontend from: {FRONTEND_DIR}")
    print(f"📂 [ROUTING] API tracking Gui_Frames from: {GUI_FRAMES_DIR}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 [STOP] Server stopped by user.")
        httpd.server_close()

if __name__ == "__main__":
    run()
