import inspect
import os

# Managers/discovery_orchestrator.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: High-level orchestrator for VISA device discovery.
import orjson
from loguru import logger

from oaLogging.Methods.matrix_gate import matrix_log

from ..Methods.network_utils import clean_string_for_display
from ..Workers.visa_scanner import VisaScanner


class DiscoveryOrchestrator:
    """Orchestrates the lifecycle of VISA device discovery and inventory reporting."""

    def __init__(self, manager_ref=None, aes70_manager=None, output_filename="fleet_inventory.json"):
        self.manager = manager_ref
        self.aes70_manager = aes70_manager
        self.scanner = VisaScanner()
        self.output_filename = output_filename
        self.inventory = {}

    def run_discovery(self, silent=False):
        """Runs the full discovery cycle: Hunt -> Enumerate -> Probe -> Report."""
        if not silent: print("\n[1/4] HUNTING NETWORK...")
        dedicated_ips, gateway_ips = self.scanner.hunt_for_devices()

        potential_targets = []
        # A. Dedicated
        for ip in dedicated_ips:
            potential_targets.append({"Type": "DEDICATED", "Resource": f"TCPIP::{ip}::INSTR"})
        # B. Gateways
        for ip in gateway_ips:
            targets = self.scanner.get_gateway_inventory(ip)
            for t in targets:
                potential_targets.append({"Type": "GATEWAY", "Resource": f"TCPIP::{ip}::{t}::INSTR"})
        # C. USB/Local
        try:
            local_res = self.scanner.rm.list_resources("?*")
            for resource in local_res:
                if "TCPIP" not in resource and "ASRL" not in resource:
                    potential_targets.append({"Type": "LOCAL", "Resource": resource})
        except:
            pass

        if not silent: print(f"[2/4] PROBING {len(potential_targets)} POTENTIAL TARGETS...")

        for index, target in enumerate(potential_targets):
            raw_res = target["Resource"]
            display_res = clean_string_for_display(raw_res)

            conn_details = self.scanner.parse_resource_details(display_res)
            idn = self.scanner.query_device_safe(raw_res)

            device_entry = {
                "id": str(index + 1),
                "type": target["Type"],
                "resource_string": display_res,
                "ip_address": conn_details["IP"],
                "interface_port": conn_details["Interface"],
                "gpib_address": conn_details["GPIB_Addr"],
            }

            if idn:
                mfg, model, serial, firm = self.scanner.parse_idn(idn)
                device_entry.update({
                    "status": "Active", "manufacturer": mfg, "model": model,
                    "serial_number": serial, "firmware": firm
                })
                device_entry = self.scanner.augment_device_details(device_entry)
            else:
                device_entry.update({
                    "status": "Unresponsive", "manufacturer": "Unknown", "model": "Unknown",
                    "serial_number": "Unknown", "firmware": "Unknown",
                    "device_type": "Unknown", "notes": "Connection Timed Out"
                })

            self.inventory[str(index + 1)] = device_entry

        return self.inventory

    def save_inventory(self, dir_path=None):
        """Saves the current inventory to a JSON file."""
        if not self.inventory:
            return False

        save_dir = dir_path or os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(save_dir, self.output_filename)

        try:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(orjson.dumps(self.inventory, option=orjson.OPT_INDENT_2))
            return full_path
        except Exception as e:
            logger.error(f"Error saving inventory: {e}")
            return False

    def print_report(self):
        """Prints the final fleet inventory to the console in a formatted table."""
        print("\n[4/4] FINAL FLEET INVENTORY")
        print("=" * 140)
        print(f"{'ID':<3} | {'MODEL':<8} | {'TYPE':<20} | {'IP ADDRESS':<15} | {'ADDR':<8} | {'NOTES'}")
        print("-" * 140)

        for key, d in self.inventory.items():
            model = (d["model"][:8]) if len(d["model"]) > 8 else d["model"]
            dtype = (d["device_type"][:20]) if len(d["device_type"]) > 20 else d["device_type"]
            print(f"{key:<3} | {model:<8} | {dtype:<20} | {d['ip_address']:<15} | {d['gpib_address']:<8} | {d['notes']}")
        print("=" * 140)

    def shutdown(self):
        """Shutdown the orchestrator."""
        matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "💳🔍 [DISCOVERY] Discovery Orchestrator shutting down.", "DEBUG")
        pass
