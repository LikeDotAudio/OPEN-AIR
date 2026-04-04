from oaLogging.Methods.matrix_gate import matrix_log
# Core/visa_proxy_fleet.py
# Author: Gemini Agent
# Version: 1.0.0
#
# Description: Refactored VisaProxy for fleet management, handling device-specific communication via Manager callbacks.

import os
import inspect
import pyvisa
import time
import queue
import threading
import _queue

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()


# --- Helper functions for safe VISA operations ---
# These now interact directly with the proxy instance's manager callbacks.


def _write_safe_fleet(proxy_instance, command):
    # Safely writes a SCPI command to the instrument for the fleet proxy.
    matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 ℹ️ FleetProxy Log ({proxy_instance.device_serial}): 💳💳⬆️⬆️ Send Visa Command: Transmitting command: {command}", "TRACE")

    if not proxy_instance.inst or not proxy_instance.inst.session:
        error_msg = f"Instrument {proxy_instance.device_serial} not connected. Cannot write command."
        proxy_instance.manager._notify_error(
            serial=proxy_instance.device_serial, message=error_msg, command=command
        )
        return False

    if "<" in command or ">" in command:  # Basic check for placeholders
        error_msg = f"Command rejected. Unresolved placeholders found in '{command}' for device {proxy_instance.device_serial}."
        proxy_instance.manager._notify_error(
            serial=proxy_instance.device_serial, message=error_msg, command=command
        )
        return False

    # ⚡ DIRECT CALL: Assuming hardware state is validated or fatal if not
    proxy_instance.inst.write(command)
    matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 ℹ️ FleetProxy Log ({proxy_instance.device_serial}): ✅ Sent command: {command}", "SUCCESS")
    return True


def _query_safe_fleet(proxy_instance, command, correlation_id="N/A"):
    # Safely queries the instrument with a SCPI command and returns the response for the fleet proxy.
    matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 ℹ️ FleetProxy Log ({proxy_instance.device_serial}): 💳💳⬆️⬆️ Send Visa Command: Querying command: {command}", "TRACE")

    if not proxy_instance.inst or not proxy_instance.inst.session:
        error_msg = f"Instrument {proxy_instance.device_serial} not connected. Cannot query command."
        proxy_instance.manager._notify_error(
            serial=proxy_instance.device_serial, message=error_msg, command=command
        )
        return None

    if "<" in command or ">" in command:  # Basic check for placeholders
        error_msg = f"Query rejected. Unresolved placeholders found: '{command}' for device {proxy_instance.device_serial}."
        proxy_instance.manager._notify_error(
            serial=proxy_instance.device_serial, message=error_msg, command=command
        )
        return None

    # ⚡ DIRECT CALL: Assuming hardware state is validated or fatal if not
    # We use write then a polling read for 'Zero Exception' architecture
    proxy_instance.inst.write(command)
    
    # ⚡ POLLING READ: Instead of a blocking query() which might timeout/exception
    # Wait for data to arrive in buffer
    start_wait = time.time()
    while proxy_instance.inst.bytes_in_buffer == 0 and (time.time() - start_wait) < (proxy_instance.inst.timeout / 1000.0):
        time.sleep(0.01)
    
    if proxy_instance.inst.bytes_in_buffer == 0:
        logger.error(f"💳 ℹ️ FleetProxy Log ({proxy_instance.device_serial}): ❌ Timeout waiting for response to {command}")
        return None

    response = proxy_instance.inst.read().strip()
    
    matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 ℹ️ FleetProxy Log ({proxy_instance.device_serial}): ✅ Sent query: {command}", "SUCCESS")
    matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 ℹ️ FleetProxy Log ({proxy_instance.device_serial}): 💳💳⬇️⬇️ RX Visa Response: Received response: {response}", "TRACE")

    # Notify the manager of the response
    proxy_instance.manager._notify_response(
        serial=proxy_instance.device_serial,
        response=response,
        command=command,
        corr_id=correlation_id,
    )
    return response



