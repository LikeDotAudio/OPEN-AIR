# workers/worker_visa_pre_flight_check.py
#
# The hash calculation drops the leading zero from the hour (e.g., 08 -> 8)
# As the current hour is 20, no change is needed.

Current_Date = 20251129  ##Update on the day the change was made
Current_Time = 120000  ## update at the time it was edited and compiled
Current_iteration = 1 ## a running version number - incriments by one each time 

current_version = f"{Current_Date}.{Current_Time}.{Current_iteration}"
current_version_hash = (Current_Date * Current_Time * Current_iteration)


# A standalone utility script to scan all available VISA resources (USB, TCP/IP, Serial, etc.)
# and list them for diagnostic purposes.
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
#
# Version 20251013.202759.4 (Added full dependency status report for USB/TCPIP components)

import os
import inspect
import datetime
import pyvisa
import sys
from managers.configini.config_reader import Config                                                                          

app_constants = Config.get_instance() # Get the singleton instance      
# --- Check Optional Dependencies for PyVISA-py ---
# PyVISA-py relies on these optional packages for full functionality.
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


import workers.logger.logger as logger
# Use the global debug_log from the logger module
debug_log = logger.debug_log

# --- Global Scope Variables (as per Protocol 4.4) ---
# W: 20251013, X: 202759, Y: 4
current_version = "20251013.202759.4"
# The hash calculation drops the leading zero from the hour (20 -> 20)
current_version_hash = (20251013 * 202759 * 4)
current_file = f"{os.path.basename(__file__)}"
LOCAL_DEBUG_ENABLE = False



def list_visa_resources():
    # Lists all available VISA resources using PyVISA.
    current_function_name = inspect.currentframe().f_code.co_name
    if app_constants.global_settings['debug_enabled']:
        debug_logger(
            message="🖥️🟢 Entering list_visa_resources. Initiating full system resource scan.",
**_get_log_args()
            

        )

    # Determine which backend to try. We prioritize the pure-Python backend (@py).
    backend_to_use = '@py'
    
    try:
        # Initialize the Resource Manager, explicitly using the pure-Python backend.
        rm = pyvisa.ResourceManager(backend_to_use) 
        
        # Safely determine the loaded backend description
        try:
            # This path is generally only available for vendor backends (like NI-VISA)
            library_path = rm.library.path
            backend_info = f"{library_path}"
        except AttributeError:
            # If .library is not available, assume the pure-Python backend is loaded.
            backend_info = "PyVISA-py (pure Python backend)"

        debug_logger(message="Scanning all available VISA resources (USB, TCPIP, GPIB, ASRL/Serial)...",
                    file=current_file,
                    version=current_version,
                    function=current_function_name,
                    )
        debug_logger(message=f"Using VISA Backend: {backend_info}",
                    file=current_file,
                    version=current_version,
                    function=current_function_name,
                    )
        
        debug_logger(message="-" * 40,
                    file=current_file,
                    version=current_version,
                    function=current_function_name,
                    )
        
        # --- Dependency Status Report ---
        debug_logger(message="Dependency Status Report:",
                    file=current_file,
                    version=current_version,
                    function=current_function_name,
                    )
        
        # 1. USB Dependency Check
        if USB_SUPPORT:
            debug_logger(message="✅ USB Dependency (pyusb) is installed.",
                    file=current_file,
                    version=current_version,
                    function=current_function_name,
                    )
        else:
            debug_logger(message="❌ USB Dependency (pyusb) is MISSING. USB device discovery may fail.",
                    file=current_file,
                    version=current_version,
                    function=current_function_name,
                    )
            debug_logger(message="   Action: Run 'pip install pyusb' and ensure 'libusb' is installed on your OS.",
                    file=current_file,
                    version=current_version,
                    function=current_function_name,
                    )
            
        # 2. TCP/IP Interface Discovery Check
        if NETWORK_ALL_INTERFACES_SUPPORT:
            debug_logger(message="✅ Network Dependency (psutil) is installed (enables all interface scanning).",
                    file=current_file,
                    version=current_version,
                    function=current_function_name,
                    )
        else:
            debug_logger(message="🟡 Network Dependency (psutil) is MISSING. Discovery limited to default interface.",
                    file=current_file,
                    version=current_version,
                    function=current_function_name,
                    )
            debug_logger(message="   Action: Run 'pip install psutil'.",
                    file=current_file,
                    version=current_version,
                    function=current_function_name,
                    )

        # 3. HiSLIP (mDNS/ZeroConf) Dependency Check
        if NETWORK_HISLIP_SUPPORT:
            debug_logger(message="✅ HiSLIP Dependency (zeroconf) is installed.",
                    file=current_file,
                    version=current_version,
                    function=current_function_name,
                    )
        else:
            debug_logger(message="🟡 HiSLIP Dependency (zeroconf) is MISSING. HiSLIP resource discovery is disabled.",
                    file=current_file,
                    version=current_version,
                    function=current_function_name,
                    )
            debug_logger(message="   Action: Run 'pip install zeroconf'.",
                    file=current_file,
                    version=current_version,
                    function=current_function_name,
                    )
            
        debug_logger(message="-" * 40,
                    file=current_file,
                    version=current_version,
                    function=current_function_name,
                    )
        
        # list_resources() performs the actual scan.
        resources = rm.list_resources()

        if resources:
            debug_logger(message=f"✅ Found {len(resources)} VISA Resource(s):",
                    file=current_file,
                    version=current_version,
                    function=current_function_name,
                    )
            for i, resource in enumerate(resources, 1):
                # Attempt to determine resource type from the resource string
                resource_type = resource.split("::")[0]
                debug_logger(message=f"  {i}. {resource} ({resource_type})",
                    file=current_file,
                    version=current_version,
                    function=current_function_name,
                    )
        else:
            debug_logger(message="🟡 No VISA resources found on the system.",
                    file=current_file,
                    version=current_version,
                    function=current_function_name,
                    )
            debug_logger(message="Note: If devices are connected, check device power and physical connection.",
                    file=current_file,
                    version=current_version,
                    function=current_function_name,
                    )
        
        debug_logger(message="-" * 40,
                    file=current_file,
                    version=current_version,
                    function=current_function_name,
                    )
        debug_logger(message="✅ Scan complete.",
                    file=current_file,
                    version=current_version,
                    function=current_function_name,
                    )
        return resources

    except pyvisa.errors.LibraryError as e:
        debug_logger(message=f"❌ Error: PyVISA backend library failed to load with '{backend_to_use}'.",
                    file=current_file,
                    version=current_version,
                    function=current_function_name,
                    )
        debug_logger(message="  Ensure 'pyvisa-py' is installed and its dependencies (like 'pyusb') are met.",
                    file=current_file,
                    version=current_version,
                    function=current_function_name,
                    )
        debug_logger(message=f"  Details: {e}",
                    file=current_file,
                    version=current_version,
                    function=current_function_name,
                    )
    except Exception as e:
        debug_logger(message=f"❌ UNEXPECTED ERROR during VISA scan: {type(e).__name__}: {e}",
                    file=current_file,
                    version=current_version,
                    function=current_function_name,
                    )
        if app_constants.global_settings['debug_enabled']:
            debug_logger(
                message=f"🖥️🔴 VISA scan failed: {e}",
**_get_log_args()
                


            )
    return []

if __name__ == "__main__":
    # Execute the scan function when the script is run directly.
    list_visa_resources()