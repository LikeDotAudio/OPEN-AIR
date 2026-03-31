from oaLogging.Methods.matrix_gate import matrix_log
# Methods/visa_reboot.py
# Author: Anthony Peter Kuzub
# Version: 20250907.002515.4
#
# Description: managers/manager_visa_reboot.py

import os
import inspect
import orjson

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()

from ..Core.visa_proxy import VisaProxy  # Use VisaProxy


class VisaRebootManager:
    """
    Listens for MQTT commands to reboot the instrument and dispatches them.
    """

    def __init__(self, mqtt_connection_manager, subscriber_router, visa_proxy):
        # Initializes the manager, linking it to the MQTT controller and SCPI dispatcher.
        current_function_name = inspect.currentframe().f_code.co_name
        self.current_class_name = self.__class__.__name__

        matrix_log("core", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 🟢️️️🟢 Initiating the {self.current_class_name}. The enforcer of reboots is online!", "DEBUG")
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
            matrix_log("core", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 ✅ {self.current_class_name} initialized and listening.", "SUCCESS")

        except Exception as e:
            if LOCAL_DEBUG:
                logger.exception("💳 ❌ Error in {self.current_class_name}.{current_function_name}"
                )
                matrix_log("core", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 🟢️️️🔴 Catastrophic failure during {self.current_class_name} initialization! The error be: {e}", "DEBUG")

    def _setup_mqtt_subscriptions(self):
        # A brief, one-sentence description of the function's purpose.
        current_function_name = inspect.currentframe().f_code.co_name
        matrix_log("core", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 ▶️ {current_function_name} to subscribe to reboot topics.", "DEBUG")
        try:
            self.subscriber_router.subscribe_to_topic(
                topic_filter=self.TOPIC_REBOOT, callback_func=self._on_reboot_request
            )
            matrix_log("core", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "💳 ✅ The reboot manager did subscribe to its topics.", "SUCCESS")

        except Exception as e:
            if LOCAL_DEBUG:
                logger.exception("💳 ❌ Error in {current_function_name}")
                matrix_log("core", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 🟢️️️🔴 The subscription circuits are fried! The error be: {e}", "DEBUG")

    def _on_reboot_request(self, topic, payload):
        # Handles a request to perform a power cycle on the instrument.
        current_function_name = inspect.currentframe().f_code.co_name
        matrix_log("core", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 ▶️ {current_function_name} due to message on topic: {topic}", "DEBUG")
        try:
            # FIXED: Check if the payload value is explicitly 'true'
            data = orjson.loads(payload)
            if str(data.get("value")).lower() == "true":
                matrix_log("core", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 🔵 Command received: Power Cycle. Dispatching '{self.CMD_REBOOT_DEVICE}'.", "DEBUG")
                self.visa_proxy.write_safe(command=self.CMD_REBOOT_DEVICE)

        except (orjson.JSONDecodeError, AttributeError) as e:
            logger.error(f"💳 ❌ Error processing reboot request payload: {payload}. Error: {e}"
            )
            matrix_log("core", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 🟢️️️🔴 The reboot sequence has short-circuited! The error be: {e}", "DEBUG")