class VisaProxyFleet:
    """
    Manages a single PyVISA connection for a specific instrument in a fleet.
    Communicates via callbacks to the managing entity (FleetOrchestrator).
    """

    def __init__(
        self,
        manager_ref,
        device_serial,
        resource_name,
        instrument_model="Generic",
        manufacturer="Unknown Manufacturer",
    ):
        self.manager = manager_ref  # Reference to the FleetOrchestrator
        self.device_serial = device_serial  # Unique identifier for this device
        self.resource_name = resource_name  # e.g., 'USB0::...' or 'GPIB::10::INSTR'
        self.instrument_model = instrument_model  # e.g., 'TDS2024C'
        self.manufacturer = manufacturer  # Stored for inventory details

        matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 🟢️️️🟢 ➡️➡️ __init__ for {self.device_serial} ({self.resource_name}). Initializing proxy.", "DEBUG")

        self.inst = None  # The actual pyvisa instrument instance

        self.command_queue = queue.Queue()
        self.shutdown_flag = None
        self.worker_thread = None
        self.is_connected = False

        # Start the command processing worker immediately upon instantiation
        self.shutdown_flag = threading.Event()
        self.worker_thread = threading.Thread(
            target=self._command_processor_worker, daemon=True
        )
        self.worker_thread.start()
        matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 ℹ️ FleetProxy Log ({self.device_serial}): Command processor worker thread started.", "DEBUG")

    def shutdown(self):
        """Shuts down the proxy, stopping the worker thread and clearing resources."""
        matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 ℹ️ FleetProxy Log ({self.device_serial}): Shutting down proxy.", "DEBUG")
        if self.worker_thread and self.worker_thread.is_alive():
            if self.shutdown_flag:
                self.shutdown_flag.set()
            self.command_queue.put(None)  # Signal worker to exit
            self.worker_thread.join(timeout=2)  # Wait for thread to finish
            if self.worker_thread.is_alive():
                self.manager._notify_error(
                    serial=self.device_serial,
                    message="VisaProxyFleet worker thread did not terminate gracefully.",
                    command="shutdown",
                )
        else:
            matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 ℹ️ FleetProxy Log ({self.device_serial}): Worker thread not active or already shut down.", "DEBUG")

        # Ensure connection is closed if proxy is shut down
        if self.inst:
            # We assume close() is safe or fatal if not
            self.inst.close()
            matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 ℹ️ FleetProxy Log ({self.device_serial}): Closed PyVISA instrument instance during shutdown.", "DEBUG")
            self.inst = None
            self.is_connected = False
            self.manager._notify_status(
                serial=self.device_serial, status="DISCONNECTED"
            )

    def _command_processor_worker(self):
        """
        Worker thread to process commands from the queue.
        ⚡ OPTIMIZATION: Uses pure blocking get() with a Poison Pill for shutdown (Rule #5).
        """
        while True:
            # ⚡ BLOCKING: Consumes zero CPU while waiting for commands
            command_info = self.command_queue.get()
            
            if command_info is None: # The Poison Pill
                break

            command = command_info["command"]
            query = command_info["query"]
            correlation_id = command_info["correlation_id"]

            if query:
                _query_safe_fleet(self, command, correlation_id)
            else:
                _write_safe_fleet(self, command)

            self.command_queue.task_done()
            
        matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 ℹ️ FleetProxy Log ({self.device_serial}): Command processor worker terminated.", "DEBUG")

    def enqueue_command(self, command, query=False, correlation_id="N/A"):
        """Public method for the manager to enqueue a command to this proxy."""
        self.command_queue.put(
            {"command": command, "query": query, "correlation_id": correlation_id}
        )
        matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 ℹ️ FleetProxy Log ({self.device_serial}): Command '{command}' enqueued. Query: {query}", "DEBUG")

    def set_instrument_instance(self, inst):
        """Sets the PyVISA instrument instance and updates connection status."""
        self.inst = inst
        if self.inst:
            self.inst.timeout = 5000  # Default timeout
            matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 ℹ️ FleetProxy Log ({self.device_serial}): Proxy is now linked to instrument instance.", "DEBUG")
            self.is_connected = True
            self.manager._notify_status(serial=self.device_serial, status="CONNECTED")
        else:
            self.is_connected = False
            self.manager._notify_status(
                serial=self.device_serial, status="DISCONNECTED"
            )
            logger.warning(
                f"💳 ℹ️ FleetProxy Log ({self.device_serial}): Instrument instance is None. Connection lost."
            )
            # If the instance is set to None, it implies disconnection, so shut down the worker thread if it's still running
            # self.shutdown() # Removed to prevent recursive shutdown calls if set_instrument_instance(None) is called during shutdown

    def _reset_device_fleet(self):
        """Attempts to reset the connected instrument using standard SCPI commands."""
        matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 ℹ️ FleetProxy Log ({self.device_serial}): Attempting a system-wide reset for the device.", "DEBUG")
        logger.warning(
            f"💳 ℹ️ FleetProxy Log ({self.device_serial}): Instrument instance is None. Connection lost."
        )
        reset_success = _write_safe_fleet(self, command="*RST")

        if reset_success:
            matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 ℹ️ FleetProxy Log ({self.device_serial}): ✅ Success! The device reset command was sent.", "SUCCESS")
        else:
            self.manager._notify_error(
                serial=self.device_serial,
                message="❌ Failure! The device did not respond to the reset command.",
                command="*RST",
            )
        return reset_success

