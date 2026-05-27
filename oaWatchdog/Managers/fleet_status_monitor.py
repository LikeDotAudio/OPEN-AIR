# Managers/fleet_status_monitor.py
# Author: Anthony Peter Kuzub
# Version: 20260323.1700.1
#
# Description: monitoring/fleet_status_monitor.py

import time

import orjson

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = False
from oaComProtocols.oaComMQTT.Core.mqtt_message import MqttMessage
from oaConfigurationManager.FileReaders.config_reader import Config
from oaLogging.Core.logger import SYSTEM_LOGGER as sys_logger

app_constants = Config.get_instance()  # Get the singleton instance

from oaComProtocols.oaComMQTT.Core.mqtt_publisher_service import publish_payload
from oaComProtocols.oaComMQTT.Managers.mqtt_subscriber_router import MqttSubscriberRouter

# Static context for this module
VERSION = "20260323.1700.1"
MODULE_NAME = __name__


class FleetStatusMonitor:
    """
    The 'Traffic Light' controller for the Fleet Manager.
    - Defaults to RED (Scanning/Uninitialized).
    - Turns GREEN only when a valid Fleet JSON is published.
    """

    # Initializes the FleetStatusMonitor.
    # This constructor sets up the monitor to subscribe to scan start and complete events
    # and publishing this initial state to the GUI status light.
    # Inputs:
    #     state_mirror_engine: The state mirror engine for MQTT synchronization.
    #     subscriber_router (MqttSubscriberRouter): The MQTT subscriber router.
    # Outputs:
    #     None.
    def __init__(self, state_mirror_engine, subscriber_router: MqttSubscriberRouter):
        self.state_mirror_engine = state_mirror_engine
        self.subscriber_router = subscriber_router  # Store subscriber_router
        self.base_topic = "OpenAir/System/Status/Fleet"
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
    #     message (MqttMessage): The MQTT message object.
    # Outputs:
    #     None.
    def _on_scan_start(self, message: MqttMessage):
        self.current_state = "RED"
        self._publish_color("red")
        if LOCAL_DEBUG: sys_logger.debug("Fleet Scan Started - Status Red")

    # Callback for when a device fleet scan completes.
    # This method processes the scan completion payload, checks the number of devices found,
    # and updates the GUI status light to GREEN if devices were found, or RED otherwise.
    # Inputs:
    #     message (MqttMessage): The MQTT message object.
    # Outputs:
    #     None.
    def _on_scan_complete(self, message: MqttMessage):
        payload = message.payload
        try:
            if isinstance(payload, (bytes, str)):
                data = orjson.loads(payload)
            else:
                data = payload

            num_devices = data.get("num_devices", 0)
            if num_devices > 0:
                self.current_state = "GREEN"
                self._publish_color("green")
                if LOCAL_DEBUG: sys_logger.debug(f"Fleet Scan Complete - {num_devices} devices found. Status Green")
            else:
                self.current_state = "RED"
                self._publish_color("red")
                if LOCAL_DEBUG: sys_logger.debug("Fleet Scan Complete - No devices found. Status Red")
        except orjson.JSONDecodeError as e:
            sys_logger.warning(f"Malformed scan complete payload received: {e}")
            self.current_state = "RED"
            self._publish_color("red")
        except Exception:
            sys_logger.exception("Error processing scan complete payload")
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
        target_topic = "OpenAir/GUI/Global/Header/StatusLight"
        payload = {"color": color, "timestamp": time.time()}
        publish_payload(target_topic, orjson.dumps(payload).decode())
