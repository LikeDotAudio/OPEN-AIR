# oaComProtocols.oaComSMPTE2138/Entry.py
#
# Gatekeeper for the SMPTE ST 2138 (SMPTE2138) Communication Module. 
# Orchestrates translation (Bridge) and observation (Monitor) services.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Version 20260330.1600.1

from .Managers.smpte2138_bridge_manager import SMPTE2138BridgeManager
from .Managers.smpte2138_monitor_manager import SMPTE2138MonitorManager

__all__ = ["SMPTE2138BridgeManager", "SMPTE2138MonitorManager"]

def start_bridge(mqtt_connection, subscriber_router):
    """
    Initializes the SMPTE2138 Bridge Manager (Internal -> External).
    Used in the Core Partition.
    """
    return SMPTE2138BridgeManager(mqtt_connection, subscriber_router)

def start_monitor(mqtt_connection, subscriber_router):
    """
    Initializes the SMPTE2138 Monitor Manager (External -> Human Readable).
    Used in the UI Partition.
    """
    return SMPTE2138MonitorManager(mqtt_connection, subscriber_router)

def run_tests():
    """
    Discovers and runs all tests within the oaComProtocols.oaComSMPTE2138/Tests/ directory.
    """
    print("🔍 Discovering and running tests for oaComProtocols.oaComSMPTE2138...")
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
        print("\n🎉 All tests for oaComProtocols.oaComSMPTE2138 passed!")
    else:
        print("\n💔 Some tests for oaComProtocols.oaComSMPTE2138 failed.")

if __name__ == "__main__":
    # If no arguments are provided, default to running tests.
    # Otherwise, assume specific commands are intended (e.g., start_bridge, start_monitor).
    if len(sys.argv) > 1:
        print("Executing command...")
        # In a real application, you'd parse sys.argv and call the appropriate functions.
        # For this task, we assume direct execution without specific arguments implies testing.
    else:
        run_tests()

