# managers/VisaScipi/manager_visa_proxy.py
#
# This manager provides a safe, low-level interface for executing SCPI write
# and query commands via PyVISA. It acts as a command queue and execution
# engine for instrument communication, ensuring that I/O operations are
# serialized and handled gracefully in a background thread.
#
# Primary Responsibilities:
# - Maintain a thread-safe command queue for SCPI operations.
# - Coordinate background execution of write and query commands.
# - Manage the lifecycle of the instrument session proxy.
# - Listen for inbound MQTT commands and dispatch results/errors.
#
# Assumptions and Constraints:
# - Assumes only one instrument is active at a time per proxy instance.
# - Blocking VISA I/O is offloaded to a dedicated worker thread.
# - MQTT payloads must follow the project's standard command format.
#
# Author: Anthony Peter Kuzub
#

import os
import inspect
import pyvisa
import orjson
import time
import queue
import threading
import _queue
from workers.Command_Router.mqtt.mqtt_message import MqttMessage

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()

from .manager_visa_safe_writer import write_safe
from .manager_visa_safe_query import query_safe


class VisaProxy:
    """Manages the PyVISA connection and provides safe, serial command execution."""

    def __init__(self, mqtt_controller, subscriber_router):
        """Initializes the VisaProxy with MQTT and subscription services.

        Parameters:
        - mqtt_controller: The service used for MQTT publishing.
        - subscriber_router: The service used for MQTT topic registration.

        Returns:
        - None.

        Side effects and thread-safety:
        - Initializes an internal command queue and state variables.
        """
        current_function_name = inspect.currentframe().f_code.co_name
        if LOCAL_DEBUG: logger.debug(f"💳 🟢️️️🟢 ➡️➡️ {current_function_name}. The grand SCPI experiment begins!")
        
        # ⚡ PRECONDITION VALIDATION
        if not mqtt_controller or not subscriber_router:
            logger.error(f"💳 ❌ Critical: Missing MQTT controller or router in {current_function_name}")
            return

        self.mqtt_util = mqtt_controller
        self.subscriber_router = subscriber_router
        self.inst = None
        self.model = ""
        self.manufacturer = ""

        self.command_queue = queue.Queue()
        self.shutdown_flag = threading.Event()
        self.worker_thread = None

        self._setup_mqtt_subscriptions()


    def shutdown(self):
        """Terminates the command processor worker thread gracefully.

        Returns:
        - None.

        Side effects and thread-safety:
        - Signals the worker thread to stop and joins it.
        - Resets thread and flag state to None.
        """
        if self.worker_thread and self.worker_thread.is_alive():
            if LOCAL_DEBUG: logger.debug("💳 ℹ️ Proxy Log: Shutting down VisaProxy command processor worker.")
            if self.shutdown_flag:
                self.shutdown_flag.set()
            # Unblock the queue.get() call.
            self.command_queue.put(None)
            self.worker_thread.join(timeout=1)
            if self.worker_thread.is_alive():
                self._publish_proxy_error(
                    message="VisaProxy worker thread did not terminate gracefully."
                )
            self.worker_thread = None
            self.shutdown_flag = None
        else:
            if LOCAL_DEBUG: logger.debug("💳 ℹ️ Proxy Log: VisaProxy worker thread not active or already shut down.")

    def _command_processor_worker(self):
        """Background worker loop that executes queued SCPI commands.

        Returns:
        - None.

        Side effects and thread-safety:
        - Continuously polls the command queue until shutdown is signaled.
        - Executes blocking VISA I/O operations (write/query).
        - Handles and logs exceptions during command execution to prevent 
          thread death.
        """
        while not self.shutdown_flag.is_set():
            # ⚡ ZERO EXCEPTION: Polling check instead of catching Empty
            if self.command_queue.empty():
                time.sleep(0.1)
                continue
                
            command_info = self.command_queue.get()
            
            if command_info is None: # The Poison Pill
                break

            command = command_info["command"]
            query = command_info["query"]
            correlation_id = command_info["correlation_id"]

            if query:
                self.query_safe(command, correlation_id)
            else:
                self.write_safe(command)

            self.command_queue.task_done()
            
        if LOCAL_DEBUG: logger.debug("💳 ℹ️ Proxy Log: VisaProxy command processor worker terminated.")


    def _setup_mqtt_subscriptions(self):
        """Registers the inbound command inbox topic.

        Returns:
        - None.
        """
        topic = "OPEN-AIR/Proxy/Tx_Inbox"
        self.subscriber_router.subscribe_to_topic(topic, self._on_tx_inbox_message)
        if LOCAL_DEBUG: logger.debug(f"💳 ℹ️ Proxy Log: 💳Subscribed to '{topic}' for inbound proxy commands.")

    def _on_tx_inbox_message(self, msg: MqttMessage):
        """Handles inbound MQTT messages intended for instrument execution.

        Parameters:
        - msg: The MqttMessage object containing the command payload.

        Returns:
        - None.

        Side effects and thread-safety:
        - Enqueues command information for the background worker thread.
        """
        current_function_name = inspect.currentframe().f_code.co_name
        if LOCAL_DEBUG: logger.trace(f"💳 📡📡⬇️⬇️ PROXY IN: Tx_Inbox message received on Topic: '{msg.topic}', Payload: '{msg.payload}'. Proxy will process this as a raw SCPI command.")

        # Extract command parameters from the hardened messaging interface.
        payload_data = msg.get_json_payload()
        command = payload_data.get("command")
        query = payload_data.get("query", False)
        correlation_id = payload_data.get("correlation_id", "N/A")

        if command:
            self.command_queue.put(
                {
                    "command": command,
                    "query": query,
                    "correlation_id": correlation_id,
                }
            )
            if LOCAL_DEBUG: logger.trace(f"💳 ℹ️ Proxy Log: 💳Command '{command}' enqueued. Query: {query}")
        else:
            self._publish_proxy_error(
                message="Received empty command in Tx_Inbox.", command=msg.decode_payload()
            )

    def _publish_proxy_error(self, message: str, command: str = "N/A"):
        """Logs and publishes proxy-level error information.

        Parameters:
        - message: Detailed error description.
        - command: The SCPI command that caused the error.

        Returns:
        - None.
        """
        logger.error(f"💳 ❌ Proxy Error: {message} (Command: {command})")

    def _publish_proxy_response(
        self, response: str, command: str = "N/A", correlation_id: str = "N/A"
    ):
        """Logs the response received from an instrument query.

        Parameters:
        - response: The raw data returned by the instrument.
        - command: The original query command.
        - correlation_id: Optional ID for tracking asynchronous results.

        Returns:
        - None.
        """
        if LOCAL_DEBUG: logger.trace(f"💳 📡📡⬆️⬆️ Proxy Response: {response} (Command: {command}, CorrID: {correlation_id})")

    def set_instrument_instance(self, inst):
        """Links a physical instrument session to the proxy and starts worker.

        Parameters:
        - inst: The pyvisa.Resource instance. If None, the proxy is shut down.

        Returns:
        - None.

        Side effects and thread-safety:
        - Configures instrument session timeout.
        - Manages the lifecycle of the background worker thread.
        """
        current_function_name = inspect.currentframe().f_code.co_name
        if LOCAL_DEBUG: logger.debug(f"💳 🟢️️️🔵 Received new instrument instance. It's now my time to shine!")
        self.inst = inst
        if self.inst:
            self.inst.timeout = 5000
            if LOCAL_DEBUG: logger.success("💳 ℹ️ Proxy Log: ✅ VisaProxy is now linked to an instrument.")

            # Start the worker thread if it's not already running.
            if self.worker_thread is None or not self.worker_thread.is_alive():
                self.shutdown_flag = threading.Event()
                self.worker_thread = threading.Thread(
                    target=self._command_processor_worker, daemon=True
                )
                self.worker_thread.start()
                if LOCAL_DEBUG: logger.debug("💳 ℹ️ Proxy Log: Command processor worker thread started on connection.")
        else:
            # Cleanly shut down if the instrument is disconnected.
            self.shutdown()
            logger.warning("💳 ℹ️ Proxy Log: ✅ VisaProxy has been unlinked from the instrument.")

    def _reset_device(self):
        """Sends a standard IEEE 488.2 reset command (*RST) to the device.

        Returns:
        - True if the command was successfully sent.
        - False if communication failed.
        """
        current_function_name = inspect.currentframe().f_code.co_name
        if LOCAL_DEBUG: logger.debug(f"💳 ℹ️ Proxy Log: Attempting a system-wide reset!")
        
        logger.warning("💳 ℹ️ Proxy Log: ⚠️ Command failed. Attempting to reset the instrument with '*RST'...")
        reset_success = self.write_safe(command="*RST")

        if reset_success:
            if LOCAL_DEBUG: logger.success("💳 ℹ️ Proxy Log: ✅ Success! The device reset command was sent successfully.")
        else:
            self._publish_proxy_error(
                message="❌ Failure! The device did not respond to the reset command.",
                command="*RST",
            )
        return reset_success


    def write_safe(self, command):
        """Executes a non-query SCPI command with error handling.

        Parameters:
        - command: The SCPI string to write.

        Returns:
        - The result of the external write_safe utility.
        """
        return write_safe(self, command)

    def query_safe(self, command, correlation_id="N/A"):
        """Executes a SCPI query command and returns the response safely.

        Parameters:
        - command: The SCPI query string.
        - correlation_id: Tracking ID for the response.

        Returns:
        - The result of the external query_safe utility.
        """
        return query_safe(self, command, correlation_id)
