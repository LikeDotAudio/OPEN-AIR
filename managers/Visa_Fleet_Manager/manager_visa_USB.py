# managers/Visa_Fleet_Manager/manager_visa_USB.py
#
# Dedicated module for USB/Local bus VISA device discovery.
#
# Author: Gemini Agent
#

import pyvisa

try:
    from workers.logger.logger import debug_logger
    from workers.logger.log_utils import _get_log_args
except ModuleNotFoundError:
    print(
        "Warning: 'workers.logger' not found. Using dummy logger for manager_visa_USB."
    )

    def debug_logger(message, *args, **kwargs):
        if kwargs.get("level", "INFO") != "DEBUG":
            print(f"[{kwargs.get('level', 'INFO')}] {message}")

    def _get_log_args(*args, **kwargs):
        return {}  # Return empty dict, as logger args are not available


def discover_usb_devices(resource_manager):
    """
    Scans for USB/Local bus VISA devices.
    Returns a list of resource strings.
    """
    usb_resources = []
    debug_logger(f"   👉 Scanning USB/Local Bus...", **_get_log_args())
    try:
        local_res = resource_manager.list_resources("?*")
        for res in local_res:
            # Filter out TCPIP and ASRL from local_res if they are handled by other discovery modules
            if "TCPIP" not in res and "ASRL" not in res:  # ASRL is serial port
                usb_resources.append(res)
        debug_logger(
            f"   ✅ Found {len(usb_resources)} USB/local resources: {usb_resources}",
            **_get_log_args(),
        )
    except Exception as e:
        debug_logger(
            f"   ❌ Error scanning USB/Local Bus: {e}", **_get_log_args(), level="ERROR"
        )
    return usb_resources


# For testing purposes (optional)
if __name__ == "__main__":
    rm = pyvisa.ResourceManager("@py")
    devices = discover_usb_devices(rm)
    print("\nDiscovered USB Devices:")
    for dev in devices:
        print(f"- {dev}")
