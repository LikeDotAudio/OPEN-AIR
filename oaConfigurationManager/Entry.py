# oaConfigurationManager/Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260415.2210.1
#
# Description: Gatekeeper for the oaConfigurationManager module.

import os
import sys
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

from oaConfigurationManager.FileReaders.config_reader import Config


def get_config_instance():
    """Returns the singleton Config instance."""
    return Config.get_instance()

def initialize_config(config_path=None):
    """Initializes the configuration system."""
    return Config.get_instance(config_path)

def validate():
    """Validates the current configuration."""
    return True # TODO: Implement validation logic

def start():
    """Starts the configuration service."""
    initialize_config()
    print("🚀 [START] ConfigurationManager services started.")

def stop():
    """Stops the configuration service."""
    print("🛑 [STOP] ConfigurationManager services stopped.")

def status():
    """Returns the status of the configuration service."""
    return "active"

def run_tests():
    """
    Discover and run tests in the local Tests/ directory using unittest via subprocess.
    Ensures isolation and proper sys.path handling.
    """
    import subprocess

    print(f"📡📥📥 [TEST] {Path(__file__).parent.name}: Starting automated test discovery...")
    test_dir = current_dir / "Tests"

    if not test_dir.exists():
        print(f"📡📤📤 [TEST] {Path(__file__).parent.name}: No Tests/ directory found.")
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
            print(f"📡📤📤 [TEST] {Path(__file__).parent.name}: All tests PASSED.")
            return True
        else:
            print(f"📡📤📤 [TEST] {Path(__file__).parent.name}: Tests FAILED.")
            return False
    except Exception as e:
        print(f"🛑 [ERROR] {Path(__file__).parent.name}: Test discovery failed: {e}")
        return False

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

# Standardized exports
__all__ = [
    "Config",
    "get_config_instance",
    "initialize_config",
    "validate",
    "start",
    "stop",
    "status",
    "run_tests"
]
