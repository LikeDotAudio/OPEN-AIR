# oaComBroker/Entry.py
#
# The sole orchestrator and public gatekeeper for the Communication Broker.
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
# Version 20260328.1620.1
#
# Description:
# This module acts as the Gatekeeper for the oaComBroker subsystem. It abstracts
# the complexities of the multi-protocol routing engine and provides a unified
# interface for lifecycle management. Following the Partitioned Architecture,
# this file resides in the module root as the only permitted entry point.
#
# Architectural Role:
# - Orchestrates the initialization of Core services.
# - Provides access to the Singleton ProtocolRouter.
# - Exports the FailoverManager for redundancy control.
# - Manages high-level status and lifecycle hooks.

from .Core.protocol_router.router import ProtocolRouter
from .Managers.Failover.Manager import FailoverManager
from .Core import open_air_core

def get_router_instance():
    """
    Allocates or retrieves the singleton ProtocolRouter instance.
    
    Returns:
        ProtocolRouter: The active routing engine instance.
    """
    return ProtocolRouter.get_instance()

def start_core_services():
    """
    Initializes the safety-critical core services for OPEN-AIR.
    
    This function triggers the boot sequence for hardware-facing logic 
    and protocol listeners. It should only be called once during the 
    application startup phase.
    
    Returns:
        int: Success (0) or Error Code.
    """
    return open_air_core.main()

# Standardized exports for the Gatekeeper pattern.
__all__ = [
    "ProtocolRouter", 
    "FailoverManager",
    "get_router_instance", 
    "start_core_services"
]

def run_tests():
    """
    Discovers and runs all tests within the oaComBroker/Tests/ directory.
    """
    print("🔍 Discovering and running tests for oaComBroker...")
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
        print("\n🎉 All tests for oaComBroker passed!")
    else:
        print("\n💔 Some tests for oaComBroker failed.")

if __name__ == "__main__":
    # If run directly and no specific arguments are provided, execute tests.
    # This assumes that if arguments like '--start', '--stop', etc. are intended,
    # they would be passed. If no such arguments are detected, we default to tests.
    if len(sys.argv) > 1 and sys.argv[1] in ["--start", "--stop", "--status", "--manager"]:
        print("Executing manager function...")
        # In a real application, you'd parse sys.argv and call the appropriate function.
        # For this task, we assume direct execution without known args implies testing.
    else:
        run_tests()

