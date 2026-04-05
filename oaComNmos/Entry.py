# FolderName/FileName.py
# Author: Gemini (Collaborator)
# Version: 20260405.1315.10 (updated)

import argparse
import signal
import sys
import threading
import socket
import time
import subprocess  # Added for running tests
import os          # Added for path manipulation
import glob        # Added for finding modules (though not used in this specific file modification)
from http.server import HTTPServer, BaseHTTPRequestHandler # Import HTTPServer for explicit use

# Local module imports
from oaComNmos.Core.utils import gen_id, get_ip
from oaComNmos.Core.nmos_builder import build_node, build_device
from oaComNmos.Constants import settings
from oaComNmos.Managers import registration_manager
from oaComNmos.Workers import sap_listener_worker, heartbeat_worker
from oaComNmos import Interface # Import the interface module to access its components

# --- Test Runner Logic ---
def run_module_tests():
    """
    Automatically runs tests for the current module if Entry.py is executed directly.
    Looks for a 'Tests' subdirectory relative to the module's root.
    """
    current_file_path = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file_path) # Directory of Entry.py
    module_root = os.path.dirname(current_dir)     # Root directory of the module (e.g., oaGUIbuilder)
    tests_dir = os.path.join(module_root, "Tests")

    print(f"Checking for tests in: {tests_dir}")

    if os.path.exists(tests_dir):
        print(f"Running tests for module '{os.path.basename(module_root)}'...")
        try:
            # Construct the command to run pytest for the module's tests directory
            # Use sys.executable to ensure we use the current Python interpreter's pytest
            command = [sys.executable, "-m", "pytest", tests_dir]
            
            # Execute the command. `capture_output=True` and `text=True` for stdout/stderr.
            # `check=False` prevents raising an exception if tests fail.
            result = subprocess.run(command, capture_output=True, text=True, check=False)

            print("\n--- Test Output ---")
            print(result.stdout)
            if result.stderr:
                print("--- Test Errors ---")
                print(result.stderr)
            
            if result.returncode != 0:
                print(f"Tests for '{os.path.basename(module_root)}' failed with exit code {result.returncode}")
                # Exit the script with the test failure code if tests fail
                sys.exit(result.returncode) 
            else:
                print(f"All tests for '{os.path.basename(module_root)}' passed.")
                
        except FileNotFoundError:
            print("Error: 'pytest' command not found. Please ensure pytest is installed and accessible in your environment.")
            print("Tests were not executed.")
            sys.exit(1) # Exit if pytest is not found
        except Exception as e:
            print(f"An unexpected error occurred while running tests: {e}")
            sys.exit(1) # Exit on other exceptions
    else:
        print(f"No 'Tests' directory found for module '{os.path.basename(module_root)}' at {tests_dir}. Skipping test execution.")

# --- Global State Management ---
# A dictionary to hold all mutable shared states accessible by threads and modules.
global_state = {
    "NODE_ID": None,
    "DEVICE_ID": None,
    "NODE": {},
    "DEVICE": {},
    "SOURCES": {},
    "FLOWS": {},
    "SENDERS": {},
    "STREAMS": {}, # Shared state for SAP listener and Connection API
    "REGISTRAR_URL": None,
    "RUNNING": True, # Flag to control worker thread loops
}

# Global variable to hold the HTTP server instance for graceful shutdown.
httpd_server = None

