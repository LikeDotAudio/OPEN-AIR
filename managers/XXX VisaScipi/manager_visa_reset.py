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

from managers.configini.config_reader import Config
app_constants = Config.get_instance() # Get the singleton instance

# --- Utility and Worker Imports ---
from workers.logger.logger import  debug_logger
from workers.logger.log_utils import _get_log_args 
# from workers.mqtt.worker_mqtt_controller_util import MqttControllerUtility
from .manager_visa_proxy import VisaProxy # Use VisaProxy



class VisaResetManager:
    """
    Listens for MQTT commands to reset or reboot the instrument and dispatches them.
    """
    def __init__(self, mqtt_connection_manager, subscriber_router, visa_proxy):
        # Initializes the manager, linking it to the MQTT controller and SCPI dispatcher.
        current_function_name = inspect.currentframe().f_code.co_name
        self.current_class_name = self.__class__.__name__

        debug_logger(
            message=f"💳 🟢️️️🟢 Initiating the {self.current_class_name}. The enforcer of resets is online!",
            **_get_log_args()
            


        )
        try:
            self.mqtt_util = mqtt_connection_manager
            self.subscriber_router = subscriber_router
            self.visa_proxy = visa_proxy
            
            # --- SCPI Command Constants (No Magic Numbers) ---
            self.CMD_RESET_DEVICE = "*RST"

            # --- MQTT Topic Constants ---
            self.BASE_TOPIC = "OPEN-AIR/Device/Instrument_Connection/System_Reset"
            self.TOPIC_RESET = f"{self.BASE_TOPIC}/Reset_device/trigger"

            self._setup_mqtt_subscriptions()
            debug_logger(message=f"💳 ✅ {self.current_class_name} initialized and listening.", **_get_log_args())

        except Exception as e:
            debug_logger(message=f"💳 ❌ Error in {self.current_class_name}.{current_function_name}: {e}")
            debug_logger(
                message=f"💳 🟢️️️🔴 Catastrophic failure during {self.current_class_name} initialization! The error be: {e}",
                **_get_log_args()
                


            )

    def _setup_mqtt_subscriptions(self):
        # A brief, one-sentence description of the function's purpose.
        current_function_name = inspect.currentframe().f_code.co_name
        debug_logger(
            message=f"💳 ▶️ {current_function_name} to subscribe to reset/reboot topics.",
            **_get_log_args()
            


        )
        try:
            self.subscriber_router.subscribe_to_topic(topic_filter=self.TOPIC_RESET, callback_func=self._on_reset_request)
            debug_logger(message="💳 ✅ The reset manager did subscribe to its topics.", **_get_log_args())

        except Exception as e:
            debug_logger(message=f"💳 ❌ Error in {current_function_name}: {e}")
            debug_logger(
                message=f"💳 🟢️️️🔴 The subscription circuits are fried! The error be: {e}",
                **_get_log_args()
                


            )

    def _on_reset_request(self, topic, payload):
        current_function_name = inspect.currentframe().f_code.co_name
        debug_logger(
            message=f"💳 ▶️ {current_function_name} due to message on topic: {topic}",
            **_get_log_args()
            


        )
        try:
            # FIXED: Check if the payload value is explicitly 'true'
            data = orjson.loads(payload)
            if str(data.get("value")).lower() == 'true':
                debug_logger(message=f"💳 🔵 Command received: Soft Reset. Dispatching '{self.CMD_RESET_DEVICE}'.", **_get_log_args())
                self.visa_proxy.write_safe(command=self.CMD_RESET_DEVICE)
                
        except (orjson.JSONDecodeError, AttributeError) as e:
            debug_logger(message=f"💳 ❌ Error processing reset request payload: {payload}. Error: {e}")
            debug_logger(
                message=f"💳 🟢️️️🔴 A garbled message! The reset contraption is confused! The error be: {e}",
                **_get_log_args()
                


            )