# managers/Visa_Fleet_Manager/visa_utility_parser.py
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
        """Safely queries *IDN? from a VISA resource with timeout handling."""
        inst = None
        try:
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
        except pyvisa.errors.VisaIOError as e:
            if inst:
                try:
                    inst.close()
                except:
                    pass
            logger.debug(f"      💳⚠️ [VISA ERROR] {resource_str}: {e.description} (Code: {e.error_code})")
            if attempt == 1 and ("USB" in resource_str or "ASRL" in resource_str):
                return VisaUtilityParser.query_device_safe(rm, resource_str, attempt=2, timeout=timeout)
            return None
        except Exception as e:
            if inst:
                try:
                    inst.close()
                except:
                    pass
            logger.error(f"      💳💀 [EXCEPTION] {resource_str}: {type(e).__name__} - {e}")
            return None

    @staticmethod
    def get_local_ip():
        """Retrieves the primary local IP address."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("10.255.255.255", 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = "127.0.0.1"
        finally:
            s.close()
        return IP
