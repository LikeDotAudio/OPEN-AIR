# oaLogging/Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260330.1030.1 # Fixed exports and removed nonexistent Logger class
#
# Description: Logging Module Entry Point.

"""
import sys
import os
from pathlib import Path
oaLogging/Entry.py - The sole orchestrator for the Logging Module.

Purpose:
This file is the public entry point for 'oaLogging'. It manages the
lifecycle of the logging system and provides access to logging utilities.
"""

# --- Core Exports ---
from .Core.logger import (
    logger,
    initialize_logging,
    initialize_test_logging,
    set_log_directory,
    get_logger,
    debug_log,
    console_log,
    failure_log,
    SYSTEM_LOGGER,
    CORE_LOGGER,
    DATA_LOGGER,
    GUI_LOGGER,
    MQTT_LOGGER,
    SNMP_LOGGER,
    MIDI_LOGGER,
    OSC_LOGGER,
    ROUTER_LOGGER,
    FAILURE_LOGGER,
    TEST_LOGGER
)

# --- Exception Exports ---
from .Core.exceptions import (
    OpenAirError,
    VocalError,
    ConfigurationError,
    NetworkError,
    ProtocolError,
    ResourceError,
    HardwareError,
    CriticalModuleMissingError,
    UIConstructionError
)

# --- Manager Exports ---
from .Managers.log_filter_engine import LogFilterEngine

# --- Method Exports ---
from .Methods.error_handling import (
    vocal_failure_handler,
    vocal_capture
)

class LoggingEntry:
    """Entry point for logging management services."""
    def __init__(self):
        # print("📡📥📥 [INBOUND] Initializing LoggingEntry...")
        self.log_filter_engine = LogFilterEngine()

    def start(self, config=None, log_dir=None, partition="SYS"):
        """Starts the logging service."""
        if config and log_dir:
            initialize_logging(config, log_dir=log_dir, partition=partition)

    def stop(self):
        """Stops the logging service."""
        # Loguru doesn't require explicit stop for basic sinks, 
        # but if we use custom sinks with threads (like BatchLogSink),
        # we might need to handle cleanup if we had references to them.
        pass

    def status(self):
        """Returns the current status of the logging service."""
        return "active"

# Standardized exports for the Gatekeeper pattern.
__all__ = [
    "LoggingEntry",
    "logger",
    "initialize_logging",
    "initialize_test_logging",
    "set_log_directory",
    "get_logger",
    "debug_log",
    "console_log",
    "failure_log",
    "vocal_failure_handler",
    "vocal_capture",
    "OpenAirError",
    "VocalError",
    "ConfigurationError",
    "NetworkError",
    "ProtocolError",
    "ResourceError",
    "HardwareError",
    "CriticalModuleMissingError",
    "UIConstructionError",
    "LogFilterEngine",
    "SYSTEM_LOGGER",
    "CORE_LOGGER",
    "DATA_LOGGER",
    "GUI_LOGGER",
    "MQTT_LOGGER",
    "SNMP_LOGGER",
    "MIDI_LOGGER",
    "OSC_LOGGER",
    "ROUTER_LOGGER",
    "FAILURE_LOGGER",
    "TEST_LOGGER"
]

def run_tests():
    """
    Discovers and runs all tests within the oaLogging/Tests/ directory.
    """
    print("🔍 Discovering and running tests for oaLogging...")
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
            relative_test_file_path = test_file.relative_to(Path(__file__).parent.parent) # Path from OPEN-AIR root
            module_path_for_runner = str(relative_test_file_path).replace(os.sep, '.')[:-3] # Remove .py extension

            # Ensure the current directory is the project root so Python can find modules
            original_cwd = os.getcwd()
            os.chdir(Path(__file__).parent.parent) 

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
        print("\n🎉 All tests for oaLogging passed!")
    else:
        print("\n💔 Some tests for oaLogging failed.")

if __name__ == "__main__":
    # If no arguments are provided, default to running tests.
    # Otherwise, assume specific commands are intended.
    if len(sys.argv) > 1:
        print("Executing command...")
        # In a real application, you'd parse sys.argv and call the appropriate functions.
        # For this task, we assume direct execution without specific arguments implies testing.
    else:
        run_tests()

