# oaComProtocols.oaComVisa/Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260330.1000.1 # Updated version for structure change
#
# Description: VISA Communication Module Entry Point.

"""
import sys
import os
from pathlib import Path
oaComProtocols.oaComVisa/Entry.py - The sole orchestrator for the VISA Communication Module.

Purpose:
This file is the public entry point for 'oaComProtocols.oaComVisa'. It manages the
lifecycle of VISA instrument connections.
"""

from .Managers.discovery_orchestrator import DiscoveryOrchestrator
from .Managers.visa_manager import VisaManagerOrchestrator
from .Core.visa_proxy import VisaProxy
from .Core.visa_proxy_fleet import VisaProxyFleet
from .Core.visa_fleet import FleetOrchestrator

class VisaComEntry:
    """Entry point for VISA communication management."""
    def __init__(self):
        print("📡📥📥 [INBOUND] Initializing VisaComEntry...")
        # Placeholder for initialization logic, e.g., setting up managers
        self.discovery_orchestrator = None
        self.visa_manager = None
        self.fleet_orchestrator = None
        pass

    def start(self):
        """Starts the VISA communication services."""
        print("🚀 [VISA] Starting VISA communication...")
        # Example: Initialize managers if they aren't already
        # if not self.discovery_orchestrator:
        #     self.discovery_orchestrator = DiscoveryOrchestrator(...)
        # if not self.visa_manager:
        #     self.visa_manager = VisaManagerOrchestrator(...)
        # if not self.fleet_orchestrator:
        #     self.fleet_orchestrator = FleetOrchestrator(...)
        # ... actual start logic ...
        pass

    def stop(self):
        """Stops the VISA communication services."""
        print("🛑 [VISA] Stopping VISA communication...")
        # Placeholder for actual stop logic
        pass

    def status(self):
        """Returns the current status of the VISA communication services."""
        print("ℹ️ [VISA] Checking VISA communication status...")
        # Placeholder for actual status check logic
        return "idle" # Example status

def get_discovery_orchestrator(manager_ref, aes70_manager=None):
    """Returns a new DiscoveryOrchestrator instance."""
    return DiscoveryOrchestrator(manager_ref, aes70_manager)

def get_visa_manager(mqtt_connection_manager, subscriber_router):
    """Returns a new VisaManagerOrchestrator instance."""
    return VisaManagerOrchestrator(mqtt_connection_manager, subscriber_router)

def get_fleet_orchestrator(mqtt_connection_manager=None, subscriber_router=None, aes70_manager=None):
    """Returns a new FleetOrchestrator instance."""
    return FleetOrchestrator(mqtt_connection_manager, subscriber_router, aes70_manager)

def run_tests():
    """
    Discovers and runs all tests within the oaComProtocols.oaComVisa/Tests/ directory.
    """
    print("🔍 Discovering and running tests for oaComProtocols.oaComVisa...")
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
        print("\n🎉 All tests for oaComProtocols.oaComVisa passed!")
    else:
        print("\n💔 Some tests for oaComProtocols.oaComVisa failed.")

if __name__ == "__main__":
    # If no arguments are provided, default to running tests.
    # Otherwise, assume specific commands are intended (e.g., start, stop).
    if len(sys.argv) > 1:
        print("Executing command...")
        # In a real application, you'd parse sys.argv and call the appropriate methods
        # of VisaComEntry. For this task, we assume direct execution without specific
        # arguments implies testing.
    else:
        run_tests()


__all__ = [
    "VisaComEntry",
    "DiscoveryOrchestrator",
    "VisaManagerOrchestrator",
    "VisaProxy",
    "VisaProxyFleet",
    "FleetOrchestrator",
    "get_discovery_orchestrator",
    "get_visa_manager",
    "get_fleet_orchestrator"
]
