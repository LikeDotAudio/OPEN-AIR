# oaGuiElements.graphing/Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260415.2240.1
#
# Description: Gatekeeper for the oaGuiElements.graphing module.

import os
import subprocess
import sys
import time
from pathlib import Path

# Add the project root to sys.path for absolute imports
current_dir = Path(__file__).parent.absolute()
project_root = current_dir
while project_root.parent != project_root:
    if (project_root / "GEMINI.md").exists():
        break
    project_root = project_root.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from oaGuiManager.Core.factory.widget_registry import WidgetRegistry
from oaLogging.Core.logger import builder_logger

# Absolute imports with fallback
try:
    from oaGuiElements.Core.graphing.adapters.bar_graph_adapter import BarGraphAdapter
    from oaGuiElements.Core.graphing.adapters.plot_adapter import PlotAdapter
except ImportError:
    from adapters.bar_graph_adapter import BarGraphAdapter
    from adapters.plot_adapter import PlotAdapter

@WidgetRegistry.register("plot_widget", "bar_graph", "_GuiGraph")
class GraphEntry:
    """
    Unified Entry Point for all Graphing and Plotting Widgets.
    """
    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        if not GraphEntry._validate_config(config_data):
            builder_logger.error(f"❌ [GRAPH] Validation failed for {config_data.get('id', 'Unknown')}")
            return None

        w_type = config_data.get("type")
        if w_type in ["plot_widget", "_GuiGraph"]:
            return PlotAdapter.create(parent_widget, config_data, context, **kwargs)
        elif w_type == "bar_graph":
            return BarGraphAdapter.create(parent_widget, config_data, context, **kwargs)
        return None

    @staticmethod
    def _validate_config(config):
        if not config: return False
        if "type" not in config: return False
        return True

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

__all__ = ["GraphEntry", "start", "stop", "status", "run_tests"]
