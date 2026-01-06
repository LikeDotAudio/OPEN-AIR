import time
import orjson
from workers.mqtt.mqtt_publisher_service import publish_payload
from workers.logger.logger import debug_logger
from workers.mqtt.mqtt_subscriber_router import (
    MqttSubscriberRouter,
)  # Import MqttSubscriberRouter


class FleetStatusMonitor:
    """
    The 'Traffic Light' controller for the Fleet Manager.
    - Defaults to RED (Scanning/Uninitialized).
    - Turns GREEN only when a valid Fleet JSON is published.
    """

    def __init__(self, state_mirror_engine, subscriber_router: MqttSubscriberRouter):
        self.state_mirror_engine = state_mirror_engine
        self.subscriber_router = subscriber_router  # Store subscriber_router
        self.base_topic = "OPEN-AIR/System/Status/Fleet"
        self.current_state = "RED"  # Default state

        # 1. Listen for the signals
        # 'Start' comes from the Visa Manager beginning its work
        self.subscriber_router.subscribe_to_topic(
            f"{self.base_topic}/Start", self._on_scan_start
        )
        # 'Complete' comes from the Visa Manager finishing
        self.subscriber_router.subscribe_to_topic(
            f"{self.base_topic}/Complete", self._on_scan_complete
        )

        # 2. Publish initial state (RED) immediately on startup
        self._publish_color("red")

    def _on_scan_start(self, topic, payload):
        self.current_state = "RED"
        self._publish_color("red")
        debug_logger("🔴 Fleet Scan Started - Status Red")

    def _on_scan_complete(self, topic, payload):
        try:
            data = orjson.loads(payload)
            num_devices = data.get("num_devices", 0)
            if num_devices > 0:
                self.current_state = "GREEN"
                self._publish_color("green")
                debug_logger(
                    f"🟢 Fleet Scan Complete - {num_devices} devices found. Status Green"
                )
            else:
                self.current_state = "RED"
                self._publish_color("red")
                debug_logger("🔴 Fleet Scan Complete - No devices found. Status Red")
        except Exception as e:
            debug_logger(f"Error processing scan complete payload: {e}", level="ERROR")
            self.current_state = "RED"
            self._publish_color("red")

    def _publish_color(self, color):
        """Tells the GUI Status Light what color to be."""
        target_topic = "OPEN-AIR/GUI/Global/Header/StatusLight"
        payload = {"color": color, "ts": time.time()}
        publish_payload(target_topic, orjson.dumps(payload))
