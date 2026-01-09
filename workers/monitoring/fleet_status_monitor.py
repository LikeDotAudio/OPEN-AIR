# monitoring/fleet_status_monitor.py
#
# Monitors the status of the device fleet and controls a GUI status light (Traffic Light).
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20250821.200641.1
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

    # Initializes the FleetStatusMonitor.
    # This constructor sets up the monitor to subscribe to scan start and complete events
    # from the Visa Fleet Manager, defaulting the status to RED (scanning/uninitialized)
    # and publishing this initial state to the GUI status light.
    # Inputs:
    #     state_mirror_engine: The state mirror engine for MQTT synchronization.
    #     subscriber_router (MqttSubscriberRouter): The MQTT subscriber router.
    # Outputs:
    #     None.
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

    # Callback for when a device fleet scan starts.
    # This method updates the internal state to "RED" and publishes this color
    # to the GUI status light, indicating that a scan is in progress.
    # Inputs:
    #     topic (str): The MQTT topic the message was received on.
    #     payload: The MQTT message payload (unused in this method).
    # Outputs:
    #     None.
    def _on_scan_start(self, topic, payload):
        self.current_state = "RED"
        self._publish_color("red")
        debug_logger("🔴 Fleet Scan Started - Status Red")

    # Callback for when a device fleet scan completes.
    # This method processes the scan completion payload, checks the number of devices found,
    # and updates the GUI status light to GREEN if devices were found, or RED otherwise.
    # Inputs:
    #     topic (str): The MQTT topic the message was received on.
    #     payload: The MQTT message payload containing scan results (e.g., number of devices).
    # Outputs:
    #     None.
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

    # Publishes the specified color to the GUI Status Light via MQTT.
    # This method constructs a JSON payload containing the color and a timestamp,
    # then publishes it to a dedicated MQTT topic that controls the GUI status indicator.
    # Inputs:
    #     color (str): The color to set the status light to (e.g., "red", "green").
    # Outputs:
    #     None.
    def _publish_color(self, color):
        """Tells the GUI Status Light what color to be."""
        target_topic = "OPEN-AIR/GUI/Global/Header/StatusLight"
        payload = {"color": color, "ts": time.time()}
        publish_payload(target_topic, orjson.dumps(payload))