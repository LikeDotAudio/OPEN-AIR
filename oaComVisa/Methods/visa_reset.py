# managers/manager_visa_reset.py
#
# A dedicated manager to handle device reset commands received via MQTT.
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
#
# Version 20250907.002515.4
# FIXED: Updated subscriptions and callbacks to listen for the new '/trigger' subtopic,
# aligning with the updated actuator logic.

import os
import inspect
import orjson

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()

from ..Core.visa_proxy import VisaProxy  # Use VisaProxy
from oaThreadManager.Core.mqtt_subscriber_mixin import MqttSubscriberMixin


class VisaResetManager(MqttSubscriberMixin):
    """
    Listens for MQTT commands to reset or reboot the instrument and dispatches them.
    """

    def __init__(self, mqtt_connection_manager, subscriber_router, visa_proxy):
        # Initializes the manager, linking it to the MQTT controller and SCPI dispatcher.
        current_function_name = inspect.currentframe().f_code.co_name
        self.current_class_name = self.__class__.__name__

        if LOCAL_DEBUG: logger.debug(f"💳 🟢️️️🟢 Initiating the {self.current_class_name}. The enforcer of resets is online!")
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
            if LOCAL_DEBUG: logger.success(f"💳 ✅ {self.current_class_name} initialized and listening.")

        except Exception as e:
            if LOCAL_DEBUG:
                logger.exception(f"💳 ❌ Error in {self.current_class_name}.{current_function_name}")
                logger.debug(f"💳 🟢️️️🔴 Catastrophic failure during {self.current_class_name} initialization! The error be: {e}")

    def _on_reset_request(self, topic, payload):
        current_function_name = inspect.currentframe().f_code.co_name
        if LOCAL_DEBUG: logger.debug(f"💳 ▶️ {current_function_name} due to message on topic: {topic}")
        try:
            # FIXED: Check if the payload value is explicitly 'true'
            data = orjson.loads(payload)
            if str(data.get("value")).lower() == "true":
                if LOCAL_DEBUG: logger.debug(f"💳 🔵 Command received: Soft Reset. Dispatching '{self.CMD_RESET_DEVICE}'.")
                self.visa_proxy.write_safe(command=self.CMD_RESET_DEVICE)

        except (orjson.JSONDecodeError, AttributeError) as e:
            logger.error(f"💳 ❌ Error processing reset request payload: {payload}. Error: {e}"
            )
            if LOCAL_DEBUG: logger.debug(f"💳 🟢️️️🔴 A garbled message! The reset contraption is confused! The error be: {e}")