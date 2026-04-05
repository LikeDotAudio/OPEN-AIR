# oaComREST/Entry.py
#
# Public entry point for the REST API module. Orchestrates the lifecycle 
# of the REST manager and exposes the public monitoring API.
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
# Version 20260330.1600.1

from loguru import logger
from .Managers.rest_manager import RESTManager
from .Constants.rest_constants import LOCAL_DEBUG
from oaLogging.Methods.matrix_gate import matrix_log

_manager = None

def get_manager(state_cache_manager=None, protocol_router=None):
    """
    Singleton accessor for the RESTManager.
    """
    global _manager
    if _manager is None:
        matrix_log("comms", "rest", "get_manager", "📡⚙️🔗 [REST] Creating singleton RESTManager instance.", "DEBUG")
        _manager = RESTManager(state_cache_manager, protocol_router)
    return _manager

def start(state_cache_manager=None, protocol_router=None):
    """Convenience function to start the REST service."""
    matrix_log("comms", "rest", "start", "📡⚙️🚀 [REST] Manual service start initiated via Entry.", "DEBUG")
    return get_manager(state_cache_manager, protocol_router).start()

def stop():
    """Convenience function to stop the REST service."""
    if _manager:
        matrix_log("comms", "rest", "stop", "📡⚙️🛑 [REST] Manual service stop initiated via Entry.", "DEBUG")
        _manager.stop()

def get_status():
    """Convenience function to get the current REST service status."""
    if _manager:
        return _manager.get_status()
    
    # Return a consistent minimal status object
    from .Constants.rest_constants import REST_HOST, REST_PORT
    return {
        "running": False,
        "local_host": False,
        "sibling_host": False,
        "should_run": False,
        "initialized": False,
        "host": REST_HOST,
        "port": REST_PORT,
        "url": f"http://{REST_HOST}:{REST_PORT}",
        "docs_url": f"http://{REST_HOST}:{REST_PORT}/docs",
        "routes": []
    }

def add_monitor_callback(callback):
    """Registers a callback for real-time activity monitoring."""
    if _manager:
        _manager.add_monitor_callback(callback)

def remove_monitor_callback(callback):
    """Removes a previously registered monitor callback."""
    if _manager:
        _manager.remove_monitor_callback(callback)

def run_tests():
    """
    Discovers and runs all tests within the oaComREST/Tests/ directory.
    """
    print("🔍 Discovering and running tests for oaComREST...")
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
        print("\n🎉 All tests for oaComREST passed!")
    else:
        print("\n💔 Some tests for oaComREST failed.")

if __name__ == "__main__":
    # If no arguments are provided, default to running tests.
    # Otherwise, assume specific commands are intended (e.g., start, stop).
    if len(sys.argv) > 1:
        print("Executing command...")
        # In a real application, you'd parse sys.argv and call the appropriate functions.
        # For this task, we assume direct execution without specific arguments implies testing.
    else:
        run_tests()

__all__ = ["RESTManager", "get_manager", "start", "stop", "get_status", "add_monitor_callback", "remove_monitor_callback"]


__all__ = ["RESTManager", "get_manager", "start", "stop", "get_status", "add_monitor_callback", "remove_monitor_callback"]
