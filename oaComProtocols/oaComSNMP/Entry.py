# oaComSNMP/Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260415.2150.1
#
# Description: Gatekeeper for the oaComSNMP module.


import os
import pathlib
import subprocess
import sys
import time
from pathlib import Path

# Ensure the root directory is in the search path
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from oaConfigurationManager.FileReaders.config_reader import Config  # Config might be needed externally
from oaLogging.Methods.matrix_gate import matrix_log


# Mock dependencies if not provided by the manager
class MockMqttConnectionManager:
    def connect(self, *args, **kwargs): pass
    def disconnect(self, *args, **kwargs): pass
    def subscribe(self, *args, **kwargs): pass
    def publish(self, *args, **kwargs): pass
    def set_on_message_callback(self, *args, **kwargs): pass

# --- Core Components ---

_instance = None

def get_manager(mqtt_connection_manager=None, subscriber_router=None, run_bridge=None, **kwargs):
    """
    Singleton getter for the SNMP Manager.
    Dependencies should be passed externally.
    """
    global _instance

    if _instance is None:
        from oaComProtocols.oaComSNMP.Managers.snmp_manager import BridgeContext, SNMPManager

        matrix_log("comms", "snmp", "get_manager", "Initializing SNMP Manager...", "INFO")

        # Determine if bridge mode should run based on config or external flags
        if run_bridge is None:
            try:
                config = Config.get_instance() # Get config if available
                partition = config.get("PARTITION_ID", "STANDALONE")
                run_bridge = (partition in ["CORE", "STANDALONE"])
            except Exception:
                run_bridge = True # Default to running bridge if config is unavailable

        # Instantiate MQTT client and context using provided or default connection managers
        mqtt_client = mqtt_connection_manager if mqtt_connection_manager else MockMqttConnectionManager()
        # subscriber_router is not directly used by SNMPManager's init in this snippet

        context = BridgeContext(mqtt_client=mqtt_client)
        _instance = SNMPManager.create(context, run_bridge)
        matrix_log("comms", "snmp", "get_manager", f"SNMP Manager created. Bridge mode: {run_bridge}", "INFO")

    return _instance

def start(mqtt_connection_manager=None, subscriber_router=None, run_bridge=None):
    """
    Starts the SNMP bridge service, accepting external dependencies.
    """
    matrix_log("comms", "snmp", "start", "🚀 [SNMP] Starting SNMP bridge service...", "INFO")
    manager = get_manager(
        mqtt_connection_manager=mqtt_connection_manager,
        subscriber_router=subscriber_router,
        run_bridge=run_bridge
    )

    # Connect MQTT client if it's part of the manager's context
    if manager.context.mqtt_client and hasattr(manager.context.mqtt_client, 'connect'):
        matrix_log("comms", "snmp", "start", "Connecting to MQTT...", "INFO")
        manager.context.mqtt_client.connect()

    manager.start() # Start the SNMP manager's background services
    matrix_log("comms", "snmp", "start", "✅ SNMP bridge service started.", "SUCCESS")
    return manager # Return manager for external control

def stop():
    """Stops the SNMP bridge service."""
    global _instance
    if _instance:
        matrix_log("comms", "snmp", "stop", "🛑 [SNMP] Stopping SNMP bridge service...", "INFO")
        _instance.stop()
        if _instance.context.mqtt_client:
            _instance.context.mqtt_client.disconnect()
        _instance = None
        matrix_log("comms", "snmp", "stop", "✅ SNMP bridge service stopped.", "INFO")

def status():
    """Returns the current status of the SNMP bridge."""
    manager = get_manager() # Get instance, assume it exists if manager was ever used
    if manager:
        return manager.get_status()
    return {"running": False, "error": "SNMP manager not initialized"}

# Standalone main() function is removed.
# def main(): ...


def main():
    """
    Main function to run the SNMP bridge service in standalone mode.
    """
    matrix_log("comms", "snmp", "main", "⚡ [SNMP] Starting SNMP in standalone mode...", "INFO")

    # Run tests first
    matrix_log("comms", "snmp", "main", "Running self-tests...", "INFO")
    if not run_tests():
        matrix_log("comms", "snmp", "main", "Self-tests failed. Aborting startup.", "ERROR")
        return
    matrix_log("comms", "snmp", "main", "Self-tests passed.", "INFO")
    manager = None
    try:
        manager = start(run_bridge=True)
        matrix_log("comms", "snmp", "main", "SNMP Manager is running. Press Ctrl+C to stop.", "INFO")
        while True:
            time.sleep(1) # Keep main thread alive
    except KeyboardInterrupt:
        matrix_log("comms", "snmp", "main", "Ctrl+C detected. Stopping SNMP manager...", "INFO")
    except Exception as e:
        matrix_log("comms", "snmp", "main", f"An error occurred: {e}", "ERROR")
    finally:
        if manager:
            stop()
            matrix_log("comms", "snmp", "main", "SNMP manager stopped.", "INFO")


def run_tests():
    """
    Discover and run tests in the local Tests/ directory using unittest via subprocess.
    Ensures isolation and proper sys.path handling.
    """
    import sys

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

