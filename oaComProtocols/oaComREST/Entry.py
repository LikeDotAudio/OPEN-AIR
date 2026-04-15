# oaComProtocols.oaComREST/Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260414.1000.1
#
# Description: Gatekeeper for the REST Communication Module.
# Manages the FastAPI application lifecycle and related services.
# Refactored for centralized management by ComProtocolManager.

import sys
import os
import pathlib
import threading
import time
import subprocess
import argparse
from pathlib import Path

# Ensure project root is in sys.path for direct execution
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from oaLogging.Methods.matrix_gate import matrix_log
from oaConfigurationManager.FileReaders.config_reader import Config
from oaOchestration.Core.path_initializer import initialize_paths, DATA_LOGS_DIR

# --- Core Components ---
# These managers will be instantiated and managed by the ComProtocolManager
# FastAPI app, Uvicorn worker, MQTT transport, etc.

_rest_manager = None # Placeholder for the REST manager instance

# Mock dependencies if not provided by the manager
class MockStateCache:
    def handle_external_update(self, *args, **kwargs): pass
    def shutdown(self): pass

class MockMqttConnectionManager:
    def connect_to_broker(self, *args, **kwargs): pass
    def disconnect(self): pass
    def subscribe(self, *args, **kwargs): pass
    def publish(self, *args, **kwargs): pass

class MockSubscriberRouter:
    def add_handler(self, *args, **kwargs): pass

def get_rest_manager(state_cache_manager=None, mqtt_connection_manager=None, subscriber_router=None, protocol_router=None, run_bridge=True):
    """
    Returns the singleton REST Manager instance.
    Dependencies should be passed externally.
    """
    global _rest_manager
    if _rest_manager is None:
        from oaComProtocols.oaComREST.Managers.rest_manager import RESTManager
        # Provide mocks if not supplied by the orchestrator
        state_cache = state_cache_manager if state_cache_manager else MockStateCache()
        protocol_router = protocol_router if protocol_router else MockProtocolRouter()
        
        _rest_manager = RESTManager(
            state_cache_manager=state_cache,
            protocol_router=protocol_router
        )
        matrix_log("comms", "rest", "get_rest_manager", "REST Manager initialized.", "DEBUG")
    return _rest_manager

def start(state_cache_manager=None, mqtt_connection_manager=None, subscriber_router=None, protocol_router=None, run_bridge=True):
    """
    Initializes and starts the REST API service, accepting external dependencies.
    """
    matrix_log("comms", "rest", "start", "🚀 [REST] Starting REST API service...", "INFO")
    
    manager = get_rest_manager(
        state_cache_manager=state_cache_manager,
        mqtt_connection_manager=mqtt_connection_manager,
        subscriber_router=subscriber_router,
        protocol_router=protocol_router,
        run_bridge=run_bridge
    )
    
    # The start() method of RESTManager handles internal initialization (like FastAPI app)
    # and launching the Uvicorn worker.
    manager.start()
    matrix_log("comms", "rest", "start", "✅ REST API service started.", "SUCCESS")
    return manager # Return the manager for external control

def stop():
    """Stops the REST API service."""
    global _rest_manager
    if _rest_manager:
        matrix_log("comms", "rest", "stop", "🛑 [REST] Stopping REST API service...", "INFO")
        _rest_manager.stop()
        _rest_manager = None
        matrix_log("comms", "rest", "stop", "✅ REST API service stopped.", "INFO")

def status():
    """Returns the current status of the REST API service."""
    manager = get_rest_manager()
    if manager:
        return manager.get_status()
    return {"running": False, "error": "REST manager not initialized"}

def run_tests():
    """
    Discovers and runs all tests within the oaComProtocols.oaComREST/Tests/ directory.
    """
    print("🔍 Discovering and running tests for oaComProtocols.oaComREST...")
    test_dir = pathlib.Path(__file__).parent / "Tests"
    if not test_dir.is_dir():
        print("❌ No 'Tests/' directory found.")
        return

    test_files = sorted([f for f in test_dir.glob("test_*.py")])
    if not test_files:
        print("❌ No test files found (expected pattern: test_*.py).")
        return

    print(f"Found {len(test_files)} test files. Executing...")
    
    import subprocess
    
    all_tests_passed = True
    for test_file in test_files:
        print(f"\n--- Running: {test_file.name} ---")
        try:
            # Get the module path relative to the project root for the test runner
            relative_test_file_path = test_file.relative_to(project_root)
            module_path_for_runner = str(relative_test_file_path).replace(os.sep, '.')[:-3] # Remove .py extension

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
        print("\n🎉 All tests for oaComProtocols.oaComREST passed!")
    else:
        print("\n💔 Some tests for oaComProtocols.oaComREST failed.")
    return all_tests_passed

# Standalone main() function is removed.
# def main(): ...

__all__ = [
    "RESTManager",
    "start",
    "stop",
    "status",
    "run_tests"
]
