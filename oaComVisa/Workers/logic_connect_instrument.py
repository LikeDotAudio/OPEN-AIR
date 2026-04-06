from oaLogging.Methods.matrix_gate import matrix_log
# oaComVisa/Workers/logic_connect_instrument.py
# Author: Anthony Peter Kuzub
# Version: 20260322.1130.1
#
# Description: Provides the logic for connecting to a VISA instrument, managing the lifecycle of the connection through PyVISA and instrument identification via SCPI *IDN? queries.

import pyvisa
import inspect
import datetime

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True
from oaLogging.Core.logger import initialize_logging, set_log_directory, visa_logger
from loguru import logger

from oaConfigurationManager.FileReaders.config_reader import Config

app_constants = Config.get_instance()


class VisaConnector:
    """Manages the connection lifecycle for VISA-compliant instruments."""

    def __init__(self, visa_proxy, gui_publisher):
        """Initializes the VisaConnector with communication proxies.

        Parameters:
        - visa_proxy: The central proxy object used to store the active
          instrument session. Must not be None.
        - gui_publisher: The MQTT or GUI event dispatcher used to broadcast
          status updates. Must not be None.

        Returns:
        - None.

        Side effects and thread-safety:
        - Assigns proxy references to internal state. Not thread-safe if
          multiple threads attempt to initialize the same instance.
        """
        self.visa_proxy = visa_proxy
        self.gui_publisher = gui_publisher
        self.inst = None

    def setup_visa_instrument(self, resource_name):
        """Establishes a connection to a VISA instrument.

        Parameters:
        - resource_name: A string representing the VISA resource address
          (e.g., 'TCPIP::192.168.1.1::INSTR', 'GPIB0::7::INSTR').

        Returns:
        - A pyvisa.Resource object on success.
        - None if the connection fails or the resource is unavailable.

        Side effects and thread-safety:
        - Performs blocking I/O to initialize the hardware interface.
        - Configures instrument timeout (5s) and termination characters.
        """
        if LOCAL_DEBUG:
            matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Connecting to instrument: {resource_name}.", "DEBUG")
        try:
            rm = pyvisa.ResourceManager()
            inst = rm.open_resource(resource_name)
            # Set default communication parameters required for reliable
            # SCPI message exchange.
            inst.timeout = 5000
            inst.read_termination = "\n"
            inst.write_termination = "\n"
            inst.query_delay = 0.1

            if LOCAL_DEBUG:
                matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Connection successful to {resource_name}.", "SUCCESS")
            return inst
        except Exception as e:
            # ⚡ NON-GATED GRAVITY: Errors must remain outside debug gates.
            visa_logger.error(f"Unexpected error while connecting to {resource_name}: {e}.")
            return None

    def connect_instrument_logic(self, resource_name):
        """Handles the full connection sequence to a VISA instrument.

        This method coordinates the setup, session storage, and metadata
        extraction for a target instrument.

        Parameters:
        - resource_name: The VISA resource address string.

        Returns:
        - The pyvisa.Resource instance on success.
        - False if the connection or identification query fails.

        Side effects and thread-safety:
        - Updates the global visa_proxy with the new instrument session.
        - Dispatches multiple MQTT/GUI status messages for device metadata.
        - Performs synchronous SCPI queries; may block the calling thread.
        """
        try:
            self.inst = self.setup_visa_instrument(resource_name)
            if not self.inst:
                # Reset proxy and update UI to reflect failed connection state.
                self.visa_proxy.set_instrument_instance(inst=None)
                self.gui_publisher._publish_status("connected", False)
                self.gui_publisher._publish_status("disconnected", True)
                return False

            # Update the central proxy so other managers can access the
            # active instrument session.
            self.visa_proxy.set_instrument_instance(inst=self.inst)

            # Query instrument identity. Standard SCPI response format is:
            # <Manufacturer>,<Model>,<Serial>,<Firmware>
            idn_response = self.inst.query("*IDN?")
            idn_parts = idn_response.strip().split(",")
            manufacturer = idn_parts[0].strip() if len(idn_parts) >= 1 else "N/A"
            model = idn_parts[1].strip() if len(idn_parts) >= 2 else "N/A"
            serial_number = idn_parts[2].strip() if len(idn_parts) >= 3 else "N/A"
            firmware = idn_parts[3].strip() if len(idn_parts) >= 4 else "N/A"

            # Broadcast hardware metadata to the GUI and monitoring layers.
            self.gui_publisher._publish_status("brand", manufacturer)
            self.gui_publisher._publish_status("device_model", model)
            self.gui_publisher._publish_status("device_series", model)
            self.gui_publisher._publish_status("device_serial_number", serial_number)
            self.gui_publisher._publish_status("device_firmware", firmware)
            self.gui_publisher._publish_status("visa_resource", resource_name)
            self.gui_publisher._publish_status(
                "Time_connected", datetime.datetime.now().strftime("%H:%M:%S")
            )
            self.gui_publisher._publish_status("connected", True)
            self.gui_publisher._publish_status("disconnected", False)
            self.gui_publisher._publish_status("CONNECTED", "CONNECTED") 

            return self.inst
        except Exception as e:
            # ⚡ OPTIMIZATION: Downgrade from exception() to error() to prevent massive tracebacks during expected query failures.
            visa_logger.error(f"Error during connection logic for {resource_name}: {e}")
            return False
