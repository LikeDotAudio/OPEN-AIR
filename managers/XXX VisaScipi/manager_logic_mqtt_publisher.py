# managers/VisaScipi/manager_visa_transmit.py
#
# This manager handles publishing device status and information to the MQTT broker.
#
# Author: Anthony Peter Kuzub
#
import orjson
import time
import uuid
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args

MAX_GUI_DEVICE_SLOTS = 40


class VisaGuiPublisher:
    def __init__(self, mqtt_controller):
        self.mqtt_util = mqtt_controller
        self.GUID = str(uuid.uuid4())

    def _update_found_devices_gui(self, resources):
        # Updates the GUI's `Found_devices` listbox based on the search results,
        # supporting up to MAX_GUI_DEVICE_SLOTS (40) devices.
        try:
            base_topic = (
                "OPEN-AIR/Device/Instrument_Connection/Search_and_Connect/Found_devices"
            )

            num_resources_to_show = min(len(resources), MAX_GUI_DEVICE_SLOTS)

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
                debug_logger(
                    message="💳 ✅ First device automatically selected after search.",
                    **_get_log_args(),
                )

            debug_logger(
                message="💳 ✅ GUI device list updated with search results (up to 40 slots used).",
                **_get_log_args(),
            )
        except Exception as e:
            debug_logger(
                message=f"💳 ❌ Error in _update_found_devices_gui: {e}",
                **_get_log_args(),
            )

    def _publish_status(self, topic_suffix, value):
        # Helper function to publish a value to a specific status topic.
        if self.mqtt_util:
            base_topic = (
                "OPEN-AIR/Device/Instrument_Connection/Search_and_Connect/Device_status"
            )
            full_topic = f"{base_topic}/{topic_suffix}"
            payload_data = {
                "val": value,
                "src": "device_link_manager",
                "ts": time.time(),
                "GUID": self.GUID,
            }
            self.mqtt_util.get_client_instance().publish(
                topic=full_topic, payload=orjson.dumps(payload_data), qos=0, retain=True
            )
            debug_logger(
                message=f"💳 MQTT: Published status '{topic_suffix}' with value '{value}' to '{full_topic}'",
                **_get_log_args(),
            )

    def _publish_proxy_status(self, status: str):
        # Publishes the proxy connection status.
        topic = "OPEN-AIR/Proxy/Status"
        payload_data = {"status": status, "timestamp": time.time()}
        self.mqtt_util.get_client_instance().publish(
            topic=topic, payload=orjson.dumps(payload_data), qos=0, retain=True
        )
        debug_logger(
            message=f"💳 MQTT: Published Proxy Status '{status}' to '{topic}'",
            **_get_log_args(),
        )
