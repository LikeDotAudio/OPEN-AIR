from oaLogging.Methods.matrix_gate import matrix_log
# Methods/visa_list_visa_resources.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import pyvisa
import inspect

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfigurationManager.FileReaders.config_reader import Config

app_constants = Config.get_instance()


def list_visa_resources():
    """Lists available VISA resources (instruments) discovered by the backend.

    Returns:
    - A list of strings representing the VISA resource addresses.
    - An empty list if no resources are found or if the backend fails.

    Side effects and thread-safety:
    - Initializes a new PyVISA ResourceManager instance.
    - Performs blocking I/O to scan system hardware buses and network segments.
    """
    current_function = inspect.currentframe().f_code.co_name
    matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "💳 Listing VISA resources... Let's find some devices!", "DEBUG")
    try:
        rm = pyvisa.ResourceManager()

        # Explicitly search for all instrument types using the standard
        # wildcard pattern. This captures USB, TCPIP, GPIB, and ASRL.
        all_resources = rm.list_resources("?*::INSTR")

        # Categorize resources to provide a predictable and user-friendly 
        # order in the GUI.
        usb_resources = []
        tcpip_resources = []
        other_resources = []

        for res in all_resources:
            if res.startswith("USB"):
                usb_resources.append(res)
            elif res.startswith("TCPIP"):
                tcpip_resources.append(res)
            else:  # Catches ASRL, GPIB, etc.
                other_resources.append(res)

        # Prioritize list: USB -> TCPIP -> Other (ASRL). 
        # USB is typically most stable for local use.
        resources = usb_resources + tcpip_resources + other_resources

        matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 Found VISA resources (Reordered): {resources}.", "DEBUG")
        return list(resources)
    except Exception as e:
        error_msg = f"💳 ❌ Error listing VISA resources: {e}."

        if LOCAL_DEBUG:
            logger.debug(error_msg)
        return []
