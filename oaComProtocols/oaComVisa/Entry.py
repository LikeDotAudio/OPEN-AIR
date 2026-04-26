# oaComVisa/Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260415.2225.1
#
# Description: Gatekeeper for the oaComVisa module.

import os
import subprocess
import sys
import time
from pathlib import Path

# Add the project root to sys.path for absolute imports
current_dir = Path(__file__).parent.absolute()
project_root = current_dir
while project_root.parent != project_root:
    if (project_root / "GEMINI.md").exists():
        break
    project_root = project_root.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# --- Absolute Imports for Standalone Support ---
from oaComProtocols.oaComVisa.Core.visa_fleet import FleetOrchestrator
from oaComProtocols.oaComVisa.Core.visa_proxy import VisaProxy
from oaComProtocols.oaComVisa.Core.visa_proxy_fleet import VisaProxyFleet
from oaComProtocols.oaComVisa.Managers.discovery_orchestrator import DiscoveryOrchestrator
from oaComProtocols.oaComVisa.Managers.visa_manager import VisaManagerOrchestrator


class VisaComEntry:
    """Entry point for VISA communication management."""
    def __init__(self):
        print("📡📥📥 [INBOUND] Initializing VisaComEntry...")
        self.discovery_orchestrator = None
        self.visa_manager = None
        self.fleet_orchestrator = None

    def start(self):
        """Starts the VISA communication services."""
        print("🚀 [VISA] Starting VISA communication...")
        pass

    def stop(self):
        """Stops the VISA communication services."""
        print("🛑 [VISA] Stopping VISA communication...")
        pass

    def status(self):
        """Returns the current status of the VISA communication services."""
        print("ℹ️ [VISA] Checking VISA communication status...")
        return "idle"

def get_discovery_orchestrator(manager_ref, aes70_manager=None):
    """Returns a new DiscoveryOrchestrator instance."""
    return DiscoveryOrchestrator(manager_ref, aes70_manager)

def get_visa_manager(mqtt_connection_manager, subscriber_router):
    """Returns a new VisaManagerOrchestrator instance."""
    return VisaManagerOrchestrator(mqtt_connection_manager, subscriber_router)

def get_fleet_orchestrator(mqtt_connection_manager=None, subscriber_router=None, aes70_manager=None):
    """Returns a new FleetOrchestrator instance."""
    return FleetOrchestrator(mqtt_connection_manager, subscriber_router, aes70_manager)

_instance = None

def get_entry():
    """Returns the singleton VisaComEntry instance."""
    global _instance
    if _instance is None:
        _instance = VisaComEntry()
    return _instance

def start():
    """Standardized start command."""
    get_entry().start()

def stop():
    """Standardized stop command."""
    get_entry().stop()

def status():
    """Standardized status command."""
    return get_entry().status()

def run_tests():
    """
    Discover and run tests in the local Tests/ directory using unittest via subprocess.
    Ensures isolation and proper sys.path handling.
    """
    print(f"📡📥📥 [TEST] {Path(__file__).parent.name}: Starting automated test discovery...")
    test_dir = current_dir / "Tests"

    if not test_dir.exists():
        print(f"⚠️ [TEST] {Path(__file__).parent.name}: No Tests/ directory found.")
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
        if result.returncode in [0, 5]:
            if result.returncode == 5:
                print(f"📡📤📤 [TEST] {Path(__file__).parent.name}: No tests found, but discovery succeeded.")
            else:
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
            try:
                while True: time.sleep(1)
            except KeyboardInterrupt:
                stop()
        elif cmd == "--stop":
            stop()
        elif cmd == "--status":
            print(f"Status: {status()}")
        else:
            print(f"Unknown command: {cmd}")
    else:
        # Default standalone action if no args
        start()
        try:
            while True: time.sleep(1)
        except KeyboardInterrupt:
            stop()

__all__ = [
    "VisaComEntry",
    "DiscoveryOrchestrator",
    "VisaManagerOrchestrator",
    "VisaProxy",
    "VisaProxyFleet",
    "FleetOrchestrator",
    "get_discovery_orchestrator",
    "get_visa_manager",
    "get_fleet_orchestrator",
    "start",
    "stop",
    "status",
    "run_tests",
]
