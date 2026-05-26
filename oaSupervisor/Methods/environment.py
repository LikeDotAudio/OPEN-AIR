# oaSupervisor/Methods/environment.py
#
# Pure-ish setup helpers for the supervisor process:
#   - verify_rust_pipeline:    `maturin develop` the shared Rust core if present.
#   - resolve_partition_scripts: locate + validate the Core/UI/Web entry points.
#   - build_partition_environments: session GUID + per-partition env vars.

import os
import subprocess
import sys
from pathlib import Path


def verify_rust_pipeline(project_root, log):
    """Build the centralised Rust core in-place (develop mode) if it exists."""
    rust_core_dir = Path(project_root) / "oaRustCore"
    if not rust_core_dir.exists():
        return
    log("🏗️ [NATIVE] Verifying high-performance Rust core...")
    try:
        env = os.environ.copy()
        env["PIP_BREAK_SYSTEM_PACKAGES"] = "1"
        subprocess.check_call(
            [sys.executable, "-m", "maturin", "develop"],
            cwd=str(rust_core_dir), env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
        )
        log("✨ [NATIVE] Rust pipeline verified and active.")
    except Exception as e:
        log(f"⚠️ [WARNING] Rust build check failed: {e}. "
            f"System will attempt to run with graceful fallbacks.")


def resolve_partition_scripts(project_root, log):
    """Return (core_script, ui_script, web_script) as strings.

    Core and UI are required — missing either is fatal. Web is optional; the
    returned web_script may be None if frontEnd/Entry.py is absent.
    """
    project_root = Path(project_root)
    core_script = project_root / "oaComBroker" / "Core" / "open_air_core.py"
    ui_script = project_root / "oaGui" / "Managers" / "orchestration" / "loader_main_service.py"
    web_script = project_root / "frontEnd" / "Entry.py"

    if not core_script.exists():
        log(f"🛑 CRITICAL FAILURE: Core script not found at {core_script}")
        sys.exit(1)
    if not ui_script.exists():
        log(f"🛑 CRITICAL FAILURE: UI script not found at {ui_script}")
        sys.exit(1)
    if not web_script.exists():
        log(f"⚠️ [WARNING] Web interface launcher not found at {web_script}. "
            f"Skipping web UI.")
        web_script = None

    return (str(core_script), str(ui_script), str(web_script) if web_script else None)


def _new_session_guid():
    """Generate a non-persistent 64-bit hex session identifier."""
    return os.urandom(8).hex().upper()


def build_partition_environments(project_root, log):
    """Build (session_guid, child_env, core_env, ui_env) with the GUID injected."""
    session_guid = _new_session_guid()
    log(f"Session Identity established (Randomized): {session_guid}")

    child_env = os.environ.copy()
    child_env["OPEN_AIR_INSTANCE_GUID"] = session_guid
    child_env["PYTHONPATH"] = os.pathsep.join(
        [str(project_root), child_env.get("PYTHONPATH", "")]
    )

    core_env = child_env.copy()
    core_env["OPEN_AIR_PARTITION_ID"] = "CORE"
    ui_env = child_env.copy()
    ui_env["OPEN_AIR_PARTITION_ID"] = "UI"

    return session_guid, child_env, core_env, ui_env
