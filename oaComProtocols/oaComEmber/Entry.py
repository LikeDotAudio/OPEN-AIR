# oaComEmber/Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260415.2150.1
#
# Description: Gatekeeper for the oaComEmber module.

import os
import subprocess
from pathlib import Path

"""
import sys
oaComProtocols.oaComEmber/Entry.py - The sole orchestrator for the Ember Communication Module.

Purpose:
This file is the public entry point for 'oaComProtocols.oaComEmber'. It manages the
singleton EmberManager and exposes high-level methods for control and interaction.
"""

# Placeholder for actual manager - would normally import from .Managers.ember_manager
class EmberManager:
    def __init__(self, mqtt_connection_manager=None, state_cache_manager=None):
        self.mqtt_connection_manager = mqtt_connection_manager
        self.state_cache_manager = state_cache_manager
        self.running = False
        self.target_ip = None
        self.target_port = None
        self._callbacks = []

    def start(self):
        self.running = True
        print("🚀 [EMBER] EmberManager started.")

    def stop(self):
        self.running = False
        print("🛑 [EMBER] EmberManager stopped.")

    def connect(self, ip, port):
        self.target_ip = ip
        self.target_port = port
        print(f"🔗 [EMBER] Connecting to {ip}:{port}...")
        self.running = True # Assume success for now

    def get_status(self):
        return {
            "running": self.running,
            "connection": f"{self.target_ip}:{self.target_port}" if self.target_ip else "DISCONNECTED",
            "nodes_discovered": 0
        }

    def add_monitor_callback(self, callback):
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def remove_monitor_callback(self, callback):
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def _trigger_callbacks(self, direction, path, value, node_type=None):
        for cb in self._callbacks:
            try:
                cb(direction, path, value, node_type)
            except Exception as e:
                print(f"❌ [EMBER] Callback error: {e}")

_instance = None

def get_manager(mqtt_connection_manager=None):
    """
    Returns the singleton EmberManager instance.
    """
    global _instance
    if _instance is None:
        _instance = EmberManager(
            mqtt_connection_manager=mqtt_connection_manager
        )
    return _instance

def start():
    """Starts the Ember+ services."""
    get_manager().start()

def stop():
    """Stops the Ember+ services."""
    get_manager().stop()

def connect(ip, port):
    """Connects to an Ember+ provider."""
    get_manager().connect(ip, port)

def status():
    """Returns the current status of the Ember+ bridge."""
    return get_manager().get_status()

def add_monitor_callback(callback):
    """Registers a callback for Ember+ activity monitoring."""
    get_manager().add_monitor_callback(callback)

def remove_monitor_callback(callback):
    """Unregisters a monitoring callback."""
    get_manager().remove_monitor_callback(callback)

__all__ = [
    "EmberManager",
    "get_manager",
    "start",
    "stop",
    "connect",
    "status",
    "add_monitor_callback",
    "remove_monitor_callback",
    "run_tests",
]

def run_tests():
    """
    Discover and run tests in the local Tests/ directory using unittest via subprocess.
    Ensures isolation and proper sys.path handling.
    """
    import subprocess
    import sys
    import os
    from pathlib import Path

    print(f"📡📥📥 [TEST] {Path(__file__).parent.name}: Starting automated test discovery...")
    current_dir = Path(__file__).parent.absolute()
    test_dir = current_dir / "Tests"
    
    if not test_dir.exists():
        return True

    project_root = current_dir
    while project_root.parent != project_root:
        if (project_root / "GEMINI.md").exists():
            break
        project_root = project_root.parent
    
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
        elif cmd == "--stop":
            stop()
        elif cmd == "--status":
            print(f"Status: {status()}")
        else:
            print(f"Unknown command: {cmd}")
    else:
        # Default standalone action if no args
        start()

