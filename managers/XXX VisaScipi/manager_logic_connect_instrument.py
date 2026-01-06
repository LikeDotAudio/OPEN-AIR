# managers/VisaScipi/manager_logic_connect_instrument.py
#
# This file provides the logic for connecting to a VISA instrument.
#
# Author: Anthony Peter Kuzub
#
import pyvisa
import inspect
import datetime
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from managers.configini.config_reader import Config

app_constants = Config.get_instance()

LOCAL_DEBUG_ENABLE = False


class VisaConnector:
    def __init__(self, visa_proxy, gui_publisher):
        self.visa_proxy = visa_proxy
        self.gui_publisher = gui_publisher
        self.inst = None

    def setup_visa_instrument(self, resource_name):
        # Establishes a connection to a VISA instrument.

        current_function = inspect.currentframe().f_code.co_name
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"💳 Connecting to instrument: {resource_name}. Fingers crossed!",
                **_get_log_args(),
            )
        try:
            rm = pyvisa.ResourceManager()
            inst = rm.open_resource(resource_name)
            inst.timeout = 5000
            inst.read_termination = "\n"
            inst.write_termination = "\n"
            inst.query_delay = 0.1

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"💳 Connection successful to {resource_name}. We're in!",
                    **_get_log_args(),
                )
            return inst
        except Exception as e:
            error_msg = f"💳 ❌ An unexpected error occurred while connecting to {resource_name}: {e}."

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(message=error_msg, **_get_log_args())
            return None

    def connect_instrument_logic(self, resource_name):
        # Handles the full connection sequence to a VISA instrument.
        try:
            self.inst = self.setup_visa_instrument(resource_name)
            if not self.inst:
                self.visa_proxy.set_instrument_instance(inst=None)
                self.gui_publisher._publish_status("connected", False)
                self.gui_publisher._publish_status("disconnected", True)
                return False

            self.visa_proxy.set_instrument_instance(inst=self.inst)

            idn_response = self.inst.query("*IDN?")
            idn_parts = idn_response.strip().split(",")
            manufacturer = idn_parts[0].strip() if len(idn_parts) >= 1 else "N/A"
            model = idn_parts[1].strip() if len(idn_parts) >= 2 else "N/A"
            serial_number = idn_parts[2].strip() if len(idn_parts) >= 3 else "N/A"
            firmware = idn_parts[3].strip() if len(idn_parts) >= 4 else "N/A"

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
            self.gui_publisher._publish_proxy_status("CONNECTED")

            return self.inst
        except Exception as e:
            debug_logger(
                message=f"💳 ❌ Error during connection logic: {e}", **_get_log_args()
            )
            return False
