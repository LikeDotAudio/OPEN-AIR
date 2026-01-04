# managers/VisaScipi/manager_visa_proxy.py
#
# This manager provides a safe, low-level interface for executing SCPI write
# and query commands via PyVISA.
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

from managers.configini.config_reader import Config
app_constants = Config.get_instance()

from workers.logger.logger import  debug_logger
from workers.logger.log_utils import _get_log_args
from .manager_visa_safe_writer import write_safe
from .manager_visa_safe_query import query_safe

class VisaProxy:
    """
    Manages the PyVISA connection and provides safe, low-level command execution.
    """
    def __init__(self, mqtt_controller, subscriber_router):
        current_function_name = inspect.currentframe().f_code.co_name
        debug_logger(
            message=f"💳 🟢️️️🟢 ➡️➡️ {current_function_name}. The grand SCPI experiment begins!",
            **_get_log_args()
        )
        try:
            self.mqtt_util = mqtt_controller
            self.subscriber_router = subscriber_router
            self.inst = None
            self.model = ""
            self.manufacturer = ""
            
            self.command_queue = queue.Queue()
            self.shutdown_flag = None
            self.worker_thread = None

            self._setup_mqtt_subscriptions()

        except Exception as e:
            debug_logger(
                message=f"💳 🟢️️️🔴 By Jove, the apparatus has failed to initialize! The error be: {e}",
              **_get_log_args()
            )

    def shutdown(self):
        if self.worker_thread and self.worker_thread.is_alive():
            debug_logger(message="💳 ℹ️ Proxy Log: Shutting down VisaProxy command processor worker.", **_get_log_args())
            if self.shutdown_flag:
                self.shutdown_flag.set()
            self.command_queue.put(None)
            self.worker_thread.join(timeout=1)
            if self.worker_thread.is_alive():
                self._publish_proxy_error(message="VisaProxy worker thread did not terminate gracefully.")
            self.worker_thread = None
            self.shutdown_flag = None
        else:
            debug_logger(message="💳 ℹ️ Proxy Log: VisaProxy worker thread not active or already shut down.", **_get_log_args())

    def _command_processor_worker(self):
        while not self.shutdown_flag.is_set():
            command_info = None
            try:
                command_info = self.command_queue.get(block=False)
                if command_info is None:
                    break
                
                command = command_info["command"]
                query = command_info["query"]
                correlation_id = command_info["correlation_id"]

                if query:
                    self.query_safe(command, correlation_id)
                else:
                    self.write_safe(command)
                
                self.command_queue.task_done()
            except (_queue.Empty, queue.Empty):
                if app_constants.global_settings['debug_enabled']:
                    debug_logger(message="💳 Queue is empty, worker sleeping briefly...", **_get_log_args())
                time.sleep(0.01)
                continue
            except Exception as e:
                cmd_for_error = command_info.get("command", "N/A") if command_info is not None else "N/A"
                if app_constants.global_settings['debug_enabled']:
                    debug_logger(message=f"💳 Unhandled exception in command processor worker: {e}", **_get_log_args(), level="CRITICAL")
                self._publish_proxy_error(message=f"Error in command processor worker: {e}", command=cmd_for_error)
                if command_info is not None:
                    self.command_queue.task_done()
        debug_logger(message="💳 ℹ️ Proxy Log: VisaProxy command processor worker terminated.", **_get_log_args())

    def _setup_mqtt_subscriptions(self):
        topic = "OPEN-AIR/Proxy/Tx_Inbox"
        self.subscriber_router.subscribe_to_topic(topic, self._on_tx_inbox_message)
        debug_logger(message=f"💳 ℹ️ Proxy Log: 💳Subscribed to '{topic}' for inbound proxy commands.", **_get_log_args())

    def _on_tx_inbox_message(self, topic, payload):
        current_function_name = inspect.currentframe().f_code.co_name
        debug_logger(message=f"💳 📡📡⬇️⬇️ PROXY IN: Tx_Inbox message received on Topic: '{topic}', Payload: '{payload}'. Proxy will process this as a raw SCPI command.", **_get_log_args())

        try:
            payload_data = orjson.loads(payload)
            command = payload_data.get("command")
            query = payload_data.get("query", False)
            correlation_id = payload_data.get("correlation_id", "N/A")

            if command:
                self.command_queue.put({
                    "command": command,
                    "query": query,
                    "correlation_id": correlation_id
                })
                debug_logger(message=f"💳 ℹ️ Proxy Log: 💳Command '{command}' enqueued. Query: {query}", **_get_log_args())
            else:
                self._publish_proxy_error(message="Received empty command in Tx_Inbox.", command=payload)
        except orjson.JSONDecodeError:
            self._publish_proxy_error(message=f"💳Failed to decode JSON payload from '{topic}': {payload}")
        except Exception as e:
            self._publish_proxy_error(message=f"💳Error processing message from '{topic}': {e}", command=payload)

    def _publish_proxy_error(self, message: str, command: str = "N/A"):
        debug_logger(message=f"💳 ❌ Proxy Error: {message} (Command: {command})", **_get_log_args(), level="ERROR")

    def _publish_proxy_response(self, response: str, command: str = "N/A", correlation_id: str = "N/A"):
        debug_logger(message=f"💳 📡📡⬆️⬆️ Proxy Response: {response} (Command: {command}, CorrID: {correlation_id})", **_get_log_args())

    def set_instrument_instance(self, inst):
        current_function_name = inspect.currentframe().f_code.co_name
        debug_logger(
            message=f"💳 🟢️️️🔵 Received new instrument instance. It's now my time to shine!",
            **_get_log_args()
        )
        self.inst = inst
        if self.inst:
            self.inst.timeout = 5000
            debug_logger(message="💳 ℹ️ Proxy Log: ✅ VisaProxy is now linked to an instrument.", **_get_log_args())
            
            if self.worker_thread is None or not self.worker_thread.is_alive():
                self.shutdown_flag = threading.Event()
                self.worker_thread = threading.Thread(target=self._command_processor_worker, daemon=True)
                self.worker_thread.start()
                debug_logger(message="💳 ℹ️ Proxy Log: Command processor worker thread started on connection.", **_get_log_args())
        else:
            self.shutdown()
            debug_logger(message="💳 ℹ️ Proxy Log: ✅ VisaProxy has been unlinked from the instrument.", **_get_log_args(), level="WARNING")

    def _reset_device(self):
        current_function_name = inspect.currentframe().f_code.co_name
        debug_logger(message=f"💳 ℹ️ Proxy Log: Attempting a system-wide reset!", **_get_log_args())
        try:
            debug_logger(message="💳 ℹ️ Proxy Log: ⚠️ Command failed. Attempting to reset the instrument with '*RST'...", **_get_log_args(), level="WARNING")
            reset_success = self.write_safe(command="*RST")

            if reset_success:
                debug_logger(message="💳 ℹ️ Proxy Log: ✅ Success! The device reset command was sent successfully.", **_get_log_args())
            else:
                self._publish_proxy_error(message="❌ Failure! The device did not respond to the reset command.", command="*RST")
            return reset_success

        except Exception as e:
            error_msg = f"❌ Error in {current_function_name}: {e}"
            self._publish_proxy_error(message=error_msg)
            return False

    def write_safe(self, command):
        return write_safe(self, command)

    def query_safe(self, command, correlation_id="N/A"):
        return query_safe(self, command, correlation_id)