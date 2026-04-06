import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# Methods/network_utils.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Reusable network and string cleaning utilities for VISA modules.

import socket
import string
import urllib.request
from loguru import logger

def clean_string_for_display(s):
    """Removes non-printable characters from strings."""
    if not s:
        return ""
    return "".join(filter(lambda x: x in string.printable, s)).strip()

def get_local_ip():
    """Retrieves the local IPv4 address of the machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        IP = s.getsockname()[0]
    except Exception as e:
        matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Error getting local IP: {e}", "TRACE")
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP

def check_host(ip):
    """
    Checks for Port 111 (Gateway) and Port 5025 (SCPI).
    Returns (ip, type) if a device is found, else None.
    """
    # 1. Port 111 (VXI-11)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.3)
            result = sock.connect_ex((ip, 111))
        if result == 0:
            is_gateway = False
            try:
                from oaConfigurationManager.FileReaders.config_reader import Config
                cfg = Config.get_instance()
                url = f"{cfg.VISA_PROBE_PROTOCOL}://{ip}/{cfg.VISA_PROBE_PATH}"
                with urllib.request.urlopen(url, timeout=1) as resp:
                    if "E5810" in resp.read().decode("utf-8", errors="ignore"):
                        is_gateway = True
            except Exception as e:
                matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Error checking instruments page for {ip}: {e}", "TRACE")
                pass
            return (ip, "GATEWAY" if is_gateway else "DEDICATED")
    except Exception as e:
        matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Error connecting to Port 111 on {ip}: {e}", "TRACE")
        pass

    # 2. Port 5025 (SCPI)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.3)
        result = sock.connect_ex((ip, 5025))
        sock.close()
        if result == 0:
            return (ip, "DEDICATED")
    except Exception as e:
        matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Error connecting to Port 5025 on {ip}: {e}", "TRACE")
        pass
    return None
