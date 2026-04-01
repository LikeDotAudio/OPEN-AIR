# oaTranslator/Managers/yak_translator.py
#
# The central translation layer for YAK commands. It loads command 
# definitions, processes triggers, and builds SCPI commands.
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
# Version 20260330.1200.1

import os
import sys
from oaLogging.Methods.matrix_gate import matrix_log
import inspect

# Add the hyphenated directory to sys.path temporarily to import compiler_hook
_rs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Core", "oaTranslatorCore-rs")
if _rs_dir not in sys.path:
    sys.path.insert(0, _rs_dir)

import compiler_hook
compiler_hook.ensure_compiled()

try:
    import oatranslatorcore_rs
except ImportError as e:
    from loguru import logger
    logger.critical("🚀❌ [FATAL] Rust Translator Core module missing. Pure Rust mode is mandatory.")
    raise e
import inspect
import orjson
import pathlib
import re
import time
import random
from typing import Any
from oaComMQTT.Core.mqtt_message import MqttMessage

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config
app_constants = Config.get_instance()

from oaComMQTT.Managers.mqtt_connection import MqttConnectionManager
from oaComMQTT.Managers.mqtt_subscriber_router import MqttSubscriberRouter
from oaOchestration.Constants.project_paths import YAKETY_YAK_REPO_PATH

class YakTranslator:
    """
    Orchestrates the translation of high-level YAK commands into SCPI strings.
    
    This manager maintains an in-memory repository of command definitions 
    and handles the transformation of MQTT-triggered events into instrument-
    specific messages.
    """

    def __init__(
        self,
        mqtt_connection_manager: MqttConnectionManager,
        subscriber_router: MqttSubscriberRouter,
    ):
        """
        Initializes the YakTranslator and loads the command repository.
        
        Args:
            mqtt_connection_manager: The manager handling MQTT connectivity.
            subscriber_router: Router for managing MQTT topic subscriptions.
        """
        self.mqtt_util = mqtt_connection_manager
        self.subscriber_router = subscriber_router
        self.yak_repository = {}
        self.command_context_store = {}

        self._load_yak_repository()
        self._setup_mqtt_subscriptions()

        matrix_log("UI", "TRANSLATOR", inspect.currentframe().f_code.co_name, "✅ YakTranslator initialized and ready.", level="SUCCESS")

    def _load_yak_repository(self):
        """
        Loads YAK command definitions from the filesystem into memory.
        
        This method ensures the repository directory exists and attempts 
        to parse the JSON definition file.
        """
        repo_path = YAKETY_YAK_REPO_PATH

        if not repo_path.parent.exists():
            repo_path.parent.mkdir(parents=True, exist_ok=True)

        if repo_path.is_file() and repo_path.stat().st_size > 0:
            with open(repo_path, "rb") as f:
                self.yak_repository = orjson.loads(f.read())
            
            matrix_log("UI", "TRANSLATOR", inspect.currentframe().f_code.co_name, f"📡📥📥 [CONFIG] YAK repository loaded: {repo_path}", level="DEBUG")
        else:
            logger.warning(f"⚠️ YAK repository missing at {repo_path}")
            self.yak_repository = {}

    def _setup_mqtt_subscriptions(self):
        """
        Registers MQTT topic filters for incoming YAK command triggers.
        """
        trigger_topic_filter = "OPEN-AIR/yak/commands/#"
        self.subscriber_router.subscribe_to_topic(
            trigger_topic_filter, self._on_yak_trigger_message
        )
        matrix_log("UI", "TRANSLATOR", inspect.currentframe().f_code.co_name, f"🎧 [LISTEN] Subscribed to triggers: '{trigger_topic_filter}'", level="DEBUG")

    def _on_yak_trigger_message(self, msg: MqttMessage):
        """
        Processes incoming MQTT messages to trigger SCPI command generation.
        
        Parses the topic to identify the command path, retrieves the 
        corresponding declaration, renders the final SCPI string using 
        payload parameters, and dispatches it to the Proxy Tx_Inbox.
        
        Args:
            msg: The incoming MqttMessage object containing topic and payload.
        """
        topic = msg.topic
        payload = msg.payload
        
        # Extract command path from topic hierarchy
        yak_command_path = topic.replace("OPEN-AIR/yak/commands/", "").split("/")

        command_declaration = self._get_command_declaration(yak_command_path)
        if not command_declaration:
            logger.error(f"❌ Unknown YAK command path: {yak_command_path}")
            return

        # Handle payload parsing (bytes/str/dict)
        payload_data = orjson.loads(payload) if isinstance(payload, (bytes, str)) else payload

        scpi_template = command_declaration.get("scpi_template")
        if not scpi_template:
            logger.error(f"❌ Missing 'scpi_template' for {yak_command_path}")
            return

        final_scpi_command = self._render_scpi_command(scpi_template, payload_data)
        if not final_scpi_command:
            return

        is_query = command_declaration.get("is_query", False)
        correlation_id = f"{random.getrandbits(16):04X}"

        # Persist context for asynchronous response correlation
        self.command_context_store[correlation_id] = {
            "path_parts": yak_command_path,
            "command_details": command_declaration.get("Outputs", {}),
        }

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
        
        matrix_log("UI", "TRANSLATOR", inspect.currentframe().f_code.co_name, f"📡📤📤 [TRANSLATE] SCPI: '{final_scpi_command}' (ID: {correlation_id})", level="DEBUG")

    def _get_command_declaration(self, path_parts: list):
        """
        Navigates the internal repository to find a specific command node.
        
        Args:
            path_parts: A list of keys representing the command hierarchy.
            
        Returns:
            The command declaration dictionary if found, otherwise None.
        """
        node = self.yak_repository
        for part in path_parts:
            node = node.get(part)
            if node is None:
                return None
        return node

    def _render_scpi_command(self, scpi_template: str, params: dict):
        """
        Interpolates parameters into an SCPI template string.
        
        Args:
            scpi_template: The raw SCPI string containing {placeholder} tokens.
            params: Dictionary of values to substitute.
            
        Returns:
            The rendered SCPI command string.
        """
        return scpi_template.format(**params)

    def retrieve_command_context(self, correlation_id: str):
        """
        Retrieves and clears context associated with a correlation ID.
        
        Used by the RX manager to map instrument responses back to original 
        requests.
        
        Args:
            correlation_id: The unique hex ID for the command transaction.
            
        Returns:
            The stored context dictionary, or None if not found.
        """
        if correlation_id in self.command_context_store:
            return self.command_context_store.pop(correlation_id)
        
        logger.error(f"❌ Correlation ID mismatch: {correlation_id}")
        return None
