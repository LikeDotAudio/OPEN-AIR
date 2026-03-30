# Core/state_cache.py
# Author: Anthony Peter Kuzub
# Version: 20260323.1700.1
#
# Description: Modularized State Cache Management.

import time
import orjson
import os
from typing import Any
from loguru import logger

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = False
from oaLogging.Core.logger import data_logger
from oaConfiguration.FileReaders.config_reader import Config
from oaComMQTT.Core.mqtt_message import MqttMessage
app_constants = Config.get_instance()

# --- EXTRACTED CORE MODULES ---
from ..FileReaders import cache_io_handler
from ..Managers import cache_traffic_controller
from ..Methods import gui_state_restorer
from ..FileReaders.cache_io_handler import CacheLoadError
from .cache_save_engine import CacheSaveEngine
from .cache_search_engine import CacheSearchEngine
from .cache_observer_registry import CacheObserverRegistry

class StateRegistry:
    """The central orchestrator for application state caching, persistence, and distribution."""

    def __init__(self, mqtt_connection_manager: Any, state_mirror_engine: Any = None):
        self.mqtt = mqtt_connection_manager
        self.state_mirror_engine = state_mirror_engine
        self.subscriber_router = None
        
        # 1. Initialize Cache & Search
        self.cache = {}
        try: 
            self.cache = cache_io_handler.load_cache()
        except FileNotFoundError:
            if LOCAL_DEBUG: data_logger.info("First boot detected. Starting with fresh cache.")
        except CacheLoadError as e:
            if LOCAL_DEBUG: data_logger.error(f"Critical Cache Corruption: {e}. Starting fresh.")
        except Exception:
            if LOCAL_DEBUG: data_logger.exception("Unexpected error loading cache.")
            
        self.search_engine = CacheSearchEngine()
        self.search_engine.rebuild(self.cache)
        
        # 2. Specialized Engines
        self.save_engine = CacheSaveEngine(self.cache, data_logger, LOCAL_DEBUG)
        self.observers = CacheObserverRegistry()
        
        self._last_log_time, self._updates_since_last_log = time.time(), 0
        if LOCAL_DEBUG: data_logger.debug(f"Initialized with {len(self.cache)} entries.")

    def check_prefix_exists(self, prefix: str) -> bool: return self.search_engine.exists(prefix)
    def register_cache_observer(self, callback: Any): self.observers.register_observer(callback)
    
    def get_cached_value(self, topic: str) -> Any:
        """Retrieves the cached value for a given topic."""
        entry = self.cache.get(topic)
        return entry.get("val") if isinstance(entry, dict) else entry

    def save_preset(self, name: str):
        try:
            from oaOchestration.Core.path_initializer import DATA_RUNNING_DIR
            path = DATA_RUNNING_DIR / "presets" / f"{name}.preset.json"
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as f: f.write(orjson.dumps(self.cache, option=orjson.OPT_INDENT_2))
            if LOCAL_DEBUG: data_logger.success(f"Preset saved: {name}")
            return True
        except Exception as e: data_logger.error(f"Preset failed: {e}"); return False

    def shutdown(self): self.save_engine.shutdown()

    def subscribe_to_all_topics(self):
        """Subscribes to the root command and transmission topic filters."""
        if self.mqtt:
            base = app_constants.MQTT_BASE_TOPIC
            # --- Namespace Split: Subscribe to both Cmd and Tx namespaces ---
            roots = [f"{base}/Cmd/#", f"{base}/Tx/#", f"{base}/System/Status/#", f"{base}/System/Monitor/#"]
            
            for root in roots:
                if LOCAL_DEBUG: data_logger.debug(f"Subscribing to system root: {root}")
                self.mqtt.subscribe(root)

    def initialize_state(self) -> None:
        try:
            self.cache = cache_io_handler.load_cache()
            self.search_engine.rebuild(self.cache)
        except FileNotFoundError:
            if LOCAL_DEBUG: data_logger.info("No cache to initialize.")
            self.cache = {}
        except CacheLoadError as e:
            if LOCAL_DEBUG: data_logger.error(f"Critical Cache Corruption during init: {e}.")
            self.cache = {}
        except Exception: 
            data_logger.exception("State initialization failed")
            self.cache = {}

        if self.cache:
            from oaComBroker.Core.protocol_router.manager import ProtocolRouter
            router = ProtocolRouter.get_instance()
            for topic, payload in self.cache.items():
                val = payload.get("val") if isinstance(payload, dict) else payload
                router.ingest("DISK", topic, val, {"msg_type": "LINK_FEEDBACK", "is_settled": True, "origin_source": "DISK", "boot": True})
            gui_state_restorer.restore_timeline(self.cache, self.state_mirror_engine)

    def handle_external_update(self, topic: str, value: Any, source: str = "EXTERNAL", metadata: dict = None):
        # ⚡ FIX: Corrected import path to include .Core
        from oaTranslator.Core.manifest.builder import create_manifest
        payload = create_manifest(value, topic, source, metadata)
        
        self.cache[topic] = payload
        self.save_engine.schedule_save(topic, payload); self.search_engine.add_topic(topic)
        
        from oaComBroker.Core.protocol_router.manager import ProtocolRouter
        # The ProtocolRouter is responsible for outbound dispatch (MQTT, OSC, etc.)
        ProtocolRouter.get_instance().ingest(source, topic, value, payload)

        self.observers.notify(topic, payload)

    def _parse_mqtt_payload(self, msg: MqttMessage):
        """Standardizes MQTT payload extraction into source, value, and metadata."""
        raw = msg.get_json_payload()
        source, value, metadata = "MQTT", raw, {}
        
        if isinstance(raw, dict):
            # Check if this follows the standard Unified Message Schema (Splinker Manifest)
            if "val" in raw or "value" in raw:
                source = str(raw.get("source", "MQTT")).upper()
                value = raw.get("val") if "val" in raw else raw.get("value")
                metadata = raw.copy()
                # Preserve standard fields
                for field in ["msg_type", "msg_guid", "origin_source", "is_settled", "full_id", "boot"]:
                    if field in raw: metadata[field] = raw[field]
            else:
                # This is a raw JSON dictionary (e.g. device inventory blob)
                # Treat the entire dictionary as the value.
                value = raw
                source = "MQTT"
                metadata = {}
        
        return source, value, metadata, raw

    def _update_cache_entry(self, topic, payload):
        """Updates internal cache and schedules persistence."""
        self.cache[topic] = payload
        self.search_engine.add_topic(topic)
        self.save_engine.schedule_save(topic, payload)
        self._updates_since_last_log += 1
        
        if time.time() - self._last_log_time >= 5.0:
            if LOCAL_DEBUG: data_logger.success(f"State synced: {self._updates_since_last_log} variables.")
            self._last_log_time, self._updates_since_last_log = time.time(), 0

    def handle_incoming_mqtt(self, client, userdata, msg: MqttMessage) -> None:
        topic = msg.topic
        
        # --- Namespace Split: Strip CMD or TX from incoming topic ---
        base = app_constants.MQTT_BASE_TOPIC
        normalized = False
        if f"{base}/Cmd/" in topic:
            topic = topic.replace(f"{base}/Cmd/", f"{base}/")
            normalized = True
        elif f"{base}/Tx/" in topic:
            topic = topic.replace(f"{base}/Tx/", f"{base}/")
            normalized = True

        if normalized:
            # Create a NEW MqttMessage with the stripped topic for downstream consumption
            msg = MqttMessage(
                topic=topic,
                payload=msg.payload,
                qos=msg.qos,
                retain=msg.retain
            )
            
        if self.subscriber_router: 
            self.subscriber_router._on_message(client, userdata, msg)
            
        try:
            source, value, metadata, raw_payload = self._parse_mqtt_payload(msg)

            from oaComBroker.Core.protocol_router.manager import ProtocolRouter
            ProtocolRouter.get_instance().ingest("MQTT", topic, value, metadata)
            self.observers.notify(topic, raw_payload)

            should_process, new_payload = cache_traffic_controller.process_traffic(msg, self.cache)
            if should_process:
                self._update_cache_entry(topic, new_payload)
                
        except Exception: 
            data_logger.exception(f"Error handling MQTT for {topic}")
