import inspect

# Methods/visa_reset.py
# Author: Anthony Peter Kuzub
# Version: 20250907.002515.4
#
# Description: A dedicated manager to handle device reset commands received via MQTT.
import orjson

from oaLogging.Methods.matrix_gate import matrix_log

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = False
from loguru import logger

from oaConfigurationManager.FileReaders.config_reader import Config

app_constants = Config.get_instance()

from oaThreadManager.Core.mqtt_subscriber_mixin import MqttSubscriberMixin


class VisaResetManager(MqttSubscriberMixin):
    """
    Listens for MQTT commands to reset or reboot the instrument and dispatches them.
    """

    def __init__(self, mqtt_connection_manager, subscriber_router, visa_proxy):
        # Initializes the manager, linking it to the MQTT controller and SCPI dispatcher.
        current_function_name = inspect.currentframe().f_code.co_name
        self.current_class_name = self.__class__.__name__

        matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 🟢️️️🟢 Initiating the {self.current_class_name}. The enforcer of resets is online!", "DEBUG")
        try:
            self.mqtt_util = mqtt_connection_manager
            self.subscriber_router = subscriber_router
            self.visa_proxy = visa_proxy

            # --- SCPI Command Constants (No Magic Numbers) ---
            self.CMD_RESET_DEVICE = "*RST"

            # --- MQTT Topic Constants ---
            self.BASE_TOPIC = "OPEN-AIR/Device/Instrument_Connection/System_Reset"
            self.TOPIC_RESET = f"{self.BASE_TOPIC}/Reset_device/trigger"

            self.register_mqtt_topics({self.TOPIC_RESET: self._on_reset_request})
            matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 ✅ {self.current_class_name} initialized and listening.", "SUCCESS")

        except Exception as e:
            if LOCAL_DEBUG:
                logger.exception(f"💳 ❌ Error in {self.current_class_name}.{current_function_name}")
                matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 🟢️️️🔴 Catastrophic failure during {self.current_class_name} initialization! The error be: {e}", "DEBUG")

    def _on_reset_request(self, topic, payload):
        current_function_name = inspect.currentframe().f_code.co_name
        matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 ▶️ {current_function_name} due to message on topic: {topic}", "DEBUG")
        try:
            # FIXED: Check if the payload value is explicitly 'true'
            data = orjson.loads(payload)
            if str(data.get("value")).lower() == "true":
                matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 🔵 Command received: Soft Reset. Dispatching '{self.CMD_RESET_DEVICE}'.", "DEBUG")
                self.visa_proxy.write_safe(command=self.CMD_RESET_DEVICE)

        except (orjson.JSONDecodeError, AttributeError) as e:
            logger.error(f"💳 ❌ Error processing reset request payload: {payload}. Error: {e}"
            )
            matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 🟢️️️🔴 A garbled message! The reset contraption is confused! The error be: {e}", "DEBUG")
