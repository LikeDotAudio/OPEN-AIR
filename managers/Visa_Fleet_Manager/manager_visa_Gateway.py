# managers/Visa_Fleet_Manager/manager_visa_Gateway.py
#
# Dedicated module for Gateway-based VISA device discovery (VXI-11 HTML scraping).
#
# Author: Gemini Agent
#

import urllib.request
import urllib.parse
import re

try:
    from workers.logger.logger import debug_logger
    from workers.logger.log_utils import _get_log_args
except ModuleNotFoundError:
    print(
        "Warning: 'workers.logger' not found. Using dummy logger for manager_visa_Gateway."
    )

    def debug_logger(message, *args, **kwargs):
        if kwargs.get("level", "INFO") != "DEBUG":
            print(f"[{kwargs.get('level', 'INFO')}] {message}")

    def _get_log_args(*args, **kwargs):
        return {}  # Return empty dict, as logger args are not available


# --- CONFIGURATION (from cli_visa_find.py) ---
HTTP_TIMEOUT = 10


def discover_gateway_devices(gateway_ips):
    """
    Scrapes VXI-11 gateways for connected VISA devices.
    Returns a list of resource strings.
    """
    gateway_resources = []
    for ip in gateway_ips:
        debug_logger(f"   👉 Scraping Gateway {ip}...", **_get_log_args())
        url = f"http://{ip}/html/instrumentspage.html"
        params = {"whichbutton": "find", "timeout": "5"}
        full_url = f"{url}?{urllib.parse.urlencode(params)}"
        targets = []
        try:
            with urllib.request.urlopen(full_url, timeout=HTTP_TIMEOUT) as response:
                html = response.read().decode("utf-8", errors="ignore")
                matches = re.findall(
                    r"<option[^>]*>[\s\n]*([a-zA-Z0-9,]+)", html, re.IGNORECASE
                )
                for m in matches:
                    m = m.strip()
                    if "COM" not in m:
                        targets.append(
                            m
                        )  # Filter out COM ports, which are usually local serial
        except Exception as e:
            debug_logger(
                f"   ❌ Error scraping gateway {ip}: {e}",
                **_get_log_args(),
                level="ERROR",
            )

        debug_logger(
            f"   ✅ Found {len(targets)} resources from gateway {ip}: {targets}",
            **_get_log_args(),
        )
        for t in targets:
            visa_res = f"TCPIP::{ip}::{t}::INSTR"
            gateway_resources.append(visa_res)
            debug_logger(
                f"     ➕ Added gateway resource: {visa_res}", **_get_log_args()
            )
    return gateway_resources
