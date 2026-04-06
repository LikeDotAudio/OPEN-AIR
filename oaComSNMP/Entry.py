import pathlib
import os
import sys
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# oaComSNMP/Entry.py
#
# The sole orchestrator and public gatekeeper for the SNMP Communication Module.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260329.1045.1

"""
oaComSNMP/Entry.py - The sole orchestrator for the SNMP Communication Module.
"""

import threading
import time

# Ensure the root directory is in the search path for local module imports.
from .Managers.snmp_manager import SNMPManager, BridgeContext
from .Workers.snmp_tester import SnmpTester
from .Methods.snmp_mib_generator import MibGenerator
from .Methods.snmp_installer_generator import InstallerGenerator

_instance = None

def get_manager(state_cache_manager=None, mqtt_connection_manager=None, subscriber_router=None, run_bridge=None):
    """
    Singleton getter for the SNMP Manager.
    """
    global _instance
    
    if run_bridge is None:
        try:
            from oaConfiguration.Core.identity import IdentityManager
            ident = IdentityManager.initialize()
            partition = ident.get("PARTITION_ID", "STANDALONE")
            run_bridge = (partition in ["CORE", "STANDALONE"])
        except Exception:
            run_bridge = True

    if _instance is None:
        if state_cache_manager is None:
            from oaSplinker.Core.splinker import ControlBroker
            broker = ControlBroker.get_instance()
            state_cache_manager = getattr(broker, 'state_cache_manager', None)
        
        if mqtt_connection_manager is None:
            from oaComMQTT.Managers.mqtt_connection import MqttConnectionManager
            mqtt_connection_manager = MqttConnectionManager()
            
        if subscriber_router is None:
            from oaComMQTT.Managers.mqtt_subscriber_router import MqttSubscriberRouter
            subscriber_router = getattr(mqtt_connection_manager, 'subscriber_router', None)

        context = BridgeContext(
            state_cache_manager=state_cache_manager,
            mqtt_connection_manager=mqtt_connection_manager,
            subscriber_router=subscriber_router
        )
        _instance = SNMPManager.create(context, run_bridge)
        
    return _instance

def start():
    """Starts the SNMP bridge service."""
    manager = get_manager()
    manager.start()

def stop():
    """Stops the SNMP bridge service."""
    manager = get_manager()
    manager.stop()

def status():
    """Returns the current status of the SNMP bridge."""
    manager = get_manager()
    return manager.get_status()

def main():
    """
    Main entry point for running the SNMP Bridge as a standalone module.
    Useful for debugging or isolated service deployment.
    """
    from oaLogging.Core.logger import SNMP_LOGGER
    from oaOchestration.Core.path_initializer import initialize_paths
    from oaConfiguration.FileReaders.config_reader import Config
    
    initialize_paths()
    cfg = Config.get_instance()
    
    matrix_log("comms", "snmp", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🚀 [SNMP] Launching Standalone SNMP Module...", "INFO")
    
    # In standalone mode, we might need to initialize the MQTT connection manually
    from oaComMQTT.Managers.mqtt_connection import MqttConnectionManager
    from oaComMQTT.Managers.mqtt_subscriber_router import MqttSubscriberRouter
    from oaStateCache.Core.state_cache import StateRegistry
    
    mqtt_conn = MqttConnectionManager()
    sub_router = MqttSubscriberRouter()
    state_cache = StateRegistry(mqtt_conn)
    state_cache.subscriber_router = sub_router
    
    # Start MQTT first so SNMP can use it
    mqtt_conn.connect_to_broker(
        on_message_callback=state_cache.handle_incoming_mqtt,
        subscriber_router=sub_router
    )
    
    # Initialize the manager with our fresh services
    context = BridgeContext(
        state_cache_manager=state_cache,
        mqtt_connection_manager=mqtt_conn,
        subscriber_router=sub_router
    )
    manager = get_manager(
        state_cache_manager=state_cache,
        mqtt_connection_manager=mqtt_conn,
        subscriber_router=sub_router,
        run_bridge=True
    )
    
    manager.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        SNMP_LOGGER.warning("👋 [SNMP] Standalone shutdown requested.")
        manager.stop()
        mqtt_conn.disconnect()

if __name__ == "__main__":
    main()

__all__ = [
    "SNMPManager",
    "SnmpTester",
    "MibGenerator",
    "InstallerGenerator",
    "get_manager",
    "start",
    "stop",
    "status",
    "main"
]

def run_tests():
    """
    Discovers and runs all tests within the oaComSNMP/Tests/ directory.
    """
    print("🔍 Discovering and running tests for oaComSNMP...")
    test_dir = Path(__file__).parent / "Tests"
    if not test_dir.is_dir():
        print("❌ No 'Tests/' directory found.")
        return

    test_files = sorted([f for f in test_dir.glob("test_*.py")])
    if not test_files:
        print("❌ No test files found (expected pattern: test_*.py).")
        return

    print(f"Found {len(test_files)} test files. Executing...")
    
    import subprocess
    
    all_tests_passed = True
    for test_file in test_files:
        print(f"\n--- Running: {test_file.name} ---")
        try:
            # Get the module path relative to the project root for the test runner
            relative_test_file_path = test_file.relative_to(Path(__file__).parent.parent.parent) # Path from OPEN-AIR root
            module_path_for_runner = str(relative_test_file_path).replace(os.sep, '.')[:-3] # Remove .py extension

            # Ensure the current directory is the project root so Python can find modules
            original_cwd = os.getcwd()
            os.chdir(Path(__file__).parent.parent.parent) 

            result = subprocess.run(
                [sys.executable, "-m", "unittest", module_path_for_runner],
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
        print("\n🎉 All tests for oaComSNMP passed!")
    else:
        print("\n💔 Some tests for oaComSNMP failed.")

if __name__ == "__main__":
    # If no command-line arguments are provided, default to running tests.
    # Otherwise, assume specific commands are intended (e.g., start, stop, main).
    if len(sys.argv) > 1:
        # If arguments are present, execute the original main logic or other commands.
        # A more robust implementation would parse sys.argv and call specific functions.
        # For this task, we assume any arguments mean "don't run tests".
        print("Executing command...")
        main() 
    else:
        # If no arguments, run the tests first.
        run_tests()
        # After tests pass, you might want to explicitly start the service if needed,
        # or just let the script exit. For now, we'll let it exit.
        # If you want to start the service after tests, uncomment the following lines:
        # print("\nTests passed. Starting SNMP service...")
        # main()

__all__ = [
    "SNMPManager",
    "SnmpTester",
    "MibGenerator",
    "InstallerGenerator",
    "get_manager",
    "start",
    "stop",
    "status",
    "main"
]