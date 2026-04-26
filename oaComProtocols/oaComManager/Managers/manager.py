# /home/anthony/Documents/OPEN-AIR/oaComProtocols/oaComManager/manager.py
# Author: Gemini CLI
# Version: 20260414.1500.1
# Description: Central manager for initializing and controlling communication protocol modules.

import pathlib
import sys
import threading
import time
from typing import Any

# Ensure project root is in sys.path for direct execution
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent # Project root is two levels up
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from oaConfigurationManager.FileReaders.config_reader import Config
from oaLogging.Methods.matrix_gate import matrix_log

# --- Protocol Module Definitions ---
# This dictionary will store information about discovered modules and their callable functions.
# It's populated by discover_and_register_protocols.

class ComProtocolManager:
    """
    Manages the lifecycle and initialization of all communication protocol modules.
    Each module is expected to be self-contained for its core functionalities,
    including its own MQTT client if needed.
    """
    _instance = None
    _lock = threading.Lock()

    def __init__(self, config=None):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True

        self.config = config if config else Config.get_instance()
        self.protocol_modules: dict[str, dict[str, Any]] = {} # Stores module info (name, start, stop, status)
        self.running_threads: dict[str, threading.Thread] = {} # Tracks started module threads
        self._lock = threading.Lock()

        # Common dependencies to be shared between protocol modules if available.
        self.protocol_router = None
        self.state_cache_manager = None
        self.mqtt_connection_manager = None
        self.subscriber_router = None

        matrix_log("manager", "com_protocol", "__init__", "🚀 [ComProtocolManager] Initialized.", "INFO")

    def discover_and_register_protocols(self):
        """
        Dynamically discovers and registers protocol modules based on directory structure.
        Looks for Entry.py files in standard 'oaComProtocols/oaCom*/' subdirectories.
        """
        protocol_base_path = project_root / "oaComProtocols"

        # List of known protocol module directories to check
        protocol_dirs_to_check = [
            "oaComDNSSD", "oaComMDNS", "oaComMidi", "oaComMQTT", "oaComNmos",
            "oaComOSC", "oaComREST", "oaComSAP", "oaComSMPTE2138", "oaComSNMP",
            "oaComVISA" # Added based on previous context, though not explicitly listed by user
        ]

        for module_name_short in protocol_dirs_to_check:
            module_path = protocol_base_path / module_name_short
            entry_file_path = module_path / "Entry.py"

            if entry_file_path.is_file():
                module_full_name = f"oaComProtocols.{module_name_short}.Entry"
                try:
                    # Dynamically import the Entry point module
                    entry_module = __import__(module_full_name, fromlist=['start', 'stop', 'status'])

                    # Check for required functions
                    if hasattr(entry_module, 'start') and callable(entry_module.start) and \
                       hasattr(entry_module, 'stop') and callable(entry_module.stop):

                        self.protocol_modules[module_name_short] = {
                            "module_name": module_full_name,
                            "start": entry_module.start,
                            "stop": entry_module.stop,
                            "status": entry_module.status if hasattr(entry_module, 'status') and callable(entry_module.status) else lambda: {"running": "status() not defined"}
                        }
                        matrix_log("manager", "com_protocol", "discover", f"✅ Registered protocol module: {module_full_name}", "INFO")
                    else:
                        matrix_log("manager", "com_protocol", "discover", f"⚠️ Module {module_full_name} missing callable start/stop functions. Skipping.", "WARNING")
                except ImportError as e:
                    matrix_log("manager", "com_protocol", "discover", f"❌ Could not import module {module_full_name}: {e}. Skipping.", "ERROR")
                except Exception as e:
                    matrix_log("manager", "com_protocol", "discover", f"❌ Unexpected error registering module {module_full_name}: {e}. Skipping.", "ERROR")
            else:
                matrix_log("manager", "com_protocol", "discover", f"ℹ️ No Entry.py found for {module_path}. Skipping.", "DEBUG")

        return len(self.protocol_modules) > 0

    def initialize_common_dependencies(self):
        """Initializes common dependencies used by multiple protocol modules."""
        matrix_log("manager", "com_protocol", "initialize_dependencies", "Initializing common dependencies...", "INFO")
        try:
            # No shared MQTT connection will be initialized here.
            # Individual modules manage their own if needed.

            # Protocol router might also need initialization or singleton access
            try:
                from oaComBroker.Core.protocol_router.manager import (
                    ProtocolRouter,  # Assuming this is the central router
                )
                self.protocol_router = ProtocolRouter.get_instance() # Assuming singleton pattern
                matrix_log("manager", "com_protocol", "initialize_dependencies", "ProtocolRouter singleton retrieved.", "DEBUG")
            except Exception as e:
                matrix_log("manager", "com_protocol", "initialize_dependencies", f"Could not retrieve ProtocolRouter: {e}. Passing None.", "WARNING")
                self.protocol_router = None

            matrix_log("manager", "com_protocol", "initialize_dependencies", "Common dependency (Protocol Router) initialized.", "INFO")
            return True
        except ImportError as e:
            matrix_log("manager", "com_protocol", "initialize_dependencies", f"Failed to import common dependencies: {e}", "ERROR")
            return False
        except Exception as e:
            matrix_log("manager", "com_protocol", "initialize_dependencies", f"Error during dependency initialization: {e}", "ERROR")
            return False

    def start_all(self, **kwargs):
        """
        Starts all registered protocol modules. Each module's start function is called
        in a separate thread to ensure they run concurrently.
        Common dependencies (excluding MQTT) are passed.
        """
        with self._lock:
            if self.running_threads:
                matrix_log("manager", "com_protocol", "start_all", "⚠️ All protocols already running.", "WARNING")
                return

            matrix_log("manager", "com_protocol", "start_all", "🚀 Starting all registered protocols...", "INFO")

            # Discover and register protocols if not already done
            if not self.protocol_modules:
                self.discover_and_register_protocols()

            # Initialize common dependencies once before starting modules
            # MQTT connection is managed internally by individual modules.
            if not self.initialize_common_dependencies():
                matrix_log("manager", "com_protocol", "start_all", "❌ Failed to initialize common dependencies. Aborting start.", "ERROR")
                return

            for name, info in self.protocol_modules.items():
                try:
                    # Prepare arguments for the start function.
                    # This needs to be adaptive to each module's start() signature.
                    start_args = {}

                    # Pass common dependencies if the start function expects them.
                    # Exclude MQTT-related arguments as they are self-contained.

                    if "subscriber_router" in info["start"].__code__.co_varnames:
                        start_args["subscriber_router"] = self.subscriber_router
                    if "protocol_router" in info["start"].__code__.co_varnames:
                        start_args["protocol_router"] = self.protocol_router
                    if "run_bridge" in info["start"].__code__.co_varnames:
                        # ⚡ PARTITION PROPAGATION: Pass the run_bridge value from kwargs (from Entry.py)
                        start_args["run_bridge"] = kwargs.get("run_bridge", True)

                    # Handle specific dependencies like mqtt_publisher for DNSSD/MDNS/SAP
                    # These modules created their own StandaloneMqttPublisher internally.
                    # If they are refactored to accept an MQTT client, that would be handled here.
                    # For now, assuming they create their own.

                    # Add other common kwargs if identified
                    # start_args["some_other_param"] = kwargs.get("some_other_param")

                    thread = threading.Thread(target=info["start"], kwargs=start_args, name=f"{name}-Thread", daemon=True)
                    thread.start()
                    self.running_threads[name] = thread
                    matrix_log("manager", "com_protocol", "start_all", f"✅ Started {name} in background thread.", "SUCCESS")
                except Exception as e:
                    matrix_log("manager", "com_protocol", "start_all", f"❌ Failed to start {name}: {e}", "ERROR")

            matrix_log("manager", "com_protocol", "start_all", "All protocols started (or attempted).", "INFO")

    def stop_all(self):
        """
        Stops all running protocol modules by calling their respective stop functions.
        """
        with self._lock:
            if not self.running_threads:
                matrix_log("manager", "com_protocol", "stop_all", "⚠️ No protocols were running.", "WARNING")
                return

            matrix_log("manager", "com_protocol", "stop_all", "🛑 Stopping all registered protocols...", "INFO")
            for name, thread in list(self.running_threads.items()): # Iterate over a copy of items
                try:
                    module_info = self.protocol_modules.get(name)
                    if module_info and callable(module_info["stop"]):
                        module_info["stop"]() # Call the module's stop function
                        matrix_log("manager", "com_protocol", "stop_all", f"✅ Stopped {name}.", "SUCCESS")
                    else:
                        matrix_log("manager", "com_protocol", "stop_all", f"⚠️ {name} has no callable stop function.", "WARNING")

                    # Clean up thread reference
                    if name in self.running_threads:
                        del self.running_threads[name]

                except Exception as e:
                    matrix_log("manager", "com_protocol", "stop_all", f"❌ Error stopping {name}: {e}", "ERROR")

            matrix_log("manager", "com_protocol", "stop_all", "All protocols stopped (or attempted).", "INFO")
            self.running_threads.clear() # Ensure it's empty

    def get_status_all(self):
        """
        Gathers status from all registered and running protocol modules.
        """
        status_report = {}
        for name, info in self.protocol_modules.items():
            try:
                status_report[name] = info["status"]()
            except Exception as e:
                status_report[name] = {"error": str(e)}
                matrix_log("manager", "com_protocol", "get_status_all", f"❌ Error getting status for {name}: {e}", "ERROR")
        return status_report

    @classmethod
    def get_instance(cls, config=None):
        """Singleton getter for ComProtocolManager."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(config)
        return cls._instance

# Note: The main() function here is for demonstration/standalone testing of the manager itself.
# In a full application, the ComProtocolManager would be instantiated and controlled by the main entry point.
def main():
    """
    Standalone entry point for the ComProtocolManager.
    This demonstrates how the manager would discover, start, and stop modules.
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

    if args.start or args.run_demo:
        # Initialize common dependencies before starting all protocols
        if not manager.initialize_common_dependencies():
            print("❌ Failed to initialize common dependencies. Aborting start.")
            sys.exit(1)

        # Pass dependencies to start_all. This assumes start_all might use them.
        # The actual passing to individual module start functions is handled within start_all.
        # Exclude MQTT/Subscriber dependencies as they are self-contained.
        common_deps_to_pass = {
            "protocol_router": manager.protocol_router
        }
        # Add other dependencies that individual modules might need (e.g., context, specific configs)
        # common_deps_to_pass["some_other_param"] = manager.some_other_dependency

        manager.start_all(**common_deps_to_pass)

    if args.status or args.run_demo:
        print("\n--- Current Protocol Status ---")
        status_report = manager.get_status_all()
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
            manager.stop_all()
            print("--- DEMO mode finished ---")
            sys.exit(0)
    elif args.stop:
        manager.stop_all()
        sys.exit(0)
    elif args.start:
        print("\nProtocols started. Manager running in background. Press Ctrl+C to stop.")
        try:
            # Keep the main thread alive if protocols are in background threads
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            manager.stop_all()
            print("✅ ComProtocolManager shutdown complete.")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Unexpected error in main loop: {e}")
            manager.stop_all()
            sys.exit(1)

if __name__ == "__main__":
    main()

__all__ = ["ComProtocolManager", "main"]
