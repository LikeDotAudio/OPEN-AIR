# oaComProtocols.oaComREST/Entry.py
#
# Public entry point for the REST API module. Orchestrates the lifecycle 
# of the REST manager and exposes the public monitoring API.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Version 20260414.0020.1 (Refactored for TRUE STANDALONE - Zero External Dependencies)

import sys
import os
import pathlib
import argparse
import threading
import time
from pathlib import Path
from loguru import logger

# Ensure root directory is in the search path
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from oaComProtocols.oaComREST.Managers.rest_manager import RESTManager
from oaComProtocols.oaComREST.Core.rest_mqtt_transport import RestMqttTransport
from oaComProtocols.oaComREST.Constants.rest_constants import LOCAL_DEBUG
from oaLogging.Methods.matrix_gate import matrix_log

_manager = None

class MinimalStateRegistry:
    """
    A ultra-lightweight, zero-dependency state registry for standalone mode.
    Replaces StateRegistry and rust_cache when MQTT is disabled.
    """
    def __init__(self):
        self._state = {}
        self.rust_cache = type('RustCache', (), {
            'keys': lambda: self._state.keys(),
            'to_dict': lambda: dict(self._state)
        })()

    def handle_external_update(self, topic, value, source="REST", metadata=None):
        self._state[topic] = value
        
    def get_cached_value(self, topic):
        return self._state.get(topic)
        
    def check_prefix_exists(self, prefix):
        if not prefix.endswith('/'): prefix += '/'
        return any(k.startswith(prefix) for k in self._state.keys())

    def shutdown(self):
        self._state.clear()

class MinimalProtocolRouter:
    """Mock router for standalone REST operation."""
    def ingest(self, transport_source, topic, value):
        matrix_log("comms", "rest", "ingest", f"Standalone Ingest: {topic} = {value}", "DEBUG")
    def stop(self): pass

def get_manager(state_cache_manager=None, protocol_router=None):
    """
    Singleton accessor for the RESTManager.
    """
    global _manager
    if _manager is None:
        matrix_log("comms", "rest", "get_manager", "📡⚙️🔗 [REST] Creating singleton RESTManager instance.", "DEBUG")
        _manager = RESTManager(state_cache_manager, protocol_router)
    else:
        if state_cache_manager: _manager.state_cache = state_cache_manager
        if protocol_router: _manager.router = protocol_router
            
    return _manager

def start(state_cache_manager=None, protocol_router=None):
    """Ensures the REST service is running."""
    return get_manager(state_cache_manager, protocol_router).start()

def stop():
    """Signals the REST service to shut down."""
    global _manager
    if _manager:
        _manager.stop()

def get_status():
    """Convenience function to get the current REST service status."""
    if _manager: return _manager.get_status()
    from oaComProtocols.oaComREST.Constants.rest_constants import REST_BIND_HOST, REST_PORT
    return {"running": False, "initialized": False, "host": REST_BIND_HOST, "port": REST_PORT, "routes": []}

def add_monitor_callback(callback):
    if _manager: _manager.add_monitor_callback(callback)

def remove_monitor_callback(callback):
    if _manager: _manager.remove_monitor_callback(callback)

def run_tests():
    """Standalone unit test runner."""
    print("🔍 Discovering and running tests for oaComProtocols.oaComREST...")
    test_dir = pathlib.Path(__file__).parent / "Tests"
    if not test_dir.is_dir(): return True
    test_files = sorted([f for f in test_dir.glob("test_*.py")])
    if not test_files: return True

    import subprocess
    all_tests_passed = True
    for test_file in test_files:
        print(f"--- Running: {test_file.name} ---")
        try:
            module_path = str(test_file.relative_to(project_root)).replace(os.sep, '.')[:-3]
            original_cwd = os.getcwd()
            os.chdir(project_root) 
            result = subprocess.run([sys.executable, "-m", "unittest", module_path], capture_output=True, text=True)
            print(result.stdout)
            if result.stderr: print(result.stderr)
            if result.returncode != 0: all_tests_passed = False
        except Exception as e:
            print(f"❌ Error: {e}")
            all_tests_passed = False
        finally: os.chdir(original_cwd)
    return all_tests_passed

