# managers/VisaScipi/manager_visa_list_visa_resources.py
#
# This file provides a utility function for listing available VISA (Virtual
# Instrument Software Architecture) resources. It interfaces with the local
# VISA backend to discover connected hardware over USB, Ethernet (TCPIP),
# and Serial (ASRL) interfaces.
#
# Primary Responsibilities:
# - Query the VISA ResourceManager for all active instrument addresses.
# - Categorize and prioritize discovered resources by interface type.
# - Provide a sorted list for consistent GUI presentation.
#
# Assumptions and Constraints:
# - Requires a valid VISA backend installed on the host system.
# - TCPIP discovery may depend on the specific backend's ability to scan
#   VXI-11 or HiSLIP devices.
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

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

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
    if LOCAL_DEBUG: logger.debug("💳 Listing VISA resources... Let's find some devices!")
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

        if LOCAL_DEBUG: logger.debug(f"💳 Found VISA resources (Reordered): {resources}.")
        return list(resources)
    except Exception as e:
        error_msg = f"💳 ❌ Error listing VISA resources: {e}."

        if LOCAL_DEBUG:
            logger.debug(error_msg)
        return []
