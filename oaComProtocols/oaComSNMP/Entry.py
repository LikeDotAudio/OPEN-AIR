# oaComProtocols.oaComSNMP/Entry.py
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
# Version 20260405.2300.1

import sys
import os
from pathlib import Path
import pathlib
import threading
import time
import inspect

# Ensure the root directory is in the search path
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from oaLogging.Methods.matrix_gate import matrix_log
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
            from oaConfigurationManager.Core.identity import IdentityManager
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
            from oaComProtocols.oaComMQTT.Managers.mqtt_connection import MqttConnectionManager
            mqtt_connection_manager = MqttConnectionManager()
            
        if subscriber_router is None:
            from oaComProtocols.oaComMQTT.Managers.mqtt_subscriber_router import MqttSubscriberRouter
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
    """
    from oaLogging.Core.logger import SNMP_LOGGER
    from oaOchestration.Core.path_initializer import initialize_paths
    from oaConfigurationManager.FileReaders.config_reader import Config
    
    initialize_paths()
    cfg = Config.get_instance()
    
    matrix_log("comms", "snmp", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🚀 [SNMP] Launching Standalone SNMP Module...", "INFO")
    
    from oaComProtocols.oaComMQTT.Managers.mqtt_connection import MqttConnectionManager
    from oaComProtocols.oaComMQTT.Managers.mqtt_subscriber_router import MqttSubscriberRouter
    from oaStateCache.Core.state_cache import StateRegistry
    
    mqtt_conn = MqttConnectionManager()
    sub_router = MqttSubscriberRouter()
    state_cache = StateRegistry(mqtt_conn)
    state_cache.subscriber_router = sub_router
    
    mqtt_conn.connect_to_broker(
        on_message_callback=state_cache.handle_incoming_mqtt,
        subscriber_router=sub_router
    )
    
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

def run_tests():
    """
    Discovers and runs all tests within the oaComProtocols.oaComSNMP/Tests/ directory.
    """
    print("🔍 Discovering and running tests for oaComProtocols.oaComSNMP...")
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
            relative_test_file_path = test_file.relative_to(project_root)
            module_path_for_runner = str(relative_test_file_path).replace(os.sep, '.')[:-3]

            original_cwd = os.getcwd()
            os.chdir(project_root) 

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
                print(f"❌ Test failed for {test_file.name}")
            else:
                print(f"✅ Tests passed for {test_file.name}")

        except Exception as e:
            print(f"❌ An error occurred: {e}")
            all_tests_passed = False
        finally:
            os.chdir(original_cwd)

    if all_tests_passed:
        print("\n🎉 All tests for oaComProtocols.oaComSNMP passed!")
    else:
        print("\n💔 Some tests for oaComProtocols.oaComSNMP failed.")

__all__ = [
    "SNMPManager",
    "SnmpTester",
    "MibGenerator",
    "InstallerGenerator",
    "get_manager",
    "start",
    "stop",
    "status",
    "main",
    "run_tests"
]

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main() 
    else:
        run_tests()
