
import inspect
import re
import urllib.parse

# Workers/agent_static_ip_prober.py
# Author: Gemini Agent
# Version: 1.0.0
#
# Description: Dedicated module for Gateway-based VISA device discovery (VXI-11 HTML scraping).
import urllib.request

from oaLogging.Methods.matrix_gate import matrix_log

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = False
from loguru import logger

from oaConfigurationManager.FileReaders.config_reader import Config

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
        matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"   👉 Scraping Gateway {ip}...", "DEBUG")
        configuration = Config.get_instance()
        url = f"{configuration.VISA_PROBE_PROTOCOL}://{ip}/{configuration.VISA_PROBE_PATH}"
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

        matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"   ✅ Found {len(targets)} resources from gateway {ip}: {targets}", "DEBUG")
        for t in targets:
            visa_res = f"TCPIP::{ip}::{t}::INSTR"
            gateway_resources.append(visa_res)
            matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"     ➕ Added gateway resource: {visa_res}", "DEBUG")
    return gateway_resources
