# oaLogging/Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260415.2210.1
#
# Description: Gatekeeper for the oaLogging module.

import sys
import os
from pathlib import Path

# Standard project_root resolution
current_dir = Path(__file__).parent.absolute()
project_root = current_dir
while project_root.parent != project_root:
    if (project_root / "GEMINI.md").exists():
        break
    project_root = project_root.parent

# Ensure the project root is in sys.path for absolute imports
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# --- Core Exports ---
from oaLogging.Core.logger import (
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
from oaLogging.Core.exceptions import (
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
from oaLogging.Managers.log_filter_engine import LogFilterEngine

# --- Method Exports ---
from oaLogging.Methods.error_handling import (
    vocal_failure_handler,
    vocal_capture
)

class LoggingEntry:
    """Entry point for logging management services."""
    def __init__(self):
        self.log_filter_engine = LogFilterEngine()

    def start(self, config=None, log_dir=None, partition="SYS"):
        """Starts the logging service."""
        if config and log_dir:
            initialize_logging(config, log_dir=log_dir, partition=partition)

    def stop(self):
        """Stops the logging service."""
        pass

    def status(self):
        """Returns the current status of the logging service."""
        return "active"

def run_tests():
    """
    Discover and run tests in the local Tests/ directory using unittest via subprocess.
    Ensures isolation and proper sys.path handling.
    """
    import subprocess
    
    print(f"📡📥📥 [TEST] {Path(__file__).parent.name}: Starting automated test discovery...")
    test_dir = current_dir / "Tests"
    
    if not test_dir.exists():
        print(f"📡📤📤 [TEST] {Path(__file__).parent.name}: No Tests/ directory found.")
        return True

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

def stop():
    """Stop the module services."""
    print(f"🛑 [STOP] Stopping {Path(__file__).parent.name} services...")

def status():
    """Get the module status."""
    print(f"📊 [STATUS] Checking {Path(__file__).parent.name} status...")
    return "Running"

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

# Standardized exports
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
    "TEST_LOGGER",
    "start",
    "stop",
    "status",
    "run_tests"
]
