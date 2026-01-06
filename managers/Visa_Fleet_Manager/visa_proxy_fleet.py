# managers/Visa_Fleet_Manager/visa_proxy_fleet.py
#
# Refactored VisaProxy for fleet management, handling device-specific communication via Manager callbacks.
#
# Author: Gemini Agent
#
import os
import inspect
import pyvisa
import time
import queue
import threading
import _queue

try:
    from workers.logger.logger import debug_logger
    from workers.logger.log_utils import _get_log_args
except ModuleNotFoundError:
    print("Warning: 'workers.logger' not found. Using dummy logger for VisaProxyFleet.")

    def debug_logger(message, *args, **kwargs):
        if kwargs.get("level", "INFO") != "DEBUG":
            print(f"[{kwargs.get('level', 'INFO')}] {message}")

    def _get_log_args(*args, **kwargs):
        return {}  # Return empty dict, as logger args are not available


# --- Helper functions for safe VISA operations ---
# These now interact directly with the proxy instance's manager callbacks.


def _write_safe_fleet(proxy_instance, command):
    # Safely writes a SCPI command to the instrument for the fleet proxy.
    debug_logger(
        message=f"💳 ℹ️ FleetProxy Log ({proxy_instance.device_serial}): 💳💳⬆️⬆️ Send Visa Command: Transmitting command: {command}",
        **_get_log_args(),
    )

    if not proxy_instance.inst:
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

    try:
        proxy_instance.inst.write(command)
        debug_logger(
            message=f"💳 ℹ️ FleetProxy Log ({proxy_instance.device_serial}): ✅ Sent command: {command}",
            **_get_log_args(),
        )
        return True
    except Exception as e:
        error_msg = (
            f"Error writing command '{command}' to {proxy_instance.device_serial}: {e}"
        )
        proxy_instance.manager._notify_error(
            serial=proxy_instance.device_serial, message=error_msg, command=command
        )

        # Attempt a device-specific reset if it's not a reset command itself
        if command.strip().upper() not in ["*RST", ":SYSTem:POWer:RESet"]:
            proxy_instance._reset_device_fleet()
        return False


def _query_safe_fleet(proxy_instance, command, correlation_id="N/A"):
    # Safely queries the instrument with a SCPI command and returns the response for the fleet proxy.
    debug_logger(
        message=f"💳 ℹ️ FleetProxy Log ({proxy_instance.device_serial}): 💳💳⬆️⬆️ Send Visa Command: Querying command: {command}",
        **_get_log_args(),
    )

    if not proxy_instance.inst:
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

    try:
        response = proxy_instance.inst.query(command).strip()
        debug_logger(
            message=f"💳 ℹ️ FleetProxy Log ({proxy_instance.device_serial}): ✅ Sent query: {command}",
            **_get_log_args(),
        )
        debug_logger(
            message=f"💳 ℹ️ FleetProxy Log ({proxy_instance.device_serial}): 💳💳⬇️⬇️ RX Visa Response: Received response: {response}",
            **_get_log_args(),
        )

        # Notify the manager of the response
        proxy_instance.manager._notify_response(
            serial=proxy_instance.device_serial,
            response=response,
            command=command,
            corr_id=correlation_id,
        )
        return response
    except Exception as e:
        error_msg = f"Error querying command '{command}' from {proxy_instance.device_serial}: {e}"
        proxy_instance.manager._notify_error(
            serial=proxy_instance.device_serial, message=error_msg, command=command
        )

        # Attempt a device-specific reset if it's not a reset command itself
        if command.strip().upper() not in ["*RST", ":SYSTem:POWer:RESet"]:
            proxy_instance._reset_device_fleet()
        return None


