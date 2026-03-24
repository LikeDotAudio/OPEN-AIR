# Workers/agent_usb_enumerator.py
# Author: Gemini Agent
# Version: 1.0.0
#
# Description: Dedicated module for USB/Local bus VISA device discovery.

import pyvisa

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = False    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()


def discover_usb_devices(resource_manager):
    """
    Scans for USB/Local bus VISA devices.
    Returns a list of resource strings.
    """
    usb_resources = []
    if LOCAL_DEBUG: logger.debug(f"   👉 Scanning USB/Local Bus...")
    try:
        local_res = resource_manager.list_resources("?*")
        for res in local_res:
            # Filter out TCPIP and ASRL from local_res if they are handled by other discovery modules
            if "TCPIP" not in res and "ASRL" not in res:  # ASRL is serial port
                usb_resources.append(res)
        if LOCAL_DEBUG: logger.debug(f"   ✅ Found {len(usb_resources)} USB/local resources: {usb_resources}")
    except Exception as e:
        if LOCAL_DEBUG:
            logger.error(
                f"   ❌ Error scanning USB/Local Bus: {e}"
            )
    return usb_resources


# For testing purposes (optional)
if __name__ == "__main__":
    rm = pyvisa.ResourceManager("@py")
    devices = discover_usb_devices(rm)
    print("\nDiscovered USB Devices:")
    for dev in devices:
        print(f"- {dev}")
