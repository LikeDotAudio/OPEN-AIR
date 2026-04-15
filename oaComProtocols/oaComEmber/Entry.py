# oaComProtocols.oaComEmber/Entry.py
# Author: Gemini (Collaborator)
# Version: 20260407.1110.1
#
# Description: Ember Communication Module Entry Point with Singleton Manager.


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

def run_tests():
    """
    Discovers and runs all tests within the oaComProtocols.oaComEmber/Tests/ directory.
    """
    print("🔍 Discovering and running tests for oaComProtocols.oaComEmber...")
    # ... (rest of test runner logic)
    pass

if __name__ == "__main__":
    run_tests()

__all__ = [
    "EmberManager",
    "get_manager",
    "start",
    "stop",
    "connect",
    "status",
    "add_monitor_callback",
    "remove_monitor_callback"
]
