# oaTests/Core/Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260415.2255.1
#
# Description: Gatekeeper for the TestRunner module.

import os
import subprocess
import sys
import time
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
    from oaTests.Core.Workers.DiscoverTests import identify_test_directories
    from oaTests.Core.Workers.TestRunner import TestRunner
except ImportError:
    from Workers.DiscoverTests import identify_test_directories
    from Workers.TestRunner import TestRunner

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

    print("🏁 [COMPLETE] Test Run Finished.")

    total = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)
    passed = total - failures - errors - skipped

    print("📊 Summary:")
    print(f"   ✅ Passed:  {passed}")
    print(f"   ❌ Failed:  {failures}")
    print(f"   💥 Errors:  {errors}")
    print(f"   ⏭️ Skipped: {skipped}")
    if skipped > 0:
        for test, reason in result.skipped:
            print(f"     - {test.id()}: {reason}")

    print(f"   📈 Total:   {total}")
    print("="*60 + "")

    # --- REPORT GENERATION PHASE ---
    try:
        from datetime import datetime

        from oaTests.Workers.collate_data import collate_extra_tabs
        from oaTests.Workers.run_report_builder import ReportGenerator

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        reports_dir = os.path.join(root_path, "oaDataLogs", "Reports")
        os.makedirs(reports_dir, exist_ok=True)

        html_path = os.path.join(reports_dir, f'UnifiedReport_{timestamp}.html')
        json_path = os.path.join(reports_dir, f'UnifiedReport_{timestamp}.json')

        print("📝 [REPORT] Generating Unified Intelligence Report...")

        # Prepare data for generator
        summary = {
            "passed": passed,
            "failed": failures,
            "errors": errors,
            "skipped": skipped
        }

        # Extract details from results
        details = []
        for test, err in result.errors + result.failures:
            status = "error" if test in [e[0] for e in result.errors] else "failed"
            details.append({
                "classname": str(test.__class__.__name__),
                "name": str(test),
                "status": status,
                "message": str(err),
                "duration": "0s" # Standalone result doesn't track per-test duration easily here
            })

        extra_tabs = collate_extra_tabs(root_path)
        generator = ReportGenerator(html_path, json_path, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        generator.generate_json(summary, details)
        generator.generate_html(summary, details, extra_tabs)

        print(f"✅ [SUCCESS] Report generated at: {html_path}")
    except Exception as e:
        print(f"⚠️ [WARNING] Failed to generate report: {e}")

    # Exit with appropriate code
    sys.stdout.flush()
    sys.stderr.flush()
    time.sleep(0.5)

    # ⚡ CLEAN EXIT: Replaced SIGKILL with proper sys.exit
    sys.exit(0 if (failures + errors == 0) else 1)

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
