# managers/manager_visa_reboot.py
#
# A dedicated manager to handle device reboot commands received via MQTT.
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
#

import os
import inspect
import orjson

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()

from .visa_proxy import VisaProxy  # Use VisaProxy


class VisaRebootManager:
    """
    Listens for MQTT commands to reboot the instrument and dispatches them.
    """

    def __init__(self, mqtt_connection_manager, subscriber_router, visa_proxy):
        # Initializes the manager, linking it to the MQTT controller and SCPI dispatcher.
        current_function_name = inspect.currentframe().f_code.co_name
        self.current_class_name = self.__class__.__name__

        if LOCAL_DEBUG: logger.debug(f"💳 🟢️️️🟢 Initiating the {self.current_class_name}. The enforcer of reboots is online!")
        try:
            self.mqtt_util = mqtt_connection_manager
            self.subscriber_router = subscriber_router
            self.visa_proxy = visa_proxy

            # --- SCPI Command Constants (No Magic Numbers) ---
            self.CMD_REBOOT_DEVICE = (
                ":SYSTem:POWer:RESet"  # Per user instruction for power cycle
            )

            # --- MQTT Topic Constants ---
            self.BASE_TOPIC = "OPEN-AIR/Device/Instrument_Connection/System_Reset"
            self.TOPIC_REBOOT = f"{self.BASE_TOPIC}/Reboot_device/trigger"

            self._setup_mqtt_subscriptions()
            if LOCAL_DEBUG: logger.success(f"💳 ✅ {self.current_class_name} initialized and listening.")

        except Exception as e:
            if LOCAL_DEBUG:
                logger.exception("💳 ❌ Error in {self.current_class_name}.{current_function_name}"
                )
                if LOCAL_DEBUG: logger.debug(f"💳 🟢️️️🔴 Catastrophic failure during {self.current_class_name} initialization! The error be: {e}")

    def _setup_mqtt_subscriptions(self):
        # A brief, one-sentence description of the function's purpose.
        current_function_name = inspect.currentframe().f_code.co_name
        if LOCAL_DEBUG: logger.debug(f"💳 ▶️ {current_function_name} to subscribe to reboot topics.")
        try:
            self.subscriber_router.subscribe_to_topic(
                topic_filter=self.TOPIC_REBOOT, callback_func=self._on_reboot_request
            )
            if LOCAL_DEBUG: logger.success("💳 ✅ The reboot manager did subscribe to its topics.")

        except Exception as e:
            if LOCAL_DEBUG:
                logger.exception("💳 ❌ Error in {current_function_name}")
                if LOCAL_DEBUG: logger.debug(f"💳 🟢️️️🔴 The subscription circuits are fried! The error be: {e}")

    def _on_reboot_request(self, topic, payload):
        # Handles a request to perform a power cycle on the instrument.
        current_function_name = inspect.currentframe().f_code.co_name
        if LOCAL_DEBUG: logger.debug(f"💳 ▶️ {current_function_name} due to message on topic: {topic}")
        try:
            # FIXED: Check if the payload value is explicitly 'true'
            data = orjson.loads(payload)
            if str(data.get("value")).lower() == "true":
                if LOCAL_DEBUG: logger.debug(f"💳 🔵 Command received: Power Cycle. Dispatching '{self.CMD_REBOOT_DEVICE}'.")
                self.visa_proxy.write_safe(command=self.CMD_REBOOT_DEVICE)

        except (orjson.JSONDecodeError, AttributeError) as e:
            logger.error(f"💳 ❌ Error processing reboot request payload: {payload}. Error: {e}"
            )
            if LOCAL_DEBUG: logger.debug(f"💳 🟢️️️🔴 The reboot sequence has short-circuited! The error be: {e}")