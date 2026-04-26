# oaComREST/Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260415.2150.1
#
# Description: Gatekeeper for the oaComREST module.


import os
import pathlib
import subprocess
import sys
from pathlib import Path

# Ensure project root is in sys.path for direct execution
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from oaLogging.Methods.matrix_gate import matrix_log

# --- Core Components ---
# These managers will be instantiated and managed by the ComProtocolManager
# FastAPI app, Uvicorn worker, MQTT transport, etc.

_rest_manager = None # Placeholder for the REST manager instance

# Mock dependencies if not provided by the manager
class MockStateCache:
    def handle_external_update(self, *args, **kwargs): pass
    def shutdown(self): pass

class MockMqttConnectionManager:
    def connect_to_broker(self, *args, **kwargs): pass
    def disconnect(self): pass
    def subscribe(self, *args, **kwargs): pass
    def publish(self, *args, **kwargs): pass

class MockSubscriberRouter:
    def add_handler(self, *args, **kwargs): pass

def get_manager(state_cache_manager=None, mqtt_connection_manager=None, subscriber_router=None, protocol_router=None, run_bridge=True):
    """
    Returns the singleton REST Manager instance.
    Alias for get_rest_manager() to match system patterns.
    """
    return get_rest_manager(state_cache_manager, mqtt_connection_manager, subscriber_router, protocol_router, run_bridge)

def get_rest_manager(state_cache_manager=None, mqtt_connection_manager=None, subscriber_router=None, protocol_router=None, run_bridge=True):
    """
    Returns the singleton REST Manager instance.
    Dependencies should be passed externally.
    """
    global _rest_manager
    if _rest_manager is None:
        from oaComProtocols.oaComREST.Managers.rest_manager import RESTManager
        # Provide mocks if not supplied by the orchestrator
        state_cache = state_cache_manager if state_cache_manager else MockStateCache()

        _rest_manager = RESTManager(
            state_cache_manager=state_cache,
            protocol_router=protocol_router
        )
        matrix_log("comms", "rest", "get_rest_manager", "REST Manager initialized.", "DEBUG")
    return _rest_manager

def get_status():
    """Returns the current status of the REST API service. Alias for status()."""
    return status()

def add_monitor_callback(cb):
    """Registers a callback for REST activity monitoring."""
    manager = get_rest_manager()
    if manager:
        manager.add_monitor_callback(cb)

def start(state_cache_manager=None, mqtt_connection_manager=None, subscriber_router=None, protocol_router=None, run_bridge=True):
    """
    Initializes and starts the REST API service, accepting external dependencies.
    """
    matrix_log("comms", "rest", "start", "🚀 [REST] Starting REST API service...", "INFO")

    manager = get_rest_manager(
        state_cache_manager=state_cache_manager,
        mqtt_connection_manager=mqtt_connection_manager,
        subscriber_router=subscriber_router,
        protocol_router=protocol_router,
        run_bridge=run_bridge
    )

    # The start() method of RESTManager handles internal initialization (like FastAPI app)
    # and launching the Uvicorn worker.
    manager.start()
    matrix_log("comms", "rest", "start", "✅ REST API service started.", "SUCCESS")
    return manager # Return the manager for external control

def stop():
    """Stops the REST API service."""
    global _rest_manager
    if _rest_manager:
        matrix_log("comms", "rest", "stop", "🛑 [REST] Stopping REST API service...", "INFO")
        _rest_manager.stop()
        _rest_manager = None
        matrix_log("comms", "rest", "stop", "✅ REST API service stopped.", "INFO")

def status():
    """Returns the current status of the REST API service."""
    manager = get_rest_manager()
    if manager:
        return manager.get_status()
    return {"running": False, "error": "REST manager not initialized"}

# Standalone main() function is removed.
# def main(): ...

__all__ = [
    "RESTManager",
    "get_manager",
    "get_status",
    "add_monitor_callback",
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