class VisaProxyFleet:
    """
    Manages a single PyVISA connection for a specific instrument in a fleet.
    Communicates via callbacks to the managing entity (VisaFleetManager).
    """

    def __init__(
        self,
        manager_ref,
        device_serial,
        resource_name,
        instrument_model="Generic",
        manufacturer="Unknown Manufacturer",
    ):
        current_function_name = inspect.currentframe().f_code.co_name
        self.manager = manager_ref  # Reference to the VisaFleetManager
        self.device_serial = device_serial  # Unique identifier for this device
        self.resource_name = resource_name  # e.g., 'USB0::...' or 'GPIB::10::INSTR'
        self.instrument_model = instrument_model  # e.g., 'TDS2024C'
        self.manufacturer = manufacturer  # Stored for inventory details

        debug_logger(
            message=f"💳 🟢️️️🟢 ➡️➡️ {current_function_name} for {self.device_serial} ({self.resource_name}). Initializing proxy.",
            **_get_log_args(),
        )

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
        debug_logger(
            message=f"💳 ℹ️ FleetProxy Log ({self.device_serial}): Command processor worker thread started.",
            **_get_log_args(),
        )

    def shutdown(self):
        """Shuts down the proxy, stopping the worker thread and clearing resources."""
        debug_logger(
            message=f"💳 ℹ️ FleetProxy Log ({self.device_serial}): Shutting down proxy.",
            **_get_log_args(),
        )
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
            debug_logger(
                message=f"💳 ℹ️ FleetProxy Log ({self.device_serial}): Worker thread not active or already shut down.",
                **_get_log_args(),
            )

        # Ensure connection is closed if proxy is shut down
        if self.inst:
            try:
                self.inst.close()
                debug_logger(
                    message=f"💳 ℹ️ FleetProxy Log ({self.device_serial}): Closed PyVISA instrument instance during shutdown.",
                    **_get_log_args(),
                )
            except Exception as e:
                self.manager._notify_error(
                    serial=self.device_serial,
                    message=f"Error closing instrument during shutdown: {e}",
                    command="shutdown",
                )
            self.inst = None
            self.is_connected = False
            self.manager._notify_status(
                serial=self.device_serial, status="DISCONNECTED"
            )

    def _command_processor_worker(self):
        """Worker thread to process commands from the queue."""
        while not self.shutdown_flag.is_set():
            command_info = None
            try:
                command_info = self.command_queue.get(
                    block=True, timeout=0.5
                )  # Block with timeout
                if command_info is None:  # Exit signal
                    break

                command = command_info["command"]
                query = command_info["query"]
                correlation_id = command_info["correlation_id"]

                if query:
                    _query_safe_fleet(self, command, correlation_id)
                else:
                    _write_safe_fleet(self, command)

                self.command_queue.task_done()
            except (_queue.Empty, queue.Empty):
                # Queue is empty, continue waiting
                continue
            except Exception as e:
                cmd_for_error = (
                    command_info.get("command", "N/A")
                    if command_info is not None
                    else "N/A"
                )
                debug_logger(
                    message=f"💳 Unhandled exception in FleetProxy worker for {self.device_serial}: {e}",
                    **_get_log_args(),
                    level="CRITICAL",
                )
                self.manager._notify_error(
                    serial=self.device_serial,
                    message=f"Unhandled worker exception: {e}",
                    command=cmd_for_error,
                )
                if command_info is not None:
                    self.command_queue.task_done()  # Mark task done even on error to prevent queue buildup
        debug_logger(
            message=f"💳 ℹ️ FleetProxy Log ({self.device_serial}): Command processor worker terminated.",
            **_get_log_args(),
        )

    def enqueue_command(self, command, query=False, correlation_id="N/A"):
        """Public method for the manager to enqueue a command to this proxy."""
        self.command_queue.put(
            {"command": command, "query": query, "correlation_id": correlation_id}
        )
        debug_logger(
            message=f"💳 ℹ️ FleetProxy Log ({self.device_serial}): Command '{command}' enqueued. Query: {query}",
            **_get_log_args(),
        )

    def set_instrument_instance(self, inst):
        """Sets the PyVISA instrument instance and updates connection status."""
        current_function_name = inspect.currentframe().f_code.co_name

        self.inst = inst
        if self.inst:
            self.inst.timeout = 5000  # Default timeout
            debug_logger(
                message=f"💳 ℹ️ FleetProxy Log ({self.device_serial}): Proxy is now linked to instrument instance.",
                **_get_log_args(),
            )
            self.is_connected = True
            self.manager._notify_status(serial=self.device_serial, status="CONNECTED")
        else:
            self.is_connected = False
            self.manager._notify_status(
                serial=self.device_serial, status="DISCONNECTED"
            )
            debug_logger(
                message=f"💳 ℹ️ FleetProxy Log ({self.device_serial}): Proxy unlinked from instrument instance.",
                **_get_log_args(),
                level="WARNING",
            )
            # If the instance is set to None, it implies disconnection, so shut down the worker thread if it's still running
            # self.shutdown() # Removed to prevent recursive shutdown calls if set_instrument_instance(None) is called during shutdown

    def _reset_device_fleet(self):
        """Attempts to reset the connected instrument using standard SCPI commands."""
        debug_logger(
            message=f"💳 ℹ️ FleetProxy Log ({self.device_serial}): Attempting a system-wide reset for the device.",
            **_get_log_args(),
        )
        try:
            debug_logger(
                message=f"💳 ℹ️ FleetProxy Log ({self.device_serial}): ⚠️ Command failed. Attempting to reset the instrument with '*RST'...",
                **_get_log_args(),
                level="WARNING",
            )
            reset_success = _write_safe_fleet(self, command="*RST")

            if reset_success:
                debug_logger(
                    message=f"💳 ℹ️ FleetProxy Log ({self.device_serial}): ✅ Success! The device reset command was sent.",
                    **_get_log_args(),
                )
            else:
                self.manager._notify_error(
                    serial=self.device_serial,
                    message="❌ Failure! The device did not respond to the reset command.",
                    command="*RST",
                )
            return reset_success

        except Exception as e:
            error_msg = f"❌ Error in _reset_device_fleet for {self.device_serial}: {e}"
            self.manager._notify_error(serial=self.device_serial, message=error_msg)
            return False
