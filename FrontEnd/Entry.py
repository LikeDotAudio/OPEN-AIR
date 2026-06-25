import configparser
import json
import os
import re
import shutil
import threading
import time
import urllib.parse
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler

# Paths — Entry.py lives at frontEnd/, so the frontend root is its own directory.
FRONTEND_DIR = os.path.abspath(os.path.dirname(__file__))
GUI_FRAMES_DIR = os.path.abspath(os.path.join(FRONTEND_DIR, "../Gui_Frames"))
# Per-protocol config.ini files live beside each protocol crate.
COMPROTOCOLS_DIR = os.path.abspath(os.path.join(FRONTEND_DIR, "../BackEnd/ComProtocols"))
PORT = 8000


def get_protocol_config(proto):
    """Read BackEnd/ComProtocols/openair-<proto>/config.ini and return it as a
    nested dict {section: {key: value}}. Returns (config_dict, abs_path) or
    raises ValueError on a bad/unsafe proto name or missing file."""
    # Security: proto is a single path token (letters/digits only) so it can't
    # escape the ComProtocols directory.
    if not proto or not re.fullmatch(r"[A-Za-z0-9]+", proto):
        raise ValueError(f"Invalid protocol name: {proto!r}")
    crate_dir = os.path.abspath(os.path.join(COMPROTOCOLS_DIR, f"openair-{proto.lower()}"))
    if not crate_dir.startswith(COMPROTOCOLS_DIR):
        raise ValueError("Path outside ComProtocols")
    ini_path = os.path.join(crate_dir, "config.ini")
    if not os.path.isfile(ini_path):
        raise ValueError(f"No config.ini for protocol {proto!r}")
    parser = configparser.ConfigParser()
    parser.read(ini_path, encoding="utf-8")
    config = {section: dict(parser.items(section)) for section in parser.sections()}
    return config, ini_path

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

def strip_volatile(obj):
    """Remove runtime-only keys (e.g. value.current_value) so they never persist."""
    if isinstance(obj, dict):
        obj.pop("current_value", None)
        for v in obj.values():
            strip_volatile(v)
    elif isinstance(obj, list):
        for v in obj:
            strip_volatile(v)
    return obj


