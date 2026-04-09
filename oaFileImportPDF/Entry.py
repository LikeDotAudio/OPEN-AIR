# oaFileImportPDF/Entry.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

"""
import sys
import os
from pathlib import Path
oaFileImportPDF/Entry.py - The sole orchestrator for the PDF Import Module.
"""
from .FileReaders.from_soundbase_pdf_v1 import convert_soundbase_pdf_v1_to_markers
from .FileReaders.from_soundbase_pdf_v2 import convert_soundbase_pdf_v2_to_markers

# Aliases for backward compatibility
Marker_convert_SB_PDF_File_report_to_csv = convert_soundbase_pdf_v1_to_markers
Marker_convert_SB_v2_PDF_File_report_to_csv = convert_soundbase_pdf_v2_to_markers

__all__ = [
    "convert_soundbase_pdf_v1_to_markers",
    "convert_soundbase_pdf_v2_to_markers",
    "Marker_convert_SB_PDF_File_report_to_csv",
    "Marker_convert_SB_v2_PDF_File_report_to_csv"
]

def run_tests():
    """
    Discovers and runs all tests within the oaFileImportPDF/Tests/ directory.
    """
    print("🔍 Discovering and running tests for oaFileImportPDF...")
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
        print("\n🎉 All tests for oaFileImportPDF passed!")
    else:
        print("\n💔 Some tests for oaFileImportPDF failed.")

if __name__ == "__main__":
    # If no arguments are provided, default to running tests.
    # Otherwise, assume specific commands are intended.
    if len(sys.argv) > 1:
        print("Executing command...")
        # In a real application, you'd parse sys.argv and call the appropriate functions.
        # For this task, we assume direct execution without specific arguments implies testing.
    else:
        run_tests()

