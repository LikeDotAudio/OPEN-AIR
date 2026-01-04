# Proxy/yak_manager/manager_yak_rx.py
#
# This file (manager_yak_rx.py) processes the response from an SCPI query and publishes the parsed output values to MQTT.
# A complete and comprehensive pre-amble that describes the file and the functions within.
# The purpose is to provide clear documentation and versioning.
#
# The hash calculation drops the leading zero from the hour (e.g., 08 -> 8)
# As the current hour is 20, no change is needed.

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

import os
import inspect
from workers.logger.logger import  debug_logger
from workers.logger.log_utils import _get_log_args 
from workers.logger.log_utils import _get_log_args
from managers.configini.config_reader import Config
app_constants = Config.get_instance() # Get the singleton instance
import orjson

from managers.configini.config_reader import Config
app_constants = Config.get_instance() # Get the singleton instance

LOCAL_DEBUG_ENABLE = False

class YakRxManager:
    """
    Processes responses from the instrument and publishes outputs to MQTT.
    """
    def __init__(self, mqtt_connection_manager, subscriber_router, yak_translator):
        self.mqtt_util = mqtt_connection_manager
        self.subscriber_router = subscriber_router
        self.yak_translator = yak_translator
        self.NAB_BANDWIDTH_TRIGGER_PATH = ['yak', 'Bandwidth', 'nab', 'NAB_bandwidth_settings', 'scpi_details', 'Execute Command', 'trigger']
        self._setup_mqtt_subscriptions()

    def _setup_mqtt_subscriptions(self):
        # Subscribes to MQTT topics for receiving responses from the proxy.
        topic = "OPEN-AIR/Proxy/Rx_Outbox"
        self.subscriber_router.subscribe_to_topic(topic, self._on_rx_outbox_message)
        debug_logger(message=f"✅ YakRxManager subscribed to '{topic}' for proxy responses.", **_get_log_args())

    def _on_rx_outbox_message(self, topic, payload):
        # Handles incoming MQTT messages from the Proxy's Rx_Outbox.
        current_function_name = inspect.currentframe().f_code.co_name
        debug_logger(message=f"📥 Rx_Outbox message received on Topic: '{topic}', Payload: '{payload}'", **_get_log_args())
        
        try:
            payload_data = orjson.loads(payload)
            response_value = payload_data.get("response")
            command_sent = payload_data.get("command")
            correlation_id = payload_data.get("correlation_id")

            if correlation_id and response_value:
                command_context = self.yak_translator.retrieve_command_context(correlation_id)
                if command_context:
                    path_parts = command_context.get("path_parts")
                    command_details = command_context.get("command_details") # This would be the 'outputs' part
                    
                    if path_parts and command_details:
                        self.process_response(path_parts, {"Outputs": command_details}, response_value)
                    else:
                        debug_logger(message=f"❌ Incomplete command context retrieved for correlation_id: {correlation_id}", **_get_log_args(), level="ERROR")
                else:
                    debug_logger(message=f"❌ No command context found for correlation_id: {correlation_id}. Cannot process response.", **_get_log_args(), level="ERROR")
            else:
                debug_logger(message=f"❌ Missing 'response' or 'correlation_id' in Rx_Outbox payload: {payload}", **_get_log_args(), level="ERROR")
        except orjson.JSONDecodeError:
            debug_logger(message=f"❌ Failed to decode JSON payload from '{topic}': {payload}", **_get_log_args(), level="ERROR")
        except Exception as e:
            debug_logger(message=f"❌ Error processing Rx_Outbox message from '{topic}': {e}", **_get_log_args(), level="CRITICAL")

    def process_response(self, path_parts, command_details, response):
        """
        Parses the response and publishes the results to MQTT topics.
        """
        current_function_name = inspect.currentframe().f_code.co_name
        if app_constants.global_settings['debug_enabled']:
            debug_logger(
                message=f"🐐🐐🐐📡 The agent reports back! Response from device: '{response}'",
                **_get_log_args()


            )

        outputs = command_details.get("Outputs", {})
        if app_constants.global_settings['debug_enabled']:
            debug_logger(
                message=f"ℹ️ YakRxManager received a response from the device.",
                **_get_log_args()
            )
            debug_logger(
                message=f"ℹ️ Path Parts: {path_parts}",
                **_get_log_args()
            )
            debug_logger(
                message=f"ℹ️ Command Details: {orjson.dumps(outputs, indent=2)}",
                **_get_log_args()
            )
            debug_logger(
                message=f"ℹ️ Raw Response: {response}",
                **_get_log_args()
            )
        
        try:
            # Split the response into individual parts
            response_parts = [p.strip() for p in response.split(';')]
            output_keys = list(outputs.keys())
            
            # --- START FIX: Order Correction for NAB_bandwidth_settings ---
            
            # Check if this is the specific command with the known key swap issue
            if path_parts == self.NAB_BANDWIDTH_TRIGGER_PATH and len(output_keys) >= 5:
                if app_constants.global_settings['debug_enabled']:
                    debug_logger(
                        message=f"🔍🔵 Detected NAB_bandwidth_settings command with key order issue. Keys before fix: {output_keys}",
                        **_get_log_args()


                    )
                
                # Check the order of the 4th and 5th items in the output_keys list
                # Based on the device response, the order is: ..., Continuous_Mode_On, Sweep_Time_s
                # The current YAK metadata order is likely: ..., Sweep_Time_s, Continuous_Mode_On
                
                # The assumption is that output_keys[3] is 'Sweep_Time_s' and output_keys[4] is 'Continuous_Mode_On'
                # if the original YAK metadata was incorrectly specified.
                
                # Since the device sends: [..., VBW_Auto_On, Continuous_Mode_On, Sweep_Time_s]
                # We force the key list to match this order, assuming the metadata stores them as:
                # 0, 1, 2, 4, 3 (for continuous and sweep time)
                
                if output_keys[3].endswith("Time_s") and output_keys[4].endswith("On"):
                    # This indicates the keys are likely SWAPPED in the metadata relative to the SCPI response order.
                    
                    # Create a corrected key list
                    temp_keys = list(output_keys)
                    
                    # Swap keys at index 3 (Continuous_Mode_On) and 4 (Sweep_Time_s) to match device response order
                    # The device gives: [..., val3, val4, val5]
                    # We assume YAK metadata gives: [..., key3, key4, key5]
                    # If key4 and key5 are the ones swapped, we swap them back in the list
                    
                    # NOTE: Since the key definitions in the metadata are fixed, and the SCPI output order is fixed:
                    # SCPI Order (Response Parts Index): 3 = Continuous_Mode_On, 4 = Sweep_Time_s
                    # The YAK metadata is misaligned.
                    
                    # Let's verify what keys are at the incorrect indices and swap them to match the SCPI order
                    
                    # Expected Key at Index 3 (Response Part 4): Continuous_Mode_On/value
                    # Expected Key at Index 4 (Response Part 5): Sweep_Time_s/value

                    key_at_index_3 = output_keys[3]
                    key_at_index_4 = output_keys[4]

                    if key_at_index_3.startswith("Sweep_Time_s") and key_at_index_4.startswith("Continuous_Mode_On"):
                         # SWAP REQUIRED: Swap the 4th and 5th keys in the list to match SCPI order
                        temp_keys[3], temp_keys[4] = temp_keys[4], temp_keys[3]
                        output_keys = temp_keys
                        if app_constants.global_settings['debug_enabled']:
                            debug_logger(
                                message=f"🟢️️️🟡 Corrected YAK key swap. Keys after fix: {output_keys}",
                                **_get_log_args()


                            )
                    
            # --- END FIX ---


            if len(response_parts) != len(output_keys):
                if app_constants.global_settings['debug_enabled']:
                    debug_logger(
                        message=f"❌🔴 Mismatched response length after potential correction! Expected {len(output_keys)} parts, but received {len(response_parts)}.",
                        **_get_log_args()


                    )
                return

            # FIX: Correctly rebuild the base topic by joining the initial path parts
            # The base output topic should be constructed up to '/Outputs'
            # path_parts looks like: ['yak', 'Bandwidth', 'nab', 'NAB_bandwidth_settings', 'scpi_details', 'Execute Command', 'trigger']
            # We want: OPEN-AIR/repository/yak/Bandwidth/nab/NAB_bandwidth_settings/Outputs
            base_output_topic_parts = ['OPEN-AIR', 'yak'] + path_parts[:4] + ['Outputs']
            base_output_topic = '/'.join(base_output_topic_parts)
            
            # Match and publish each part of the response
            for i, key in enumerate(output_keys):
                raw_value = response_parts[i]
                
                # Construct the full topic for the specific output value
                output_topic = f"{base_output_topic}/{key}/value"
                
                # Publish the value to the MQTT topic
                self.mqtt_util.get_client_instance().publish(topic=output_topic, payload=raw_value, qos=0, retain=True)
                if app_constants.global_settings['debug_enabled']:
                    debug_logger(
                        message=f"💾 Published to '{output_topic}' with value: '{raw_value}'.",
                        **_get_log_args()


                    )
            
            debug_logger(message="✅ Response processed and all output values published to MQTT.", **_get_log_args())

        except Exception as e:
            debug_logger(message=f"❌ Error processing response: {e}")
            if app_constants.global_settings['debug_enabled']:
                debug_logger(
                    message=f"❌🔴 The response processing has been shipwrecked! The error be: {e}",
                    **_get_log_args()


                )