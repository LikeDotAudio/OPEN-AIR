# oaComSMPTE2138/Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260505.Modular.1
#
# Description: Gatekeeper for the oaComSMPTE2138 module.


import os
import pathlib
import sys
from pathlib import Path

# Ensure project root is in sys.path for direct execution
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent # OPEN-AIR is two levels up from Entry.py
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Absolute imports for robustness in standalone mode
from oaLogging.Methods.matrix_gate import matrix_log

# Mock dependencies if not provided by the manager
class MockMqttConnectionManager:
    def connect_to_broker(self, *args, **kwargs): pass
    def disconnect(self): pass
    def subscribe(self, *args, **kwargs): pass
    def publish(self, *args, **kwargs): pass

class MockSubscriberRouter:
    def add_handler(self, *args, **kwargs): pass

_bridge_manager = None
_monitor_manager = None

def _is_debug():
    try:
        from oaComProtocols.oaComSMPTE2138.Managers.smpte2138_bridge_manager import _is_debug as bridge_debug
        return bridge_debug()
    except Exception:
        from oaLogging.Methods.matrix_gate import is_debug_allowed
        return is_debug_allowed(system="comms", element="smpte2138")

def start_bridge(mqtt_connection_manager=None, subscriber_router=None):
    """Initializes and starts the SMPTE2138 Bridge manager."""
    global _bridge_manager
    if _bridge_manager is None:
        from oaComProtocols.oaComSMPTE2138.Managers.smpte2138_bridge_manager import SMPTE2138BridgeManager
        # Handle missing dependencies if not provided by the manager
        mqtt_conn = mqtt_connection_manager if mqtt_connection_manager else MockMqttConnectionManager()
        sub_router = subscriber_router if subscriber_router else MockSubscriberRouter()

        _bridge_manager = SMPTE2138BridgeManager(mqtt_conn, sub_router)
        _bridge_manager.start()
        if _is_debug():
            matrix_log("comms", "smpte2138", "start_bridge", "✅ SMPTE2138 Bridge started.", "SUCCESS")
    return _bridge_manager

def start_monitor(mqtt_connection_manager=None, subscriber_router=None):
    """Initializes and starts the SMPTE2138 Monitor manager."""
    global _monitor_manager
    if _monitor_manager is None:
        from oaComProtocols.oaComSMPTE2138.Managers.smpte2138_monitor_manager import SMPTE2138MonitorManager
        # Handle missing dependencies if not provided by the manager
        mqtt_conn = mqtt_connection_manager if mqtt_connection_manager else MockMqttConnectionManager()
        sub_router = subscriber_router if subscriber_router else MockSubscriberRouter()

        _monitor_manager = SMPTE2138MonitorManager(mqtt_conn, sub_router)
        _monitor_manager.start()
        if _is_debug():
            matrix_log("comms", "smpte2138", "start_monitor", "✅ SMPTE2138 Monitor started.", "SUCCESS")
    return _monitor_manager

def start(mqtt_connection_manager=None, subscriber_router=None, **kwargs):
    """
    Initializes and starts the SMPTE2138 Bridge and Monitor managers.
    Accepts external MQTT connection and subscriber router.
    """
    if _is_debug():
        matrix_log("comms", "smpte2138", "start", "🚀 [ST2138] Starting SMPTE2138 services...", "INFO")
    
    start_bridge(mqtt_connection_manager, subscriber_router)
    start_monitor(mqtt_connection_manager, subscriber_router)
    
    if _is_debug():
        matrix_log("comms", "smpte2138", "start", "✅ SMPTE2138 services started.", "SUCCESS")

def stop():
    """
    Stops the SMPTE2138 Bridge and Monitor managers.
    """
    global _bridge_manager, _monitor_manager

    if _is_debug():
        matrix_log("comms", "smpte2138", "stop", "🛑 [ST2138] Stopping Bridge and Monitor managers...", "INFO")

    if _bridge_manager:
        _bridge_manager.stop()
        _bridge_manager = None
    if _monitor_manager:
        _monitor_manager.stop()
        _monitor_manager = None

    if _is_debug():
        matrix_log("comms", "smpte2138", "stop", "✅ SMPTE2138 managers stopped.", "INFO")

def status():
    """
    Returns the current status of the SMPTE 2138 managers.
    """
    status_report = {}
    if _bridge_manager:
        status_report["bridge"] = _bridge_manager.get_status()
    else:
        status_report["bridge"] = {"running": False, "message": "Not initialized"}

    if _monitor_manager:
        status_report["monitor"] = _monitor_manager.get_status()
    else:
        status_report["monitor"] = {"running": False, "message": "Not initialized"}

    return status_report

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

__all__ = ["start", "stop", "status", "run_tests"]
