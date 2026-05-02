# oaTranslator/Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260415.2225.1
#
# Description: Gatekeeper for the oaTranslator module.
# The sole orchestrator for the Translator Module.

import os
import subprocess
import sys
import time
from pathlib import Path

# --- Project Path Setup ---
current_dir = Path(__file__).parent.absolute()
project_root = current_dir
while project_root.parent != project_root:
    if (project_root / "GEMINI.md").exists():
        break
    project_root = project_root.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# --- Absolute Imports for Standalone Support ---
from oaTranslator.Managers.yak_translator import YakTranslator
from oaTranslator.Managers.instrument_controller import InstrumentController
from oaTranslator.Managers.yak_trigger_handler import (
    handle_yak_monitor_traffic,
    register_monitor_callback,
    unregister_monitor_callback,
)

_instance = None

def get_translator(mqtt_connection_manager=None, subscriber_router=None):
    """Returns the singleton YakTranslator instance."""
    global _instance
    if _instance is None:
        _instance = YakTranslator(mqtt_connection_manager, subscriber_router)
    return _instance

def start(mqtt_connection_manager=None, subscriber_router=None):
    """
    Initializes and starts the Translator service.
    """
    print(f"🚀 [START] Starting {Path(__file__).parent.name} services...")
    return get_translator(mqtt_connection_manager, subscriber_router)

def stop():
    """
    Shuts down the Translator service.
    """
    global _instance
    if _instance:
        print(f"🛑 [STOP] Stopping {Path(__file__).parent.name} services...")
        _instance = None

def status():
    """Returns the current status of the Translator."""
    return "active" if _instance else "stopped"

def run_tests():
    """
    Discover and run tests in the local Tests/ directory using unittest via subprocess.
    Ensures isolation and proper sys.path handling.
    """
    print(f"📡📥📥 [TEST] {Path(__file__).parent.name}: Starting automated test discovery...")
    test_dir = current_dir / "Tests"

    if not test_dir.exists():
        print(f"⚠️ [TEST] {Path(__file__).parent.name}: No Tests/ directory found.")
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
            try:
                while True: time.sleep(1)
            except KeyboardInterrupt:
                stop()
        elif cmd == "--stop":
            stop()
        elif cmd == "--status":
            print(f"Status: {status()}")
        else:
            print(f"Unknown command: {cmd}")
    else:
        # Default standalone action if no args
        start()
        try:
            while True: time.sleep(1)
        except KeyboardInterrupt:
            stop()

__all__ = [
    "YakTranslator",
    "InstrumentController",
    "register_monitor_callback",
    "unregister_monitor_callback",
    "handle_yak_monitor_traffic",
    "get_translator",
    "start",
    "stop",
    "status",
    "run_tests"
]
