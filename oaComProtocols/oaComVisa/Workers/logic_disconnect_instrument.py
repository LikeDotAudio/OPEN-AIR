from oaLogging.Methods.matrix_gate import matrix_log
# Workers/logic_disconnect_instrument.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import inspect

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = False
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfigurationManager.FileReaders.config_reader import Config

app_constants = Config.get_instance()


def disconnect_instrument(inst):
    """Closes the connection to a VISA instrument.

    Parameters:
    - inst: The pyvisa.Resource instance to close. Can be None.

    Returns:
    - True if the instrument was successfully closed.
    - False if no instrument was provided or if an error occurred during
      the closing process.

    Side effects and thread-safety:
    - Performs blocking I/O to terminate the hardware session.
    - Does not modify global state; only affects the provided object.
    """
    current_function = inspect.currentframe().f_code.co_name
    matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "💳 Disconnecting instrument... Saying goodbye!", "DEBUG")
    if inst:
        try:
            inst.close()

            matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "💳 Instrument connection closed. All done!", "DEBUG")
            return True
        except Exception as e:
            error_message = f"💳 ❌ An unexpected error occurred while disconnecting instrument: {e}."

            if LOCAL_DEBUG:
                logger.debug(error_message)
            return False
    matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "💳 No instrument to disconnect. Already gone!", "DEBUG")
    return False


class VisaDisconnector:
    """Manages the disconnection sequence and state cleanup for VISA instruments."""

    def __init__(self, visa_proxy, gui_publisher):
        """Initializes the VisaDisconnector with communication proxies.

        Parameters:
        - visa_proxy: The central proxy used to manage the active instrument.
        - gui_publisher: The dispatcher for status updates.

        Returns:
        - None.
        """
        self.visa_proxy = visa_proxy
        self.gui_publisher = gui_publisher

    def disconnect_instrument_logic(self, inst):
        """Disconnects the application from the target VISA instrument.

        This method coordinates the hardware disconnection, proxy reset,
        and UI metadata clearing.

        Parameters:
        - inst: The active pyvisa.Resource instance. Can be None.

        Returns:
        - True if the disconnection logic completed successfully.
        - False if the underlying hardware close operation failed.

        Side effects and thread-safety:
        - Resets the global visa_proxy instrument instance to None.
        - Publishes multiple status updates to clear device-specific info.
        """
        if not inst:
            # If no instrument is present, ensure the proxy is reset and 
            # the UI reflects the disconnected state.
            self.visa_proxy.set_instrument_instance(inst=None)
            self.gui_publisher._publish_proxy_status("DISCONNECTED")
            return True

        result = disconnect_instrument(inst)

        # Clear the proxy session regardless of whether the close succeeded,
        # as the session is no longer viable.
        self.visa_proxy.set_instrument_instance(inst=None)

        # Reset all UI fields to 'N/A' to indicate no active hardware.
        self.gui_publisher._publish_status("disconnected", True)
        self.gui_publisher._publish_status("connected", False)
        self.gui_publisher._publish_status("brand", "N/A")
        self.gui_publisher._publish_status("device_model", "N/A")
        self.gui_publisher._publish_status("device_series", "N/A")
        self.gui_publisher._publish_status("device_serial_number", "N/A")
        self.gui_publisher._publish_status("device_firmware", "N/A")
        self.gui_publisher._publish_status("visa_resource", "N/A")
        self.gui_publisher._publish_status("Time_connected", "N/A")
        self.gui_publisher._publish_proxy_status("DISCONNECTED")

        return result