def shutdown_handler(sig, frame):
    """
    Gracefully handles shutdown signals (SIGINT, SIGTERM) by setting the RUNNING
    flag to False and shutting down the HTTP server.
    """
    print("
[Entry] Shutdown signal received. Stopping services...")
    global_state["RUNNING"] = False # Signal worker threads to stop their loops

    # Attempt to shut down the HTTP server gracefully if it's running.
    if httpd_server:
        try:
            # httpd_server.shutdown() is generally preferred for cleaner termination
            # It unblocks serve_forever() in a separate thread.
            httpd_server.shutdown() 
            print("[Entry] NMOS Connection API server shut down.")
        except Exception as e:
            print(f"[Entry] Error during HTTP server shutdown: {e}")
    
    print("[Entry] All services stopped. Exiting.")
    sys.exit(0)

def main():
    """
    Main function to initialize, configure, and run the SAP-to-NMOS bridge.
    Parses arguments, sets up global state, starts worker threads, and
    launches the NMOS Connection API server.
    """
    global httpd_server # Allow modification of the global server instance

    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="SAP to NMOS Bridge: Discovers SAP streams and registers them as NMOS resources.")
    parser.add_argument("--registrar", required=True, help="URL of the NMOS registration API (e.g., http://localhost:4000)")
    args = parser.parse_args()

    global_state["REGISTRAR_URL"] = args.registrar
    host_ip = get_ip() # Determine the local IP address once at startup.

    # --- Initialize Global IDs and Resources ---
    global_state["NODE_ID"] = gen_id()
    global_state["DEVICE_ID"] = gen_id()

    print(f"[Entry] Initializing bridge. Node ID: {global_state['NODE_ID']}, Device ID: {global_state['DEVICE_ID']}, Host IP: {host_ip}")

    # Build initial Node and Device resources using the determined host IP and configured port.
    global_state["NODE"] = build_node(global_state["NODE_ID"], host_ip, settings.PORT)
    global_state["DEVICE"] = build_device(global_state["DEVICE_ID"], global_state["NODE_ID"], host_ip, settings.PORT)

    # --- Initial Registration of Node and Device ---
    # Register the Node and Device resources with the NMOS registry upon startup.
    registration_manager.register_all_resources(
        global_state["REGISTRAR_URL"],
        global_state["NODE"],
        global_state["DEVICE"],
        global_state["SOURCES"], # Initially empty
        global_state["FLOWS"],   # Initially empty
        global_state["SENDERS"]  # Initially empty
    )

    # --- Start Worker Threads ---
    # 1. SAP Listener Thread: Listens for SAP announcements.
    sap_thread = threading.Thread(
        target=sap_listener_worker,
        args=(
            global_state["REGISTRAR_URL"],
            global_state["NODE_ID"],
            global_state["DEVICE_ID"],
            host_ip,
            global_state, # Pass the entire global state dictionary
            registration_manager # Pass the registration manager module
        ),
        daemon=True, # Allows the main thread to exit even if this thread is running
        name="SAPListenerThread"
    )
    sap_thread.start()
    print("[Entry] SAP Listener thread started.")

    # 2. Heartbeat Thread: Periodically pings the registrar to maintain Node registration.
    heartbeat_thread = threading.Thread(
        target=heartbeat_worker,
        args=(
            global_state["REGISTRAR_URL"],
            global_state["NODE_ID"],
            global_state, # Pass the global state dictionary
            registration_manager # Pass the registration manager module
        ),
        daemon=True,
        name="HeartbeatThread"
    )
    heartbeat_thread.start()
    print("[Entry] Heartbeat thread started.")

    # --- Start NMOS Connection API Server ---
    # Set the shared state variables in the connection_api module so the handler can access them.
    # This ensures that updates to SOURCES, FLOWS, SENDERS, STREAMS are reflected.
    connection_api.NODE = global_state["NODE"]
    connection_api.DEVICE = global_state["DEVICE"]
    connection_api.SOURCES = global_state["SOURCES"]
    connection_api.FLOWS = global_state["FLOWS"]
    connection_api.SENDERS = global_state["SENDERS"]
    connection_api.STREAMS = global_state["STREAMS"] # Crucially shared with SAP listener

    # Instantiate and start the HTTP server for the Connection API.
    # We run it in a separate thread so the main thread can manage signals and keep alive.
    server_address = ("0.0.0.0", settings.PORT)
    # Use HTTPServer from connection_api module, assuming it's correctly imported.
    httpd_server = connection_api.HTTPServer(server_address, connection_api.NmosConnectionApiHandler)
    
    server_runner_thread = threading.Thread(target=httpd_server.serve_forever, name="ConnectionAPIServerThread")
    server_runner_thread.daemon = True
    server_runner_thread.start()
    print(f"[Entry] NMOS Connection API server started on 0.0.0.0:{settings.PORT}")

    # --- Signal Handling Setup ---
    # Register the shutdown_handler for SIGINT (Ctrl+C) and SIGTERM signals.
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    print("[Entry] Service started successfully. Press Ctrl+C to stop.")

    # --- Main thread keep-alive loop ---
    # This loop prevents the main thread from exiting, allowing daemon threads to continue running.
    # It also allows for checking the RUNNING flag and handling interrupts if signal handlers fail.
    while global_state["RUNNING"]:
        try:
            time.sleep(1) # Sleep briefly to avoid busy-waiting
        except KeyboardInterrupt:
            # If Ctrl+C is pressed and signal handler didn't catch it for some reason,
            # trigger shutdown manually.
            shutdown_handler(None, None) 

if __name__ == "__main__":
    # Standard Python entry point.
    # Check if the script is being run directly.
    # If so, first attempt to run tests.
    # Determine the current module's root directory relative to Entry.py
    current_file_path = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file_path) # Directory of Entry.py
    module_root = os.path.dirname(current_dir)     # Root directory of the module (e.g., oaGUIbuilder)
    tests_dir = os.path.join(module_root, "Tests")

    if os.path.exists(tests_dir):
        print(f"Running tests for module '{os.path.basename(module_root)}'...")
        try:
            # Construct the command to run pytest for the module's tests directory
            command = [sys.executable, "-m", "pytest", tests_dir]
            
            # Execute the command. `capture_output=True` and `text=True` for stdout/stderr.
            # `check=False` prevents raising an exception if tests fail.
            result = subprocess.run(command, capture_output=True, text=True, check=False)

            print("\n--- Test Output ---")
            print(result.stdout)
            if result.stderr:
                print("--- Test Errors ---")
                print(result.stderr)
            
            if result.returncode != 0:
                print(f"Tests for '{os.path.basename(module_root)}' failed with exit code {result.returncode}")
                sys.exit(result.returncode) # Exit with error code if tests fail
            else:
                print(f"All tests for '{os.path.basename(module_root)}' passed.")
                
        except FileNotFoundError:
            print("Error: 'pytest' command not found. Please ensure pytest is installed and accessible in your environment.")
            print("Tests were not executed.")
            sys.exit(1) # Exit if pytest is not found
        except Exception as e:
            print(f"An unexpected error occurred while running tests: {e}")
            sys.exit(1) # Exit on other exceptions
    else:
        print(f"No 'Tests' directory found for module '{os.path.basename(module_root)}' at {tests_dir}. Skipping test execution.")

    # If tests passed or were skipped, proceed with the original main execution logic.
    main()
