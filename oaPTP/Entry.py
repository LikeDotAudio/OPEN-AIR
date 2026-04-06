# oaPTP/Entry.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

"""
oaPTP/Entry.py - The sole orchestrator for the PTP Module.

Purpose:
This file is the public entry point for 'oaPTP'. It manages the 
lifecycle of the PTP sniffer and provides high-level 
monitoring and control interfaces.
"""

from .Core.ptp import PtpManager

_instance = None

def get_manager(mqtt_connection_manager=None, subscriber_router=None):
    """Returns the singleton PtpManager instance."""
    global _instance
    if _instance is None:
        _instance = PtpManager(mqtt_connection_manager, subscriber_router)
    return _instance

def start(mqtt_connection_manager=None, subscriber_router=None):
    """
    Initializes and starts the PTP service.
    """
    manager = get_manager(mqtt_connection_manager, subscriber_router)
    return manager.start()

def stop():
    """
    Shuts down the PTP service.
    """
    if _instance:
        _instance.stop()

def status():
    """Returns the current status of the PTP manager."""
    return "running" if _instance and _instance.sniffer_thread and _instance.sniffer_thread.is_alive() else "stopped"

def run_tests():
    """
    Discovers and runs all tests within the oaPTP/Tests/ directory.
    """
    print("🔍 Discovering and running tests for oaPTP...")
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
        print("\n🎉 All tests for oaPTP passed!")
    else:
        print("\n💔 Some tests for oaPTP failed.")

if __name__ == "__main__":
    # If no arguments are provided, default to running tests.
    # Otherwise, assume specific commands are intended (e.g., start, stop, status).
    if len(sys.argv) > 1:
        print("Executing command...")
        # In a real application, you'd parse sys.argv and call the appropriate functions.
        # For this task, we assume direct execution without specific arguments implies testing.
    else:
        run_tests()

