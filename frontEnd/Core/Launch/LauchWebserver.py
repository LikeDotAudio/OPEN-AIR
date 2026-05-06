import os
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse

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
                    with open(full_path, 'r', encoding='utf-8') as f:
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

class APIRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

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
