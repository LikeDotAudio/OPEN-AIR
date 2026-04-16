# oaTests/Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260415.2150.1
#
# Description: Gatekeeper for the oaTests module.

import subprocess
from pathlib import Path

import sys
import os

def _inject_project_root():
    """Calculates and injects the project root into sys.path."""
    # Current file: project_root/oaTests/Entry.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    return project_root

def main():
    """
    Entry point for the OPEN-AIR Testing Module.
    Initializes the Textual UI for test management.
    """
    project_root = _inject_project_root()

    try:
        # Initialize specialized test logging
        from oaLogging.Entry import initialize_test_logging, TEST_LOGGER
        test_log_dir = os.path.join(project_root, "oaDataLogs", "TestLog")
        initialize_test_logging(test_log_dir)
        TEST_LOGGER.info("🧪 [INIT] Test Logging System Online.")

        # Import the Textual App from the Interface sub-module
        from oaTests.Interface.TestsUI import TestsApp
        app = TestsApp(project_root)
        app.run()
    except ImportError as e:
        print(f"🛑 [ERROR] Failed to load testing interface: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"🛑 [CRITICAL] Unexpected error during test suite execution: {e}")
        sys.exit(1)


def run_tests():
    """
    Discover and run tests in the local Tests/ directory using unittest via subprocess.
    Ensures isolation and proper sys.path handling.
    """
    import subprocess
    import sys
    import os
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
    main()

def stop():
    """Stop the module services."""
    print(f"🛑 [STOP] Stopping {Path(__file__).parent.name} services...")

def status():
    """Get the module status."""
    print(f"📊 [STATUS] Checking {Path(__file__).parent.name} status...")
    return "Running"

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
