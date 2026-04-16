# oaPTP/Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260415.2250.1
#
# Description: Gatekeeper for the oaPTP module.
# The sole orchestrator for the PTP Module.

import os
import sys
import subprocess
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
from oaPTP.Core.ptp import PtpManager, register_ptp_callback, unregister_ptp_callback

_instance = None

def get_manager(mqtt_connection_manager=None, subscriber_router=None):
    """Returns the singleton PtpManager instance."""
    global _instance
    if _instance is None:
        _instance = PtpManager(mqtt_connection_manager, subscriber_router)
    return _instance

def start(mqtt_connection_manager=None, subscriber_router=None):
    """
    Initializes and starts the PTP service.
    """
    print(f"🚀 [START] Starting {Path(__file__).parent.name} services...")
    manager = get_manager(mqtt_connection_manager, subscriber_router)
    manager.start()
    return manager

def stop():
    """
    Shuts down the PTP service.
    """
    global _instance
    if _instance:
        print(f"🛑 [STOP] Stopping {Path(__file__).parent.name} services...")
        _instance.stop()
        _instance = None

def status():
    """Returns the current status of the PTP manager."""
    global _instance
    if not _instance:
        return "stopped"
    return "running" if _instance.sniffer_thread and _instance.sniffer_thread.is_alive() else "stalled"

def run_tests():
    """
    Discover and run tests in the local Tests/ directory using unittest via subprocess.
    Ensures isolation and proper sys.path handling.
    """
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
                while True:
                    time.sleep(1)
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
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            stop()

__all__ = ["get_manager", "start", "stop", "status", "run_tests", "register_ptp_callback", "unregister_ptp_callback"]
