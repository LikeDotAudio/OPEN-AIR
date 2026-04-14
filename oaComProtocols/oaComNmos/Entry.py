# FolderName/FileName.py
# Author: Gemini (Collaborator)
# Version: 20260414.0010.1 (Fixed stop NameError and Shutdown flow)

import sys
import argparse
import signal
import threading
import socket
import time
import subprocess
import os
import pathlib

# Ensure root directory is in the search path
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Standard OPEN-AIR Imports
from oaLogging.Methods.matrix_gate import matrix_log
from oaConfigurationManager.FileReaders.config_reader import Config

# Local module imports
from oaComProtocols.oaComNmos.Core.event_bus import nmos_event_bus
from oaComProtocols.oaComNmos.Core.nmos_builder import build_node, build_device
from oaComProtocols.oaComNmos.Constants import settings
from oaComProtocols.oaComNmos.Managers import registration_manager
from oaComProtocols.oaComNmos.Workers.sap_listener_worker import sap_listener_worker, heartbeat_worker
from oaComProtocols.oaComNmos.Interface import connection_api
from oaComProtocols.oaComNmos.IS07.transports import Is07Bridge
from oaComProtocols.oaComNmos.Core.utils import gen_id, get_ip

# --- Global State Management ---
global_state = {
    "NODE_ID": None,
    "DEVICE_ID": None,
    "NODE": {},
    "DEVICE": {},
    "SOURCES": {},
    "FLOWS": {},
    "SENDERS": {},
    "STREAMS": {},
    "REGISTRAR_URL": "http://localhost:4000",
    "RUNNING": False,
    "BRIDGE": None
}

class NmosBridgeManager:
    """
    Orchestrates NMOS MQTT and IS-07 bridging.
    ⚡ SELF-CONTAINED: Uses internal Is07Bridge transports for all monitoring.
    """
    def __init__(self, registrar_url):
        self.bridge = Is07Bridge(registrar_url)
        self.is_running = False
        
    def start(self):
        if self.is_running: return
        self.is_running = True
        
        # ⚡ SELF-CONTAINED CONNECTION: Using internal paho-based transport
        connection_params_mqtt = {
            "destination_host": "localhost",
            "destination_port": 1883,
            "broker_protocol": "mqtt"
        }
        connection_params_ws = {
            "connection_uri": f"ws://localhost:{settings.PORT}/is07",
            "reconnect": True
        }
        
        # Register a local handler for general MQTT monitoring
        self.bridge.set_message_handler(self._on_internal_transport_message)
        
        # Connect internal transports
        self.bridge.initialize_transports(connection_params_mqtt, connection_params_ws)
        
        # ⚡ DIRECT SUBSCRIPTION: Monitor the entire namespace using internal transport
        self.bridge.subscribe_to_events("OPEN-AIR/#", transport_type="mqtt")
        
        print("✅ [NMOS] IS-07 Bridge transports active (Internal MQTT).")

    def stop(self):
        self.is_running = False
        self.bridge.shutdown()

    def _on_internal_transport_message(self, transport_type, topic, payload):
        """Unified callback from internal Is07Bridge transports."""
        if not self.is_running: return
        
        # ⚡ MONITORING: If it's MQTT traffic, broadcast to GUI
        if transport_type == "mqtt" and topic:
            if "NMOS" in topic.upper(): return # Loop prevention
            nmos_event_bus.publish("NMOS_EVENT", transport="MQTT", etype="STATE_CHANGE", eid=topic, payload=payload)
        else:
            # Handle standard IS-07 events (e.g., from WebSocket or specific IS-07 MQTT topics)
            nmos_event_bus.publish("NMOS_EVENT", transport=transport_type.upper(), etype="IS07_EVENT", eid="IS-07", payload=payload)

def start(registrar_url=None):
    """Standardized start command for NMOS bridge."""
    if global_state["RUNNING"]: return
    
    if registrar_url:
        global_state["REGISTRAR_URL"] = registrar_url
        
    global_state["RUNNING"] = True
    host_ip = get_ip()
    global_state["NODE_ID"] = gen_id()
    global_state["DEVICE_ID"] = gen_id()
    
    global_state["NODE"] = build_node(global_state["NODE_ID"], host_ip, settings.PORT)
    global_state["DEVICE"] = build_device(global_state["DEVICE_ID"], global_state["NODE_ID"], host_ip, settings.PORT)

    registration_manager.register_all_resources(
        global_state["REGISTRAR_URL"],
        global_state["NODE"],
        global_state["DEVICE"],
        global_state["SOURCES"],
        global_state["FLOWS"],
        global_state["SENDERS"]
    )

    # Start Workers
    threading.Thread(target=sap_listener_worker, args=(global_state["REGISTRAR_URL"], global_state["NODE_ID"], global_state["DEVICE_ID"], host_ip, global_state, registration_manager), daemon=True).start()
    threading.Thread(target=heartbeat_worker, args=(global_state["REGISTRAR_URL"], global_state["NODE_ID"], global_state, registration_manager), daemon=True).start()

    # Start API Server
    connection_api.STATE["NODE"] = global_state["NODE"]
    connection_api.STATE["DEVICE"] = global_state["DEVICE"]
    connection_api.STATE["SOURCES"] = global_state["SOURCES"]
    connection_api.STATE["FLOWS"] = global_state["FLOWS"]
    connection_api.STATE["SENDERS"] = global_state["SENDERS"]
    connection_api.STATE["STREAMS"] = global_state["STREAMS"]

    threading.Thread(target=connection_api.run_server, kwargs={"host": "0.0.0.0", "port": settings.PORT}, daemon=True).start()
    print(f"🚀 [NMOS] NMOS Bridge & API Server active on {host_ip}:{settings.PORT}")
    print(f"🔌 [NMOS] IS-07 WebSocket available at ws://{host_ip}:{settings.PORT}/is07")

