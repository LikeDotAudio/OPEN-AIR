# oaComProtocols.oaComMidi/Entry.py
#
# The sole orchestrator and public gatekeeper for the MIDI Communication Module.
#
# Author: Anthony Peter Kuzub (Original), Gemini CLI (Refactored)
# Blog: www.Like.audio (Contributor to this project)
#
# Version 20260413.2355.1 (Consolidated to Single Window with Tabs)

import sys
import os
import pathlib
import argparse
from pathlib import Path
import threading

# Ensure root directory is in the search path
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import tkinter as tk # GUI imports will be handled by the central manager or run conditionally
from tkinter import ttk
import time
from loguru import logger
from oaLogging.Methods.matrix_gate import matrix_log

# --- Core Components ---
# These managers will be instantiated and managed by the ComProtocolManager
# MidiManager, MIDIPortController, MIDIHardwareLock, MIDIProtocolMapper

_manager_instance = None

# Mock dependencies if not provided by the manager
class MockStateCache:
    def handle_external_update(self, *args, **kwargs): pass
    def shutdown(self): pass

class MockMqttConnectionManager:
    def connect_to_broker(self, *args, **kwargs): pass
    def disconnect(self): pass
    def subscribe(self, *args, **kwargs): pass
    def publish(self, *args, **kwargs): pass

class MockSubscriberRouter:
    def add_handler(self, *args, **kwargs): pass

def get_manager(**kwargs):
    """
    Singleton getter for the MIDI Manager.
    Dependencies (state_cache_manager, mqtt_connection_manager, etc.) should be passed via kwargs.
    If mqtt_connection_manager is not provided, MidiManager will manage its own internal connection.
    """
    global _manager_instance
    if _manager_instance is None:
        from oaComProtocols.oaComMidi.Managers.midi_manager import MidiManager
        
        # Provide default mock dependencies if not passed, for basic structure
        state_cache = kwargs.get("state_cache_manager", MockStateCache())
        # MIDI Manager now needs its own MQTT connection, not necessarily a shared one.
        # If it requires connection details, they should be passed or configured externally.
        # For self-containment, it will initialize its own MQTT connection if not provided.
        mqtt_conn = kwargs.get("mqtt_connection_manager", None) 
        sub_router = kwargs.get("subscriber_router", MockSubscriberRouter())
        run_bridge = kwargs.get("run_bridge", True)
        use_protocol_router = kwargs.get("use_protocol_router", True)
        enable_direct_mqtt = kwargs.get("enable_direct_mqtt", True)

        # If MQTT connection is not provided externally, MidiManager should handle its own connection internally.
        _manager_instance = MidiManager(
            state_cache_manager=state_cache,
            run_bridge=run_bridge,
            use_protocol_router=use_protocol_router,
            enable_direct_mqtt=enable_direct_mqtt
        )
        matrix_log("comms", "midi", "get_manager", "MIDI Manager initialized.", "DEBUG")
    else:
        # Update existing instance if new dependencies are provided
        for key, value in kwargs.items():
            if hasattr(_manager_instance, key):
                setattr(_manager_instance, key, value)
    return _manager_instance

def start(state_cache_manager=None, mqtt_connection_manager=None, subscriber_router=None, run_bridge=True, use_protocol_router=True, enable_direct_mqtt=True):
    """
    Starts the MIDI bridge service, accepting external dependencies.
    If mqtt_connection_manager is not provided, MidiManager should handle its own connection internally.
    """
    matrix_log("comms", "midi", "start", "🚀 [MIDI] Starting MIDI bridge service...", "INFO")
    manager = get_manager(
        state_cache_manager=state_cache_manager,
        mqtt_connection_manager=mqtt_connection_manager,
        subscriber_router=subscriber_router,
        run_bridge=run_bridge,
        use_protocol_router=use_protocol_router,
        enable_direct_mqtt=enable_direct_mqtt
    )
    manager.start()
    matrix_log("comms", "midi", "start", "MIDI Manager started.", "INFO")

def stop():
    """Stops the MIDI bridge service."""
    global _manager_instance
    if _manager_instance:
        _manager_instance.stop()
        _manager_instance = None # Allow re-initialization if needed
        matrix_log("comms", "midi", "stop", "MIDI Manager stopped.", "INFO")

def status():
    """Returns the current status of the MIDI bridge."""
    manager = get_manager() # Get instance, assume it exists if manager was ever used
    return manager.get_port_info()

# run_tests function remains useful for module-specific testing
def run_tests():
    """
    Discovers and runs all tests within the oaComProtocols.oaComMidi/Tests/ directory.
    """
    print("🔍 Discovering and running tests for oaComProtocols.oaComMidi...")
    test_dir = pathlib.Path(__file__).parent / "Tests"
    if not test_dir.is_dir():
        print("❌ No 'Tests/' directory found.")
        return True

    test_files = sorted([f for f in test_dir.glob("test_*.py")])
    if not test_files:
        print("❌ No test files found (expected pattern: test_*.py).")
        return True

    print(f"Found {len(test_files)} test files. Executing...")
    
    import subprocess
    
    all_tests_passed = True
    for test_file in test_files:
        print(f"\n--- Running: {test_file.name} ---")
        try:
            relative_test_file_path = test_file.relative_to(project_root)
            module_path_for_runner = str(relative_test_file_path).replace(os.sep, '.')[:-3]

            original_cwd = os.getcwd()
            os.chdir(project_root) 

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
    return all_tests_passed

# Standalone main() function is removed.
# def main(): ...

__all__ = [
    "MidiManager", "MIDIPortController", "MIDIHardwareLock", "MIDIProtocolMapper",
    "get_manager", "start", "stop", "status"
]
