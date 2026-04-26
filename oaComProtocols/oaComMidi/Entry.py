# oaComMidi/Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260415.2245.1
#
# Description: Gatekeeper for the oaComMidi module.
# Manages the lifecycle of the MIDI bridge service.

import os
import pathlib
import subprocess
import sys
import time
from pathlib import Path

# Ensure root directory is in the search path
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir
while project_root.parent != project_root:
    if (project_root / "GEMINI.md").exists():
        break
    project_root = project_root.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from oaLogging.Methods.matrix_gate import matrix_log

# --- Core Components ---
# These managers will be instantiated and managed by the ComProtocolManager

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
    """
    global _manager_instance
    if _manager_instance is None:
        from oaComProtocols.oaComMidi.Managers.midi_manager import MidiManager

        state_cache = kwargs.get("state_cache_manager", MockStateCache())
        mqtt_conn = kwargs.get("mqtt_connection_manager", None)
        sub_router = kwargs.get("subscriber_router", MockSubscriberRouter())
        run_bridge = kwargs.get("run_bridge", True)
        use_protocol_router = kwargs.get("use_protocol_router", True)
        enable_direct_mqtt = kwargs.get("enable_direct_mqtt", True)

        _manager_instance = MidiManager(
            state_cache_manager=state_cache,
            run_bridge=run_bridge,
            use_protocol_router=use_protocol_router,
            enable_direct_mqtt=enable_direct_mqtt
        )
        matrix_log("comms", "midi", "get_manager", "MIDI Manager initialized.", "DEBUG")
    return _manager_instance

def start(state_cache_manager=None, mqtt_connection_manager=None, subscriber_router=None, run_bridge=True, use_protocol_router=True, enable_direct_mqtt=True):
    """
    Starts the MIDI bridge service, accepting external dependencies.
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
    return manager

def stop():
    """Stops the MIDI bridge service."""
    global _manager_instance
    if _manager_instance:
        matrix_log("comms", "midi", "stop", "🛑 [MIDI] Stopping MIDI bridge service...", "INFO")
        _manager_instance.stop()
        _manager_instance = None
        matrix_log("comms", "midi", "stop", "MIDI Manager stopped.", "INFO")

def status():
    """Returns the current status of the MIDI bridge."""
    manager = get_manager()
    if manager:
        return manager.get_port_info()
    return "stopped"

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
        if result.returncode == 0:
            print(f"📡📤📤 [TEST] {Path(__file__).parent.name}: All tests PASSED.")
            return True
        else:
            print(f"📡📤📤 [TEST] {Path(__file__).parent.name}: Tests FAILED.")
            return False
    except Exception as e:
        print(f"🛑 [ERROR] {Path(__file__).parent.name}: Test discovery failed: {e}")
        return False

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
                while True:
                    time.sleep(1)
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
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            stop()

    "start",
    "stop",
    "status",
    "run_tests",
__all__ = ["get_manager", "start", "stop", "status", "run_tests"]
