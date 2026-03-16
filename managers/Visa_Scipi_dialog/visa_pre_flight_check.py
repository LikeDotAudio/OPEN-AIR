# workers/worker_visa_pre_flight_check.py
#
# A standalone utility script to scan all available VISA resources (USB, TCP/IP, Serial, etc.)
# and list them for diagnostic purposes.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Version 20251013.202759.4

import os
import inspect
import datetime
import pyvisa
import sys

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger

from managers.configini.config_reader import Config

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
    if LOCAL_DEBUG: logger.debug("🖥️🟢 Entering list_visa_resources. Initiating full system resource scan.")

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

        if LOCAL_DEBUG: logger.debug("Scanning all available VISA resources (USB, TCPIP, GPIB, ASRL/Serial)...")
        logger.debug(f"Using VISA Backend: {backend_info}")
        logger.debug("-" * 40)

        # --- Dependency Status Report ---
        logger.debug("Dependency Status Report:")

        # 1. USB Dependency Check
        if USB_SUPPORT:
            if LOCAL_DEBUG: logger.success("✅ USB Dependency (pyusb) is installed.")
        else:
            logger.error("❌ USB Dependency (pyusb) is missing. USB scanning disabled.")
            logger.debug("   Action: Run 'pip install pyusb' and ensure 'libusb' is installed on your OS.")

        # 2. TCP/IP Interface Discovery Check
        if NETWORK_ALL_INTERFACES_SUPPORT:
            if LOCAL_DEBUG: logger.success("✅ Network Dependency (psutil) is installed (enables all interface scanning).")
        else:
            if LOCAL_DEBUG: logger.debug("🟡 Network Dependency (psutil) is MISSING. Discovery limited to default interface.")
            logger.debug("   Action: Run 'pip install psutil'.")

        # 3. HiSLIP (mDNS/ZeroConf) Dependency Check
        if NETWORK_HISLIP_SUPPORT:
            if LOCAL_DEBUG: logger.success("✅ HiSLIP Dependency (zeroconf) is installed.")
        else:
            if LOCAL_DEBUG: logger.debug("🟡 HiSLIP Dependency (zeroconf) is MISSING. HiSLIP resource discovery is disabled.")
            logger.debug("   Action: Run 'pip install zeroconf'.")

        logger.debug("-" * 40)

        # list_resources() performs the actual scan.
        resources = rm.list_resources()

        if resources:
            if LOCAL_DEBUG: logger.success(f"✅ Found {len(resources)} VISA Resource(s):")
            for i, resource in enumerate(resources, 1):
                resource_type = resource.split("::")[0]
                if LOCAL_DEBUG: logger.debug(f"  {i}. {resource} ({resource_type})")
        else:
            logger.debug("🟡 No VISA resources found on the system.")
            logger.debug("Note: If devices are connected, check device power and physical connection.")

        logger.debug("-" * 40)
        logger.success("✅ Scan complete.")
        return resources

    except pyvisa.errors.LibraryError as e:
        logger.error(f"❌ Error: PyVISA backend library failed to load with '{backend_to_use}'.")
        if LOCAL_DEBUG: logger.debug("  Ensure 'pyvisa-py' is installed and its dependencies are met.")
        logger.debug(f"  Details: {e}")
    except Exception as e:
        logger.exception("❌ UNEXPECTED ERROR during VISA scan")
    return []


if __name__ == "__main__":
    list_visa_resources()