def _extract_readme_json(md_text):
    """Return the first ```json fenced block in a markdown file, parsed; or None."""
    m = re.search(r"```json\s*\n(.*?)\n```", md_text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception:
        return None


def _add_components(content, category, relpath, components, legends, seen):
    """Append widget entries from a parsed sample dict (deduped by name); merge
    every _LEGEND enum block into the shared legends lookup."""
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
        if key == "_README":
            continue
        # Skip non-widget entries (no "type") and names already supplied.
        if not isinstance(schema, dict) or "type" not in schema:
            continue
        if key in seen:
            continue
        seen.add(key)
        components.append({
            "name": key,
            "category": category,
            "type": schema.get("type", "unknown"),
            "schema": schema,
            "path": relpath,
        })


def get_grab_bag():
    """Build the WYSIWYG palette. The libControl component READMEs are the source
    of truth: each <Component>/Readme.md embeds one ```json sample block. We scan
    those first (authoritative), then fall back to oaGuiElements/*/sample.json for
    any widget a README has not already provided (deduped by sample name). Returns
    a flat, categorized component list + merged enum legends for the editor."""
    components = []
    legends = {}
    seen = set()

    # 1. libControl component READMEs — authoritative.
    lib_root = os.path.join(FRONTEND_DIR, "libControl")
    for dirpath, _dirnames, filenames in os.walk(lib_root):
        readme = next((f for f in filenames if f.lower() == "readme.md"), None)
        if not readme:
            continue
        full = os.path.join(dirpath, readme)
        try:
            content = _extract_readme_json(open(full, encoding="utf-8").read())
        except Exception:
            content = None
        if not content:
            continue
        rel = os.path.relpath(dirpath, lib_root).split(os.sep)
        # Category = the libControl group folder (buttons, faders, …); a component
        # sitting at the libControl root (BreakLine) is grouped as "structure".
        category = rel[0] if len(rel) > 1 else "structure"
        _add_components(content, category, os.path.relpath(full, FRONTEND_DIR),
                        components, legends, seen)

    # 2. oaGuiElements/*/sample.json — fallback for widgets with no libControl README.
    oag_root = os.path.abspath(os.path.join(FRONTEND_DIR, "..", "oaGuiElements"))
    for dirpath, _dirnames, filenames in os.walk(oag_root):
        if "sample.json" not in filenames:
            continue
        full = os.path.join(dirpath, "sample.json")
        try:
            with open(full, encoding="utf-8") as f:
                content = json.load(f)
        except Exception:
            continue
        rel_parts = os.path.relpath(dirpath, oag_root).split(os.sep)
        # Category = first meaningful folder segment (skip Core/Assets wrappers).
        meaningful = [p for p in rel_parts if p not in ("Core", "Assets", ".")]
        category = meaningful[0] if meaningful else "General"
        _add_components(content, category, os.path.relpath(full, oag_root),
                        components, legends, seen)

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

                strip_volatile(content)  # never persist value.current_value
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

        # Serve a protocol's config.ini (parsed) for the protocol panels to
        # display + publish to MQTT. e.g. /api/config?proto=osc
        if parsed_path.path == '/api/config':
            query = urllib.parse.parse_qs(parsed_path.query)
            proto = query.get('proto', [None])[0]
            try:
                config, ini_path = get_protocol_config(proto)
            except ValueError as e:
                self._send_json(404, {"ok": False, "error": str(e)})
                return
            self._send_json(200, {
                "ok": True,
                "proto": proto,
                "path": os.path.relpath(ini_path, os.path.join(FRONTEND_DIR, "..")),
                "config": config,
            })
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

def open_in_chrome(url):
    """Open `url` in Chrome, falling back to Chromium then the default browser."""
    # Browsers webbrowser may already know about.
    for name in ("google-chrome", "chrome", "chromium", "chromium-browser"):
        try:
            webbrowser.get(name).open(url)
            return
        except webbrowser.Error:
            pass
    # Otherwise locate a Chrome/Chromium binary directly.
    candidates = [
        "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for cand in candidates:
        path = cand if os.path.exists(cand) else shutil.which(cand)
        if path:
            try:
                webbrowser.get(f'"{path}" %s').open(url)
                return
            except webbrowser.Error:
                pass
    # Last resort: the system default browser.
    webbrowser.open(url)


def run(server_class=HTTPServer, handler_class=APIRequestHandler, port=PORT, open_browser=True):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    url = f"http://localhost:{port}"
    print(f"🚀 [DEPLOY] Starting Open-Air Web Server on {url}")
    print(f"📂 [ROUTING] Serving frontend from: {FRONTEND_DIR}")
    print(f"📂 [ROUTING] API tracking Gui_Frames from: {GUI_FRAMES_DIR}")
    if open_browser:
        # The socket is already bound/listening, so the browser can connect while
        # serve_forever() spins up. Delay slightly so the first request lands cleanly.
        print(f"🌐 [LAUNCH] Opening {url} in Chrome…")
        threading.Timer(1.0, lambda: open_in_chrome(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 [STOP] Server stopped by user.")
        httpd.server_close()

if __name__ == "__main__":
    # DEPRECATED entry point. The frontend server still lives here and is reused
    # by the top-level launcher, but running this file directly is deprecated:
    # it only serves the frontend and does NOT start the Rust backend.
    # Use `python3 openair.py` from the project root instead.
    import warnings
    warnings.warn(
        "FrontEnd/Entry.py is deprecated; run `python3 openair.py` from the "
        "project root to launch the full stack (Rust core + frontend).",
        DeprecationWarning,
        stacklevel=2,
    )
    print("⚠️  [DEPRECATED] FrontEnd/Entry.py serves the frontend ONLY.")
    print("    Run `python3 openair.py` from the project root for the full stack.")
    run()
