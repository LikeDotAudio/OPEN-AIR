# ==========================================
# Header: flatten_protocols.py
# Purpose: flatten_protocols.py implementation.
# Description: Logic and implementation for flatten_protocols.py implementation.
# 
# Version: 26.07.05.1
# Change Log:
# - 2026-07-05: Initial annotation and documentation added.
# ==========================================

import os
import shutil

base_dir = "/home/anthony/Documents/OPEN-AIR/oaComProtocols"

folders_to_delete = ["Core", "Managers", "Workers", "Interface"]

for folder in os.listdir(base_dir):
    protocol_dir = os.path.join(base_dir, folder)
    if os.path.isdir(protocol_dir) and folder.startswith("oaCom"):
        print(f"Cleaning {folder}...")
        deleted_anything = False
        for sub in folders_to_delete:
            sub_path = os.path.join(protocol_dir, sub)
            if os.path.exists(sub_path):
                shutil.rmtree(sub_path)
                print(f"  Deleted {sub_path}")
                deleted_anything = True
        
        # Rewrite Entry.py ONLY if we actually deleted legacy folders
        if deleted_anything:
            entry_path = os.path.join(protocol_dir, "Entry.py")
            if os.path.exists(entry_path):
                with open(entry_path, "w") as f:
                    f.write("""
import configparser
import pathlib
from oaLogging.Methods.matrix_gate import matrix_log

class GenericManager:
    def __init__(self, *args, **kwargs):
        pass
    def start(self):
        matrix_log("comms", "generic", "start", f"Native Rust implementation pending for {__name__}", "WARNING")
    def stop(self):
        pass
    def get_status(self):
        return {"running": False, "engine": "rust_pending"}

_instance = None
# Inline comment: Logic for get_manager
def get_manager(*args, **kwargs):
    global _instance
    if _instance is None:
        _instance = GenericManager(*args, **kwargs)
    return _instance

# Inline comment: Logic for start_bridge
def start_bridge(*args, **kwargs):
    return get_manager(*args, **kwargs)

# Inline comment: Logic for get_discovery_orchestrator
def get_discovery_orchestrator(*args, **kwargs):
    return get_manager(*args, **kwargs)

# Inline comment: Logic for start
def start(*args, **kwargs):
    manager = get_manager(*args, **kwargs)
    manager.start()

# Inline comment: Logic for stop
def stop():
    if _instance:
        _instance.stop()

# Inline comment: Logic for status
def status():
    if _instance:
        return _instance.get_status()
    return {"running": False}

__all__ = ["get_manager", "start_bridge", "get_discovery_orchestrator", "start", "stop", "status"]
""")
            print(f"  Rewrote {entry_path} to generic Rust stub.")
