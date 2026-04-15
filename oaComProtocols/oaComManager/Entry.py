# /home/anthony/Documents/OPEN-AIR/oaComProtocols/oaComManager/Entry.py
# Author: Gemini CLI
# Version: 20260414.1500.1
# Description: Entry point for the Communication Protocol Manager.

# This module will orchestrate the startup and shutdown of all other
# communication protocol modules.

import sys
import os
import pathlib
import threading
import time
import argparse
from pathlib import Path

# Ensure project root is in sys.path for direct execution
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent # Project root is two levels up
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from oaLogging.Methods.matrix_gate import matrix_log
from oaComProtocols.oaComManager.manager import ComProtocolManager
from oaConfigurationManager.Entry import Config # Assuming Config is needed for manager

def start_all_protocols():
    """
    Initializes and starts all communication protocol managers.
    This function will be the primary startup mechanism.
    It passes common dependencies (excluding shared MQTT) to the modules.
    """
    matrix_log("manager", "entry", "start_all_protocols", "🚀 [MANAGER] Initializing Communication Protocol Manager...", "INFO")
    
    config = Config.get_instance() # Get singleton config if needed
    
    # Ensure manager instance exists
    protocol_manager = ComProtocolManager.get_instance(config=config)
    
    # Discover modules before starting
    protocol_manager.discover_and_register_protocols()
    
    # Initialize common dependencies (e.g., state cache, protocol router)
    # MQTT is managed internally by each protocol module.
    if not protocol_manager.initialize_common_dependencies():
        matrix_log("manager", "entry", "start_all_protocols", "❌ Failed to initialize common dependencies. Aborting start.", "ERROR")
        sys.exit(1)

    # Prepare arguments for start_all. This should include dependencies that individual modules might need.
    common_deps_to_pass = {
        "protocol_router": protocol_manager.protocol_router
        # MQTT connection manager and subscriber router are NOT passed, as they are self-contained.
    }
    # Add any other common parameters identified from module start() signatures.
    # Example: common_deps_to_pass["run_bridge"] = True 

    matrix_log("manager", "entry", "start_all_protocols", "Starting all registered protocols...", "INFO")
    protocol_manager.start_all(**common_deps_to_pass)
    
    matrix_log("manager", "entry", "start_all_protocols", "✅ All registered protocols launched.", "SUCCESS")
    return protocol_manager # Return manager for potential control

def stop_all_protocols(protocol_manager):
    """
    Shuts down all managed communication protocol modules.
    """
    if protocol_manager:
        matrix_log("manager", "entry", "stop_all_protocols", "🛑 Shutting down all protocols...", "INFO")
        protocol_manager.stop_all()
        matrix_log("manager", "entry", "stop_all_protocols", "✅ All protocols stopped.", "INFO")
    else:
        matrix_log("manager", "entry", "stop_all_protocols", "⚠️ Protocol manager not initialized, cannot stop protocols.", "WARNING")

def status():
    """
    Retrieves the status of all managed communication protocol modules.
    """
    try:
        # Use get_instance to ensure we are interacting with the singleton manager
        protocol_manager = ComProtocolManager.get_instance()
        if not protocol_manager:
            return {"error": "ComProtocolManager not initialized"}
        return protocol_manager.get_status_all()
    except Exception as e:
        matrix_log("manager", "entry", "status", f"❌ Error getting status: {e}", "ERROR")
        return {"error": str(e)}

def main():
    """
    Standalone entry point for the Communication Protocol Manager.
    This demonstrates how the manager would start and stop modules.
    It's intended to be called by a higher-level application entry point.
    """
    parser = argparse.ArgumentParser(description="OPEN-AIR Communication Protocol Manager")
    parser.add_argument("--start", action="store_true", help="Start all managed protocols")
    parser.add_argument("--stop", action="store_true", help="Stop all managed protocols")
    parser.add_argument("--status", action="store_true", help="Get status of all managed protocols")
    parser.add_argument("--run-demo", action="store_true", help="Run manager in demo mode (start, wait, stop)")
    parser.add_argument("--discover", action="store_true", help="Discover and list registered protocols")

    args = parser.parse_args()

    # Initialize the singleton manager
    manager = ComProtocolManager.get_instance() 

    if args.discover:
        manager.discover_and_register_protocols()
        print("--- Discovered Protocol Modules ---")
        if manager.protocol_modules:
            for name, info in manager.protocol_modules.items():
                print(f"  - {name} ({info['module_name']})")
        else:
            print("  No protocol modules found.")
        print("---------------------------------")
        sys.exit(0)

    # Prepare common dependencies only if starting protocols
    common_deps_to_pass = {}
    if args.start or args.run_demo:
        if not manager.initialize_common_dependencies():
            print("❌ Failed to initialize common dependencies. Aborting start.")
            sys.exit(1)
        
        # Populate common_deps from the manager's initialized dependencies.
        # Exclude MQTT/Subscriber dependencies as they are self-contained.
        common_deps_to_pass = {
            "protocol_router": manager.protocol_router
        }
        # Add any other dependencies that individual modules might need from the manager.
        # Example: common_deps_to_pass["some_other_param"] = manager.some_other_dependency

    if args.start or args.run_demo:
        manager.start_all(**common_deps_to_pass)

    if args.status or args.run_demo:
        print("\n--- Current Protocol Status ---")
        status_report = status()
        if not status_report:
            print("  No protocols discovered or managed.")
        else:
            for name, status_data in status_report.items():
                print(f"  {name}: {status_data}")
        print("-----------------------------")
        if args.run_demo: print("\n")

    if args.run_demo:
        print("--- Running in DEMO mode for 15 seconds ---")
        try:
            time.sleep(15)
        except KeyboardInterrupt:
            pass
        finally:
            stop_all_protocols(manager)
            print("--- DEMO mode finished ---")
            sys.exit(0)
    elif args.stop:
        stop_all_protocols(manager)
        sys.exit(0)
    elif args.start:
        print("\nProtocols started. Manager running in background. Press Ctrl+C to stop.")
        try:
            # Keep the main thread alive if protocols are in background threads
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            stop_all_protocols(manager)
            print("✅ ComProtocolManager shutdown complete.")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Unexpected error in main loop: {e}")
            stop_all_protocols(manager)
            sys.exit(1)

if __name__ == "__main__":
    main()

__all__ = ["ComProtocolManager", "start_all_protocols", "stop_all_protocols", "status", "main"]
