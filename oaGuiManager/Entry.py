# oaGuiManager/Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260415.2150.1
#
# Description: Gatekeeper for the oaGuiManager module.


import os
import sys
from pathlib import Path

# Add project root to sys.path to allow absolute imports when run as a script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from oaGuiManager.Core.bootstrap_sequence import AsyncBootstrapEngine
from oaGuiManager.Core.composition_root import UICompositionRoot
from oaGuiManager.Core.shutdown_coordinator import ShutdownCoordinator
from oaGuiManager.Core.ui_window import UIWindowManager

"""
oaGuiManager/Entry.py - Gatekeeper for oaGuiManager
"""

def start(root=None, app_constants=None):
    """
    Starts the UI Manager lifecycle.

    Args:
        root (tk.Tk, optional): Existing Tk root window.
        app_constants (Config, optional): Application configuration.

    Returns:
        tuple: (root, shared_services, bootstrap_engine)
    """
    if not root:
        root = UIWindowManager.create_root_window()

    if not app_constants:
        from oaConfigurationManager.FileReaders.config_reader import Config
        app_constants = Config.get_instance()

    from oaGuiSplashScreen.Methods.splash_screen import SplashScreen
    splash = SplashScreen(root, app_constants.CURRENT_VERSION, app_constants.global_settings["debug_enabled"])
    splash.set_status("Composing Service Graph...")

    composition_root = UICompositionRoot(root, app_constants)
    shared_services = composition_root.build_services()

    shutdown_coordinator = ShutdownCoordinator(root, shared_services, True)
    shutdown_coordinator.attach_to_root()

    bootstrap_engine = AsyncBootstrapEngine(root, splash, shared_services, app_constants, shutdown_coordinator)

    import threading
    threading.Thread(target=bootstrap_engine.run, daemon=True).start()

    return root, shared_services, bootstrap_engine

def stop(root, shared_services=None):
    """
    Stops the UI Manager and performs cleanup.
    """
    if shared_services and "shutdown_coordinator" in shared_services:
        shared_services["shutdown_coordinator"].shutdown()
    elif root:
        root.destroy()

def status():
    """
    Returns the status of the UI Manager.
    """
    return "Running" if "tkinter" in sys.modules else "Stopped"

# Standardized exports
    "UIWindowManager",
    "ShutdownCoordinator",
    "AsyncBootstrapEngine",
    "UICompositionRoot",
    "start",
    "stop",
    "status"



def run_tests():
    """
    Discover and run tests in the local Tests/ directory using unittest via subprocess.
    Ensures isolation and proper sys.path handling.
    """
    import subprocess
    import sys
    from pathlib import Path

    print(f"📡📥📥 [TEST] {Path(__file__).parent.name}: Starting automated test discovery...")
    current_dir = Path(__file__).parent.absolute()
    test_dir = current_dir / "Tests"

    if not test_dir.exists():
        return True

    project_root = current_dir
    while project_root.parent != project_root:
        if (project_root / "GEMINI.md").exists():
            break
        project_root = project_root.parent

    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root) + os.pathsep + env.get("PYTHONPATH", "")

    try:
        rel_test_dir = os.path.relpath(test_dir, project_root)
        result = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", rel_test_dir, "-p", "test_*.py"],
            cwd=str(project_root),
            env=env,
            capture_output=False
        )
        if result.returncode == 0:
            print(f"📡📤📤 [TEST] {Path(__file__).parent.name}: All tests PASSED.")
            return True
        else:
            print(f"📡📤📤 [TEST] {Path(__file__).parent.name}: Tests FAILED.")
            return False
    except Exception as e:
        print(f"🛑 [ERROR] {Path(__file__).parent.name}: Test discovery failed: {e}")
        return False

def start():
    """Start the module services."""
    print(f"🚀 [START] Starting {Path(__file__).parent.name} services...")

def stop():
    """Stop the module services."""
    print(f"🛑 [STOP] Stopping {Path(__file__).parent.name} services...")

if __name__ == "__main__":
    # Absolute FIRST action: run tests
    if not run_tests():
        print("❌ [CRITICAL] Tests failed. Aborting execution.")
        sys.exit(1)

    # Standalone execution logic
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "--start":
            start()
        elif cmd == "--stop":
            stop()
        elif cmd == "--status":
            print(f"Status: {status()}")
        else:
            print(f"Unknown command: {cmd}")
    else:
        # Default standalone action if no args
        start()

    "start",
    "stop",
    "status",
    "run_tests",
__all__ = ["start", "stop", "status", "run_tests"]
