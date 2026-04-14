# oaComProtocols.oaComOSC/Entry.py
#
# The sole orchestrator and public gatekeeper for the OSC Communication Module.
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
# Version 20260329.1105.1
#
# Description:
# This file serves as the gatekeeper and primary interface for all OSC-related
# operations. It manages the singleton OSCManager and exposes high-level 
# methods for control and interaction.

import sys
import os
import pathlib
import argparse
from pathlib import Path

# Ensure root directory is in the search path
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from oaComProtocols.oaComOSC.Managers.osc_manager import OSCManager
from oaComProtocols.oaComOSC.Workers.osc_rx_server import OscRxServer
from oaComProtocols.oaComOSC.Workers.osc_tx_client import OscTxClient

_instance = None

def get_manager(context=None, state_cache_manager=None, mqtt_connection_manager=None, run_bridge=True):
    """
    Returns the singleton OSCManager instance.
    If not already initialized, it creates it with the provided managers.
    """
    global _instance
    
    # ⚡ ROBUST SINGLETON: Check if the manager is already initialized in another 
    # copy of this module (happens when run as __main__ and imported as a package)
    if _instance is None:
        try:
            import oaComProtocols.oaComOSC.Entry as osc_entry
            if osc_entry is not sys.modules[__name__] and osc_entry._instance:
                _instance = osc_entry._instance
        except (ImportError, AttributeError):
            pass

    if _instance is None:
        _instance = OSCManager(
            context=context,
            state_cache_manager=state_cache_manager, 
            mqtt_connection_manager=mqtt_connection_manager, 
            run_bridge=run_bridge
        )
    else:
        # Update existing instance if new dependencies are provided
        if context:
            _instance.context = context
        if state_cache_manager:
            _instance.state_cache_manager = state_cache_manager
        if mqtt_connection_manager:
            _instance.mqtt_connection_manager = mqtt_connection_manager
            
    return _instance

def start():
    """Starts the OSC bridge services."""
    manager = get_manager()
    manager.start()

def stop():
    """Stops the OSC bridge services."""
    manager = get_manager()
    manager.stop()

def status():
    """Returns the current status of the OSC bridge."""
    manager = get_manager()
    return manager.get_status()

def send(address, value, meta=None):
    """
    High-level method to send an OSC message.
    Can be called directly from the UI or other modules.
    """
    manager = get_manager()
    manager.send(address, value, meta)

def add_monitor_callback(callback):
    """Registers a callback for OSC activity monitoring."""
    manager = get_manager()
    manager.add_monitor_callback(callback)

def remove_monitor_callback(callback):
    """Unregisters a monitoring callback."""
    manager = get_manager()
    manager.remove_monitor_callback(callback)

def set_bridge_mode(enabled):
    """Toggles bridge mode on the singleton instance."""
    manager = get_manager()
    manager.set_bridge_mode(enabled)

def run_tests():
    """
    Discovers and runs all tests within the oaComProtocols.oaComOSC/Tests/ directory.
    """
    print("🔍 Discovering and running tests for oaComProtocols.oaComOSC...")
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
        print(f"--- Running: {test_file.name} ---")
        try:
            # Get the module path relative to the project root for the test runner
            relative_test_file_path = test_file.relative_to(project_root)
            module_path_for_runner = str(relative_test_file_path).replace(os.sep, '.')[:-3]

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
        print("🎉 All tests for oaComProtocols.oaComOSC passed!")
    else:
        print("💔 Some tests for oaComProtocols.oaComOSC failed.")
    return all_tests_passed

def main():
    """
    Main entry point for running the OSC module as a standalone application.
    Runs tests first, then launches the GUI.
    """
    # 1. Parse Arguments
    parser = argparse.ArgumentParser(description="OPEN-AIR OSC Module Standalone")
    parser.add_argument("--skip-tests", action="store_true", help="Skip pre-flight unit tests")
    args, unknown = parser.parse_known_args()

    # 2. Run Tests First
    if not args.skip_tests and not run_tests():
        print("🛑 Tests failed. Aborting GUI launch.")
        return

    # 3. Initialize Paths and Logging
    from oaLogging.Core.logger import initialize_logging, set_log_directory
    from oaOchestration.Core.path_initializer import initialize_paths, DATA_LOGS_DIR

    initialize_paths()
    set_log_directory(DATA_LOGS_DIR, partition="OSC-STANDALONE")

    # 4. Start OSC Manager (Standalone mode will auto-activate internal MQTT relay)
    manager = get_manager()
    
    # 5. Launch GUI
    try:
        import tkinter as tk
        from tkinter import ttk
        from oaComProtocols.oaComOSC.Interface.gui_OSC import OscDashboardImplementation

        root = tk.Tk()
        root.title("OPEN-AIR | OSC Control Hub (STANDALONE)")
        root.geometry("1100x850")
        root.configure(bg="#2b2b2b")

        def on_closing():
            stop()
            root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_closing)

        # ⚡ DASHBOARD: Host directly in the root for a unified view
        gui = OscDashboardImplementation(root, config={})
        gui.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        print("✅ [OSC] Standalone Control Hub deployed (Integrated MQTT Relay).")
        root.mainloop()

    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"❌ [OSC] Critical error in GUI main loop: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            stop()
        except Exception as e:
            print(f"❌ [OSC] Error during cleanup: {e}")
        print("🏁 [OSC] Standalone shutdown complete.")

if __name__ == "__main__":
    main()


# Standardized exports
__all__ = [
    "OSCManager",
    "OscRxServer",
    "OscTxClient",
    "get_manager",
    "start",
    "stop",
    "status",
    "send",
    "add_monitor_callback",
    "remove_monitor_callback",
    "set_bridge_mode",
    "main"
]
