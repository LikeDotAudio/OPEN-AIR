# Proxy/yak_manager/manager_yak_rx.py
#
# This file (manager_yak_rx.py) processes the response from an SCPI query and publishes the parsed output values to MQTT.
# REFACTORED for Partitioned Architecture (Core Only).
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
# Version 20260221.Partition.1

import os
import inspect
import orjson
from typing import Any
from workers.Command_Router.mqtt.mqtt_message import MqttMessage

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()

class YakRxManager:
    """
    Processes responses from the instrument and publishes outputs to MQTT.
    """

    def __init__(self, mqtt_connection_manager, subscriber_router, yak_translator, state_cache_manager=None):
        self.mqtt_util = mqtt_connection_manager
        self.subscriber_router = subscriber_router
        self.yak_translator = yak_translator
        self.state_cache_manager = state_cache_manager
        self.NAB_BANDWIDTH_TRIGGER_PATH = [
            "yak",
            "Bandwidth",
            "nab",
            "NAB_bandwidth_settings",
            "scpi_details",
            "Execute Command",
            "trigger",
        ]
        self._setup_mqtt_subscriptions()

    def _setup_mqtt_subscriptions(self):
        # Subscribes to MQTT topics for receiving responses from the proxy.
        topic = "OPEN-AIR/Proxy/Rx_Outbox"
        self.subscriber_router.subscribe_to_topic(topic, 
                                                  self._on_rx_outbox_message)
        if LOCAL_DEBUG:
            logger.success(f"✅✅✅ [SUCCESS] YakRxManager subscribed to "
                           f"'{topic}' for proxy responses.")

    def _on_rx_outbox_message(self, msg: MqttMessage):
        # Handles incoming MQTT messages from the Proxy's Rx_Outbox.
        if LOCAL_DEBUG:
            logger.debug(f"🐐🚜📡 [YAK] Rx_Outbox message received on "
                         f"Topic: '{msg.topic}'")

        # Leverage hardened messaging interface
        try:
            payload_data = msg.get_json_payload()
        except Exception:
            # Gravity of Errors: Non-gated failure reporting.
            import traceback
            logger.error(f"🐐🚜📡 [YAK] ERROR: Failed to parse JSON payload "
                         f"from {msg.topic}. Forensic Report:\n"
                         f"{traceback.format_exc()}")
            return
            
        response_value = payload_data.get("response")
        command_sent = payload_data.get("command")
        correlation_id = payload_data.get("correlation_id")

        if correlation_id and response_value:
            command_context = self.yak_translator.retrieve_command_context(
                correlation_id)
            if command_context:
                path_parts = command_context.get("path_parts")
                command_details = command_context.get("command_details")

                if path_parts and command_details:
                    self.process_response(
                        path_parts, {"Outputs": command_details}, response_value
                    )
                else:
                    logger.error(f"🐐🚜📡 [YAK] ERROR: Incomplete command "
                                 f"context for {correlation_id}")
            else:
                logger.error(f"🐐🚜📡 [YAK] ERROR: No command context found "
                             f"for {correlation_id}.")
        else:
            logger.error(f"🐐🚜📡 [YAK] ERROR: Missing 'response' or "
                         f"'correlation_id' in Rx_Outbox payload.")

    def process_response(self, path_parts: list, command_details: dict, 
                         response: str):
        """
        Parses the response and publishes the results to MQTT topics.
        """
        if LOCAL_DEBUG:
            logger.debug(f"🐐🚜📡 [YAK] The agent reports back! "
                         f"Response from device: '{response}'")

        outputs = command_details.get("Outputs", {})
        if LOCAL_DEBUG:
            logger.debug(f"🐐🚜📡 [YAK] Received response from device.")
            logger.debug(f"🐐🚜📡 [YAK] Path Parts: {path_parts}")
            logger.trace(f"🐐🚜📡 [YAK] Raw Response: {response}")

        # Split the response into individual parts
        response_parts = [p.strip() for p in response.split(";")]
        output_keys = list(outputs.keys())

        # --- NAB_bandwidth_settings Order Correction ---
        if path_parts == self.NAB_BANDWIDTH_TRIGGER_PATH and len(output_keys) >= 5:
            if output_keys[3].endswith("Time_s") and output_keys[4].endswith("On"):
                temp_keys = list(output_keys)
                key_at_index_3 = output_keys[3]
                key_at_index_4 = output_keys[4]

                if (key_at_index_3.startswith("Sweep_Time_s") and 
                    key_at_index_4.startswith("Continuous_Mode_On")):
                    temp_keys[3], temp_keys[4] = temp_keys[4], temp_keys[3]
                    output_keys = temp_keys
                    if LOCAL_DEBUG:
                        logger.debug("🐐🚜📡 [YAK] Corrected YAK key swap.")

        if len(response_parts) != len(output_keys):
            logger.error(f"🐐🚜📡 [YAK] ERROR: Mismatched response length! "
                         f"Expected {len(output_keys)}, got "
                         f"{len(response_parts)}.")
            return

        # Construction of the base output topic
        base_output_topic_parts = ["OPEN-AIR", "yak"] + path_parts[:4] + ["Outputs"]
        base_output_topic = "/".join(base_output_topic_parts)

        # Match and publish each part of the response
        for i, key in enumerate(output_keys):
            raw_value = response_parts[i]
            output_topic = f"{base_output_topic}/{key}/value"

            if self.state_cache_manager:
                self.state_cache_manager.handle_external_update(
                    output_topic, 
                    raw_value, 
                    source="VISA"
                )
            else:
                self.mqtt_util.get_client_instance().publish(
                    topic=output_topic, payload=raw_value, qos=0, retain=True
                )
            
            if LOCAL_DEBUG:
                logger.debug(f"🐐🚜📡 [YAK] Published to '{output_topic}' "
                             f"value: '{raw_value}'.")

        if LOCAL_DEBUG:
            logger.success("✅✅✅ [SUCCESS] Response processed and published.")
