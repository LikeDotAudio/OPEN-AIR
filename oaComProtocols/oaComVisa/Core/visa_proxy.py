# Core/visa_proxy.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: This manager provides a safe, low-level interface for executing SCPI write

import inspect
import queue
import threading
import time

# --- Standard OPEN-AIR Logging ---
from loguru import logger

from oaComProtocols.oaComMQTT.Core.mqtt_message import MqttMessage
from oaConfigurationManager.FileReaders.config_reader import Config
from oaLogging.Methods.matrix_gate import matrix_log

app_constants = Config.get_instance()

from .visa_safe_query import query_safe
from .visa_safe_writer import write_safe


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
        matrix_log("comms", "visa", current_function_name, f"💳 🟢️️️🟢 ➡️➡️ {current_function_name}. The grand SCPI experiment begins!", "DEBUG")

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
            matrix_log("comms", "visa", "shutdown", "💳 ℹ️ Proxy Log: Shutting down VisaProxy command processor worker.", "DEBUG")
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
            matrix_log("comms", "visa", "shutdown", "💳 ℹ️ Proxy Log: VisaProxy worker thread not active or already shut down.", "DEBUG")

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

            try:
                command = command_info["command"]
                query = command_info["query"]
                correlation_id = command_info["correlation_id"]

                if query:
                    self.query_safe(command, correlation_id)
                else:
                    self.write_safe(command)
            except Exception as e:
                # ⚡ THREAD SAFETY: Catching all exceptions to prevent worker death
                self._publish_proxy_error(
                    message=f"Exception during background command execution: {str(e)}",
                    command=command_info.get("command", "Unknown")
                )
            finally:
                self.command_queue.task_done()

        matrix_log("comms", "visa", "_command_processor_worker", "💳 ℹ️ Proxy Log: VisaProxy command processor worker terminated.", "DEBUG")


    def _setup_mqtt_subscriptions(self):
        """Registers the inbound command inbox topic.

        Returns:
        - None.
        """
        topic = "OPEN-AIR/Proxy/Tx_Inbox"
        self.subscriber_router.subscribe_to_topic(topic, self._on_tx_inbox_message)
        matrix_log("comms", "visa", "_setup_mqtt_subscriptions", f"💳 ℹ️ Proxy Log: 💳Subscribed to '{topic}' for inbound proxy commands.", "DEBUG")

    def _on_tx_inbox_message(self, message: MqttMessage):
        """Handles inbound MQTT messages intended for instrument execution.

        Parameters:
        - message: The MqttMessage object containing the command payload.

        Returns:
        - None.

        Side effects and thread-safety:
        - Enqueues command information for the background worker thread.
        """
        current_function_name = inspect.currentframe().f_code.co_name
        matrix_log("comms", "visa", current_function_name, f"💳 📡📡⬇️⬇️ PROXY IN: Tx_Inbox message received on Topic: '{message.topic}', Payload: '{message.payload}'. Proxy will process this as a raw SCPI command.", "TRACE")

        # Extract command parameters from the hardened messaging interface.
        payload_data = message.get_json_payload()
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
            matrix_log("comms", "visa", current_function_name, f"💳 ℹ️ Proxy Log: 💳Command '{command}' enqueued. Query: {query}", "TRACE")
        else:
            self._publish_proxy_error(
                message="Received empty command in Tx_Inbox.", command=message.decode_payload()
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
        matrix_log("comms", "visa", "_publish_proxy_response", f"💳 📡📡⬆️⬆️ Proxy Response: {response} (Command: {command}, CorrID: {correlation_id})", "TRACE")

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
        matrix_log("comms", "visa", current_function_name, "💳 🟢️️️🔵 Received new instrument instance. It's now my time to shine!", "DEBUG")
        self.inst = inst
        if self.inst:
            self.inst.timeout = 5000
            matrix_log("comms", "visa", current_function_name, "💳 ℹ️ Proxy Log: ✅ VisaProxy is now linked to an instrument.", "SUCCESS")

            # Start the worker thread if it's not already running.
            if self.worker_thread is None or not self.worker_thread.is_alive():
                self.shutdown_flag = threading.Event()
                self.worker_thread = threading.Thread(
                    target=self._command_processor_worker, daemon=True
                )
                self.worker_thread.start()
                matrix_log("comms", "visa", current_function_name, "💳 ℹ️ Proxy Log: Command processor worker thread started on connection.", "DEBUG")
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
        matrix_log("comms", "visa", current_function_name, "💳 ℹ️ Proxy Log: Attempting a system-wide reset!", "DEBUG")

        logger.warning("💳 ℹ️ Proxy Log: ⚠️ Command failed. Attempting to reset the instrument with '*RST'...")
        reset_success = self.write_safe(command="*RST")

        if reset_success:
            matrix_log("comms", "visa", current_function_name, "💳 ℹ️ Proxy Log: ✅ Success! The device reset command was sent successfully.", "SUCCESS")
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
