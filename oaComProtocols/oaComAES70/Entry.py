# oaComProtocols.oaComAES70/Entry.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

"""
oaComProtocols.oaComAES70/Entry.py - The sole orchestrator for the AES70 Communication Module.

Purpose:
This file is the public entry point for 'oaComProtocols.oaComAES70'. It manages the 
lifecycle of the AES70/OCA connection and provides high-level 
monitoring and control interfaces.
"""

from .Core.aes70 import AES70Manager

_instance = None

def get_manager(state_cache=None, run_bridge=True):
    """Returns the singleton AES70Manager instance."""
    global _instance
    if _instance is None:
        _instance = AES70Manager(state_cache, run_bridge)
    return _instance

def start(state_cache=None):
    """
    Initializes and starts the AES70 service.
    """
    manager = get_manager(state_cache)
    return manager.start()

def stop():
    """
    Shuts down the AES70 service.
    """
    if _instance:
        _instance.stop()

def status():
    """Returns the current status of the AES70 manager."""
    # Logic to derive status from manager state
    return "running" if _instance else "stopped"

# Standardized exports
__all__ = [
    "AES70Manager",
    "get_manager",
    "start",
    "stop",
    "status"
]

def run_tests():
    print("🔍 Discovering and running tests for oaComProtocols.oaComAES70...")
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
        print("\n🎉 All tests for oaComProtocols.oaComAES70 passed!")
    else:
        print("\n💔 Some tests for oaComProtocols.oaComAES70 failed.")

if __name__ == "__main__":
    # Check if specific commands are given, otherwise run tests
    if "--start" in sys.argv or "--stop" in sys.argv or "--status" in sys.argv or "--manager" in sys.argv:
        # If any of the known manager functions are called, execute them
        # This is a simplification; a more robust CLI would parse arguments properly
        print("Running manager functions...")
        # The actual logic for handling --start, --stop, etc. would be here
        # For now, we'll just print a message and proceed to tests if no known args are present
        # A better approach would be to use argparse.
        # We'll assume if no specific command is given, it defaults to tests.
        # If we detect any of these, we *might* want to skip tests.
        # For now, let's assume only explicit commands skip tests.

        # If there are any other arguments, assume it's for the manager functions
        # and skip tests. Otherwise, run tests.
        if len(sys.argv) > 1 and sys.argv[1] not in ["--start", "--stop", "--status", "--manager"]:
             print("Executing non-test command.")
        else:
             run_tests()
    else:
        # Default behavior: run tests if no specific command is provided
        run_tests()
