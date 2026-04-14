# oaComProtocols.oaComSNMP/Entry.py
# ⚡ STANDALONE: 100% independent SNMP Orchestrator.
# No dependencies on ProtocolRouter, StateCache, or shared MQTT Managers.

import sys
import os
from pathlib import Path
import pathlib
import threading
import time

# Ensure the root directory is in the search path
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from oaLogging.Methods.matrix_gate import matrix_log
from oaComProtocols.oaComSNMP.Managers.snmp_manager import SNMPManager, BridgeContext
from oaComProtocols.oaComSNMP.Core.snmp_mqtt_client import SnmpMqttClient

_instance = None

def get_manager(run_bridge=None):
    """
    Singleton getter for the SNMP Manager.
    """
    global _instance
    
    if run_bridge is None:
        try:
            from oaConfigurationManager.Core.identity import IdentityManager
            ident = IdentityManager.initialize()
            partition = ident.get("PARTITION_ID", "STANDALONE")
            run_bridge = (partition in ["CORE", "STANDALONE"])
        except:
            run_bridge = True

    if _instance is None:
        # ⚡ NATIVE MQTT CLIENT
        mqtt_client = SnmpMqttClient(client_id=f"SNMP-Standalone-{'Bridge' if run_bridge else 'Observer'}")
        
        context = BridgeContext(mqtt_client=mqtt_client)
        _instance = SNMPManager.create(context, run_bridge)
        
    return _instance

def start():
    """Starts the SNMP bridge service."""
    manager = get_manager()
    if manager.context.mqtt_client:
        manager.context.mqtt_client.connect()
    manager.start()

def stop():
    """Stops the SNMP bridge service."""
    manager = get_manager()
    manager.stop()
    if manager.context.mqtt_client:
        manager.context.mqtt_client.disconnect()

def status():
    """Returns the current status of the SNMP bridge."""
    manager = get_manager()
    return manager.get_status()

def run_tests():
    print("🔍 Discovering and running tests for oaComProtocols.oaComSNMP...")
    test_dir = Path(__file__).parent / "Tests"
    if not test_dir.is_dir(): return

    import subprocess
    test_files = sorted([f for f in test_dir.glob("test_*.py")])
    for test_file in test_files:
        print(f"\n--- Running: {test_file.name} ---")
        try:
            relative_path = test_file.relative_to(project_root)
            module_path = str(relative_path).replace(os.sep, '.')[:-3]
            subprocess.run([sys.executable, "-m", "unittest", module_path], check=False)
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Standalone entry point."""
    run_tests()
    
    from oaOchestration.Core.path_initializer import initialize_paths
    initialize_paths()
    
    matrix_log("comms", "snmp", "main", "🚀 [SNMP] Launching 100% Standalone SNMP Module...", "INFO")
    
    manager = get_manager(run_bridge=True)
    
    # ⚡ CONNECT NATIVE MQTT
    if manager.context.mqtt_client:
        manager.context.mqtt_client.connect()
    
    matrix_log("comms", "snmp", "main", "⚙️ [SNMP] Starting background services thread...", "INFO")
    manager.start()
    
    # Launch GUI
    try:
        import tkinter as tk
        from tkinter import ttk
        from oaComProtocols.oaComSNMP.Interface.snmp_log_impl import SnmpLogImplementation
        from oaComProtocols.oaComSNMP.Interface.snmp_mib_impl import SnmpMibImplementation
        from oaComProtocols.oaComSNMP.Interface.snmp_status_impl import SnmpStatusImplementation
        from oaComProtocols.oaComSNMP.Interface.snmp_verify_mib_impl import SnmpVerifyMibImplementation
        from oaComProtocols.oaComSNMP.Interface.snmp_verify_oid_impl import SnmpVerifyOidImplementation

        root = tk.Tk()
        root.title("OPEN-AIR | SNMP Standalone")
        root.geometry("1200x800")
        
        notebook = ttk.Notebook(root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        config = {
            "app_instance": type('App', (), {'snmp_manager': manager})(),
            "mqtt_client": manager.context.mqtt_client
        }
        
        interfaces = [
            ("Status", SnmpStatusImplementation),
            ("Delta Monitor", SnmpLogImplementation),
            ("MIB Definition", SnmpMibImplementation),
            ("MIB Verify", SnmpVerifyMibImplementation),
            ("OID Verify", SnmpVerifyOidImplementation)
        ]
        
        for title, cls in interfaces:
            tab = tk.Frame(notebook, bg="#2b2b2b")
            notebook.add(tab, text=title)
            gui = cls(tab, config=config)
            gui.pack(fill=tk.BOTH, expand=True)

        matrix_log("comms", "snmp", "main", "✅ [SNMP] Standalone GUI deployed.", "SUCCESS")
        root.mainloop()

    except KeyboardInterrupt: pass
    finally:
        manager.stop()
        if manager.context.mqtt_client:
            manager.context.mqtt_client.disconnect()

if __name__ == "__main__":
    main()
