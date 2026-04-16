# oaGuiEditorWYSIWYG/Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260416.0150.1
#
# Description: Gatekeeper for the oaGuiEditorWYSIWYG module.

import sys
import os
from pathlib import Path

# Standard project_root resolution
current_dir = Path(__file__).parent.absolute()
project_root = current_dir
while project_root.parent != project_root:
    if (project_root / "GEMINI.md").exists():
        break
    project_root = project_root.parent

# Ensure the project root is in sys.path for absolute imports
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from oaLogging.Methods.matrix_gate import matrix_log
from oaGuiEditorWYSIWYG.Managers.wysiwyg_editor import WysiwygEditor

def launch_editor(parent_window, **kwargs):
    """
    Standard entry point to launch the WYSIWYG Editor.
    """
    return WysiwygEditor.launch(parent_window, **kwargs)


def run_tests():
    """
    Discover and run tests in the local Tests/ directory using unittest via subprocess.
    Ensures isolation and proper sys.path handling.
    """
    import subprocess
    
    matrix_log("ui", "gui_builder", "run_tests", f"🚦🚦🚦 [PIPELINE] {Path(__file__).parent.name}: Starting automated test discovery...", "INFO")
    test_dir = current_dir / "Tests"
    
    if not test_dir.exists():
        matrix_log("ui", "gui_builder", "run_tests", f"🚦🚦🚦 [PIPELINE] {Path(__file__).parent.name}: No Tests/ directory found.", "WARNING")
        return True

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
            matrix_log("ui", "gui_builder", "run_tests", f"🚦🚦🚦 [PIPELINE] {Path(__file__).parent.name}: All tests PASSED.", "SUCCESS")
            return True
        else:
            matrix_log("ui", "gui_builder", "run_tests", f"🚦🚦🚦 [PIPELINE] {Path(__file__).parent.name}: Tests FAILED.", "ERROR")
            return False
    except Exception as e:
        # MANDATE: Errors are NOT gated.
        print(f"❌ {Path(__file__).parent.name}: Test discovery failed: {e}")
        return False

def start(json_path=None):
    """
    Start the module services. Defaults to launching the Standalone GUI.
    """
    matrix_log("ui", "gui_builder", "start", f"🚀🚀🚀 [LAUNCHING] Starting {Path(__file__).parent.name} Standalone GUI...", "INFO")
    
    # 1. Resolve target JSON path
    target_path = json_path
    if not target_path:
        # Check command line for a non-flag path argument
        for arg in sys.argv[1:]:
            if not arg.startswith("-"):
                target_path = arg
                break
    
    # 2. Apply Defaults if no path provided
    if not target_path:
        # Default target for design work
        default_json = project_root / "oaGui" / "Assets" / "left_50" / "top_100" / "0_Spectrum" / "3_Instrument" / "2_bandwidth" / "bandwidth.json"
        if default_json.exists():
            target_path = default_json
        else:
            # Recursive search fallback
            target_path = next(project_root.rglob("*.json"), None)

    if not target_path:
        print("❌ [ERROR] No JSON layout file found to launch.")
        return

    # 3. Hand-off to established run_builder logic
    from oaGuiEditorWYSIWYG.Managers.run_builder import main as launch_main
    
    # We temporarily adjust sys.argv to satisfy run_builder's main() requirements
    original_argv = sys.argv[:]
    sys.argv = [sys.argv[0], str(target_path)]
    
    try:
        launch_main()
    finally:
        sys.argv = original_argv

def stop():
    """Stop the module services."""
    matrix_log("ui", "gui_builder", "stop", f"🛑🛑🛑 [STOPPED] Stopping {Path(__file__).parent.name} services...", "INFO")

def status():
    """Get the module status."""
    return "Running" if "tkinter" in sys.modules else "Stopped"

if __name__ == "__main__":
    # Absolute FIRST action: run tests
    if not run_tests():
        print("❌ [CRITICAL] Tests failed. Aborting execution.")
        sys.exit(1)
    
    # Standalone execution logic
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "--status":
            print(f"Status: {status()}")
        elif cmd == "--test":
            # Tests already run above
            pass
        elif cmd == "--start":
            start()
        else:
            # Assume it's a file path
            start()
    else:
        # Default standalone action if no args
        start()

# Standardized exports
__all__ = [
    "WysiwygEditor",
    "launch_editor",
    "start",
    "stop",
    "status",
    "run_tests"
]
