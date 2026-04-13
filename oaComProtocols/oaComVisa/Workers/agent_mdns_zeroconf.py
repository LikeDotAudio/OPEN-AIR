import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# Workers/agent_mdns_zeroconf.py
# Author: Gemini Agent
# Version: 1.0.0
#
# Description: Dedicated module for mDNS/ZeroConf discovery (critical for AES70 _oca._tcp).

import socket
import time
from typing import List, Tuple, Dict
from concurrent.futures import ThreadPoolExecutor
from zeroconf import Zeroconf, ServiceBrowser, ServiceListener, ServiceInfo

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfigurationManager.FileReaders.config_reader import Config

app_constants = Config.get_instance()

class AES70DiscoveryListener(ServiceListener):
    """Listens for AES70 (_oca._tcp) devices on the network."""
    def __init__(self):
        self.found_devices = {}

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        pass

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        if name in self.found_devices:
            del self.found_devices[name]

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if info:
            ip = socket.inet_ntoa(info.addresses[0])
            port = info.port
            self.found_devices[name] = {
                "ip": ip,
                "port": port,
                "server": info.server,
                "properties": {k.decode(): v.decode() if isinstance(v, bytes) else v for k, v in info.properties.items()}
            }
            matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"📻 AES70 Found: {name} at {ip}:{port}", "SUCCESS")

def discover_aes70_devices(timeout: float = 2.0) -> Dict[str, dict]:
    """Scans for AES70 devices using mDNS."""
    matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "📡 Starting mDNS scan for AES70 (_oca._tcp)...", "DEBUG")
    zc = Zeroconf()
    listener = AES70DiscoveryListener()
    browser = ServiceBrowser(zc, "_oca._tcp.local.", listener)
    
    time.sleep(timeout)
    zc.close()
    
    return listener.found_devices

def _get_local_ip():
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

def _check_host(ip):
    """Legacy: Checks for Port 111 (VXI-11) and Port 5025 (SCPI)."""
    import urllib.request
    
    # 1. Port 111 (VXI-11)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.3)
            result = sock.connect_ex((ip, 111))
            if result == 0:
                is_gateway = False
                try:
                    configuration = Config.get_instance()
                    url = f"{configuration.VISA_PROBE_PROTOCOL}://{ip}/{configuration.VISA_PROBE_PATH}"
                    with urllib.request.urlopen(url, timeout=1) as resp:
                        if "E5810" in resp.read().decode("utf-8", errors="ignore"):
                            is_gateway = True
                except Exception:
                    pass
                return (ip, "GATEWAY" if is_gateway else "DEDICATED")
    except Exception:
        pass

    # 2. Port 5025 (SCPI)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.3)
            result = sock.connect_ex((ip, 5025))
            if result == 0:
                return (ip, "DEDICATED")
    except Exception:
        pass
    return None

def discover_ip_devices() -> Tuple[List[str], List[str]]:
    """
    Legacy: Hunts the local network for VISA/SCPI devices.
    Renamed internally to avoid conflict, but exported for orchestrator.
    """
    matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "💳🌐 Scanning network for VISA devices (Port Scan)...", "DEBUG")
    my_ip = _get_local_ip()
    if my_ip == "127.0.0.1":
        logger.warning("Could not determine local IP. Skipping network hunt.")
        return [], []

    subnet = ".".join(my_ip.split(".")[:-1])
    targets_to_scan = [f"{subnet}.{i}" for i in range(1, 255) if f"{subnet}.{i}" != my_ip]

    gateways = []
    dedicated = []

    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(_check_host, ip) for ip in targets_to_scan]
        for future in futures:
            try:
                result = future.result()
                if result:
                    ip, type_ = result
                    if type_ == "GATEWAY": gateways.append(ip)
                    else: dedicated.append(ip)
            except Exception as e:
                matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Error getting scan result: {e}", "TRACE")
                pass

    # Also trigger AES70 discovery here and merge if needed, 
    # but for now keeping them as separate return channels for the orchestrator.
    aes70_devices = discover_aes70_devices()
    for name, data in aes70_devices.items():
        # Inject AES70 IPs into the dedicated list so the orchestrator probes them too
        if data["ip"] not in dedicated:
            dedicated.append(data["ip"])

    matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"✅ IP/mDNS Scan complete. Dedicated: {len(dedicated)}, Gateways: {len(gateways)}, AES70: {len(aes70_devices)}", "SUCCESS")
    return dedicated, gateways
