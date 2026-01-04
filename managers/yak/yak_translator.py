# Proxy/yak_manager/yak_translator.py
#
# This file defines the `YakTranslator` class, which acts as the intermediary (translation layer)
# between the application's logic/GUI and the low-level VISA Proxy. It loads YAK (JSON) command
# definitions, processes triggers, builds SCPI commands with substitutions, and publishes them
# to the Proxy's MQTT Tx_Inbox.
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
# Version 20251225.000000.1

import os
import inspect
import orjson
import pathlib
import re
import time # For timestamping MQTT messages
import uuid # For correlation IDs

from managers.configini.config_reader import Config
app_constants = Config.get_instance() # Get the singleton instance

from workers.logger.logger import  debug_logger
from workers.logger.log_utils import _get_log_args
from workers.mqtt.mqtt_connection_manager import MqttConnectionManager
from workers.mqtt.mqtt_subscriber_router import MqttSubscriberRouter
from workers.setup.worker_project_paths import YAKETY_YAK_REPO_PATH 

# Imports for command building logic (will be refactored into this class)
# from managers.yak_manager.yak_repository_parser import get_command_node, lookup_scpi_command, lookup_inputs, lookup_outputs
# from managers.yak_manager.yak_command_builder import fill_scpi_placeholders

class YakTranslator:
    """
    The central translation layer for YAK commands.
    It loads command definitions, processes triggers, builds SCPI commands,
    and publishes them to the VisaProxy.
    """
    def __init__(self, mqtt_connection_manager: MqttConnectionManager, subscriber_router: MqttSubscriberRouter):
        self.mqtt_util = mqtt_connection_manager
        self.subscriber_router = subscriber_router
        self.yak_repository = {} # In-memory storage for YAK command definitions
        self.command_context_store = {} # Store command details keyed by correlation_id
        
        self._load_yak_repository()
        self._setup_mqtt_subscriptions()
        
        debug_logger(message="✅ YakTranslator initialized and ready to translate!", **_get_log_args())

    def _load_yak_repository(self):
        """
        Loads the YAK command definitions from the JSON file into memory.
        """
        current_function_name = inspect.currentframe().f_code.co_name
        repo_path = YAKETY_YAK_REPO_PATH # Assuming this is correctly defined in worker_project_paths.py
        
        if not repo_path.parent.exists():
            repo_path.parent.mkdir(parents=True, exist_ok=True)

        if repo_path.is_file() and repo_path.stat().st_size > 0:
            try:
                with open(repo_path, 'r') as f:
                    self.yak_repository = orjson.loads(f.read())
                debug_logger(message=f"🐂 YAK repository loaded from {repo_path}", **_get_log_args())
            except orjson.JSONDecodeError as e:
                debug_logger(message=f"❌ Error decoding JSON from YAK repository file {repo_path}: {e}. Initializing empty repository.", **_get_log_args())
                self.yak_repository = {}
            except Exception as e:
                debug_logger(message=f"❌ Error loading YAK repository from {repo_path}: {e}. Initializing empty repository.", **_get_log_args())
                self.yak_repository = {}
        else:
            debug_logger(message=f"🟡 YAK repository file not found or empty at {repo_path}. Initializing empty repository.", **_get_log_args())
            self.yak_repository = {}

    def _setup_mqtt_subscriptions(self):
        """
        Subscribes to MQTT topics that trigger YAK command translation.
        This would be topics like "OPEN-AIR/yak/commands/..."
        """
        # For now, let's assume a generic trigger topic, similar to old YaketyYakManager
        trigger_topic_filter = "OPEN-AIR/yak/commands/#" # Example: listen for commands that need translation
        self.subscriber_router.subscribe_to_topic(trigger_topic_filter, self._on_yak_trigger_message)
        debug_logger(message=f"👂 Subscribed to YAK trigger topic: '{trigger_topic_filter}'", **_get_log_args())
        
        # Also need to subscribe to the repo update topic if YakTranslator also handles repo updates (from YaketyYakManager)
        # Assuming repo updates are handled by a separate mechanism or the YakTranslator will just load from file
        # If the plan is for YakTranslator to also update repo_memory, then it needs a listener for that.
        # For now, focusing on command translation.

    def _on_yak_trigger_message(self, topic, payload):
        """
        Callback for incoming MQTT messages that trigger YAK command translation.
        Parses the topic, looks up the command in the repository, builds it, and publishes to VisaProxy.
        """
        current_function_name = inspect.currentframe().f_code.co_name
        debug_logger(message=f"📥 YAK Trigger received on Topic: '{topic}', Payload: '{payload}'", **_get_log_args())

        try:
            # The payload will likely contain parameters for substitution in the SCPI command.
            # Example payload: {"command_key": "CENTER_FREQ_SET", "value": 100.0, "units": "MHz"}
            # Or perhaps the topic itself contains enough info.
            
            # For simplicity, assume payload contains the arguments for the command
            # and the topic contains path to the command declaration in the repo.
            
            # Extract command path from topic (e.g., OPEN-AIR/yak/commands/INSTRUMENT/MEASUREMENT/FREQ)
            # Remove "OPEN-AIR/yak/commands/" prefix
            yak_command_path = topic.replace("OPEN-AIR/yak/commands/", "").split('/')
            
            # Find the command definition in the loaded yak_repository
            command_declaration = self._get_command_declaration(yak_command_path)
            
            if not command_declaration:
                debug_logger(message=f"❌ No YAK declaration found for command path: {yak_command_path}", **_get_log_args(), level="ERROR")
                return

            # Assume payload contains parameters for substitution
            # e.g., if command is "FREQ {value} {units}", payload could be {"value": 100, "units": "MHZ"}
            payload_data = orjson.loads(payload)

            # Build the SCPI command
            scpi_template = command_declaration.get("scpi_template")
            if not scpi_template:
                debug_logger(message=f"❌ No 'scpi_template' found in YAK declaration for {yak_command_path}", **_get_log_args(), level="ERROR")
                return

            # Perform substitutions (using a simplified version of yak_command_builder logic)
            final_scpi_command = self._fill_scpi_placeholders(scpi_template, payload_data)
            
            if not final_scpi_command:
                debug_logger(message=f"❌ Failed to build SCPI command from template: {scpi_template} and payload: {payload_data}", **_get_log_args(), level="ERROR")
                return

            # Determine if it's a query or write based on declaration
            is_query = command_declaration.get("is_query", False)
            
            # Generate correlation ID for response handling
            correlation_id = str(uuid.uuid4())

            # Store command context for YakRxManager
            self.command_context_store[correlation_id] = {
                "path_parts": yak_command_path, 
                "command_details": command_declaration.get("Outputs", {}) 
            }

            # Publish to VisaProxy's Tx_Inbox
            proxy_payload = {
                "command": final_scpi_command,
                "query": is_query,
                "correlation_id": correlation_id
            }
            self.mqtt_util.get_client_instance().publish(topic="OPEN-AIR/Proxy/Tx_Inbox", payload=orjson.dumps(proxy_payload), qos=0, retain=False)
            debug_logger(message=f"⬆️ Published SCPI command to Proxy Tx_Inbox: '{final_scpi_command}' (Query: {is_query}, CorrID: {correlation_id})", **_get_log_args())

        except orjson.JSONDecodeError:
            debug_logger(message=f"❌ Invalid JSON payload for YAK trigger on topic '{topic}': {payload}", **_get_log_args(), level="ERROR")
        except Exception as e:
            debug_logger(message=f"❌ Error processing YAK trigger for topic '{topic}': {e}", **_get_log_args(), level="CRITICAL")

    def _get_command_declaration(self, path_parts: list):
        """
        Navigates the yak_repository to find the command declaration.
        Example path_parts: ["INSTRUMENT", "MEASUREMENT", "FREQ", "SET"]
        """
        node = self.yak_repository
        for part in path_parts:
            node = node.get(part)
            if node is None:
                return None
        return node

    def _fill_scpi_placeholders(self, scpi_template: str, params: dict):
        """
        Fills placeholders in an SCPI command template using parameters from a dictionary.
        Example: "FREQ {value}{units}" with {"value": 100, "units": "MHZ"} -> "FREQ 100MHZ"
        """
        try:
            # Use f-string formatting style
            formatted_command = scpi_template.format(**params)
            return formatted_command
        except KeyError as e:
            debug_logger(message=f"❌ Missing parameter for SCPI template '{scpi_template}': {e}", **_get_log_args(), level="ERROR")
            return None
        except Exception as e:
            debug_logger(message=f"❌ Error filling SCPI placeholders for template '{scpi_template}': {e}", **_get_log_args(), level="ERROR")
            return None

    def retrieve_command_context(self, correlation_id: str):
        """
        Retrieves and removes the command context associated with a correlation ID.
        """
        if correlation_id in self.command_context_store:
            context = self.command_context_store.pop(correlation_id) # Retrieve and remove
            debug_logger(message=f"✅ Retrieved command context for CorrID: {correlation_id}", **_get_log_args())
            return context
        else:
            debug_logger(message=f"❌ No command context found for CorrID: {correlation_id}", **_get_log_args(), level="WARNING")
            return None