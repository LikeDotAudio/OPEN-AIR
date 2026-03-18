# managers/STATE_VISA_FLEET_Manager/manager_visa_Gateway.py
#
# Dedicated module for Gateway-based VISA device discovery (VXI-11 HTML scraping).
#
# Author: Gemini Agent
#

import urllib.request
import urllib.parse
import re
import os

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.config_reader import Config

app_constants = Config.get_instance()


# --- CONFIGURATION (from cli_visa_find.py) ---
HTTP_TIMEOUT = 10


def discover_gateway_devices(gateway_ips):
    """
    Scrapes VXI-11 gateways for connected VISA devices.
    Returns a list of resource strings.
    """
    gateway_resources = []
    for ip in gateway_ips:
        if LOCAL_DEBUG: logger.debug(f"   👉 Scraping Gateway {ip}...")
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
            if LOCAL_DEBUG:
                logger.error(
                    f"   ❌ Error scraping gateway {ip}: {e}")

        if LOCAL_DEBUG: logger.debug(f"   ✅ Found {len(targets)} resources from gateway {ip}: {targets}")
        for t in targets:
            visa_res = f"TCPIP::{ip}::{t}::INSTR"
            gateway_resources.append(visa_res)
            if LOCAL_DEBUG: logger.debug(f"     ➕ Added gateway resource: {visa_res}")
    return gateway_resources
