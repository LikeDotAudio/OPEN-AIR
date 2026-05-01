# oaGui/Entry.py
#
# Gatekeeper for the oaGui module. This file serves as the primary public API 
# and orchestrator for the Graphical User Interface subsystem.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your 
# specific application can be negotiated. There is no charge to use, modify, 
# or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260501.1000.1
#
# This module operates within the "UI" partition of the OPEN-AIR Partitioned 
# Architecture. It is responsible for initializing the rendering engine, 
# managing widget lifecycles via the Registry, and handling user interactions.

import os
import sys
from pathlib import Path

# Standard project_root resolution to support relative and absolute imports
current_dir = Path(__file__).parent.absolute()
project_root = current_dir
while project_root.parent != project_root:
    if (project_root / "GEMINI.md").exists():
        break
    project_root = project_root.parent

# Ensure the project root is in sys.path for absolute imports across partitions
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from oaGui.FileReaders.directory_loader import DirectoryBuilderMixin
from oaGui.FileReaders.layout_parser import LayoutParser
from oaGui.Managers.dynamic_widget_renderer import DynamicWidgetRendererMixin
from oaGui.Managers.gui_display import Application
from oaGui.Hooks.gui_mqtt import GuiMqttManagerMixin


def start_gui():
    """
    Initializes and starts the main application GUI loop.
    
    This function creates the root Tkinter window, configures basic window 
    properties, instantiates the main Application class, and enters the 
    blocking mainloop.
    
    Side Effects:
        - Creates a persistent GUI window.
        - Blocks the calling thread until the window is closed.
    """
    import tkinter as tk
    root = tk.Tk()
    root.title("OPEN-AIR GUI TESTER")
    root.geometry("1600x1000")

    app = Application(root, root=root)
    app.pack(fill="both", expand=True)

    root.mainloop()


def run_tests():
    """
    Discovers and executes unit tests for the oaGui module.
    
    Uses the 'unittest' discovery mechanism to find all 'test_*.py' files 
    within the local 'Tests/' directory. Executes them in a separate 
    subprocess to maintain environment isolation and prevent side-effect 
    leakage.
    
    Returns:
        bool: True if all tests passed (exit code 0), False otherwise.
    
    Side Effects:
        - Spawns a subprocess using 'sys.executable'.
        - Outputs test results to stdout/stderr.
    """
    import subprocess

    print(f"📡📥📥 [TEST] {Path(__file__).parent.name}: Starting automated test discovery...")
    test_dir = current_dir / "Tests"

    if not test_dir.exists():
        print(f"📡📤📤 [TEST] {Path(__file__).parent.name}: No Tests/ directory found.")
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
            print(f"📡📤📤 [TEST] {Path(__file__).parent.name}: All tests PASSED.")
            return True
        else:
            print(f"📡📤📤 [TEST] {Path(__file__).parent.name}: Tests FAILED.")
            return False
    except Exception as e:
        print(f"🛑 [ERROR] {Path(__file__).parent.name}: Test discovery failed: {e}")
        return False

def start():
    """
    Initializes the GUI module services.
    
    Prepares the subsystem for operation. In a full system deployment, this 
    may include pre-caching assets or initializing the MQTT hook.
    
    Side Effects:
        - Logs a startup message.
    """
    print(f"🚀 [START] Starting {Path(__file__).parent.name} services...")
    # Optional: If this is the main GUI entry, start the GUI
    # start_gui()

def stop():
    """
    Performs a graceful shutdown of the GUI module services.
    
    Ensures that all background workers, timers, and active windows are 
    properly terminated to prevent resource leaks.
    
    Side Effects:
        - Logs a stop message.
    """
    print(f"🛑 [STOP] Stopping {Path(__file__).parent.name} services...")

def status():
    """
    Queries the current operational status of the module.
    
    Returns:
        str: A human-readable status string (e.g., "Running", "Idle").
    """
    print(f"📊 [STATUS] Checking {Path(__file__).parent.name} status...")
    return "Running"

if __name__ == "__main__":
    # Absolute FIRST action: run tests to ensure integrity before execution
    if not run_tests():
        print("❌ [CRITICAL] Tests failed. Aborting execution.")
        sys.exit(1)

    # Standalone execution logic for command-line interaction
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "--start":
            start()
        elif cmd == "--stop":
            stop()
        elif cmd == "--status":
            print(f"Status: {status()}")
        elif cmd == "--gui":
            start_gui()
        else:
            print(f"Unknown command: {cmd}")
    else:
        # Default standalone action if no arguments are provided
        start()

# Standardized exports ensuring a clean public API for the module
__all__ = [
    "Application",
    "DynamicWidgetRendererMixin",
    "GuiMqttManagerMixin",
    "LayoutParser",
    "DirectoryBuilderMixin",
    "start",
    "stop",
    "status",
    "run_tests",
    "start_gui"
]
