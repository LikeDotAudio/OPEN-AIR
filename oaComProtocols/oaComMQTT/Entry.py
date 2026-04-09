# oaComProtocols.oaComMQTT/Entry.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

"""
import sys
import os
from pathlib import Path
oaComProtocols.oaComMQTT/Entry.py - The sole orchestrator for the MQTT Communication Module.

Purpose:
This file is the public entry point for 'oaComProtocols.oaComMQTT'. It manages the 
lifecycle of the MQTT connection and provides high-level publisher/subscriber
interfaces to the rest of the project.
"""

from .Managers.mqtt_connection import MqttConnectionManager
from .Managers.mqtt_subscriber_router import MqttSubscriberRouter
from .Managers.mqtt_manager import MqttManager
from .Core.mqtt_message import MqttMessage
from .Core import mqtt_publisher_service
from .Methods.mqtt_topic_utils import (
    generate_topic_path_from_filepath,
    get_topic,
    generate_base_topic,
    generate_widget_topic
)

def get_connection_manager():
    """Returns the singleton MqttConnectionManager instance."""
    return MqttConnectionManager()

def get_subscriber_router():
    """Returns the singleton MqttSubscriberRouter instance."""
    return MqttSubscriberRouter()

def get_mqtt_manager(subscriber_router, mqtt_client, state_cache_manager):
    """Returns a new MqttManager instance."""
    return MqttManager(subscriber_router, mqtt_client, state_cache_manager)

def start_mqtt_services(broker_address="localhost", broker_port=1883):
    """
    Initializes the MQTT connection and starts the publisher worker.
    """
    manager = get_connection_manager()
    router = get_subscriber_router()
    
    # Initialize connection
    manager.connect_to_broker(
        address=broker_address, 
        port=broker_port, 
        subscriber_router=router
    )
    
    # Start background publisher worker
    mqtt_publisher_service.start_publisher_worker()
    return manager

def stop_mqtt_services():
    """
    Shuts down MQTT connection and publisher services.
    """
    mqtt_publisher_service.shutdown_publisher_worker()

# Standardized exports
__all__ = [
    "MqttConnectionManager",
    "MqttSubscriberRouter",
    "MqttManager",
    "MqttMessage",
    "mqtt_publisher_service",
    "get_connection_manager",
    "get_subscriber_router",
    "get_mqtt_manager",
    "start_mqtt_services",
    "stop_mqtt_services",
    "generate_topic_path_from_filepath",
    "get_topic",
    "generate_base_topic",
    "generate_widget_topic"
]

def run_tests():
    """
    Discovers and runs all tests within the oaComProtocols.oaComMQTT/Tests/ directory.
    """
    print("🔍 Discovering and running tests for oaComProtocols.oaComMQTT...")
    test_dir = Path(__file__).parent / "Tests"
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
            relative_test_file_path = test_file.relative_to(Path(__file__).parent.parent.parent) # Path from OPEN-AIR root
            module_path_for_runner = str(relative_test_file_path).replace(os.sep, '.')[:-3] # Remove .py extension

            # Ensure the current directory is the project root so Python can find modules
            original_cwd = os.getcwd()
            os.chdir(Path(__file__).parent.parent.parent) 

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
        print("\n🎉 All tests for oaComProtocols.oaComMQTT passed!")
    else:
        print("\n💔 Some tests for oaComProtocols.oaComMQTT failed.")

if __name__ == "__main__":
    # If no arguments are provided, default to running tests.
    # Otherwise, assume specific commands are intended (e.g., start, stop).
    if len(sys.argv) > 1:
        print("Executing command...")
        # In a real application, you'd parse sys.argv and call the appropriate functions.
        # For this task, we assume direct execution without specific arguments implies testing.
    else:
        run_tests()

