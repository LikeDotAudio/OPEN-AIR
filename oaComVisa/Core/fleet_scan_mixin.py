import orjson
import traceback
from loguru import logger
LOCAL_DEBUG = True

class FleetScanMixin:
    """Manages the discovery scan sequence and MQTT status broadcasting."""

    def trigger_scan(self):
        """Initiates a comprehensive network scan for VISA instruments."""
        self.initial_scan_complete_event.clear()
        if LOCAL_DEBUG: logger.debug("💳🚢🔍 [VISA] Scan Triggered via API.")
            
        self._publish_scan_status("Start", {"status": "scanning"})
        try:
            num_devices_found = self.discovery_orchestrator.scan_and_manage_fleet()
            self._publish_scan_status("Complete", {"status": "ready", "num_devices": num_devices_found})
        except Exception as e:
            logger.exception(f"💳🚢🔍 [VISA] CRITICAL: Fleet scan failed.\nForensic Report:\n{traceback.format_exc()}")
        
        self.initial_scan_complete_event.set()

    def wait_for_initial_scan(self, timeout=None):
        """Blocks the calling thread until the first device scan completes."""
        if LOCAL_DEBUG: logger.debug("⏳ Waiting for initial VISA fleet scan to complete...")
        completed = self.initial_scan_complete_event.wait(timeout=timeout)
        if completed:
            if LOCAL_DEBUG: logger.success("✅ Initial VISA fleet scan complete.")
        else:
            if LOCAL_DEBUG: logger.debug("⚠️ Timed out waiting for initial VISA fleet scan.")
        return completed

    def _publish_scan_status(self, status, payload):
        """Sends scan progress information to the MQTT status topic."""
        if self.mqtt_bridge and self.mqtt_bridge.is_connected:
            topic = f"OPEN-AIR/System/Status/Fleet/{status}"
            self.mqtt_bridge.mqtt_manager.publish(topic, orjson.dumps(payload).decode())
            if LOCAL_DEBUG: logger.debug(f"Published scan status '{status}' to '{topic}'")
