# oaTranslator/Methods/yak_receiver.py
#
# Processes responses from SCPI queries and publishes the parsed output
# values to MQTT. Maps instrument data back to the YAK hierarchy.
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
# Version 20260406.1945.1

import inspect

# --- Standard Debug Logging Setup ---
from loguru import logger

from oaComProtocols.oaComMQTT.Core.mqtt_message import MqttMessage
from oaConfigurationManager.FileReaders.config_reader import Config
from oaLogging.Methods.matrix_gate import matrix_log

app_constants = Config.get_instance()

class YakReceiverManager:
    """
    Handles instrument responses and dispatches data to the MQTT broker.
    
    This manager correlates incoming instrument responses with previously 
    issued commands, parses the payload based on YAK definitions, and 
    updates the system state via MQTT and the state cache.

    Responsibilities:
        - Response Correlation: Matches 'Rx_Outbox' messages to 'Tx_Inbox' IDs.
        - Payload De-serialization: Parses semi-colon delimited SCPI replies.
        - State Propagation: Updates the StateCache with hardware-fresh values.
        - Legacy Correction: Handles hardware quirks for specific trigger paths.

    Constraints:
        - Operates within the UI Partition.
        - Depends on 'YakTranslator' for context retrieval.
        - Assumes 'OPEN-AIR/Proxy/Rx_Outbox' topic availability.
    """

    def __init__(self, mqtt_connection_manager, subscriber_router,
                 yak_translator, state_cache_manager=None):
        """
        Initializes the YakRxManager and establishes proxy subscriptions.

        Args:
            mqtt_connection_manager: Global MQTT connectivity handler.
            subscriber_router: The filter-based message router.
            yak_translator: The translator instance holding active context.
            state_cache_manager (optional): Local store for rapid state recall.
        """
        self.mqtt_util = mqtt_connection_manager
        self.subscriber_router = subscriber_router
        self.yak_translator = yak_translator
        self.state_cache_manager = state_cache_manager

        # Hardware Workaround: Fixed path for bandwidth trigger corrections.
        self.NAB_BANDWIDTH_TRIGGER_PATH = [
            "yak", "Bandwidth", "nab", "NAB_bandwidth_settings",
            "scpi_details", "Execute Command", "trigger",
        ]
        self._setup_mqtt_subscriptions()

    def _setup_mqtt_subscriptions(self):
        """Registers the primary Proxy outbox filter for instrument responses."""
        topic = "OPEN-AIR/Proxy/Rx_Outbox"
        self.subscriber_router.subscribe_to_topic(topic, self._on_rx_outbox_message)
        matrix_log("UI", "TRANSLATOR", inspect.currentframe().f_code.co_name,
                   f"✅ [INIT] YakRxManager listening on '{topic}'",
                   level="SUCCESS")

    def _on_rx_outbox_message(self, message: MqttMessage):
        """
        Callback for processing messages from the instrument proxy.
        
        Extracts the correlation ID to retrieve the original YAK command 
        context, then hands off the raw response for parsing.

        Args:
            message: The MQTT message containing response, command, and ID.

        Side Effects:
            - Purges correlation context from the YakTranslator on match.
        """
        try:
            payload_data = message.get_json_payload()
        except Exception as e:
            logger.error(f"❌ [RX] Payload parse failure: {e}")
            return

        response_value = payload_data.get("response")
        correlation_id = payload_data.get("correlation_id")

        if correlation_id and response_value:
            # Retrieve the 'why' behind this response from the translator.
            command_context = self.yak_translator.retrieve_command_context(
                correlation_id)
            if command_context:
                path_parts = command_context.get("path_parts")
                command_details = command_context.get("command_details")

                if path_parts and command_details:
                    self.process_response(path_parts,
                                         {"Outputs": command_details},
                                         response_value)
                else:
                    logger.error(f"❌ [RX] Incomplete context for {correlation_id}")
            else:
                logger.error(f"❌ [RX] Unknown correlation ID: {correlation_id}")
        else:
            logger.error("❌ [RX] Missing response or correlation ID.")

    def process_response(self, path_parts: list, command_details: dict,
                         response: str):
        """
        Parses an instrument response and publishes values to the MQTT broker.
        
        Args:
            path_parts: The hierarchical path to the command in the YAK repo.
            command_details: The expected output structure (dictionary).
            response: The raw string response from the instrument.

        Side Effects:
            - Publishes one or more MQTT messages to 'OPEN-AIR/yak/.../value'.
            - Updates the StateCache if available.
        """
        outputs = command_details.get("Outputs", {})
        # Split hardware response; SCPI standard usually implies ';' delimiter.
        response_parts = [p.strip() for p in response.split(";")]
        output_keys = list(outputs.keys())

        # --- Hardware Quirk Correction ---
        # Correct for legacy bandwidth setting key-order discrepancies
        # observed in specific firmware versions.
        if path_parts == self.NAB_BANDWIDTH_TRIGGER_PATH and len(output_keys) >= 5:
            if (output_keys[3].startswith("Sweep_Time_s") and
                output_keys[4].startswith("Continuous_Mode_On")):
                output_keys[3], output_keys[4] = output_keys[4], output_keys[3]
                matrix_log("UI", "TRANSLATOR", inspect.currentframe().f_code.co_name,
                           "🔄 [CORRECT] Key swap applied for bandwidth path.",
                           level="DEBUG")

        if len(response_parts) != len(output_keys):
            logger.error(f"❌ [RX] Length mismatch! Expected {len(output_keys)}, "
                         f"got {len(response_parts)}.")
            return

        # Construct the canonical YAK output topic hierarchy.
        base_output_topic = "/".join(["OPEN-AIR", "yak"] + path_parts[:4] + ["Outputs"])

        for i, key in enumerate(output_keys):
            raw_value = response_parts[i]
            output_topic = f"{base_output_topic}/{key}/value"

            # Route to Cache Manager for atomic persistence.
            if self.state_cache_manager:
                self.state_cache_manager.handle_external_update(
                    output_topic, raw_value, source="VISA")
            else:
                self.mqtt_util.get_client_instance().publish(
                    topic=output_topic, payload=raw_value, qos=0, retain=True)

            matrix_log("UI", "TRANSLATOR", inspect.currentframe().f_code.co_name,
                       f"📡📤📤 [STATE] {output_topic} -> {raw_value}",
                       level="DEBUG")
