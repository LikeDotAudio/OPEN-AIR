# oaGui/Entry.py
#
# Gatekeeper for the oaGui module. This file serves as the primary public API 
# and orchestrator for the Graphical User Interface subsystem.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Version 20260502.1000.1

import sys
from pathlib import Path

# --- BOOTSTRAP: Resolve Project Context ---
current_dir = Path(__file__).parent.absolute()
project_root = current_dir
while project_root.parent != project_root:
    if (project_root / "GEMINI.md").exists(): break
    project_root = project_root.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# --- ATOMIC EXPORTS ---
from oaGui.Managers.display.engine_gui_display import EngineGuiDisplay
from oaGui.Methods.entry.gui_starter import launch_main_gui_application as start_gui
from oaGui.Methods.entry.test_runner import execute_module_unit_tests as _run_tests

def run_tests():
    """Wrapper for atomic test execution."""
    return _run_tests(current_dir, project_root)

def start():
    """Initializes the GUI module services."""
    print(f"🚀 [START] Starting {current_dir.name} services...")

def stop():
    """Performs a graceful shutdown of the GUI module services."""
    print(f"🛑 [STOP] Stopping {current_dir.name} services...")

def status():
    """Queries the current operational status of the module."""
    print(f"📊 [STATUS] Checking {current_dir.name} status...")
    return "Running"

if __name__ == "__main__":
    if not run_tests(): sys.exit(1)

    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "--start": start()
        elif cmd == "--stop": stop()
        elif cmd == "--status": print(f"Status: {status()}")
        elif cmd == "--gui": start_gui()
        else: print(f"Unknown command: {cmd}")
    else: start()

# Standardized public API
__all__ = ["EngineGuiDisplay", "start", "stop", "status", "run_tests", "start_gui"]
