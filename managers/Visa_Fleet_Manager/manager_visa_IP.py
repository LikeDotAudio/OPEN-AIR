# managers/Visa_Fleet_Manager/manager_visa_IP.py
#
# Dedicated module for IP-based VISA device discovery (TCPIP, VXI-11 gateways).
#
# Author: Gemini Agent
#

import socket
import urllib.request
import urllib.parse
import re
from concurrent.futures import ThreadPoolExecutor

try:
    from workers.logger.logger import debug_logger
    from workers.logger.log_utils import _get_log_args
except ModuleNotFoundError:
    print(
        "Warning: 'workers.logger' not found. Using dummy logger for manager_visa_IP."
    )

    def debug_logger(message, *args, **kwargs):
        if kwargs.get("level", "INFO") != "DEBUG":
            print(f"[{kwargs.get('level', 'INFO')}] {message}")

    def _get_log_args(*args, **kwargs):
        return {}  # Return empty dict, as logger args are not available


# --- CONFIGURATION (from cli_visa_find.py) ---
HTTP_TIMEOUT = 5


def _get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP


def _check_host(ip):
    """Checks for Port 111 (VXI-11) and Port 5025 (SCPI)."""
    debug_logger(f"   🔍 Checking host: {ip}", **_get_log_args())
    # 1. Port 111 (VXI-11)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.3)
        result = sock.connect_ex((ip, 111))
        sock.close()
        if result == 0:
            is_gateway = False
            try:
                url = f"http://{ip}/html/instrumentspage.html"
                with urllib.request.urlopen(url, timeout=1) as resp:
                    if "E5810" in resp.read().decode("utf-8", errors="ignore"):
                        is_gateway = True
            except:
                pass
            debug_logger(
                f"     ✅ Host {ip}: Port 111 open. Type: {'GATEWAY' if is_gateway else 'DEDICATED'}",
                **_get_log_args(),
            )
            return (ip, "GATEWAY" if is_gateway else "DEDICATED")
        else:
            debug_logger(
                f"⚠️ Host{ip}: Port 111 closed.", **_get_log_args(), level="WARNING"
            )
    except Exception as e:
        debug_logger(
            f"⚠️ Host{ip}: Error checking Port 111: {e}",
            **_get_log_args(),
            level="WARNING",
        )

    # 2. Port 5025 (SCPI)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.3)
        result = sock.connect_ex((ip, 5025))
        sock.close()
        if result == 0:
            #  debug_logger(f"     ✅ Host {ip}: Port 5025 open. Type: DEDICATED", **_get_log_args())
            return (ip, "DEDICATED")
        else:
            debug_logger(
                f"⚠️ Host{ip}: Port 5025 closed.", **_get_log_args(), level="WARNING"
            )
    except Exception as e:
        debug_logger(
            f"⚠️ Host{ip}: Error checking Port 5025: {e}",
            **_get_log_args(),
            level="WARNING",
        )
    return None


def discover_ip_devices():
    """
    Hunts the local network for VISA-enabled devices (dedicated IPs and VXI-11 gateways).
    Returns two lists: (dedicated_ips, gateway_ips).
    """
    debug_logger("💳 🔍 Hunting network for VISA devices...", **_get_log_args())
    my_ip = _get_local_ip()
    if my_ip == "127.0.0.1":
        debug_logger(
            "Could not determine local IP. Skipping network hunt.",
            **_get_log_args(),
            level="WARNING",
        )
        return [], []

    subnet = ".".join(my_ip.split(".")[:-1])

    targets_to_scan = [
        f"{subnet}.{i}" for i in range(1, 255) if f"{subnet}.{i}" != my_ip
    ]

    gateways = []
    dedicated = []

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(_check_host, ip): ip for ip in targets_to_scan}
        for future in futures:
            res = future.result()
            if res:
                ip, type_ = res
                if type_ == "GATEWAY":
                    gateways.append(ip)
                else:
                    dedicated.append(ip)

    if dedicated:
        debug_logger(f"✅ Found Dedicated: {dedicated}", **_get_log_args())
    if gateways:
        debug_logger(f"✅ Found Gateways: {gateways}", **_get_log_args())
    if not dedicated and not gateways:
        debug_logger(f"   ⚪ No network devices found.", **_get_log_args())

    return dedicated, gateways
