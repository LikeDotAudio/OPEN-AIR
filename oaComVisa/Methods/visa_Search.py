import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# Methods/visa_Search.py
# Author: Anthony Peter Kuzub (Refactored)
# Version: 1.0.0
#
# Description: Dedicated module for probing VISA devices and parsing their identification.

import pyvisa
import time
import re
import string
import threading
import socket
import sys
import os

# Add the hyphenated directory to sys.path temporarily to import compiler_hook
_rs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Core", "oaVisaCore-rs")
if _rs_dir not in sys.path:
    sys.path.insert(0, _rs_dir)

import compiler_hook
compiler_hook.ensure_compiled()

try:
    import oavisacore_rs
except ImportError as e:
    from loguru import logger
    logger.critical("🚀❌ [FATAL] Rust VISA Core module missing. Pure Rust mode is mandatory.")
    raise e

try:
    from oavisascanner_rs import VisaScanner
    scanner_rs = VisaScanner()
    HAS_SCANNER_RS = True
except ImportError:
    HAS_SCANNER_RS = False

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True
from loguru import logger
from oaConfiguration.FileReaders.config_reader import Config
from .visa_utility_parser import VisaUtilityParser

app_constants = Config.get_instance()

# --- CONFIGURATION ---
# Increased timeout for discovery to prevent UI hangs on dead IP addresses but
# allow slow network devices to respond.
VISA_TIMEOUT = 5000

# Global registry of locks to prevent concurrent probes to the same gateway/IP.
_IP_LOCKS = {}
_IP_LOCKS_MUTEX = threading.Lock()

def _get_lock_for_ip(ip_address):
    """Retrieves or creates a mutex for a specific IP address."""
    with _IP_LOCKS_MUTEX:
        if ip_address not in _IP_LOCKS:
            _IP_LOCKS[ip_address] = threading.Lock()
        return _IP_LOCKS[ip_address]


