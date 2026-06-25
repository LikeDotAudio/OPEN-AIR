#!/usr/bin/env python3
"""openair.py — single entry point for the OPEN-AIR application.

This is the ONE launcher for the whole stack. It fully replaces the old
``FrontEnd/Entry.py`` (now a deprecated stub) — everything needed to serve the
frontend lives here. It brings up, in one process tree:

  1. The Rust core (``oaRustCore`` — the pyo3 extension the BackEnd/Core Python
     helpers call into): built with cargo and imported in-process.
  2. The native Rust orchestrator binary (``open-air-orchestrator`` — async
     protocol agents + WebSocket API): built and launched as a subprocess.
  3. The HTML5 frontend: served over HTTP (static files + the /api/* endpoints
     the WYSIWYG editor and protocol panels use) and opened in the browser.

Rust failures are non-fatal: if the toolchain or a build step fails, the
frontend still comes up so the UI is usable, and a clear warning is printed.

Usage:
    python3 openair.py [options]

Options:
    --port N           Frontend static/API server port (default: 8000).
    --core-port N      Rust orchestrator port (default: 8001).
    --no-build         Skip cargo builds; use whatever artifacts already exist.
    --release          Build the Rust artifacts in release mode (default: debug).
    --no-orchestrator  Do not launch the Rust orchestrator binary.
    --no-rust          Skip all Rust work (core import + orchestrator). Frontend only.
    --no-browser       Do not auto-open the browser.
"""

import argparse
import atexit
import configparser
import errno
import importlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import urllib.parse
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

# --- Paths ------------------------------------------------------------------
ROOT = os.path.abspath(os.path.dirname(__file__))
FRONTEND_DIR = os.path.join(ROOT, "FrontEnd")
GUI_FRAMES_DIR = os.path.join(ROOT, "Gui_Frames")
COMPROTOCOLS_DIR = os.path.join(ROOT, "BackEnd", "ComProtocols")
CORE_DIR = os.path.join(ROOT, "BackEnd", "Core")
CORE_MANIFEST = os.path.join(CORE_DIR, "Cargo.toml")
ORCHESTRATOR_BIN_NAME = "open-air-orchestrator"
RUST_LIB_NAME = "liboaRustCore.so"   # produced by cargo/maturin
PY_MODULE_SO = "oaRustCore.so"       # name Python needs to import `oaRustCore`

DEFAULT_FRONTEND_PORT = 8000
DEFAULT_CORE_PORT = 8001


def _log(msg):
    print(msg, flush=True)


# ============================================================================
# Rust: build
# ============================================================================
def build_rust(release: bool) -> bool:
    """Build the Core workspace (oaRustCore lib + orchestrator bin). Returns
    True on success."""
    cargo = shutil.which("cargo")
    if not cargo:
        _log("⚠️  [RUST] cargo not found on PATH — skipping Rust build.")
        return False
    base = [cargo, "build", "--manifest-path", CORE_MANIFEST]
    if release:
        base.append("--release")
    # Build the pyo3 core and the orchestrator binary in SEPARATE invocations.
    # The protocol crates expose their pyo3 modules behind a `python` feature that
    # oaRustCore enables; building both members at once would unify pyo3's
    # extension-module feature onto the orchestrator, which must NOT link
    # libpython. Separate `-p` builds keep their feature sets independent.
    # Compiler warnings (unused imports, `non_snake_case` on the pyo3 module
    # exports whose names must match the Python import, etc.) are benign but flood
    # the launcher on every run. Swallow cargo's output on success and only surface
    # it when a build FAILS — real errors still come through. Set
    # OPENAIR_VERBOSE_BUILD=1 to stream the full output (warnings included).
    verbose = bool(os.environ.get("OPENAIR_VERBOSE_BUILD"))
    for pkg in ("oaRustCore", "open-air-orchestrator"):
        _log(f"🦀 [RUST] Building {pkg} ({'release' if release else 'debug'})…")
        try:
            subprocess.run(base + ["-p", pkg], check=True,
                           capture_output=not verbose, text=True)
        except subprocess.CalledProcessError as e:
            _log(f"❌ [RUST] Build of {pkg} failed (exit {e.returncode}).")
            if not verbose:
                if e.stdout:
                    _log(e.stdout.rstrip())
                if e.stderr:
                    _log(e.stderr.rstrip())
            return False
    _log("✅ [RUST] Build complete.")
    return True


