# oaGui/Methods/entry/test_runner.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Discovers and executes unit tests for the oaGui module in an isolated subprocess.

import os
import subprocess
import sys
from pathlib import Path


def execute_module_unit_tests(module_path: Path, project_root: Path):
    """
    Discovers and executes all 'test_*.py' files in the local 'Tests/' directory.
    Returns True if all tests passed, False otherwise.
    """
    print(f"📡📥📥 [TEST] {module_path.name}: Starting automated test discovery...")
    test_dir = module_path / "Tests"

    if not test_dir.exists():
        print(f"📡📤📤 [TEST] {module_path.name}: No Tests/ directory found.")
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
            print(f"📡📤📤 [TEST] {module_path.name}: All tests PASSED.")
            return True

        print(f"📡📤📤 [TEST] {module_path.name}: Tests FAILED.")
        return False

    except Exception as error:
        print(f"🛑 [ERROR] {module_path.name}: Test discovery failed: {error}")
        return False
