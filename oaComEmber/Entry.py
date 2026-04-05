# oaComEmber/Entry.py
# Author: Gemini (Collaborator)
# Version: 20260323.1640.1
#
# Description: Ember Communication Module Entry Point.

"""
oaComEmber/Entry.py - The sole orchestrator for the Ember Communication Module.

Purpose:
This file is the public entry point for 'oaComEmber'. It manages the
lifecycle of the Ember+ connection.
"""

class EmberComEntry:
    """Entry point for Ember communication."""
    def __init__(self):
        print("📡📥📥 [INBOUND] Initializing EmberComEntry...")
        # Placeholder for actual initialization logic
        pass

    def start(self):
        """Starts the Ember+ communication service."""
        print("🚀 [EMBER] Starting Ember+ service...")
        # Placeholder for actual start logic
        pass

    def stop(self):
        """Stops the Ember+ communication service."""
        print("🛑 [EMBER] Stopping Ember+ service...")
        # Placeholder for actual stop logic
        pass

    def status(self):
        """Returns the current status of the Ember+ communication service."""
        print("ℹ️ [EMBER] Checking Ember+ service status...")
        # Placeholder for actual status check logic
        return "idle" # Example status

def run_tests():
    """
    Discovers and runs all tests within the oaComEmber/Tests/ directory.
    """
    print("🔍 Discovering and running tests for oaComEmber...")
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
        print("\n🎉 All tests for oaComEmber passed!")
    else:
        print("\n💔 Some tests for oaComEmber failed.")

if __name__ == "__main__":
    # If no arguments are provided, default to running tests.
    # Otherwise, assume specific commands are intended (e.g., start, stop, status).
    if len(sys.argv) > 1:
        print("Executing command...")
        # In a real application, you'd parse sys.argv and call the appropriate method
        # of EmberComEntry. For this task, we assume direct execution without specific
        # arguments implies testing.
    else:
        run_tests()


__all__ = [
    "EmberComEntry",
]
