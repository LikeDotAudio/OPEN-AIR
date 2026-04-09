# oaComProtocols.oaComMidi/Entry.py
#
# The sole orchestrator and public gatekeeper for the MIDI Communication Module.
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
# Version 20260328.1410.1

"""
import sys
import os
from pathlib import Path
oaComProtocols.oaComMidi/Entry.py - The sole orchestrator for the MIDI Communication Module.
"""

from .Managers.midi_manager import MidiManager
from .Core.midi_port_controller import MIDIPortController
from .Core.midi_hardware_lock import MIDIHardwareLock
from .Core.midi_protocol_mapper import MIDIProtocolMapper
from .Interface import MidiDashboard, MidiKeyboard, get_midi_color

_instance = None

def get_manager(state_cache_manager=None, run_bridge=True):
    global _instance
    if _instance is None:
        _instance = MidiManager(
            state_cache_manager=state_cache_manager, 
            run_bridge=run_bridge
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
        print("\n🎉 All tests for oaComProtocols.oaComMidi passed!")
    else:
        print("\n💔 Some tests for oaComProtocols.oaComMidi failed.")

if __name__ == "__main__":
    # If no arguments are provided, default to running tests.
    # Otherwise, assume specific commands are intended (e.g., start, stop, status).
    if len(sys.argv) > 1:
        print("Executing command...")
        # In a real application, you'd parse sys.argv and call the appropriate manager function.
        # For this task, we assume direct execution without specific arguments implies testing.
    else:
        run_tests()


__all__ = [
    "MidiManager",
    "MIDIPortController",
    "MIDIHardwareLock",
    "MIDIProtocolMapper",
    "MidiDashboard",
    "MidiKeyboard",
    "get_midi_color",
    "get_manager",
    "start",
    "stop",
    "status"
]
