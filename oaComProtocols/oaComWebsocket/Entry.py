# oaComProtocols.oaComWebsocket/Entry.py
# Author: Gemini (Collaborator)
# Version: 20260405.1548.2 (updated)

"""
import sys
import os
Entry point for the oaComProtocols.oaComWebsocket module.
Provides reusable WebSocket client and server functionalities.
"""

import subprocess
import glob

import websocket # For WebSocket client
import threading # For threading
import json
import time
from typing import Optional, Callable, Dict, Any

# Import the actual WebSocketEventTransport class
from .Core.websocket_transport import WebSocketEventTransport
# Import the EventTransport ABC if it's used directly in Entry.py
from .Core.abc import EventTransport

# Placeholder for a higher-level WebSocket manager
class WebSocketManager:
    """
    A higher-level manager for WebSocket connections.
    """
    def __init__(self):
        print("WebSocketManager initialized.")
        pass

# --- Test Runner Logic ---
def run_module_tests():
    """
    Automatically runs tests for the current module if Entry.py is executed directly.
    Looks for a 'Tests' subdirectory relative to the module's root.
    """
    current_file_path = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file_path) # Directory of Entry.py
    module_root = os.path.dirname(current_dir)     # Root directory of the module (e.g., oaComProtocols.oaComWebsocket)
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

__all__ = [
    "WebSocketEventTransport",
    "WebSocketManager",
]

# If this script is run directly, execute the tests first.
if __name__ == "__main__":
    run_module_tests()
    # If tests pass or are skipped, we should ideally call a module-specific main function
    # or simply allow the script to exit if there's no direct execution logic.
    # Since this module mainly defines classes for import, we'll just pass.
    print("Entry point executed after tests.")
    pass 
