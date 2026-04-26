import inspect

# Methods/visa_pre_flight_check.py
# Author: Anthony Peter Kuzub
# Version: 20251013.202759.4
#
# Description: A standalone utility script to scan all available VISA resources (USB, TCP/IP, Serial, etc.)
import os

import pyvisa
from loguru import logger

from oaConfigurationManager.FileReaders.config_reader import Config

# --- Standard Debug Logging Setup ---
from oaLogging.Methods.matrix_gate import matrix_log

app_constants = Config.get_instance()

# --- Check Optional Dependencies for PyVISA-py ---
try:
    import usb.core
    USB_SUPPORT = True
except ImportError:
    USB_SUPPORT = False

try:
    import psutil
    NETWORK_ALL_INTERFACES_SUPPORT = True
except ImportError:
    NETWORK_ALL_INTERFACES_SUPPORT = False

try:
    import zeroconf
    NETWORK_HISLIP_SUPPORT = True
except ImportError:
    NETWORK_HISLIP_SUPPORT = False


# --- Global Scope Variables ---
current_version = "20251013.202759.4"
current_file = os.path.basename(__file__)


def list_visa_resources():
    """Lists all available VISA resources using PyVISA."""
    matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🖥️🟢 Entering list_visa_resources. Initiating full system resource scan.", "DEBUG")

    # Determine which backend to try. We prioritize the pure-Python backend (@py).
    backend_to_use = "@py"

    try:
        # Initialize the Resource Manager
        rm = pyvisa.ResourceManager(backend_to_use)

        # Safely determine the loaded backend description
        try:
            backend_info = rm.library.path
        except AttributeError:
            backend_info = "PyVISA-py (pure Python backend)"

        matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "Scanning all available VISA resources (USB, TCPIP, GPIB, ASRL/Serial)...", "DEBUG")
        matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Using VISA Backend: {backend_info}", "DEBUG")
        logger.debug("-" * 40)

        # --- Dependency Status Report ---
        matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "Dependency Status Report:", "DEBUG")

        # 1. USB Dependency Check
        if USB_SUPPORT:
            matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "✅ USB Dependency (pyusb) is installed.", "SUCCESS")
        else:
            logger.error("❌ USB Dependency (pyusb) is missing. USB scanning disabled.")
            matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "   Action: Run 'pip install pyusb' and ensure 'libusb' is installed on your OS.", "DEBUG")

        # 2. TCP/IP Interface Discovery Check
        if NETWORK_ALL_INTERFACES_SUPPORT:
            matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "✅ Network Dependency (psutil) is installed (enables all interface scanning).", "SUCCESS")
        else:
            matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🟡 Network Dependency (psutil) is MISSING. Discovery limited to default interface.", "DEBUG")
            matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "   Action: Run 'pip install psutil'.", "DEBUG")

        # 3. HiSLIP (mDNS/ZeroConf) Dependency Check
        if NETWORK_HISLIP_SUPPORT:
            matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "✅ HiSLIP Dependency (zeroconf) is installed.", "SUCCESS")
        else:
            matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🟡 HiSLIP Dependency (zeroconf) is MISSING. HiSLIP resource discovery is disabled.", "DEBUG")
            matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "   Action: Run 'pip install zeroconf'.", "DEBUG")

        logger.debug("-" * 40)

        # list_resources() performs the actual scan.
        resources = rm.list_resources()

        if resources:
            matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"✅ Found {len(resources)} VISA Resource(s):", "SUCCESS")
            for i, resource in enumerate(resources, 1):
                resource_type = resource.split("::")[0]
                matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"  {i}. {resource} ({resource_type})", "DEBUG")
        else:
            matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🟡 No VISA resources found on the system.", "DEBUG")
            matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "Note: If devices are connected, check device power and physical connection.", "DEBUG")

        logger.debug("-" * 40)
        matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "✅ Scan complete.", "SUCCESS")
        return resources

    except pyvisa.errors.LibraryError as e:
        logger.error(f"❌ Error: PyVISA backend library failed to load with '{backend_to_use}'.")
        matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "  Ensure 'pyvisa-py' is installed and its dependencies are met.", "DEBUG")
        matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"  Details: {e}", "DEBUG")
    except Exception:
        logger.exception("❌ UNEXPECTED ERROR during VISA scan")
    return []


if __name__ == "__main__":
    list_visa_resources()
