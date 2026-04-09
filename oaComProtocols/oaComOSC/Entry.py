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
from pathlib import Path
from .Managers.osc_manager import OSCManager
from .Workers.osc_rx_server import OscRxServer
from .Workers.osc_tx_client import OscTxClient

_instance = None

def get_manager(state_cache_manager=None, mqtt_connection_manager=None, run_bridge=True):
    """
    Returns the singleton OSCManager instance.
    If not already initialized, it creates it with the provided managers.
    If called without managers, it relies on OSCManager's internal fallbacks.
    """
    global _instance
    if _instance is None:
        _instance = OSCManager(
            state_cache_manager=state_cache_manager, 
            mqtt_connection_manager=mqtt_connection_manager, 
            run_bridge=run_bridge
        )
    else:
        # ⚡ STANDALONE: Update existing instance if new dependencies are provided
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
        print("\n🎉 All tests for oaComProtocols.oaComOSC passed!")
    else:
        print("\n💔 Some tests for oaComProtocols.oaComOSC failed.")

if __name__ == "__main__":
    # If no arguments are provided, default to running tests.
    # Otherwise, assume specific commands are intended (e.g., start, stop, send).
    if len(sys.argv) > 1:
        print("Executing command...")
        # In a real application, you'd parse sys.argv and call the appropriate functions.
        # For this task, we assume direct execution without specific arguments implies testing.
    else:
        run_tests()


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
    "set_bridge_mode"
]