def _target_dir(release: bool) -> str:
    return os.path.join(CORE_DIR, "target", "release" if release else "debug")


# ============================================================================
# Rust: pyo3 core
# ============================================================================
def load_rust_core(release: bool):
    """Make the compiled ``oaRustCore`` cdylib importable and import it.

    cargo emits ``liboaRustCore.so``; Python needs it named ``oaRustCore.so`` on
    sys.path. We (re)point BackEnd/Core/oaRustCore.so at the fresh artifact and
    import it. Returns the module, or None on failure."""
    built = os.path.join(_target_dir(release), RUST_LIB_NAME)
    link = os.path.join(CORE_DIR, PY_MODULE_SO)

    if not os.path.exists(built):
        _log(f"⚠️  [CORE] {RUST_LIB_NAME} not found at {built} — is the build done?")
        return None

    # Refresh the import symlink (the old one pointed at a now-removed path).
    try:
        if os.path.islink(link) or os.path.exists(link):
            os.remove(link)
        os.symlink(os.path.relpath(built, CORE_DIR), link)
    except OSError as e:
        _log(f"⚠️  [CORE] Could not create {PY_MODULE_SO} symlink: {e}")

    if CORE_DIR not in sys.path:
        sys.path.insert(0, CORE_DIR)

    try:
        mod = importlib.import_module("oaRustCore")
    except Exception as e:  # ImportError or native init failure
        _log(f"❌ [CORE] Failed to import oaRustCore: {e}")
        return None
    _log(f"✅ [CORE] oaRustCore loaded ({getattr(mod, '__file__', '?')}).")
    return mod


# ============================================================================
# Rust: orchestrator
# ============================================================================
def _kill_stale_orchestrators():
    """Terminate any leftover orchestrator processes from earlier runs (the
    binary is exclusively ours). Debugger stops often orphan it, leaving its
    ports held; clean them up before launching a fresh one."""
    if not shutil.which("pgrep"):
        return
    try:
        out = subprocess.run(["pgrep", "-f", ORCHESTRATOR_BIN_NAME],
                             capture_output=True, text=True, timeout=3).stdout
    except Exception:
        return
    me = os.getpid()
    for pid in (int(p) for p in out.split() if p.isdigit()):
        if pid == me:
            continue
        try:
            os.kill(pid, signal.SIGTERM)
            _log(f"🧹 [ORCH] terminated stale orchestrator PID {pid}.")
        except OSError:
            pass


def _pdeathsig():
    """preexec_fn: on Linux, ask the kernel to SIGTERM this child when the
    launcher dies — so a debugger-killed launcher doesn't orphan it."""
    try:
        import ctypes
        # PR_SET_PDEATHSIG = 1, signal 15 (SIGTERM)
        ctypes.CDLL("libc.so.6", use_errno=True).prctl(1, 15, 0, 0, 0)
    except Exception:
        pass


def launch_orchestrator(release: bool, core_port: int):
    """Spawn the native orchestrator binary on `core_port`. Returns the Popen
    handle (registered for cleanup) or None on failure."""
    binary = os.path.join(_target_dir(release), ORCHESTRATOR_BIN_NAME)
    if not os.path.exists(binary):
        _log(f"⚠️  [ORCH] Binary not found at {binary} — skipping orchestrator.")
        return None

    _kill_stale_orchestrators()  # avoid AddrInUse from a previous run's orphan
    env = dict(os.environ, OPENAIR_CORE_PORT=str(core_port))
    _log(f"🚀 [ORCH] Launching {ORCHESTRATOR_BIN_NAME} on port {core_port}…")
    try:
        proc = subprocess.Popen(
            [binary], env=env,
            preexec_fn=_pdeathsig if sys.platform == "linux" else None,
        )
    except OSError as e:
        _log(f"❌ [ORCH] Failed to launch orchestrator: {e}")
        return None
    _log(f"🦀 [ORCH] {ORCHESTRATOR_BIN_NAME} running (PID {proc.pid}).")

    def _cleanup():
        if proc.poll() is None:
            _log("🛑 [ORCH] Stopping orchestrator…")
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

    atexit.register(_cleanup)
    return proc


