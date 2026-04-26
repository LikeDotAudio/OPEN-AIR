# oaComProtocols/oaComManager/Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260415.2210.1
#
# Description: Gatekeeper for the oaComManager module.

import os
import sys
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

from oaComProtocols.oaComManager.Managers.manager import ComProtocolManager
from oaConfigurationManager.FileReaders.config_reader import Config
from oaLogging.Methods.matrix_gate import matrix_log


def start_all_protocols():
    """
    Initializes and starts all communication protocol managers.
    Partition-aware: Only CORE/STANDALONE partitions run physical hardware bridges.
    """
    partition_id = os.environ.get("OPEN_AIR_PARTITION_ID", "STANDALONE")
    matrix_log("manager", "entry", "start_all_protocols", f"🚀 [MANAGER] Initializing ComProtocolManager for partition: {partition_id}", "INFO")

    config = Config.get_instance()
    protocol_manager = ComProtocolManager.get_instance(config=config)
    protocol_manager.discover_and_register_protocols()

    if not protocol_manager.initialize_common_dependencies():
        matrix_log("manager", "entry", "start_all_protocols", "❌ Failed to initialize common dependencies. Aborting start.", "ERROR")
        sys.exit(1)

    # ⚡ PARTITION ENFORCEMENT:
    # We only want to run the heavy hardware bridges in the CORE partition.
    # The UI partition should just be an observer.
    run_bridge = (partition_id in ["CORE", "STANDALONE"])

    common_deps_to_pass = {
        "protocol_router": protocol_manager.protocol_router,
        "run_bridge": run_bridge
    }

    matrix_log("manager", "entry", "start_all_protocols", f"Starting registered protocols (Active Bridges: {run_bridge})...", "INFO")
    protocol_manager.start_all(**common_deps_to_pass)

    matrix_log("manager", "entry", "start_all_protocols", "✅ All registered protocols launched.", "SUCCESS")
    return protocol_manager

def stop_all_protocols(protocol_manager=None):
    """
    Shuts down all managed communication protocol modules.
    """
    if protocol_manager is None:
        protocol_manager = ComProtocolManager.get_instance()

    if protocol_manager:
        matrix_log("manager", "entry", "stop_all_protocols", "🛑 Shutting down all protocols...", "INFO")
        protocol_manager.stop_all()
        matrix_log("manager", "entry", "stop_all_protocols", "✅ All protocols stopped.", "INFO")
    else:
        matrix_log("manager", "entry", "stop_all_protocols", "⚠️ Protocol manager not initialized, cannot stop protocols.", "WARNING")

def status():
    """
    Retrieves the status of all managed communication protocol modules.
    """
    try:
        protocol_manager = ComProtocolManager.get_instance()
        if not protocol_manager:
            return {"error": "ComProtocolManager not initialized"}
        return protocol_manager.get_status_all()
    except Exception as e:
        matrix_log("manager", "entry", "status", f"❌ Error getting status: {e}", "ERROR")
        return {"error": str(e)}

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

def start():
    """Start all protocols and keep running."""
    print(f"🚀 [START] Starting {Path(__file__).parent.name} services...")
    mgr = start_all_protocols()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_all_protocols(mgr)

def stop():
    """Stop all protocols."""
    stop_all_protocols()

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
    "ComProtocolManager",
    "start_all_protocols",
    "stop_all_protocols",
    "start",
    "stop",
    "status",
    "run_tests"
]
