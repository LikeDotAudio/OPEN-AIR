# oaTests/Workers/TestRunner/Entry.py
# Author: Anthony Peter Kuzub
# Version: 1.1.0
#
# Description: Standalone CLI entry point for the OPEN-AIR Test Runner.

import sys
import os
import pathlib

# Ensure project root is in the search path for local module imports.
# This file is project_root/oaTests/Workers/TestRunner/Entry.py
current_file_path = pathlib.Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import logic from the local directory
try:
    from .DiscoverTests import identify_test_directories
    from .TestRunner import TestRunner
except ImportError:
    # Handle direct execution where '.' might not work
    from DiscoverTests import identify_test_directories
    from TestRunner import TestRunner

def main():
    """
    Executes the standalone CLI test runner.
    """
    print("\n" + "="*60)
    print("🚀 OPEN-AIR STANDALONE TEST RUNNER")
    print("="*60)
    
    root_path = str(project_root)
    print(f"📂 Project Root: {root_path}")
    
    print("\n🔍 Discovering tests...")
    found_dirs = identify_test_directories(root_path)
    print(f"📂 Discovery identified {len(found_dirs)} test-containing folders.")
    
    print("\n🔬 Executing test suite...")
    print("-" * 60)
    
    # Initialize runner without callback to use default console output
    runner = TestRunner()
    result = runner.run(found_dirs, top_level_dir=root_path)
    
    print("-" * 60)
    print(f"\n🏁 [COMPLETE] Test Run Finished.")
    
    total = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)
    passed = total - failures - errors - skipped
    
    print(f"📊 Summary:")
    print(f"   ✅ Passed:  {passed}")
    print(f"   ❌ Failed:  {failures}")
    print(f"   💥 Errors:  {errors}")
    print(f"   ⏭️ Skipped: {skipped}")
    print(f"   📈 Total:   {total}")
    print("="*60 + "\n")
    
    # Exit with appropriate code
    if failures > 0 or errors > 0:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