def main():
    parser = argparse.ArgumentParser(description="OPEN-AIR REST Module Standalone")
    parser.add_argument("--pure", action="store_true", help="Run without MQTT or State Cache dependencies")
    parser.add_argument("--skip-tests", action="store_true", help="Skip pre-flight unit tests")
    args, unknown = parser.parse_known_args()

    if not args.skip_tests and not run_tests():
        print("🛑 Tests failed. Aborting launch.")
        return

    from oaLogging.Core.logger import initialize_logging, set_log_directory
    from oaOchestration.Core.path_initializer import initialize_paths, DATA_LOGS_DIR
    initialize_paths()
    set_log_directory(DATA_LOGS_DIR, partition="REST-STANDALONE")
    
    mqtt_conn = None
    state_cache = None
    router = None
    
    if args.pure:
        # ⚡ PURE STANDALONE: Zero dependencies on external modules
        print("🕊️  [REST] Running in PURE STANDALONE mode (No MQTT/Global State).")
        state_cache = MinimalStateRegistry()
        router = MinimalProtocolRouter()
    else:
        # SYSTEM MODE: Use standard OPEN-AIR infrastructure
        try:
            from oaComProtocols.oaComMQTT.Managers.mqtt_connection import MqttConnectionManager
            from oaStateCache.Core.state_cache import StateRegistry
            # from oaComBroker.Core.protocol_router.manager import ProtocolRouter
            
            router = MinimalProtocolRouter() # ProtocolRouter.get_instance()
            mqtt_conn = MqttConnectionManager()
            state_cache = StateRegistry(mqtt_conn)
            router.set_state_cache(state_cache)
            router.set_mqtt_manager(mqtt_conn)
            
            mqtt_conn.connect_to_broker(on_message_callback=state_cache.handle_incoming_mqtt)
            mqtt_conn.subscribe("#")
            router.start()
        except ImportError as e:
            print(f"⚠️ [REST] System mode requested but dependencies missing ({e}). Falling back to PURE.")
            state_cache = MinimalStateRegistry()
            router = MinimalProtocolRouter()

    # Start REST Manager
    manager = get_manager(state_cache_manager=state_cache, protocol_router=router)
    manager.start()
    
    # Launch GUI
    try:
        import tkinter as tk
        from tkinter import ttk
        from oaComProtocols.oaComREST.Interface.gui_REST import RestDashboard
        from oaComProtocols.oaComREST.Interface.gui_REST_tree import RestTreeImplementation

        root = tk.Tk()
        root.title(f"OPEN-AIR | REST Hub ({'PURE' if args.pure else 'SYSTEM'} MODE)")
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
        
        tab1 = tk.Frame(notebook, bg="#2b2b2b")
        notebook.add(tab1, text=" 🌍 REST DASHBOARD ")
        RestDashboard(tab1, config={"state_cache_manager": state_cache, "protocol_router": router}).pack(fill=tk.BOTH, expand=True)

        tab2 = tk.Frame(notebook, bg="#2b2b2b")
        notebook.add(tab2, text=" 🌲 API TREE ")
        RestTreeImplementation(tab2, config={"state_cache_manager": state_cache, "protocol_router": router}).pack(fill=tk.BOTH, expand=True)

        print(f"✅ [REST] Standalone GUI active.")
        root.mainloop()

    except KeyboardInterrupt: pass
    except Exception as e:
        print(f"❌ [REST] Error: {e}")
        import traceback; traceback.print_exc()
    finally:
        manager.stop()
        if hasattr(router, 'stop'): router.stop()
        if mqtt_conn: mqtt_conn.disconnect()
        if hasattr(state_cache, 'shutdown'): state_cache.shutdown()
        print("🏁 [REST] Standalone shutdown complete.")

if __name__ == "__main__":
    main()

__all__ = ["RESTManager", "RestMqttTransport", "get_manager", "start", "stop", "get_status", "run_tests", "main"]
