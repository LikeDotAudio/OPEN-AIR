# Core/fleet_scan_manager.py
# Author: Anthony Peter Kuzub
# Version: 2.0.0
#
# Description: Refactored Scan Manager (Composition over Inheritance).

import inspect
import threading
import traceback

import orjson
from loguru import logger

from oaLogging.Methods.matrix_gate import matrix_log


class ScanManager:
    """Manages the discovery scan sequence and MQTT status broadcasting."""

    def __init__(self, orchestrator):
        self._orchestrator = orchestrator
        self.initial_scan_complete_event = threading.Event()

    def trigger_scan(self):
        """Initiates a comprehensive network scan for VISA instruments."""
        self.initial_scan_complete_event.clear()
        matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "💳🚢🔍 [VISA] Scan Triggered via API.", "DEBUG")

        self._publish_scan_status("Start", {"status": "scanning"})
        try:
            num_devices_found = self._orchestrator.discovery_orchestrator.scan_and_manage_fleet()
            self._publish_scan_status("Complete", {"status": "ready", "num_devices": num_devices_found})
        except Exception:
            logger.exception(f"💳🚢🔍 [VISA] CRITICAL: Fleet scan failed.\nForensic Report:\n{traceback.format_exc()}")

        self.initial_scan_complete_event.set()

    def wait_for_initial_scan(self, timeout=None):
        """Blocks the calling thread until the first device scan completes."""
        matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "⏳ Waiting for initial VISA fleet scan to complete...", "DEBUG")
        completed = self.initial_scan_complete_event.wait(timeout=timeout)
        if completed:
            matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "✅ Initial VISA fleet scan complete.", "SUCCESS")
        else:
            matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "⚠️ Timed out waiting for initial VISA fleet scan.", "DEBUG")
        return completed

    def _publish_scan_status(self, status, payload):
        """Sends scan progress information to the MQTT status topic."""
        bridge = self._orchestrator.mqtt_bridge
        if bridge and bridge.is_connected:
            topic = f"OpenAir/System/Status/Fleet/{status}"
            bridge.mqtt_manager.publish(topic, orjson.dumps(payload).decode())
            matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Published scan status '{status}' to '{topic}'", "DEBUG")
