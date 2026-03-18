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
# Version 20260221.Partition.1

import os
import inspect
import orjson
import pathlib
import re
import time  # For timestamping MQTT messages
import random  # For correlation IDs
from typing import Any
from oaComMQTT.mqtt_message import MqttMessage

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.config_reader import Config

app_constants = Config.get_instance()

from oaComMQTT.mqtt_connection import MqttConnectionManager
from oaComMQTT.mqtt_subscriber_router import MqttSubscriberRouter
from oaOchestration.project_paths import YAKETY_YAK_REPO_PATH

class YakTranslator:
    """
    The central translation layer for YAK commands.
    It loads command definitions, processes triggers, builds SCPI commands,
    and publishes them to the VisaProxy.
    """

    def __init__(
        self,
        mqtt_connection_manager: MqttConnectionManager,
        subscriber_router: MqttSubscriberRouter,
    ):
        self.mqtt_util = mqtt_connection_manager
        self.subscriber_router = subscriber_router
        self.yak_repository = {}  # In-memory storage for YAK command definitions
        self.command_context_store = {}  # Store command details keyed by correlation_id

        self._load_yak_repository()
        self._setup_mqtt_subscriptions()

        if LOCAL_DEBUG: logger.success("✅ YakTranslator initialized and ready to translate!")

    def _load_yak_repository(self):
        """
        Loads the YAK command definitions from the JSON file into memory.
        """
        repo_path = YAKETY_YAK_REPO_PATH

        if not repo_path.parent.exists():
            repo_path.parent.mkdir(parents=True, exist_ok=True)

        if repo_path.is_file() and repo_path.stat().st_size > 0:
            # We assume the file is valid. If not, it crashes (crash-only).
            with open(repo_path, "rb") as f:
                self.yak_repository = orjson.loads(f.read())
            
            if LOCAL_DEBUG: logger.debug(f"🐂 YAK repository loaded from {repo_path}")
        else:
            if LOCAL_DEBUG: logger.debug(f"🟡 YAK repository file not found or empty at {repo_path}. Initializing empty repository.")
            self.yak_repository = {}

    def _setup_mqtt_subscriptions(self):
        """
        Subscribes to MQTT topics that trigger YAK command translation.
        """
        trigger_topic_filter = "OPEN-AIR/yak/commands/#"
        self.subscriber_router.subscribe_to_topic(
            trigger_topic_filter, self._on_yak_trigger_message
        )
        if LOCAL_DEBUG: logger.debug(f"👂 Subscribed to YAK trigger topic: '{trigger_topic_filter}'")

    def _on_yak_trigger_message(self, msg: MqttMessage):
        """
        Callback for incoming MQTT messages that trigger YAK command translation.
        No try/except here. If something is malformed, the Core crashes and Supervisor restarts it.
        """
        topic = msg.topic
        payload = msg.payload
        if LOCAL_DEBUG: logger.debug(f"📥 YAK Trigger received on Topic: '{topic}', Payload: '{payload}'")

        # Extract command path from topic
        yak_command_path = topic.replace("OPEN-AIR/yak/commands/", "").split("/")

        # Find the command definition
        command_declaration = self._get_command_declaration(yak_command_path)

        if not command_declaration:
            logger.error(f"❌ No YAK declaration found for command path: {yak_command_path}")
            return

        # Parse payload
        if isinstance(payload, (bytes, str)):
            payload_data = orjson.loads(payload)
        else:
            payload_data = payload

        # Build the SCPI command
        scpi_template = command_declaration.get("scpi_template")
        if not scpi_template:
            logger.error(f"❌ No 'scpi_template' found in YAK declaration for {yak_command_path}")
            return

        # Perform substitutions
        final_scpi_command = self._fill_scpi_placeholders(
            scpi_template, payload_data
        )

        if not final_scpi_command:
            return

        # Determine if it's a query or write based on declaration
        is_query = command_declaration.get("is_query", False)

        # Generate correlation ID for response handling
        correlation_id = f"{random.getrandbits(16):04X}"

        # Store command context for YakRxManager
        self.command_context_store[correlation_id] = {
            "path_parts": yak_command_path,
            "command_details": command_declaration.get("Outputs", {}),
        }

        # Publish to VisaProxy's Tx_Inbox
        proxy_payload = {
            "command": final_scpi_command,
            "query": is_query,
            "correlation_id": correlation_id,
        }
        self.mqtt_util.get_client_instance().publish(
            topic="OPEN-AIR/Proxy/Tx_Inbox",
            payload=orjson.dumps(proxy_payload).decode(),
            qos=0,
            retain=False,
        )
        if LOCAL_DEBUG: logger.debug(f"⬆️ Published SCPI command to Proxy Tx_Inbox: '{final_scpi_command}' (Query: {is_query}, CorrID: {correlation_id})")

    def _get_command_declaration(self, path_parts: list):
        """
        Navigates the yak_repository to find the command declaration.
        """
        node = self.yak_repository
        for part in path_parts:
            node = node.get(part)
            if node is None:
                return None
        return node

    def _fill_scpi_placeholders(self, scpi_template: str, params: dict):
        """
        Fills placeholders in an SCPI command template.
        """
        # Explicitly check for required keys in params if possible, 
        # or let .format() raise KeyError and crash (crash-only).
        formatted_command = scpi_template.format(**params)
        return formatted_command

    def retrieve_command_context(self, correlation_id: str):
        """
        Retrieves and removes the command context associated with a correlation ID.
        """
        if correlation_id in self.command_context_store:
            context = self.command_context_store.pop(correlation_id)
            if LOCAL_DEBUG: logger.success(f"✅ Retrieved command context for CorrID: {correlation_id}")
            return context
        else:
            logger.error(f"❌ No command context found for CorrID: {correlation_id}")
            return None