# ============================================================================
# MQTT: publish each protocol's config.ini on startup
# ============================================================================
def _list_protocols_with_config():
    """Return [(proto, ini_path)] for every openair-<proto> crate shipping a config.ini."""
    out = []
    if not os.path.isdir(COMPROTOCOLS_DIR):
        return out
    for entry in sorted(os.listdir(COMPROTOCOLS_DIR)):
        if entry.startswith("openair-"):
            ini = os.path.join(COMPROTOCOLS_DIR, entry, "config.ini")
            if os.path.isfile(ini):
                out.append((entry[len("openair-"):], ini))
    return out


def publish_protocol_configs():
    """Publish every protocol's config.ini (retained) to the MQTT bus so the
    backend protocols announce themselves the moment the app starts — before any
    GUI panel is opened.

    For each protocol we publish, retained, to the protocol's own `topic` from
    its config.ini (default OpenAir/System/Protocols/<proto>):
      <topic>/config  -> the parsed config.ini as JSON
      <topic>/status  -> "online"

    Best-effort: warns and returns on any failure (no client lib / no broker)."""
    try:
        import paho.mqtt.client as mqtt
    except ImportError:
        _log("⚠️  [MQTT] paho-mqtt not installed; skipping config publish "
             "(`pip install paho-mqtt`).")
        return

    protos = _list_protocols_with_config()
    if not protos:
        _log("⚠️  [MQTT] No protocol config.ini files found; nothing to publish.")
        return

    # Broker connection comes from the mqtt protocol's own config.ini.
    host, port = "127.0.0.1", 1883
    try:
        mqtt_cfg, _ = get_protocol_config("mqtt")
        sect = mqtt_cfg.get("mqtt", {})
        host = sect.get("host", host)
        port = int(sect.get("tcp_port", port))
    except Exception:
        pass

    try:
        try:
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)  # paho 2.x
        except (AttributeError, TypeError):
            client = mqtt.Client()                                  # paho 1.x
        client.connect(host, port, keepalive=30)
        client.loop_start()
    except Exception as e:
        _log(f"⚠️  [MQTT] Could not connect to broker {host}:{port}: {e}")
        _log("        Protocol configs not published — is mosquitto running?")
        return

    infos, published = [], []
    for proto, ini_path in protos:
        try:
            config, _ = get_protocol_config(proto)
        except ValueError:
            continue
        sect = config.get(proto, {})
        topic = sect.get("topic", f"OpenAir/System/Protocols/{proto}")
        payload = json.dumps({
            "value": config,
            "path": os.path.relpath(ini_path, ROOT),
            "source": "backend",
        })
        infos.append(client.publish(f"{topic}/config", payload, qos=1, retain=True))
        infos.append(client.publish(f"{topic}/status", "online", qos=1, retain=True))
        published.append(topic)

    for info in infos:
        try:
            info.wait_for_publish(timeout=2)
        except Exception:
            pass
    client.loop_stop()
    client.disconnect()

    _log(f"📡 [MQTT] Published {len(published)} protocol configs (retained) to {host}:{port}:")
    for t in published:
        _log(f"   • {t}/config  (+ /status=online)")


# ============================================================================
# Frontend server (formerly FrontEnd/Entry.py, now owned here)
# ============================================================================
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
                "path": os.path.relpath(ini_path, ROOT),
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
                image_abs_path = os.path.abspath(os.path.join(ROOT, clean_rel))

                if image_abs_path.startswith(ROOT) and os.path.exists(image_abs_path):
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

        # Default to serving the launch page
        if parsed_path.path == '/':
            self.path = '/Core/Launch/index.html'

        return super().do_GET()


def open_in_chrome(url):
    """Open `url` in Chrome, falling back to Chromium then the default browser."""
    for name in ("google-chrome", "chrome", "chromium", "chromium-browser"):
        try:
            webbrowser.get(name).open(url)
            return
        except webbrowser.Error:
            pass
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
    webbrowser.open(url)


