# oaComProtocols.oaComMidi/Entry.py
#
# The sole orchestrator and public gatekeeper for the MIDI Communication Module.
#
# Author: Anthony Peter Kuzub (Original), Gemini CLI (Refactored)
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260411.1515.2 (Refactored for Dual Windows)

import sys
import os
from pathlib import Path

# --- PROJECT ROOT INITIALIZATION ---
# This allows running the module directly as a script from within its own directory.
# It ensures that 'oaLogging', 'oaComBroker', etc., are found in sys.path.
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import tkinter as tk # Added for GUI
import time # Added for standalone mode loop
from loguru import logger # Added for logging in Application class
from oaLogging.Methods.matrix_gate import matrix_log # Added for logging

# --- OPTIONAL GUI EXPORTS (V3.2.1 Decoupling) ---
try:
    # Import necessary GUI components for the Application class
    from oaComProtocols.oaComMidi.Interface import MidiDashboard, MidiOutputGenerator
    # MidiKeyboard, get_midi_color might still be needed by the views themselves
    from oaComProtocols.oaComMidi.Interface.Input.midi_keyboard import MidiKeyboard, get_midi_color
    GUI_AVAILABLE = True
except (ImportError, Exception) as e:
    logger.error(f"GUI components not available: {e}")
    MidiDashboard = None
    MidiOutputGenerator = None
    MidiKeyboard = None
    get_midi_color = None
    GUI_AVAILABLE = False

from oaComProtocols.oaComMidi.Managers.midi_manager import MidiManager
from oaComProtocols.oaComMidi.Core.midi_port_controller import MIDIPortController
from oaComProtocols.oaComMidi.Core.midi_hardware_lock import MIDIHardwareLock
from oaComProtocols.oaComMidi.Core.midi_protocol_mapper import MIDIProtocolMapper

_instance = None

def get_manager(state_cache_manager=None, run_bridge=True, use_protocol_router=True, enable_direct_mqtt=True):
    global _instance
    if _instance is None:
        _instance = MidiManager(
            state_cache_manager=state_cache_manager, 
            run_bridge=run_bridge,
            use_protocol_router=use_protocol_router,
            enable_direct_mqtt=enable_direct_mqtt
        )
    return _instance

def start():
    manager = get_manager()
    manager.start()

def stop():
    manager = get_manager()
    manager.stop()

def status():
    manager = get_manager()
    return manager.get_port_info()

def run_tests():
    """
    Discovers and runs all tests within the oaComProtocols.oaComMidi/Tests/ directory.
    """
    print("🔍 Discovering and running tests for oaComProtocols.oaComMidi...")
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
        print(f"--- Running: {test_file.name} ---")
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
        print("🎉 All tests for oaComProtocols.oaComMidi passed!")
    else:
        print("💔 Some tests for oaComProtocols.oaComMidi failed.")
    return all_tests_passed

# --- Dual Window Application Structure ---

class OutputWindow(tk.Toplevel):
    """Separate window for MIDI Output controls."""
    def __init__(self, master, midi_manager):
        super().__init__(master)
        self.title("OPEN-AIR MIDI Output Generator")
        self.geometry("900x700") # Larger default size, no fixed offset
        self.configure(bg="#2b2b2b")
        self.midi_manager = midi_manager
        
        # Ensure it stays on top initially or at least is visible
        self.lift()
        self.focus_force()
        
        self.output_view = MidiOutputGenerator(self, midi_manager=self.midi_manager)
        self.output_view.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Refresh ports multiple times to ensure hardware is caught
        self.after(500, self.output_view._refresh_ports)
        self.after(2000, self.output_view._refresh_ports)

class StandaloneMidiApp(tk.Tk):
    """Main MIDI Controller window (Input View)."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title("OPEN-AIR MIDI Controller (Input)")
        self.geometry("1000x800") # Larger default size
        self.configure(bg="#2b2b2b")

        # Master Hardware Controller (Disconnected from ProtocolRouter)
        # enable_direct_mqtt=True ensures it broadcasts to MQTT directly
        self.midi_manager = get_manager(state_cache_manager=None, run_bridge=True, use_protocol_router=False, enable_direct_mqtt=True)
        self.midi_manager.start()

        # Instantiate Input View in the main window
        self.input_view = MidiDashboard(self, midi_manager=self.midi_manager, config={"app_instance": self})
        self.input_view.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Launch the Output Window after a short delay to ensure root is mapped
        self.output_window = None
        self.after(100, self._launch_output_window)
        
        # Initial UI refresh for input view
        self.after(500, self.input_view._refresh_ui)
        self.after(2000, self.input_view._refresh_ui)

        # Ensure manager is stopped when main window is closed
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _launch_output_window(self):
        """Creates the secondary Toplevel window."""
        logger.info("🎹 [MIDI-ENTRY] Launching Output Window...")
        self.output_window = OutputWindow(self, self.midi_manager)

    def on_closing(self):
        """Handles cleanup when the application window is closed."""
        if self.midi_manager:
            logger.info("Stopping MIDI manager before closing application.")
            self.midi_manager.stop()
        self.destroy()

# --- End of Dual Window Application Structure ---

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "run-gui":
            if GUI_AVAILABLE:
                app = StandaloneMidiApp() 
                app.mainloop()
            else:
                print("GUI components are not available.")
        elif command == "start-standalone":
            manager = get_manager(state_cache_manager=None, run_bridge=True)
            manager.start()
            try:
                while True: time.sleep(1)
            except KeyboardInterrupt:
                manager.stop()
        elif command == "status":
            print(status())
        else:
            print(f"Unknown command: {command}")
    else:
        tests_passed = run_tests()
        if tests_passed and GUI_AVAILABLE: 
            app = StandaloneMidiApp() 
            app.mainloop()
        elif GUI_AVAILABLE:
            print("Tests failed. GUI not launched.")

__all__ = [
    "MidiManager",
    "MIDIPortController",
    "MIDIHardwareLock",
    "MIDIProtocolMapper",
    "MidiDashboard",
    "get_midi_color",
    "get_manager",
    "start",
    "stop",
    "status"
]
