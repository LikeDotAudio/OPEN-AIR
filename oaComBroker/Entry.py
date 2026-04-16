# oaComBroker/Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260415.2215.1
#
# Description: Gatekeeper for the oaComBroker module.

import sys
import os
import threading
import time
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

from oaComBroker.Core.event_bus import EventBus
from oaComBroker.Core.protocol_router.manager import ProtocolRouter

def start():
    """Starts the Communication Broker service (OpenAir Core)."""
    from oaComBroker.Core.open_air_core import main as core_main
    
    # Run core_main in a background thread if called from start()
    # unless we want it to block. In Entry.py, start() usually 
    # should be non-blocking or at least clearly defined.
    # For now, let's allow it to be called as a script to block.
    print("🚀 [START] ComBroker services starting...")
    thread = threading.Thread(target=core_main, daemon=True)
    thread.start()
    return thread

def stop():
    """Stops the Communication Broker service."""
    router = ProtocolRouter.get_instance()
    if router:
        router.shutdown()
    print("🛑 [STOP] ComBroker services stopped.")

def status():
    """Returns the status of the Communication Broker."""
    router = ProtocolRouter.get_instance()
    # ProtocolRouter doesn't have a direct is_running, but we can check if it has a rust_router
    return "Running" if router and hasattr(router, 'rust_router') else "Stopped"

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
        # Run from project root to ensure module resolution works correctly
        result = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", str(test_dir.relative_to(project_root)), "-p", "test_*.py"],
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
            # In script mode, start() might want to block
            from oaComBroker.Core.open_air_core import main as core_main
            core_main()
        elif cmd == "--stop":
            stop()
        elif cmd == "--status":
            print(f"Status: {status()}")
        else:
            print(f"Unknown command: {cmd}")
    else:
        # Default standalone action if no args
        from oaComBroker.Core.open_air_core import main as core_main
        core_main()

# Standardized exports
__all__ = [
    "ProtocolRouter",
    "EventBus",
    "start",
    "stop",
    "status",
    "run_tests"
]
