import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# Workers/visa_scanner.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Core scanning and probing logic for VISA device discovery.

import pyvisa
import urllib.request
import urllib.parse
import re
import string
import time
from concurrent.futures import ThreadPoolExecutor
from loguru import logger

from ..Constants.visa_devices import KNOWN_DEVICES
from ..Methods.network_utils import clean_string_for_display, get_local_ip, check_host

# --- CONFIGURATION ---
HTTP_TIMEOUT = 5
VISA_TIMEOUT = 5000

class VisaScanner:
    """Handles the heavy-lifting of network hunting and device probing."""

    def __init__(self, resource_manager=None):
        try:
            self.rm = resource_manager or pyvisa.ResourceManager("@py")
        except Exception as e:
            matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"PyVISA-py fallback: {e}", "DEBUG")
            self.rm = pyvisa.ResourceManager()

    def hunt_for_devices(self):
        """Scans the local subnet for potential VISA gateways and dedicated SCPI devices."""
        my_ip = get_local_ip()
        if my_ip == "127.0.0.1":
            return [], []
        
        subnet = ".".join(my_ip.split(".")[:-1])
        targets_to_scan = [f"{subnet}.{i}" for i in range(1, 255) if f"{subnet}.{i}" != my_ip]

        gateways = []
        dedicated = []

        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = {executor.submit(check_host, ip): ip for ip in targets_to_scan}
            for future in futures:
                res = future.result()
                if res:
                    ip, type_ = res
                    if type_ == "GATEWAY":
                        gateways.append(ip)
                    else:
                        dedicated.append(ip)
        return dedicated, gateways

    def query_device_safe(self, resource_str, attempt=1):
        """Attempts to query *IDN? from a resource string safely."""
        inst = None
        try:
            inst = self.rm.open_resource(resource_str)
            inst.timeout = VISA_TIMEOUT
            inst.read_termination = "\n"
            inst.write_termination = "\n"
            idn = inst.query("*IDN?").strip()
            inst.close()
            return clean_string_for_display(idn)
        except Exception as e:
            matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Error querying device {resource_str}: {e}", "TRACE")
            if inst:
                try:
                    inst.close()
                except:
                    pass
            if attempt == 1 and ("USB" in resource_str or "ASRL" in resource_str):
                return self.query_device_safe(resource_str, attempt=2)
            return None

    def get_gateway_inventory(self, ip):
        """Scrapes a VXI-11 gateway (like E5810A) for its instrument list."""
        from oaConfigurationManager.FileReaders.config_reader import Config
        cfg = Config.get_instance()
        url = f"{cfg.VISA_PROBE_PROTOCOL}://{ip}/{cfg.VISA_PROBE_PATH}"
        params = {"whichbutton": "find", "timeout": "5"}
        full_url = f"{url}?{urllib.parse.urlencode(params)}"
        targets = []
        try:
            with urllib.request.urlopen(full_url, timeout=HTTP_TIMEOUT) as response:
                html = response.read().decode("utf-8", errors="ignore")
                matches = re.findall(r"<option[^>]*>[\s\n]*([a-zA-Z0-9,]+)", html, re.IGNORECASE)
                for m in matches:
                    m = m.strip()
                    if "COM" not in m:
                        targets.append(m)
        except Exception as e:
            matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Error getting gateway inventory from {ip}: {e}", "TRACE")
        return targets

    @staticmethod
    def parse_resource_details(res_str):
        """Extracts IP and Interface details from a VISA resource string."""
        details = {"IP": "Unknown", "Interface": "Unknown", "GPIB_Addr": "N/A"}
        clean_res = clean_string_for_display(res_str)
        parts = clean_res.split("::")

        if clean_res.startswith("TCPIP"):
            if len(parts) >= 2:
                details["IP"] = parts[1]
                if len(parts) > 2 and "," in parts[2]:
                    sub_parts = parts[2].split(",")
                    details["Interface"] = sub_parts[0]
                    details["GPIB_Addr"] = ",".join(sub_parts[1:])
                else:
                    details["Interface"] = "Ethernet"
                    details["GPIB_Addr"] = "Direct"
        elif clean_res.startswith("USB"):
            details["Interface"] = "USB"
            details["IP"] = "USB"
            details["GPIB_Addr"] = "Direct"
        return details

    @staticmethod
    def parse_idn(idn_str):
        """Parses a standard SCPI IDN string into Manufacturing, Model, Serial, Firmware."""
        if not idn_str:
            return ("Unknown", "Unknown", "", "")
        parts = idn_str.split(",")
        while len(parts) < 4:
            parts.append("")
        return (parts[0].strip(), parts[1].strip(), parts[2].strip(), parts[3].strip())

    @staticmethod
    def augment_device_details(device_entry):
        """Augments entry with Knowledge Base info (Type/Notes)."""
        model = device_entry.get("model", "Unknown")
        device_entry["device_type"] = "Unknown Instrument"
        device_entry["notes"] = "Not in Knowledge Base"

        if model in KNOWN_DEVICES:
            info = KNOWN_DEVICES[model]
            device_entry["device_type"] = info["type"]
            device_entry["notes"] = info["notes"]

        return device_entry
