# managers/VisaScipi/manager_visa_disconnect_instrument.py
#
# This file provides a utility function for disconnecting from a VISA (Virtual Instrument Software Architecture) resource.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#

import inspect
from workers.logger.logger import  debug_logger
from workers.logger.log_utils import _get_log_args
from managers.configini.config_reader import Config

app_constants = Config.get_instance()

LOCAL_DEBUG_ENABLE = False

def disconnect_instrument(inst):
    # Closes the connection to a VISA instrument.
   
    current_function = inspect.currentframe().f_code.co_name
    if app_constants.global_settings['debug_enabled']:
        debug_logger(message="💳 Disconnecting instrument... Saying goodbye!", **_get_log_args())
    if inst:
        try:
            inst.close()
            
            if app_constants.global_settings['debug_enabled']:
                debug_logger(message="💳 Instrument connection closed. All done!", **_get_log_args())
            return True
        except Exception as e:
            error_msg = f"💳 ❌ An unexpected error occurred while disconnecting instrument: {e}."
            
            if app_constants.global_settings['debug_enabled']:
                debug_logger(message=error_msg, **_get_log_args())
            return False
    if app_constants.global_settings['debug_enabled']:
        debug_logger(message="💳 No instrument to disconnect. Already gone!", **_get_log_args())
    return False

class VisaDisconnector:
    def __init__(self, visa_proxy, gui_publisher):
        self.visa_proxy = visa_proxy
        self.gui_publisher = gui_publisher

    def disconnect_instrument_logic(self, inst):
        # Disconnects the application from the currently connected VISA instrument.
        if not inst:
            self.visa_proxy.set_instrument_instance(inst=None)
            self.gui_publisher._publish_proxy_status("DISCONNECTED")
            return True
            
        result = disconnect_instrument(inst)
        
        self.visa_proxy.set_instrument_instance(inst=None)
        
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