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
# Version 20260413.2355.1 (Consolidated to Single Window with Tabs)

import sys
import os
import pathlib
import argparse
import threading
from pathlib import Path

# Ensure root directory is in the search path
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import tkinter as tk
from tkinter import ttk
import time
from loguru import logger
from oaLogging.Methods.matrix_gate import matrix_log

# --- OPTIONAL GUI EXPORTS (V3.2.1 Decoupling) ---
try:
    from oaComProtocols.oaComMidi.Interface import MidiDashboard, MidiOutputGenerator
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

class StandaloneState:
    """Mock state registry for pure standalone mode."""
    def handle_external_update(self, topic, value, source="MIDI", metadata=None):
        pass
    def shutdown(self):
        pass

def get_manager(state_cache_manager=None, run_bridge=True, use_protocol_router=True, enable_direct_mqtt=True):
    """
    Returns the singleton MIDI manager.
    """
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
    """Starts the MIDI bridge service."""
    manager = get_manager()
    manager.start()

def stop():
    """Stops the MIDI bridge service."""
    global _instance
    if _instance:
        _instance.stop()

def status():
    """Returns the current status of the MIDI bridge."""
    manager = get_manager()
    return manager.get_port_info()

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
        print(f"--- Running: {test_file.name} ---")
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
        print("🎉 All tests for oaComProtocols.oaComMidi passed!")
    else:
        print("💔 Some tests for oaComProtocols.oaComMidi failed.")
    return all_tests_passed

def main():
    """
    Standalone entry point for MIDI with GUI support.
    """
    # 1. Parse Arguments
    parser = argparse.ArgumentParser(description="OPEN-AIR MIDI Module Standalone")
    parser.add_argument("--pure", action="store_true", help="Run without MQTT or State Cache dependencies")
    parser.add_argument("--skip-tests", action="store_true", help="Skip pre-flight unit tests")
    args, unknown = parser.parse_known_args()

    # 2. Run Tests First
    if not args.skip_tests and not run_tests():
        print("🛑 Tests failed. Aborting GUI launch.")
        return

    # 3. Initialize Paths and Logging
    from oaLogging.Core.logger import initialize_logging, set_log_directory
    from oaOchestration.Core.path_initializer import initialize_paths, DATA_LOGS_DIR
    
    initialize_paths()
    set_log_directory(DATA_LOGS_DIR, partition="MIDI-STANDALONE")
    
    matrix_log("comms", "midi", "main", "🚀 [MIDI] Launching Standalone MIDI Module...", "INFO")

    # 4. Initialize Background Services
    mqtt_conn = None
    state_cache = None
    router = None
    
    if args.pure:
        print("🕊️  [MIDI] Running in PURE STANDALONE mode.")
        state_cache = StandaloneState()
    else:
        try:
            from oaComProtocols.oaComMQTT.Managers.mqtt_connection import MqttConnectionManager
            from oaStateCache.Core.state_cache import StateRegistry
            from oaComBroker.Core.protocol_router.manager import ProtocolRouter

            router = ProtocolRouter.get_instance()
            mqtt_conn = MqttConnectionManager()
            state_cache = StateRegistry(mqtt_conn)
            
            router.set_state_cache(state_cache)
            router.set_mqtt_manager(mqtt_conn)
            
            mqtt_conn.connect_to_broker(on_message_callback=state_cache.handle_incoming_mqtt)
            mqtt_conn.subscribe("OPEN-AIR/MIDI/#")
            router.start()
        except ImportError:
            print("⚠️ System mode requested but dependencies missing. Falling back to PURE.")
            state_cache = StandaloneState()

    # 5. Start MIDI Manager
    # If in PURE mode, enable_direct_mqtt=True will use the internal MidiMqttWorker
    manager = get_manager(
        state_cache_manager=state_cache, 
        run_bridge=True, 
        use_protocol_router=(not args.pure), 
        enable_direct_mqtt=True
    )
    if router:
        router.set_snmp_manager(manager) # Standard pattern
    manager.start()
    
    # 6. Launch GUI
    if GUI_AVAILABLE:
        try:
            root = tk.Tk()
            root.title(f"OPEN-AIR | MIDI Controller ({'PURE' if args.pure else 'SYSTEM'} mode)")
            root.geometry("1100x850")
            root.configure(bg="#2b2b2b")
            
            style = ttk.Style()
            style.theme_use('clam')
            style.configure("TNotebook", background="#2b2b2b", borderwidth=0)
            style.configure("TNotebook.Tab", background="#3c3f41", foreground="#ffffff", padding=[15, 5])
            style.map("TNotebook.Tab", background=[("selected", "#4b6eaf")])

            notebook = ttk.Notebook(root)
            notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            def on_closing():
                root.quit()
                root.destroy()
            root.protocol("WM_DELETE_WINDOW", on_closing)
            
            # Tab 1: Input
            tab1 = tk.Frame(notebook, bg="#2b2b2b")
            notebook.add(tab1, text=" 🎹 MIDI INPUT ")
            input_view = MidiDashboard(tab1, midi_manager=manager, config={"app_instance": root})
            input_view.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            # Tab 2: Output
            tab2 = tk.Frame(notebook, bg="#2b2b2b")
            notebook.add(tab2, text=" 📤 MIDI OUTPUT ")
            output_view = MidiOutputGenerator(tab2, midi_manager=manager)
            output_view.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            print(f"✅ [MIDI] Standalone GUI deployed.")
            root.mainloop()

        except KeyboardInterrupt:
            pass
        finally:
            manager.stop()
            if router: router.stop()
            if mqtt_conn: mqtt_conn.disconnect()
            state_cache.shutdown()
            print("🏁 [MIDI] Standalone shutdown complete.")
    else:
        print("❌ GUI components not available. Shutdown.")
        manager.stop()

if __name__ == "__main__":
    main()

__all__ = [
    "MidiManager",
    "MIDIPortController",
    "MIDIHardwareLock",
    "MIDIProtocolMapper",
    "MidiMqttTransport",
    "MidiDashboard",
    "get_midi_color",
    "get_manager",
    "start",
    "stop",
    "status"
]
"get_manager",
    "start",
    "stop",
    "status"
]
