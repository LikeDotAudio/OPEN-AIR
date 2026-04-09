# oaDocumentation/Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260330.1000.1 # Updated version for structure change
#
# Description: Documentation Module Entry Point.

"""
import sys
import os
from pathlib import Path
oaDocumentation/Entry.py - The sole orchestrator for the Documentation Module.

Purpose:
This file is the public entry point for 'oaDocumentation'. It manages the
documentation retrieval and display logic.
"""

class DocumentationEntry:
    """Entry point for documentation management services."""
    def __init__(self):
        print("📡📥📥 [INBOUND] Initializing DocumentationEntry...")
        pass

    def start(self):
        """Starts the documentation service (e.g., loads documentation index)."""
        print("📚 [DOCS] Starting Documentation service...")
        # Placeholder for start logic, e.g., indexing documentation files
        pass

    def stop(self):
        """Stops the documentation service."""
        print("🛑 [DOCS] Stopping Documentation service...")
        # Placeholder for stop logic
        pass

    def status(self):
        """Returns the current status of the documentation service."""
        print("ℹ️ [DOCS] Checking Documentation service status...")
        # Placeholder for status check logic
        return "ready" # Example status

def main():
    """Entry point for script execution."""
    # This might be adapted to use DocumentationEntry or perform other actions
    print("Running Documentation module main entry point.")
    docs_manager = DocumentationEntry()
    docs_manager.start()
    print(f"Status: {docs_manager.status()}")
    docs_manager.stop()

# Standardized exports
__all__ = [
    "DocumentationEntry",
    "main"
]

def run_tests():
    """
    Discovers and runs all tests within the oaDocumentation/Tests/ directory.
    """
    print("🔍 Discovering and running tests for oaDocumentation...")
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
        print("\n🎉 All tests for oaDocumentation passed!")
    else:
        print("\n💔 Some tests for oaDocumentation failed.")

if __name__ == '__main__':
    # If no command-line arguments are provided, default to running tests.
    # Otherwise, assume specific commands are intended (e.g., start, stop, validate).
    if len(sys.argv) > 1:
        print("Executing command...")
        # In a real application, you'd parse sys.argv and call the appropriate functions.
        # For this task, we assume direct execution without specific arguments implies testing.
        main() # Call the original main function if arguments are present
    else:
        run_tests()
        # If tests pass, we can optionally call main() or simply let the script exit.
        # For this implementation, we'll let it exit after tests.


if __name__ == '__main__':
    main()
