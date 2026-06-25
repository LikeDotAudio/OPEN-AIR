#!/usr/bin/env python3
"""openair.py — single entry point for the OPEN-AIR application.

This is the launcher that replaces ``FrontEnd/Entry.py``. It brings up the whole
stack in one process tree:

  1. Builds and imports the Rust core (``oaRustCore`` — the pyo3 extension that
     the Python helpers in BackEnd/Core call into).
  2. Builds and launches the native Rust orchestrator binary
     (``open-air-orchestrator`` — the async protocol agents + WebSocket API).
  3. Serves the HTML5 frontend and opens it in the browser (the role that
     ``FrontEnd/Entry.py`` used to fill).

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
import importlib
import os
import shutil
import subprocess
import sys

# --- Paths ------------------------------------------------------------------
ROOT = os.path.abspath(os.path.dirname(__file__))
FRONTEND_DIR = os.path.join(ROOT, "FrontEnd")
CORE_DIR = os.path.join(ROOT, "BackEnd", "Core")
CORE_MANIFEST = os.path.join(CORE_DIR, "Cargo.toml")
ORCHESTRATOR_BIN_NAME = "open-air-orchestrator"
RUST_LIB_NAME = "liboaRustCore.so"   # produced by cargo/maturin
PY_MODULE_SO = "oaRustCore.so"       # name Python needs to import `oaRustCore`

DEFAULT_FRONTEND_PORT = 8000
DEFAULT_CORE_PORT = 8001


def _log(msg):
    print(msg, flush=True)


# --- Rust: build -------------------------------------------------------------
def build_rust(release: bool) -> bool:
    """Build the Core workspace (oaRustCore lib + orchestrator bin). Returns
    True on success. A single `cargo build` covers both workspace members."""
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
    for pkg in ("oaRustCore", "open-air-orchestrator"):
        _log(f"🦀 [RUST] Building {pkg} ({'release' if release else 'debug'})…")
        try:
            subprocess.run(base + ["-p", pkg], check=True)
        except subprocess.CalledProcessError as e:
            _log(f"❌ [RUST] Build of {pkg} failed (exit {e.returncode}).")
            return False
    _log("✅ [RUST] Build complete.")
    return True


def _target_dir(release: bool) -> str:
    return os.path.join(CORE_DIR, "target", "release" if release else "debug")


# --- Rust: pyo3 core ---------------------------------------------------------
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


# --- Rust: orchestrator ------------------------------------------------------
def launch_orchestrator(release: bool, core_port: int):
    """Spawn the native orchestrator binary on `core_port`. Returns the Popen
    handle (registered for cleanup) or None on failure."""
    binary = os.path.join(_target_dir(release), ORCHESTRATOR_BIN_NAME)
    if not os.path.exists(binary):
        _log(f"⚠️  [ORCH] Binary not found at {binary} — skipping orchestrator.")
        return None

    env = dict(os.environ, OPENAIR_CORE_PORT=str(core_port))
    _log(f"🚀 [ORCH] Launching {ORCHESTRATOR_BIN_NAME} on port {core_port}…")
    try:
        proc = subprocess.Popen([binary], env=env)
    except OSError as e:
        _log(f"❌ [ORCH] Failed to launch orchestrator: {e}")
        return None

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


# --- Frontend ----------------------------------------------------------------
def serve_frontend(port: int, open_browser: bool):
    """Serve the HTML5 frontend by reusing FrontEnd/Entry.py's HTTP server.
    Blocks until interrupted (Ctrl-C)."""
    if FRONTEND_DIR not in sys.path:
        sys.path.insert(0, FRONTEND_DIR)
    try:
        entry = importlib.import_module("Entry")
    except Exception as e:
        _log(f"❌ [WEB] Could not load the frontend server (FrontEnd/Entry.py): {e}")
        raise
    # Entry.run() binds the socket, optionally opens Chrome, then serve_forever().
    entry.run(port=port, open_browser=open_browser)


# --- Main --------------------------------------------------------------------
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
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    _log("=" * 64)
    _log("🎛️  OPEN-AIR launcher")
    _log("=" * 64)

    if not args.no_rust:
        if not args.no_build:
            build_rust(args.release)
        # Load the in-process pyo3 core.
        load_rust_core(args.release)
        # Launch the native orchestrator (separate process).
        if not args.no_orchestrator:
            launch_orchestrator(args.release, args.core_port)
    else:
        _log("⏭️  [RUST] --no-rust set; skipping Rust core and orchestrator.")

    _log(f"🌐 [WEB] Serving frontend on http://localhost:{args.port}")
    try:
        serve_frontend(args.port, open_browser=not args.no_browser)
    except KeyboardInterrupt:
        _log("\n🛑 [STOP] Shutting down.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