def probe_devices(resource_manager, potential_targets):
    """
    Probes a list of potential VISA resources to gather detailed information.

    Args:
        resource_manager: The PyVISA ResourceManager instance.
        potential_targets (list): A list of dictionaries, each with 'Type' and 'Resource' keys.
                                  E.g., [{"Type": "DEDICATED", "Resource": "TCPIP::192.168.1.10::INSTR"}]

    Returns:
        dict: A dictionary of probed device entries, keyed by device identifier (serial number or sanitized resource).
    """
    matrix_log("core", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 🔍 manager_visa_Search: Received {len(potential_targets)} potential targets for probing: {potential_targets}", "DEBUG")
    device_collection = {}

    if HAS_SCANNER_RS:
        # ⚡ PURE RUST PRE-PROBE: Concurrently check for TCP reachability
        matrix_log("core", "visa", "probe_devices", "⚡ Starting concurrent reachability scan...", "DEBUG")
        tcp_map = {}
        probe_list = []
        for target in potential_targets:
            res = target["Resource"]
            if "TCPIP" in res:
                parts = res.split("::")
                if len(parts) > 1:
                    ip = parts[1]
                    tcp_map[ip] = target
                    probe_list.append((ip, 111))
                    probe_list.append((ip, 5025))
                    probe_list.append((ip, 4880))
        
        if probe_list:
            reachability = scanner_rs.check_reachability(probe_list, 1000)
            reachable_ips = {r["ip"] for r in reachability if r["reachable"]}
            
            filtered = []
            for target in potential_targets:
                res = target["Resource"]
                if "TCPIP" in res:
                    parts = res.split("::")
                    if len(parts) > 1 and parts[1] in reachable_ips:
                        filtered.append(target)
                    else:
                        matrix_log("core", "visa", "probe_devices", f"   ⏭️ Skipping unreachable host: {res}", "DEBUG")
                else:
                    filtered.append(target)
            potential_targets = filtered
            matrix_log("core", "visa", "probe_devices", f"⚡ Reachability scan complete. {len(potential_targets)} targets remaining.", "SUCCESS")

    try:
        for idx, target in enumerate(potential_targets):
            raw_res = target["Resource"]
            display_res = VisaUtilityParser.clean_string_for_display(raw_res)

            matrix_log("core", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"   🎯 Probing {display_res} ... ", "DEBUG")

            conn_details = VisaUtilityParser.parse_resource_details(display_res)
            
            # Use per-IP locking to prevent 'wrong xid' desync on multi-port gateways
            ip = conn_details["IP"]
            lock = _get_lock_for_ip(ip)
            
            idn = None
            try:
                with lock:
                    idn = VisaUtilityParser.query_device_safe(resource_manager, raw_res)
            except socket.timeout:
                logger.warning(f"      💳⚠️ [TIMEOUT] Socket timeout for {display_res}.")
                idn = None
            except Exception as e:
                logger.error(f"      💳💀 [CRITICAL] Unhandled exception during probe for {display_res}: {e}")
                idn = None

            device_entry = {
                # "id": str(idx + 1), # Will be replaced by serial or similar unique ID
                "type": target["Type"],
                "resource_string": display_res,
                "ip_address": conn_details["IP"],
                "interface_port": conn_details["Interface"],
                "gpib_address": conn_details["GPIB_Addr"],
            }

            if idn:
                matrix_log("core", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"SUCCESS", "SUCCESS")
                mfg, model, serial_num, firm = VisaUtilityParser.parse_idn(
                    idn
                )  # Use VisaUtilityParser for basic parsing

                device_identifier = serial_num
                if not device_identifier or device_identifier == "0":
                    # Construct unique ID from IP last octet, interface port number, and GPIB address
                    # Example: "222-7-1" from IP 44.44.44.222, gpib7, 1

                    last_octet = "Unknown"
                    if conn_details["IP"] and "." in conn_details["IP"]:
                        last_octet = conn_details["IP"].split(".")[-1]
                    elif conn_details["IP"] == "USB":  # Handle USB IP
                        last_octet = "USB"

                    interface_port_num = "Unknown"
                    if conn_details["Interface"]:
                        match = re.search(r"\d+", conn_details["Interface"])
                        if match:
                            interface_port_num = match.group(0)
                        else:
                            interface_port_num = conn_details[
                                "Interface"
                            ]  # Use full string if no number

                    gpib_addr = (
                        conn_details["GPIB_Addr"]
                        if conn_details["GPIB_Addr"] != "N/A"
                        else "Unknown"
                    )

                    # Combine to form the new device_identifier
                    # Sanitize components to ensure valid identifier (e.g., replace non-alphanumeric with '_')
                    device_identifier_parts = [
                        last_octet,
                        interface_port_num,
                        gpib_addr,
                    ]
                    sanitized_parts = [
                        re.sub(r"[^\w\-]+", "_", str(p))
                        for p in device_identifier_parts
                    ]

                    device_identifier = "-".join(sanitized_parts)

                    matrix_log("core", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"      Generated new device_identifier for empty/0 serial: {device_identifier}", "DEBUG")

                # Ensure the device_identifier is unique across the collection
                original_identifier = device_identifier
                counter = 1
                while device_identifier in device_collection:
                    device_identifier = f"{original_identifier}_{counter}"
                    counter += 1

                device_entry.update(
                    {
                        "status": "Active",
                        "manufacturer": mfg,
                        "model": model,
                        "serial_number": serial_num,
                        "firmware": firm,
                        "idn_string": idn,
                        # "idn_details": {} # Will be added by supervisor with robust parser
                    }
                )
            else:
                if LOCAL_DEBUG: logger.warning(f"FAILED (IDN Query Error)")
                device_identifier = re.sub(
                    r"[^\w\-]+", "_", raw_res
                )  # Still need identifier for unresponsive devices
                device_entry.update(
                    {
                        "status": "Unresponsive",
                        "manufacturer": "Unknown",
                        "model": "Unknown",
                        "serial_number": "Unknown",
                        "firmware": "Unknown",
                        "device_type": "Unknown",
                        "notes": "Connection Timed Out",
                    }
                )

            device_collection[device_identifier] = device_entry
    except Exception as e:
        if LOCAL_DEBUG:
            logger.error(
                f"💳 🔍 CRITICAL manager_visa_Search: Exception in probe_devices loop: {e}")

    matrix_log("core", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 🔍 manager_visa_Search: Finished probing. Returning {len(device_collection)} probed devices: {device_collection}", "DEBUG")
    return device_collection


# For testing purposes (optional)
if __name__ == "__main__":
    rm = pyvisa.ResourceManager("@py")
    # Example potential targets (replace with real data for testing)
    example_targets = [
        {"Type": "LOCAL", "Resource": "USB0::0x1234::0x5678::SN12345::INSTR"},
        {"Type": "DEDICATED", "Resource": "TCPIP::192.168.1.10::INSTR"},
    ]
    probed_devices = probe_devices(rm, example_targets)
    print("\nProbed Devices:")
    for dev_id, dev_data in probed_devices.items():
        print(f"  {dev_id}: {dev_data}")
