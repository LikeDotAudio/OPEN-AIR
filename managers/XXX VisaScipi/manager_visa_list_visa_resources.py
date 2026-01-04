# managers/VisaScipi/manager_visa_list_visa_resources.py
#
# This file provides a utility function for listing available VISA (Virtual Instrument Software Architecture) resources.
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

import pyvisa
import inspect
from workers.logger.logger import  debug_logger
from workers.logger.log_utils import _get_log_args
from managers.configini.config_reader import Config

app_constants = Config.get_instance()

LOCAL_DEBUG_ENABLE = False

def list_visa_resources():
    # Lists available VISA resources (instruments).
   
    current_function = inspect.currentframe().f_code.co_name
    if app_constants.global_settings['debug_enabled']:
        debug_logger(message="💳 Listing VISA resources... Let's find some devices!", **_get_log_args())
    try:
        rm = pyvisa.ResourceManager()
        
        # KEY CHANGE: Explicitly search for all instrument types, especially TCPIP.
        # '?*::INSTR' is the wildcard search pattern for all resource types supported by the backend.
        all_resources = rm.list_resources('?*::INSTR') 

        # --- Resource Reordering Logic (FIX) ---
        usb_resources = []
        tcpip_resources = []
        other_resources = []

        for res in all_resources:
            if res.startswith('USB'):
                usb_resources.append(res)
            elif res.startswith('TCPIP'):
                tcpip_resources.append(res)
            else: # Catches ASRL, GPIB, etc.
                other_resources.append(res)
        
        # Prioritize list: USB -> TCPIP -> Other (ASRL)
        resources = usb_resources + tcpip_resources + other_resources
        # --- End Resource Reordering Logic ---
        
        if app_constants.global_settings['debug_enabled']:
            debug_logger(message=f"💳 Found VISA resources (Reordered): {resources}.", **_get_log_args())
        return list(resources)
    except Exception as e:
        error_msg = f"💳 ❌ Error listing VISA resources: {e}."
        
        if app_constants.global_settings['debug_enabled']:
            debug_logger(message=error_msg, **_get_log_args())
        return []