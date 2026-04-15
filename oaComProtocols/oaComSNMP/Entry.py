# oaComProtocols.oaComSNMP/Entry.py
# ⚡ STANDALONE: 100% independent SNMP Orchestrator.
# No dependencies on ProtocolRouter, StateCache, or shared MQTT Managers.
# Refactored for centralized management by ComProtocolManager.

import sys
import os
import pathlib
import threading
import time
import subprocess
import unittest
from pathlib import Path

# Ensure the root directory is in the search path
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from oaLogging.Methods.matrix_gate import matrix_log
from oaConfigurationManager.FileReaders.config_reader import Config # Config might be needed externally

# Mock dependencies if not provided by the manager
class MockMqttConnectionManager:
    def connect(self, *args, **kwargs): pass
    def disconnect(self, *args, **kwargs): pass
    def subscribe(self, *args, **kwargs): pass
    def publish(self, *args, **kwargs): pass
    def set_on_message_callback(self, *args, **kwargs): pass

# --- Core Components ---
from oaComProtocols.oaComSNMP.Managers.snmp_manager import SNMPManager, BridgeContext
from oaComProtocols.oaComSNMP.Core.snmp_mqtt_client import SnmpMqttClient

_instance = None

def get_manager(mqtt_connection_manager=None, subscriber_router=None, run_bridge=None, **kwargs):
    """
    Singleton getter for the SNMP Manager.
    Dependencies should be passed externally.
    """
    global _instance
    
    if _instance is None:
        from oaComProtocols.oaComSNMP.Managers.snmp_manager import SNMPManager, BridgeContext
        from oaComProtocols.oaComSNMP.Core.snmp_mqtt_client import SnmpMqttClient

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

def run_tests():
    """
    Discovers and runs all tests within the oaComProtocols.oaComSNMP/Tests/ directory.
    """
    print("🔍 Discovering and running tests for oaComProtocols.oaComSNMP...")
    test_dir = pathlib.Path(__file__).parent / "Tests"
    if not test_dir.is_dir():
        print("❌ No 'Tests/' directory found.")
        return True

    test_files = sorted([f for f in test_dir.glob("test_*.py")])
    if not test_files:
        print("❌ No test files found (expected pattern: test_*.py).")
        return True

    print(f"Found {len(test_files)} test files. Executing...")
    
    import subprocess
    
    all_tests_passed = True
    for test_file in test_files:
        print(f"\n--- Running: {test_file.name} ---")
        try:
            relative_path = test_file.relative_to(project_root)
            module_path = str(relative_path).replace(os.sep, '.')[:-3]

            original_cwd = os.getcwd()
            os.chdir(project_root) 

            result = subprocess.run(
                [sys.executable, "-m", "unittest", module_path],
                capture_output=True,
                text=True,
                check=False
            )
            
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
            
            if result.returncode != 0:
                all_tests_passed = False
                print(f"❌ Test failed for {test_file.name} with exit code {result.returncode}")
            else:
                print(f"✅ Tests passed for {test_file.name}")

        except Exception as e:
            print(f"❌ An error occurred while running tests for {test_file.name}: {e}")
            all_tests_passed = False
        finally:
            os.chdir(original_cwd)

    if all_tests_passed:
        print("\n🎉 All tests for oaComProtocols.oaComSNMP passed!")
    else:
        print("\n💔 Some tests for oaComProtocols.oaComSNMP failed.")
    return all_tests_passed

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

if __name__ == "__main__":
    main()

__all__ = ["start", "stop", "status", "run_tests", "main"]
