# FlameGraph/Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260415.2150.1
#
# Description: Gatekeeper for the FlameGraph module.

import subprocess
from pathlib import Path

import sys
import os
import pathlib
import threading
from loguru import logger

# 1. Setup Environment: MUST BE FIRST to allow internal imports
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# oaTests/Methods/FlameGraph/Entry.py

try:
    from oaTests.Methods.FlameGraph.Managers.flame_manager import FlameManager
except (ImportError, ModuleNotFoundError):
    from Managers.flame_manager import FlameManager

def main():
    """
    Orchestrates a full profiling session of the OpenAir application.
    """
    matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🔥 [ENTRY] Initializing Performance Profiling Session...", "INFO")
    
    manager = FlameManager()
    
    # 1. Start Profiling
    manager.start_profiling()
    
    # 2. Register Panic Callback (Handle "Halting and Catching Fire")
    try:
        from oaWatchdog.Managers.watchdog import register_panic_callback
        # Register a callback to ensure report is generated on critical failure
        register_panic_callback(lambda: manager.generate_report())
        matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🔥 [ENTRY] Panic callback registered with Watchdog.", "INFO")
    except ImportError:
        logger.warning("🔥 [ENTRY] Watchdog not found. Panic callbacks disabled.")
    except Exception as e:
        logger.error(f"🔥 [ENTRY] Failed to register panic callback: {e}")

    # 3. Launch the Application
    matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🔥 [ENTRY] Launching OpenAir Application...", "INFO")
    try:
        import openair
        # Assuming openair has a main() entry point that starts the app
        # and blocking until the app is closed.
        openair.main()
    except KeyboardInterrupt:
        matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🔥 [ENTRY] Session interrupted by user (KeyboardInterrupt).", "INFO")
    except Exception as e:
        logger.exception(f"🔥 [ENTRY] Application crashed during profiling: {e}")
    finally:
        # 4. Stop Profiling and Generate Report
        manager.stop_profiling()
        report_path = manager.generate_report()
        
        if report_path:
            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"🔥 [ENTRY] Performance profiling session complete.", "SUCCESS")
            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"🔥 [ENTRY] Report: {report_path}", "INFO")
        else:
            logger.error("🔥 [ENTRY] Failed to synthesize final report.")


def run_tests():
    """
    Discover and run tests in the local Tests/ directory using unittest via subprocess.
    Ensures isolation and proper sys.path handling.
    """
    import subprocess
    import sys
    import os
    from pathlib import Path

    print(f"📡📥📥 [TEST] {Path(__file__).parent.name}: Starting automated test discovery...")
    current_dir = Path(__file__).parent.absolute()
    test_dir = current_dir / "Tests"
    
    if not test_dir.exists():
        return True

    project_root = current_dir
    while project_root.parent != project_root:
        if (project_root / "GEMINI.md").exists():
            break
        project_root = project_root.parent
    
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
            print(f"📡📤📤 [TEST] {Path(__file__).parent.name}: All tests PASSED.")
            return True
        else:
            print(f"📡📤📤 [TEST] {Path(__file__).parent.name}: Tests FAILED.")
            return False
    except Exception as e:
        print(f"🛑 [ERROR] {Path(__file__).parent.name}: Test discovery failed: {e}")
        return False

def start():
    """Start the module services."""
    print(f"🚀 [START] Starting {Path(__file__).parent.name} services...")
    main()

def stop():
    """Stop the module services."""
    print(f"🛑 [STOP] Stopping {Path(__file__).parent.name} services...")

def status():
    """Get the module status."""
    print(f"📊 [STATUS] Checking {Path(__file__).parent.name} status...")
    return "Running"

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
        elif cmd == "--stop":
            stop()
        elif cmd == "--status":
            print(f"Status: {status()}")
        else:
            print(f"Unknown command: {cmd}")
    else:
        # Default standalone action if no args
        start()

__all__ = ["start", "stop", "status", "run_tests"]
