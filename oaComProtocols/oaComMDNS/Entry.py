# oaComMDNS/Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260415.2150.1
#
# Description: Gatekeeper for the oaComMDNS module.

import subprocess
from pathlib import Path

import sys
import time
import signal
import os
import pathlib

current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from oaLogging.Methods.matrix_gate import matrix_log
# Core components are now managed externally, except for their own internal MQTT publisher
from oaComProtocols.oaComMDNS.Core.mdns_listener import MDNSListener

_listener = None
_publisher_instance = None

def start(rx_callback=None, tx_callback=None):
    """Initializes and starts the MDNS listener, using its own MQTT publisher."""
    global _listener, _publisher_instance
    if _listener is not None:
        return
    
    # Module manages its own MQTT publisher and connection
    from oaComProtocols.oaComMDNS.Core.mqtt_publisher import StandaloneMqttPublisher
    _publisher_instance = StandaloneMqttPublisher(client_id="MDNS_Standalone", tx_callback=tx_callback)
    _publisher_instance.connect()
    
    _listener = MDNSListener(_publisher_instance, rx_callback=rx_callback)
    _listener.start()
    matrix_log("comms", "mdns", "start", "🚀 [MDNS] Listener and self-contained MQTT publisher started.", "INFO")

def stop():
    """Stops the MDNS listener and disconnects its own MQTT publisher."""
    global _listener, _publisher_instance
    if _listener:
        _listener.stop()
        _listener = None
        matrix_log("comms", "mdns", "stop", "🛑 [MDNS] Listener stopped.", "INFO")
    if _publisher_instance:
        _publisher_instance.disconnect()
        _publisher_instance = None
        matrix_log("comms", "mdns", "stop", "🛑 [MDNS] MQTT publisher disconnected.", "INFO")

def status():
    """Returns the current operational status of the MDNS receiver."""
    return {"running": _listener is not None, "publisher_connected": _publisher_instance is not None and _publisher_instance.is_connected()}

# Standalone main() function is removed.
# def main(): ...


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
