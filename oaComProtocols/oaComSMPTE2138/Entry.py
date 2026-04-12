# oaComProtocols.oaComSMPTE2138/Entry.py
#
# Gatekeeper for the SMPTE ST 2138 (SMPTE2138) Communication Module. 
# Orchestrates translation (Bridge) and observation (Monitor) services.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Version 20260330.1600.1

import sys
import os
import pathlib
import signal
import time
from pathlib import Path

# Ensure project root is in sys.path for direct execution
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent # OPEN-AIR is two levels up from Entry.py
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Absolute imports for robustness in standalone mode
from oaComProtocols.oaComSMPTE2138.Managers.smpte2138_bridge_manager import SMPTE2138BridgeManager
from oaComProtocols.oaComSMPTE2138.Managers.smpte2138_monitor_manager import SMPTE2138MonitorManager

__all__ = ["SMPTE2138BridgeManager", "SMPTE2138MonitorManager"]

def start_bridge(mqtt_connection, subscriber_router):
    """
    Initializes and starts the SMPTE2138 Bridge Manager (Internal -> External).
    Used in the Core Partition.
    """
    mgr = SMPTE2138BridgeManager(mqtt_connection, subscriber_router)
    mgr.start()
    return mgr

def start_monitor(mqtt_connection, subscriber_router):
    """
    Initializes and starts the SMPTE2138 Monitor Manager (External -> Human Readable).
    Used in the UI Partition.
    """
    mgr = SMPTE2138MonitorManager(mqtt_connection, subscriber_router)
    mgr.start()
    return mgr

def run_tests():
    """
    Discovers and runs all tests within the oaComProtocols.oaComSMPTE2138/Tests/ directory.
    """
    print("🔍 Discovering and running tests for oaComProtocols.oaComSMPTE2138...")
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
            # Adjust to project root (OPEN-AIR)
            relative_test_file_path = test_file.relative_to(project_root)
            module_path_for_runner = str(relative_test_file_path).replace(os.sep, '.')[:-3] # Remove .py extension

            # Ensure the current directory is the project root so Python can find modules
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
                print(f"❌ Test failed for {test_file.name} with exit code {result.returncode}")
            else:
                print(f"✅ Tests passed for {test_file.name}")

        except Exception as e:
            print(f"❌ An error occurred while running tests for {test_file.name}: {e}")
            all_tests_passed = False
        finally:
            os.chdir(original_cwd)

    if all_tests_passed:
        print("\n🎉 All tests for oaComProtocols.oaComSMPTE2138 passed!")
    else:
        print("\n💔 Some tests for oaComProtocols.oaComSMPTE2138 failed.")
    return all_tests_passed

if __name__ == "__main__":
    # If run directly and no specific arguments are provided, run tests then launch standalone.
    if len(sys.argv) > 1 and sys.argv[1] == "--test-only":
        run_tests()
        sys.exit(0)
    
    # 1. Run Tests first
    if not run_tests():
        print("🛑 Tests failed. Aborting standalone startup.")
        sys.exit(1)

    print("\n🚀 [ST2138] Starting Standalone SMPTE 2138 Service...")
    
    # Imports needed for standalone execution
    import tkinter as tk
    from oaComProtocols.oaComMQTT.Managers.mqtt_connection import MqttConnectionManager
    from oaComProtocols.oaComMQTT.Managers.mqtt_subscriber_router import MqttSubscriberRouter
    from oaComProtocols.oaComSMPTE2138.Interface.smpte2138_monitor import SMPTE2138MonitorImplementation
    from oaLogging.Core.logger import initialize_logging, set_log_directory
    from oaOchestration.Core.path_initializer import initialize_paths, DATA_LOGS_DIR

    # Environment Setup
    initialize_paths()
    set_log_directory(DATA_LOGS_DIR, partition="ST2138")
    
    # Infrastructure
    mqtt_conn = MqttConnectionManager()
    sub_router = MqttSubscriberRouter()
    
    # Managers
    bridge = SMPTE2138BridgeManager(mqtt_conn, sub_router)
    monitor_manager = SMPTE2138MonitorManager(mqtt_conn, sub_router)
    
    # Connect to MQTT
    print("📡 [ST2138] Connecting to MQTT Broker...")
    mqtt_conn.connect_to_broker(subscriber_router=sub_router)

    # Launch GUI
    print("🖥️ [ST2138] Launching Monitor GUI...")
    root = tk.Tk()
    root.title("OPEN-AIR: SMPTE ST 2138 Monitor")
    root.geometry("1000x700")
    
    app = SMPTE2138MonitorImplementation(root)
    app.pack(fill=tk.BOTH, expand=True)
    
    def on_closing():
        print("\n🛑 [ST2138] Stopping service...")
        bridge.stop()
        monitor_manager.stop()
        root.destroy()
        sys.exit(0)

    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Handle signals
    def signal_handler(sig, frame):
        root.after(0, on_closing)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("✅ [ST2138] Service is active and online.")
    root.mainloop()

