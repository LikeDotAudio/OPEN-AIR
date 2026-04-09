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
# Version 20260406.1935.1

import os
import sys
from loguru import logger
from oaLogging.Methods.matrix_gate import matrix_log
import inspect

# --- RUST ACCELERATION LAYER (PyO3) ---
try:
    from oaStateCache.Core.oaTranslatorCore_rs import compiler_hook
    compiler_hook.ensure_compiled()
    from oatranslatorcore_rs import *
    HAS_RUST = True
except ImportError:
    logger.warning("⚠️ [TRANSLATOR] oatranslatorcore_rs not found. "
                   "Pure Rust mode is preferred for performance.")
    HAS_RUST = False
except Exception as e:
    logger.error(f"❌ [TRANSLATOR] Failed to initialize Rust Core: {e}")
    HAS_RUST = False

import orjson
import pathlib
import re
import time
import random
from typing import Any
from oaComProtocols.oaComMQTT.Core.mqtt_message import MqttMessage

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import initialize_logging, set_log_directory

from oaConfigurationManager.FileReaders.config_reader import Config
app_constants = Config.get_instance()

from oaComProtocols.oaComMQTT.Managers.mqtt_connection import MqttConnectionManager
from oaComProtocols.oaComMQTT.Managers.mqtt_subscriber_router import MqttSubscriberRouter
from oaOchestration.Constants.project_paths import YAKETY_YAK_REPO_PATH