def _who_holds_port(port):
    """Best-effort: return a short string identifying the PID(s) holding `port`."""
    for cmd in (["lsof", "-ti", f":{port}"], ["ss", "-ltnp"]):
        exe = shutil.which(cmd[0])
        if not exe:
            continue
        try:
            out = subprocess.run([exe, *cmd[1:]], capture_output=True, text=True, timeout=3).stdout
        except Exception:
            continue
        if cmd[0] == "lsof":
            pids = out.split()
            if pids:
                return f"PID(s) {', '.join(pids)} (stop with: kill {' '.join(pids)})"
        else:
            for line in out.splitlines():
                if f":{port} " in line or line.rstrip().endswith(f":{port}"):
                    return line.strip()
    return "another process"


def serve_frontend(port: int, open_browser: bool) -> bool:
    """Serve the HTML5 frontend (static files + /api/*). Blocks until Ctrl-C.
    Returns False if the port is already in use (handled gracefully)."""
    try:
        httpd = ThreadingHTTPServer(('', port), APIRequestHandler)
    except OSError as e:
        if e.errno == errno.EADDRINUSE:
            holder = _who_holds_port(port)
            _log(f"❌ [WEB] Port {port} is already in use by {holder}.")
            _log(f"        Another OPEN-AIR/server instance is likely running. "
                 f"Stop it, or start with a different port: python3 openair.py --port {port + 1}")
            return False
        raise

    httpd.daemon_threads = True
    url = f"http://localhost:{port}"
    _log(f"🚀 [WEB] Serving frontend on {url} (server PID {os.getpid()})")
    _log(f"📂 [WEB] Frontend root: {FRONTEND_DIR}")
    _log(f"📂 [WEB] Gui_Frames API root: {GUI_FRAMES_DIR}")
    if open_browser:
        _log(f"🌐 [WEB] Opening {url} in the browser…")
        threading.Timer(1.0, lambda: open_in_chrome(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        _log("\n🛑 [STOP] Server stopped by user.")
    finally:
        httpd.server_close()
    return True


# ============================================================================
# Main
# ============================================================================
def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Launch the OPEN-AIR stack (Rust core + frontend).")
    p.add_argument("--port", type=int, default=DEFAULT_FRONTEND_PORT,
                   help=f"Frontend server port (default {DEFAULT_FRONTEND_PORT}).")
    p.add_argument("--core-port", type=int, default=DEFAULT_CORE_PORT,
                   help=f"Rust orchestrator port (default {DEFAULT_CORE_PORT}).")
    p.add_argument("--no-build", action="store_true", help="Skip cargo builds.")
    p.add_argument("--release", action="store_true", help="Build Rust in release mode.")
    p.add_argument("--no-orchestrator", action="store_true",
                   help="Do not launch the Rust orchestrator binary.")
    p.add_argument("--no-rust", action="store_true",
                   help="Skip all Rust (core import + orchestrator).")
    p.add_argument("--no-browser", action="store_true", help="Do not open the browser.")
    p.add_argument("--no-mqtt", action="store_true",
                   help="Do not publish protocol config.ini files to MQTT on startup.")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    _log("=" * 64)
    _log("🎛️  OPEN-AIR launcher")
    _log("=" * 64)

    core = None
    orch = None
    if not args.no_rust:
        if not args.no_build:
            build_rust(args.release)
        # Load the in-process pyo3 core (runs inside THIS process, no own PID).
        core = load_rust_core(args.release)
        # Launch the native orchestrator (separate process, own PID).
        if not args.no_orchestrator:
            orch = launch_orchestrator(args.release, args.core_port)
    else:
        _log("⏭️  [RUST] --no-rust set; skipping Rust core and orchestrator.")

    # Consolidated PID report so every running piece is easy to find/kill.
    _log("─" * 64)
    _log("🧭 [PID] Running processes:")
    _log(f"   • launcher + web server      : {os.getpid()}")
    _log(f"   • oaRustCore (pyo3, in-proc) : {os.getpid() if core is not None else 'not loaded'}"
         + ("  ← same process as launcher" if core is not None else ""))
    _log(f"   • open-air-orchestrator (rust): {orch.pid if orch is not None else 'not running'}")
    _log("─" * 64)

    # Announce every protocol's config.ini on the bus (retained) so they show up
    # immediately under OpenAir/System/Protocols/<proto> without opening a panel.
    if not args.no_mqtt:
        publish_protocol_configs()

    ok = serve_frontend(args.port, open_browser=not args.no_browser)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
