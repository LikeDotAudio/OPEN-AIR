# oaDocumentation/Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260415.2150.1
#
# Description: Gatekeeper for the oaDocumentation module.



import os
import sys
from pathlib import Path

"""
oaDocumentation/Entry.py - The sole orchestrator for the Documentation Module.

Purpose:
This file is the public entry point for 'oaDocumentation'. It manages the
documentation retrieval and display logic.
"""

class DocumentationEntry:
    """Entry point for documentation management services."""
    def __init__(self):
        print("📡📥📥 [INBOUND] Initializing DocumentationEntry...")
        pass

    def start(self):
        """Starts the documentation service (e.g., loads documentation index)."""
        print("📚 [DOCS] Starting Documentation service...")
        # Placeholder for start logic, e.g., indexing documentation files
        pass

    def stop(self):
        """Stops the documentation service."""
        print("🛑 [DOCS] Stopping Documentation service...")
        # Placeholder for stop logic
        pass

    def status(self):
        """Returns the current status of the documentation service."""
        print("ℹ️ [DOCS] Checking Documentation service status...")
        # Placeholder for status check logic
        return "ready" # Example status

def main():
    """Entry point for script execution."""
    # This might be adapted to use DocumentationEntry or perform other actions
    print("Running Documentation module main entry point.")
    docs_manager = DocumentationEntry()
    docs_manager.start()
    print(f"Status: {docs_manager.status()}")
    docs_manager.stop()

# Standardized exports
__all__ = [
    "DocumentationEntry",
    "main",
    "start",
    "stop",
    "status",
    "run_tests",
]


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
        if result.returncode in [0, 5]:
            if result.returncode == 5:
                print(f"📡📤📤 [TEST] {Path(__file__).parent.name}: No tests found, but discovery succeeded.")
            else:
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