class YakTranslator:
    """
    Orchestrates the translation of high-level YAK commands into SCPI strings.
    
    This manager maintains an in-memory repository of command definitions 
    and handles the transformation of MQTT-triggered events into instrument-
    specific messages.

    Responsibilities:
        - Command Repository Management: Loads and caches YAK JSON definitions.
        - SCPI Orchestration: Renders templates into hardware-ready strings.
        - Transaction Correlation: Tracks IDs to link async instrument replies.
        - Interface Isolation: Maps UI-neutral YAK paths to Core-level SCPI.

    Constraints:
        - Operates within the UI Partition (Translation Layer).
        - Requires 'YAKETY_YAK_REPO_PATH' to be accessible for initialization.
        - Depends on 'oaComProtocols.oaComMQTT' for trigger ingress.
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

        Side Effects:
            - Performs blocking I/O to load the YAK repository from disk.
            - Registers global MQTT filters.
        """
        self.mqtt_util = mqtt_connection_manager
        self.subscriber_router = subscriber_router
        self.yak_repository = {}
        self.command_context_store = {}

        self._load_yak_repository()
        self._setup_mqtt_subscriptions()

        matrix_log("UI", "TRANSLATOR", inspect.currentframe().f_code.co_name, 
                   "✅ YakTranslator initialized and ready.", level="SUCCESS")

    def _load_yak_repository(self):
        """
        Loads YAK command definitions from the filesystem into memory.
        
        Navigates to the project-defined repository path and ingests the 
        JSON command schema. If missing, attempts to initialize a skeletal 
        defaults file.
        """
        repo_path = YAKETY_YAK_REPO_PATH

        if not repo_path.parent.exists():
            repo_path.parent.mkdir(parents=True, exist_ok=True)

        if repo_path.is_file() and repo_path.stat().st_size > 0:
            with open(repo_path, "rb") as f:
                self.yak_repository = orjson.loads(f.read())
            
            matrix_log("UI", "TRANSLATOR", inspect.currentframe().f_code.co_name, 
                       f"📡📥📥 [CONFIG] YAK repository loaded: {repo_path}", 
                       level="DEBUG")
        else:
            # ⚡ RESILIENCE: Handle missing repository with graceful fallback.
            matrix_log("UI", "TRANSLATOR", inspect.currentframe().f_code.co_name, 
                       f"ℹ️ YAK repository missing. Creating default.", 
                       level="INFO")
            self.yak_repository = {}
            try:
                with open(repo_path, "wb") as f:
                    f.write(orjson.dumps({}))
            except Exception as e:
                logger.error(f"❌ Failed to create default YAK repository: {e}")

    def _setup_mqtt_subscriptions(self):
        """Registers the primary MQTT trigger filter for the translator."""
        trigger_topic_filter = "OPEN-AIR/yak/commands/#"
        self.subscriber_router.subscribe_to_topic(
            trigger_topic_filter, self._on_yak_trigger_message
        )
        matrix_log("UI", "TRANSLATOR", inspect.currentframe().f_code.co_name, 
                   f"🎧 [LISTEN] Subscribed to triggers: '{trigger_topic_filter}'", 
                   level="DEBUG")

    def _on_yak_trigger_message(self, msg: MqttMessage):
        """
        Processes incoming MQTT messages to trigger SCPI command generation.
        
        Parses the topic to identify the command path, retrieves the 
        corresponding declaration, renders the final SCPI string using 
        payload parameters, and dispatches it to the Proxy Tx_Inbox.
        
        Args:
            msg: The incoming MqttMessage object containing topic and payload.

        Side Effects:
            - Publishes a translated SCPI payload to 'OPEN-AIR/Proxy/Tx_Inbox'.
            - Updates the internal context store for correlation.
        """
        topic = msg.topic
        payload = msg.payload
        
        # Strip the prefix to resolve the relative YAK path hierarchy.
        yak_command_path = topic.replace("OPEN-AIR/yak/commands/", "").split("/")

        declaration = self._get_command_declaration(yak_command_path)
        if not declaration:
            logger.error(f"❌ Unknown YAK command path: {yak_command_path}")
            return

        # Handle various incoming formats; prefer pre-parsed dict if available.
        payload_parsed = orjson.loads(payload) if isinstance(payload, (bytes, str)) else payload

        scpi_template = declaration.get("scpi_template")
        if not scpi_template:
            logger.error(f"❌ Missing 'scpi_template' for {yak_command_path}")
            return

        final_scpi_command = self._render_scpi_command(scpi_template, payload_parsed)
        if not final_scpi_command:
            return

        is_query = declaration.get("is_query", False)
        # Generate a lightweight 16-bit correlation ID for async tracking.
        correlation_id = f"{random.getrandbits(16):04X}"

        # Persist command context to map instrument responses back to original path.
        self.command_context_store[correlation_id] = {
            "path_parts": yak_command_path,
            "command_details": declaration.get("Outputs", {}),
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
        
        matrix_log("UI", "TRANSLATOR", inspect.currentframe().f_code.co_name, 
                   f"📡📤📤 [TRANSLATE] SCPI: '{final_scpi_command}' "
                   f"(ID: {correlation_id})", level="DEBUG")

    def _get_command_declaration(self, path_parts: list):
        """
        Navigates the internal repository tree to locate a command node.
        
        Args:
            path_parts: Ordered list of keys representing the command path.
            
        Returns:
            dict: The command declaration node if found, otherwise None.
        """
        node = self.yak_repository
        for part in path_parts:
            node = node.get(part)
            if node is None:
                return None
        return node

    def _render_scpi_command(self, scpi_template: str, params: dict):
        """
        Interpolates parameters into a hardware-specific SCPI template.
        
        Args:
            scpi_template: Raw SCPI string containing brace-wrapped tokens.
            params: Key-value pairs for string interpolation.
            
        Returns:
            str: The rendered, ready-to-transmit SCPI command.
        """
        return scpi_template.format(**params)

    def retrieve_command_context(self, correlation_id: str):
        """
        Retrieves and purges context associated with a specific transaction.
        
        Used by the RX manager to bridge instrument responses back to the 
        originating YAK command path and UI state updates.
        
        Args:
            correlation_id: The unique transaction identifier.
            
        Returns:
            dict: The stored context dictionary, or None on ID mismatch.
        """
        if correlation_id in self.command_context_store:
            return self.command_context_store.pop(correlation_id)
        
        logger.error(f"❌ Correlation ID mismatch: {correlation_id}")
        return None