def stop():
    """Stops the NMOS bridge and API server."""
    global_state["RUNNING"] = False
    if global_state["BRIDGE"]:
        global_state["BRIDGE"].stop()

def status():
    """Returns the current status of the NMOS bridge."""
    return {
        "running": global_state["RUNNING"],
        "node_id": global_state["NODE_ID"],
        "registrar": global_state["REGISTRAR_URL"]
    }

def run_tests():
    """
    Discovers and runs all tests within the oaComProtocols.oaComNmos/Tests/ directory.
    """
    print("🔍 Discovering and running tests for oaComProtocols.oaComNmos...")
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
            # Get the module path relative to the project root for the test runner
            relative_test_file_path = test_file.relative_to(project_root)
            module_path_for_runner = str(relative_test_file_path).replace(os.sep, '.')[:-3]

            # Ensure the current directory is the project root so Python can find modules
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
        print("🎉 All tests for oaComProtocols.oaComNmos passed!")
    else:
        print("💔 Some tests for oaComProtocols.oaComNmos failed.")
    return all_tests_passed

def main():
    """Standalone entry point for NMOS with GUI support."""
    from oaLogging.Core.logger import initialize_logging, set_log_directory
    from oaOchestration.Core.path_initializer import initialize_paths
    
    initialize_paths()
    set_log_directory(os.path.join(os.getcwd(), "oaDataLogs"), partition="NMOS")
    
    matrix_log("comms", "nmos", "main", "🚀 [NMOS] Launching Standalone NMOS Module...", "INFO")
    
    # 1. Start NMOS Core & Bridge (Internal MQTT)
    start()
    global_state["BRIDGE"] = NmosBridgeManager(global_state["REGISTRAR_URL"])
    
    # 2. Launch Consolidated GUI
    try:
        import tkinter as tk
        from tkinter import ttk
        from oaComProtocols.oaComNmos.Interface import (
            NmosCommandsMonitorImplementation,
            NmosConnectionMonitorImplementation,
            NmosWebsocketManagerImplementation
        )

        root = tk.Tk()
        root.title("OPEN-AIR NMOS Controller")
        root.geometry("1100x850")
        root.configure(bg="#2b2b2b")
        
        def on_closing():
            stop()
            root.quit()
            root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # ⚡ TABBED INTERFACE STYLE
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook", background="#2b2b2b", borderwidth=0)
        style.configure("TNotebook.Tab", background="#3c3f41", foreground="#ffffff", padding=[15, 5])
        style.map("TNotebook.Tab", background=[("selected", "#4b6eaf")])

        notebook = ttk.Notebook(root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        config = {
            "global_state": global_state,
            "mqtt_connection_manager": None,
            "subscriber_router": None,
            "state_cache": None
        }

        # Tab 1: Registration Status
        conn_tab = tk.Frame(notebook, bg="#2b2b2b")
        notebook.add(conn_tab, text=" 📡 REGISTRATION ")
        conn_gui = NmosConnectionMonitorImplementation(conn_tab, config=config)
        conn_gui.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 2: Commands & Events
        cmd_tab = tk.Frame(notebook, bg="#2b2b2b")
        notebook.add(cmd_tab, text=" 📝 COMMANDS & EVENTS ")
        cmd_gui = NmosCommandsMonitorImplementation(cmd_tab, config=config)
        cmd_gui.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 3: WebSocket Manager
        ws_tab = tk.Frame(notebook, bg="#2b2b2b")
        notebook.add(ws_tab, text=" 🔌 WEBSOCKET ")
        ws_gui = NmosWebsocketManagerImplementation(ws_tab, config=config)
        ws_gui.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        print("✅ [NMOS] Consolidated GUI deployed.")
        
        # 3. Start Bridge Transports AFTER GUI is ready
        global_state["BRIDGE"].start()
        
        root.mainloop()

    except KeyboardInterrupt:
        pass
    finally:
        stop()

if __name__ == "__main__":
    if "run-tests-only" in sys.argv:
        run_tests()
    else:
        # ⚡ PRE-FLIGHT CHECK: Run all tests before launching standalone
        if run_tests():
            main()
        else:
            print("🚫 Standalone launch aborted due to test failures.")

__all__ = ["start", "stop", "status", "main", "run_tests", "global_state", "Is07MqttTransport", "Is07WebSocketTransport"]
op", "status", "main", "run_tests", "global_state"]
