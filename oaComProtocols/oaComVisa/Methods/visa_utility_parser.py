# Methods/visa_utility_parser.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import socket
import string

import pyvisa
from loguru import logger

# --- CONFIGURATION ---
VISA_TIMEOUT = 5000

class VisaUtilityParser:
    """Centralized utilities for VISA device discovery and string parsing."""

    @staticmethod
    def clean_string_for_display(s):
        """Filters non-printable characters from a string."""
        if not s:
            return ""
        return "".join(filter(lambda x: x in string.printable, s)).strip()

    @staticmethod
    def parse_idn(idn_str):
        """Parses a standard *IDN? response string."""
        if not idn_str:
            return ("Unknown", "Unknown", "", "")
        parts = idn_str.split(",")
        while len(parts) < 4:
            parts.append("")
        return (parts[0].strip(), parts[1].strip(), parts[2].strip(), parts[3].strip())

    @staticmethod
    def parse_resource_details(res_str):
        """Parses a VISA resource string for IP and connection details."""
        details = {"IP": "Unknown", "Interface": "Unknown", "GPIB_Addr": "N/A"}
        clean_res = VisaUtilityParser.clean_string_for_display(res_str)
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
    def query_device_safe(rm, resource_str, attempt=1, timeout=VISA_TIMEOUT):
        """Safely queries *IDN? from a VISA resource with defensive pre-checks."""

        # ⚡ NETWORK PRE-CHECK: If TCPIP, verify port 5025 (standard SCPI) or 111 (VXI-11) is open
        # This prevents blocking on dead IP addresses before PyVISA even tries.
        if "TCPIP" in resource_str:
            details = VisaUtilityParser.parse_resource_details(resource_str)
            ip = details["IP"]
            if ip != "Unknown":
                # Check 5025 (Raw) or 111 (RPC/VXI-11)
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(1.0)
                    # connect_ex returns 0 on success, no exception
                    res_5025 = sock.connect_ex((ip, 5025))

                if res_5025 != 0:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.settimeout(1.0)
                        res_111 = sock.connect_ex((ip, 111))
                    if res_111 != 0:
                        logger.warning(f"      💳⚠️ [VISA] Network host {ip} is unreachable (5025/111 closed).")
                        return None

        # If we reach here, we have high confidence the resource is reachable.
        # We proceed with PyVISA calls.
        inst = None
        try:
            inst = rm.open_resource(resource_str)
            inst.timeout = timeout
            # Standard SCPI terminations
            inst.read_termination = "\n"
            inst.write_termination = "\n"

            raw_idn = inst.query("*IDN?")
            idn = VisaUtilityParser.clean_string_for_display(raw_idn)
            if not idn:
                raise HardwareError(f"💳⚠️ [VISA] Device at {resource_str} returned empty IDN.")
            return idn

        except pyvisa.errors.VisaIOError as e:
            raise HardwareError(f"💳⚠️ [VISA] IO Error for {resource_str}: {e.description}")
        except Exception as e:
            if isinstance(e, HardwareError): raise
            raise HardwareError(f"💳⚠️ [VISA] Unexpected error probing {resource_str}: {e}")
        finally:
            if inst:
                try: inst.close()
                except Exception as close_err:
                    logger.warning(f"💳⚠️ [VISA] Failed to close resource {resource_str}: {close_err}")

    @staticmethod
    def get_local_ip():
        """Retrieves the primary local IP address without using exceptions."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # connect() on a UDP socket doesn't actually send a packet,
        # so it's extremely unlikely to throw.
        try:
            s.connect(("10.255.255.255", 1))
            IP = s.getsockname()[0]
        except Exception as e:
            logger.warning(f"🌐 [NETWORK] Failed to auto-detect IP, falling back to localhost: {e}")
            IP = "127.0.0.1"
        finally:
            s.close()
        return IP
