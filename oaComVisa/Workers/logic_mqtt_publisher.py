import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# Workers/logic_mqtt_publisher.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: This manager handles publishing device status and information to the MQTT broker.

import orjson
import time
import random

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()

MAX_GUI_DEVICE_SLOTS = 40


class VisaGuiPublisher:
    """Dispatches instrument telemetry and GUI state updates via MQTT."""

    def __init__(self, mqtt_controller):
        """Initializes the VisaGuiPublisher with an MQTT controller.

        Parameters:
        - mqtt_controller: The service providing access to the MQTT client.

        Returns:
        - None.
        """
        self.mqtt_util = mqtt_controller
        self.GUID = f"{random.getrandbits(16):04X}"

    def _update_found_devices_gui(self, resources):
        """Updates the GUI's device selection list based on search results.

        This method populates the first N slots with found resource names
        and explicitly clears any remaining slots up to MAX_GUI_DEVICE_SLOTS.

        Parameters:
        - resources: A list of strings containing VISA resource addresses.

        Returns:
        - None.

        Side effects and thread-safety:
        - Performs multiple non-blocking MQTT publish operations.
        """
        try:
            base_topic = (
                "OPEN-AIR/Device/Instrument_Connection/Search_and_Connect/Found_devices"
            )

            num_resources_to_show = min(len(resources), MAX_GUI_DEVICE_SLOTS)

            # Populate active slots with discovered resource addresses.
            for i in range(1, num_resources_to_show + 1):
                option_topic_prefix = f"{base_topic}/options/{i}"
                device_name = resources[i - 1]

                payload_active_true = orjson.dumps(
                    {"val": True, "src": "system", "ts": time.time(), "GUID": self.GUID}
                )
                self.mqtt_util.get_client_instance().publish(
                    topic=f"{option_topic_prefix}/active",
                    payload=payload_active_true,
                    qos=0,
                    retain=False,
                )
                self.mqtt_util.get_client_instance().publish(
                    topic=f"{option_topic_prefix}/label_active",
                    payload=device_name,
                    qos=0,
                    retain=False,
                )
                self.mqtt_util.get_client_instance().publish(
                    topic=f"{option_topic_prefix}/label_inactive",
                    payload=device_name,
                    qos=0,
                    retain=False,
                )

            # Clear unused slots to ensure the GUI list reflects the current search.
            for i in range(num_resources_to_show + 1, MAX_GUI_DEVICE_SLOTS + 1):
                option_topic_prefix = f"{base_topic}/options/{i}"

                payload_active_false = orjson.dumps(
                    {
                        "val": False,
                        "src": "system",
                        "ts": time.time(),
                        "GUID": self.GUID,
                    }
                )
                payload_empty_label = orjson.dumps(
                    {"val": "", "src": "system", "ts": time.time(), "GUID": self.GUID}
                )

                self.mqtt_util.get_client_instance().publish(
                    topic=f"{option_topic_prefix}/active",
                    payload=payload_active_false,
                    qos=0,
                    retain=False,
                )
                self.mqtt_util.get_client_instance().publish(
                    topic=f"{option_topic_prefix}/label_active",
                    payload=payload_empty_label,
                    qos=0,
                    retain=False,
                )
                self.mqtt_util.get_client_instance().publish(
                    topic=f"{option_topic_prefix}/label_inactive",
                    payload=payload_empty_label,
                    qos=0,
                    retain=False,
                )

            # Auto-select the first device for user convenience.
            if resources:
                first_device_topic = f"{base_topic}/options/1/selected"
                payload_selected_true = orjson.dumps(
                    {"val": True, "src": "system", "ts": time.time(), "GUID": self.GUID}
                )
                self.mqtt_util.get_client_instance().publish(
                    topic=first_device_topic,
                    payload=payload_selected_true,
                    qos=0,
                    retain=False,
                )
                matrix_log("core", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "💳 ✅ First device automatically selected after search.", "SUCCESS")

            matrix_log("core", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "💳 ✅ GUI device list updated with search results (up to 40 slots used).", "SUCCESS")
        except Exception as e:
            if LOCAL_DEBUG:
                logger.exception("💳 ❌ Error in _update_found_devices_gui")

    def _publish_status(self, topic_suffix, value):
        """Publishes a device-specific status value to the broker.

        Parameters:
        - topic_suffix: The sub-topic under Device_status (e.g., 'connected').
        - value: The data to publish (can be bool, string, or number).

        Returns:
        - None.

        Side effects and thread-safety:
        - Publishes with the 'retain' flag set to True to ensure persistent state.
        """
        if self.mqtt_util:
            base_topic = (
                "OPEN-AIR/Device/Instrument_Connection/Search_and_Connect/Device_status"
            )
            full_topic = f"{base_topic}/{topic_suffix}"
            
            # ⚡ ANTI-FEEDBACK SPEC: Define identity and origin to prevent
            # recursive message loops.
            payload_data = {
                "val": value,
                "src": "VISA",
                "ts": time.time(),
                "GUID": self.GUID,
                "msg_type": "SPLICE_ACTION",
                "origin_source": "VISA"
            }
            self.mqtt_util.get_client_instance().publish(
                topic=full_topic, payload=orjson.dumps(payload_data).decode(), qos=0, retain=True
            )
            matrix_log("core", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 MQTT: Published status '{topic_suffix}' with value '{value}' to '{full_topic}'", "DEBUG")

    def _publish_proxy_status(self, status: str):
        """Publishes the high-level proxy connection status.

        Parameters:
        - status: A string representing the proxy state (e.g., 'CONNECTED', 'DISCONNECTED').

        Returns:
        - None.
        """
        topic = "OPEN-AIR/Proxy/Status"
        payload_data = {"status": status, "timestamp": time.time()}
        self.mqtt_util.get_client_instance().publish(
            topic=topic, payload=orjson.dumps(payload_data).decode(), qos=0, retain=True
        )
        matrix_log("core", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 MQTT: Published Proxy Status '{status}' to '{topic}'", "DEBUG")
