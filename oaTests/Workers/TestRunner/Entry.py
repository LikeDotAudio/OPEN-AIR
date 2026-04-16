# TestRunner/Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260415.2255.1
#
# Description: Gatekeeper for the TestRunner module.

import os
import sys
import subprocess
import time
import signal
from pathlib import Path

# ⚡ SAFETY: Prevent segmentation faults from real MIDI drivers in test environment
if os.environ.get("OPEN_AIR_SKIP_REAL_MIDI") is None:
    os.environ["OPEN_AIR_SKIP_REAL_MIDI"] = "1"

# Add the project root to sys.path for absolute imports
current_dir = Path(__file__).parent.absolute()
project_root = current_dir
while project_root.parent != project_root:
    if (project_root / "GEMINI.md").exists():
        break
    project_root = project_root.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Absolute imports with fallback
try:
    from oaTests.Workers.TestRunner.DiscoverTests import identify_test_directories
    from oaTests.Workers.TestRunner.TestRunner import TestRunner
except ImportError:
    from DiscoverTests import identify_test_directories
    from TestRunner import TestRunner

def main():
    """
    Executes the standalone CLI test runner.
    """
    print("" + "="*60)
    print("🚀 OPEN-AIR STANDALONE TEST RUNNER")
    print("="*60)
    
    root_path = str(project_root)
    print(f"📂 Project Root: {root_path}")
    
    print("🔍 Discovering tests...")
    found_dirs = identify_test_directories(root_path)
    print(f"📂 Discovery identified {len(found_dirs)} test-containing folders.")
    
    print("🔬 Executing test suite...")
    print("-" * 60)
    
    # Initialize runner without callback to use default console output
    runner = TestRunner()
    result = runner.run(found_dirs, top_level_dir=root_path)
    
    print("-" * 60)
    
    # ⚡ CLEANUP PHASE: Prevent Segfaults on Exit
    print("🧹 Commencing post-test cleanup...")
    try:
        from oaComBroker.Core.protocol_router.manager import ProtocolRouter
        router = ProtocolRouter.get_instance()
        if router:
            router.stop()
            
        from oaComProtocols.oaComMQTT.Managers.mqtt_connection import MqttConnectionManager
        mqtt = MqttConnectionManager()
        if mqtt:
            mqtt.disconnect()

        from oaComProtocols.oaComMidi.Managers.midi_manager import MidiManager
        midi = MidiManager()
        if midi:
            midi.stop()
            
        # Give threads a moment to die
        time.sleep(1.0)
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")

    print(f"🏁 [COMPLETE] Test Run Finished.")
    
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
    if skipped > 0:
        for test, reason in result.skipped:
            print(f"     - {test.id()}: {reason}")

    print(f"   📈 Total:   {total}")
    print("="*60 + "")
    
    # Exit with appropriate code
    sys.stdout.flush()
    sys.stderr.flush()
    time.sleep(0.5)

    # ⚡ SILENT EXIT: Use kill -9 to prevent segfaults from native extension destructors
    os.kill(os.getpid(), signal.SIGKILL)

def run_tests():
    """
    Discover and run tests in the local Tests/ directory using unittest via subprocess.
    Ensures isolation and proper sys.path handling.
    """
    print(f"📡📥📥 [TEST] {Path(__file__).parent.name}: Starting automated test discovery...")
    test_dir = current_dir / "Tests"
    
    if not test_dir.exists():
        print(f"⚠️ [TEST] {Path(__file__).parent.name}: No Tests/ directory found.")
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
        if result.returncode in [0, 5]:
            if result.returncode == 5:
                print(f"📡📤📤 [TEST] {Path(__file__).parent.name}: No tests found, but discovery succeeded.")
            else:
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
            try:
                while True: time.sleep(1)
            except KeyboardInterrupt:
                stop()
        elif cmd == "--stop":
            stop()
        elif cmd == "--status":
            print(f"Status: {status()}")
        else:
            print(f"Unknown command: {cmd}")
    else:
        # Default standalone action if no args
        start()
        try:
            while True: time.sleep(1)
        except KeyboardInterrupt:
            stop()

__all__ = ["start", "stop", "status", "run_tests"]
