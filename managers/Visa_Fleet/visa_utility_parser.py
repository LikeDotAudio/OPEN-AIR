# managers/Visa_Fleet/visa_utility_parser.py
import string
import socket
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
        # ⚡ DEFENSIVE CHECK: Verify resource exists in system before opening
        available_resources = rm.list_resources()
        if resource_str not in available_resources:
            logger.warning(f"      💳⚠️ [VISA] Resource {resource_str} not found in system.")
            return None

        # ⚡ NETWORK PRE-CHECK: If TCPIP, verify port 5025 (standard SCPI) or 111 (VXI-11) is open
        if "TCPIP" in resource_str:
            details = VisaUtilityParser.parse_resource_details(resource_str)
            ip = details["IP"]
            if ip != "Unknown":
                # Check 5025 (Raw) or 111 (RPC/VXI-11)
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1.0)
                # connect_ex returns 0 on success, no exception
                res_5025 = sock.connect_ex((ip, 5025))
                sock.close()
                
                if res_5025 != 0:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1.0)
                    res_111 = sock.connect_ex((ip, 111))
                    sock.close()
                    if res_111 != 0:
                        logger.warning(f"      💳⚠️ [VISA] Network host {ip} is unreachable (5025/111 closed).")
                        return None

        # If we reach here, we have high confidence the resource is reachable.
        # We proceed with PyVISA calls. If they still throw, it's a fatal HW error.
        inst = rm.open_resource(resource_str)
        inst.timeout = timeout
        inst.read_termination = "\n"
        inst.write_termination = "\n"

        raw_idn = inst.query("*IDN?")
        idn = VisaUtilityParser.clean_string_for_display(raw_idn)
        inst.close()

        if not idn:
            return None
        return idn

    @staticmethod
    def get_local_ip():
        """Retrieves the primary local IP address without using exceptions."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # connect() on a UDP socket doesn't actually send a packet, 
        # so it's extremely unlikely to throw.
        s.connect(("10.255.255.255", 1))
        IP = s.getsockname()[0]
        s.close()
        return IP

