# oaComNmos/Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260415.2150.1
#
# Description: Gatekeeper for the oaComNmos module.


import sys
import os
import pathlib
import signal
import threading
import socket
import time
import subprocess
from pathlib import Path

# Ensure project root is in sys.path for direct execution
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Standard OPEN-AIR Imports
from oaLogging.Methods.matrix_gate import matrix_log
from oaConfigurationManager.FileReaders.config_reader import Config

# Local module imports
from oaComProtocols.oaComNmos.Core.utils import gen_id, get_ip
from oaComProtocols.oaComNmos.Core.event_bus import nmos_event_bus
from oaComProtocols.oaComNmos.Core.nmos_builder import build_node, build_device
from oaComProtocols.oaComNmos.Constants import settings
from oaComProtocols.oaComNmos.Managers import registration_manager
from oaComProtocols.oaComNmos.Workers.sap_listener_worker import sap_listener_worker, heartbeat_worker
from oaComProtocols.oaComNmos.Interface import connection_api
from oaComProtocols.oaComNmos.IS07.transports import Is07Bridge # This uses internal MQTT client

# --- Global State Management ---
# This state will be managed externally by ComProtocolManager or initialized internally if standalone.
global_state = {
    "NODE_ID": None,
    "DEVICE_ID": None,
    "NODE": {},
    "DEVICE": {},
    "SOURCES": {},
    "FLOWS": {},
    "SENDERS": {},
    "STREAMS": {},
    "REGISTRAR_URL": "http://localhost:4000",
    "RUNNING": False,
    "BRIDGE": None # Will be set by start function
}

# --- Internal Managers/Components ---
# These will be managed by the ComProtocolManager, but initialized internally here if not provided.
_bridge_manager = None 

def initialize_global_state(registrar_url=None):
    """Initializes global state for NMOS module. Called by start()."""
    if not global_state.get("RUNNING", False):
        matrix_log("comms", "nmos", "initialize_global_state", "Initializing NMOS global state...", "INFO")
        
        state = {
            "NODE_ID": gen_id(),
            "DEVICE_ID": gen_id(),
            "NODE": {}, "DEVICE": {}, "SOURCES": {}, "FLOWS": {}, "SENDERS": {}, "STREAMS": {},
            "REGISTRAR_URL": registrar_url if registrar_url else "http://localhost:4000",
            "RUNNING": True,
            "BRIDGE": None # Will be set by start function
        }
        
        host_ip = get_ip()
        state["NODE"] = build_node(state["NODE_ID"], host_ip, settings.PORT)
        state["DEVICE"] = build_device(state["DEVICE_ID"], state["NODE_ID"], host_ip, settings.PORT)
        
        global_state.update(state) # Update the global_state dictionary
        
        registration_manager.register_all_resources(
            global_state["REGISTRAR_URL"],
            global_state["NODE"],
            global_state["DEVICE"],
            global_state["SOURCES"],
            global_state["FLOWS"],
            global_state["SENDERS"]
        )
        matrix_log("comms", "nmos", "initialize_global_state", f"NMOS State initialized with NodeID: {global_state['NODE_ID']}", "SUCCESS")
    else:
        matrix_log("comms", "nmos", "initialize_global_state", "NMOS global state already initialized.", "DEBUG")

def start(registrar_url=None, state_cache_manager=None, mqtt_connection_manager=None, subscriber_router=None):
    """
    Starts the NMOS bridge and API server.
    Accepts external dependencies but initializes internal MQTT if none provided.
    """
    global _bridge_manager
    if global_state.get("RUNNING", False):
        matrix_log("comms", "nmos", "start", "NMOS bridge is already running.", "WARNING")
        return

    matrix_log("comms", "nmos", "start", "🚀 [NMOS] Starting NMOS bridge and API server...", "INFO")
    
    # Initialize global state if not already done
    if not global_state.get("RUNNING", False):
        initialize_global_state(registrar_url)
    
    # Initialize the bridge manager. It uses internal MQTT clients by default if none provided.
    # The `Is07Bridge` constructor handles internal MQTT connection if mqtt_connection_manager is None.
    _bridge_manager = Is07Bridge(global_state["REGISTRAR_URL"])
    
    # Start Workers (SAP and Heartbeat)
    # These threads should ideally be managed by the ComProtocolManager or started here if self-contained.
    # For now, assume they are started here if needed for standalone operation.
    # If managed externally, these threads might be started by the manager.
    threading.Thread(target=sap_listener_worker, args=(global_state["REGISTRAR_URL"], global_state["NODE_ID"], global_state["DEVICE_ID"], get_ip(), global_state, registration_manager), daemon=True).start()
    threading.Thread(target=heartbeat_worker, args=(global_state["REGISTRAR_URL"], global_state["NODE_ID"], global_state, registration_manager), daemon=True).start()
    
    # Start API Server (connection_api)
    connection_api.STATE["NODE"] = global_state["NODE"]
    connection_api.STATE["DEVICE"] = global_state["DEVICE"]
    connection_api.STATE["SOURCES"] = global_state["SOURCES"]
    connection_api.STATE["FLOWS"] = global_state["FLOWS"]
    connection_api.STATE["SENDERS"] = global_state["SENDERS"]
    connection_api.STATE["STREAMS"] = global_state["STREAMS"]
    
    api_thread = threading.Thread(target=connection_api.run_server, kwargs={"host": "0.0.0.0", "port": settings.PORT}, daemon=True)
    api_thread.start()

    # Start internal bridge transports AFTER core components are set up
    _bridge_manager.start()

    matrix_log("comms", "nmos", "start", f"✅ [NMOS] Bridge and API Server active on {get_ip()}:{settings.PORT}", "SUCCESS")
    matrix_log("comms", "nmos", "start", f"🔌 [NMOS] IS-07 WebSocket available at ws://{get_ip()}:{settings.PORT}/is07", "INFO")

def stop():
    """Stops the NMOS bridge and API server."""
    global _bridge_manager
    if _bridge_manager and _bridge_manager.is_running:
        _bridge_manager.stop()
        matrix_log("comms", "nmos", "stop", "NMOS Bridge stopped.", "INFO")
    
    global_state["RUNNING"] = False
    
    # Workers and API server are daemon threads and will exit with the main process.
    # If they were non-daemon, explicit stop logic would be needed here.

def status():
    """Returns the current status of the NMOS bridge."""
    return {
        "running": global_state.get("RUNNING", False),
        "node_id": global_state.get("NODE_ID", "N/A"),
        "registrar": global_state.get("REGISTRAR_URL", "N/A"),
        "bridge_running": _bridge_manager.is_running if _bridge_manager else False
    }

# Standalone main() function is removed.
# def run_tests(): ...
# if __name__ == "__main__": ...

    "start", "stop", "status", "global_state", "NmosBridgeManager",
    "Is07MqttTransport", "Is07WebSocketTransport", "initialize_global_state"
]

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
